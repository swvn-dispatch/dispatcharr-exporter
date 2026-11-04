"""Timeshift stream metric collection."""

import logging

from .shared import CHANNEL_KEY_PREFIX, ChannelMetadataField, labels

logger = logging.getLogger(__name__)

def collect(context, families, totals):
    from apps.channels.models import Channel
    from apps.m3u.models import M3UAccountProfile

    settings = context.settings
    try:
        _ts_channel_cache = {}

        def _resolve_ts_channel(channel_id):
            if channel_id not in _ts_channel_cache:
                try:
                    _ts_channel_cache[channel_id] = Channel.objects.select_related('channel_group', 'logo').get(id=channel_id)
                except Exception:
                    _ts_channel_cache[channel_id] = None
            return _ts_channel_cache[channel_id]

        for session in (context.timeshift_data or {}).get('timeshift_sessions', []):
            try:
                totals["all"] += 1
                totals["timeshift"] += 1

                channel_id = session.get('channel_id')
                channel = _resolve_ts_channel(channel_id)
                channel_number = getattr(channel, 'channel_number', 'N/A') if channel else 'N/A'
                channel_group = channel.channel_group.name if channel and channel.channel_group else 'none'

                logo_url = ""
                if channel and getattr(channel, 'logo', None):
                    logo_path = f"/api/channels/logos/{channel.logo.id}/cache/"
                    base_url = (settings or {}).get('base_url', '').strip()
                    logo_url = f"{base_url.rstrip('/')}{logo_path}" if base_url else logo_path

                stats_channel_id = session.get('stats_channel_id', '')
                real_channel_uuid = session.get('channel_uuid', '')
                session_id = session.get('session_id', '')
                channel_name = session.get('channel_name', 'Catch-up')

                base_labels = [
                    ("type", "timeshift"),
                    ("channel_uuid", stats_channel_id),
                    ("channel_number", channel_number),
                ]

                try:
                    channel_number_value = float(channel_number)
                except (ValueError, TypeError):
                    channel_number_value = 0.0

                state = "paused" if session.get('paused') else "active"

                metadata_labels = base_labels + [
                    ("channel_name", channel_name),
                    ("channel_group", channel_group),
                    ("real_channel_uuid", real_channel_uuid),
                    ("session_id", session_id),
                    ("state", state),
                    ("logo_url", logo_url),
                    ("video_codec", session.get("video_codec", "")),
                    ("resolution", session.get("resolution", "")),
                    ("audio_codec", session.get("audio_codec", "")),
                    ("stream_type", session.get("stream_type", "")),
                ]

                connections = session.get('connections', [])

                # ── Active provider/profile (from the first connection's
                # upstream M3U profile, same as live's single-active-stream model) ──
                provider = "Unknown"
                provider_type = "Unknown"
                profile_id = None
                profile_name = "Unknown"
                profile_connections_count = 0
                profile_max = 0

                if connections:
                    m3u_profile_id = connections[0].get('m3u_profile_id')
                    if m3u_profile_id:
                        try:
                            profile_id = int(m3u_profile_id)
                            active_profile = M3UAccountProfile.objects.select_related('m3u_account').get(id=profile_id)
                            profile_name = active_profile.name
                            if active_profile.m3u_account:
                                provider = active_profile.m3u_account.name
                                provider_type = active_profile.m3u_account.account_type
                            profile_max = active_profile.max_streams
                            if context.redis_client:
                                profile_connections_count = int(context.redis_client.get(f"profile_connections:{profile_id}") or 0)
                        except Exception as e:
                            logger.debug(f"Error getting timeshift M3U profile {m3u_profile_id}: {e}")

                metadata_labels += [
                    ("provider", provider),
                    ("provider_type", provider_type),
                    ("profile_id", profile_id if profile_id else "none"),
                    ("profile_name", profile_name),
                ]

                families["dispatcharr_stream_channel_number"].add(channel_number_value, labels(base_labels))
                families["dispatcharr_stream_active_clients"].add(session.get("connection_count", len(connections)), labels(base_labels))

                if profile_id:
                    families["dispatcharr_stream_profile_connections"].add(profile_connections_count, labels(base_labels))
                    families["dispatcharr_stream_profile_max_connections"].add(profile_max, labels(base_labels))

                if connections:
                    connected_ats = [c.get('connected_at') for c in connections if c.get('connected_at')]
                    if connected_ats:
                        uptime_seconds = max(0, int(context.timestamp - min(connected_ats)))
                        families["dispatcharr_stream_uptime_seconds"].add(uptime_seconds, labels(base_labels))

                    avg_bitrate_bps = (connections[0].get('avg_bitrate_kbps') or 0) * 1000
                    if avg_bitrate_bps > 0:
                        families["dispatcharr_stream_avg_bitrate_bps"].add(avg_bitrate_bps, labels(base_labels))

                families["dispatcharr_stream_metadata"].add(1, labels(metadata_labels))

                # ── EPG programming, anchored to the requested catch-up
                # position (not real time) ──────────────────────────
                programme_start_raw = session.get('programme_start')
                if programme_start_raw and channel and getattr(channel, 'epg_data', None):
                    try:
                        from apps.timeshift.helpers import parse_catchup_timestamp
                        from apps.epg.models import ProgramData
                        from datetime import timezone as dt_timezone

                        anchor_naive = parse_catchup_timestamp(programme_start_raw)
                        if anchor_naive:
                            anchor_dt = anchor_naive.replace(tzinfo=dt_timezone.utc)
                            anchor_str = anchor_dt.strftime('%m-%d-%H:%M')

                            current_program = ProgramData.objects.filter(
                                epg=channel.epg_data,
                                start_time__lte=anchor_dt,
                                end_time__gte=anchor_dt,
                            ).first()
                            previous_program = ProgramData.objects.filter(
                                epg=channel.epg_data,
                                end_time__lt=anchor_dt,
                            ).order_by('-end_time').first()
                            next_program = ProgramData.objects.filter(
                                epg=channel.epg_data,
                                start_time__gt=anchor_dt,
                            ).order_by('start_time').first()

                            def _format_ts_program(program, prefix, title_prefix=""):
                                if not program:
                                    return [
                                        (f"{prefix}_title", ""),
                                        (f"{prefix}_subtitle", ""),
                                        (f"{prefix}_description", ""),
                                        (f"{prefix}_start_time", ""),
                                        (f"{prefix}_end_time", ""),
                                    ]
                                title = f"{title_prefix}{program.title}" if title_prefix else program.title
                                return [
                                    (f"{prefix}_title", title),
                                    (f"{prefix}_subtitle", program.sub_title),
                                    (f"{prefix}_description", program.description),
                                    (f"{prefix}_start_time", program.start_time.isoformat()),
                                    (f"{prefix}_end_time", program.end_time.isoformat()),
                                ]

                            if previous_program or current_program or next_program:
                                epg_labels = base_labels.copy()
                                epg_labels.extend(_format_ts_program(previous_program, 'previous'))
                                epg_labels.extend(_format_ts_program(current_program, 'current', title_prefix=f"Catchup-{anchor_str}: "))
                                epg_labels.extend(_format_ts_program(next_program, 'next'))

                                progress = 0.0
                                if current_program:
                                    total_duration = (current_program.end_time - current_program.start_time).total_seconds()
                                    elapsed = (anchor_dt - current_program.start_time).total_seconds()
                                    progress = min(1.0, max(0.0, elapsed / total_duration)) if total_duration > 0 else 0.0

                                families["dispatcharr_stream_programming"].add(progress, labels(epg_labels))
                    except Exception as e:
                        logger.debug(f"Error fetching EPG program for timeshift channel {channel_id}: {e}")

            except Exception as e:
                logger.debug(f"Error processing timeshift session {session.get('session_id')}: {e}")

    except Exception as e:
        logger.debug(f"Error collecting timeshift stream metrics: {e}")
