"""Live stream metric collection."""

import logging

from .shared import CHANNEL_KEY_PREFIX, ChannelMetadataField, labels

logger = logging.getLogger(__name__)

def collect(context, families, totals):
    from apps.channels.models import Channel, Stream
    from apps.m3u.models import M3UAccountProfile

    settings = context.settings
    try:
        for key in context.redis_client.scan_iter(match="channel_stream:*"):
            totals["all"] += 1
            totals["live"] += 1

            try:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                channel_id = key_str.split(':', 1)[1]

                stream_id = context.redis_client.get(key)
                if stream_id:
                    stream_id = int(stream_id.decode('utf-8') if isinstance(stream_id, bytes) else stream_id)

                    try:
                        channel = Channel.objects.select_related('logo', 'channel_group').get(id=int(channel_id))
                        channel_uuid = str(channel.uuid)
                        channel_name = channel.name
                        channel_number = getattr(channel, 'channel_number', 'N/A')
                        channel_group = channel.channel_group.name if channel.channel_group else "none"

                        logo_url = ""
                        if hasattr(channel, 'logo') and channel.logo:
                            logo_path = f"/api/channels/logos/{channel.logo.id}/cache/"
                            base_url = settings.get('base_url', '').strip()
                            if base_url:
                                logo_url = f"{base_url.rstrip('/')}{logo_path}"
                            else:
                                logo_url = logo_path
                        logo_url = logo_url

                        metadata_key = f"{CHANNEL_KEY_PREFIX}:channel:{channel_uuid}:metadata"
                        metadata = context.redis_client.hgetall(metadata_key) or {}

                        def get_metadata(field, default="0"):
                            val = metadata.get(field)
                            if val is None:
                                return default
                            return str(val)

                        active_stream_id_str = get_metadata(ChannelMetadataField.STREAM_ID, None)
                        if active_stream_id_str and active_stream_id_str != '0':
                            try:
                                stream_id = int(active_stream_id_str)
                            except (ValueError, TypeError):
                                logger.debug(f"Invalid active stream ID in metadata: {active_stream_id_str}")

                        init_time = float(get_metadata(ChannelMetadataField.INIT_TIME, '0'))
                        uptime_seconds = int(context.timestamp - init_time) if init_time > 0 else 0

                        stream_profile_id = get_metadata(ChannelMetadataField.STREAM_PROFILE, '0')
                        stream_profile_name = 'Unknown'
                        if stream_profile_id and stream_profile_id != '0':
                            try:
                                from core.models import StreamProfile
                                profile = StreamProfile.objects.get(id=int(stream_profile_id))
                                stream_profile_name = profile.name
                            except Exception:
                                stream_profile_name = f'Profile-{stream_profile_id}'
                        else:
                            try:
                                sp = channel.get_stream_profile()
                                if sp:
                                    stream_profile_name = sp.name
                            except Exception:
                                pass

                        video_codec = get_metadata(ChannelMetadataField.VIDEO_CODEC, 'unknown')
                        resolution = get_metadata(ChannelMetadataField.RESOLUTION, 'unknown')
                        source_fps = get_metadata(ChannelMetadataField.SOURCE_FPS, '0')
                        video_bitrate = get_metadata(ChannelMetadataField.VIDEO_BITRATE, '0')
                        ffmpeg_output_bitrate = get_metadata(ChannelMetadataField.FFMPEG_OUTPUT_BITRATE, '0')
                        ffmpeg_speed = get_metadata(ChannelMetadataField.FFMPEG_SPEED, '0')

                        total_bytes = int(get_metadata(ChannelMetadataField.TOTAL_BYTES, '0'))
                        total_mb = round(total_bytes / 1024 / 1024, 2)
                        avg_bitrate_bps = round((total_bytes * 8 / uptime_seconds), 2) if uptime_seconds > 0 else 0

                        client_set_key = f"{CHANNEL_KEY_PREFIX}:channel:{channel_uuid}:clients"
                        active_clients = context.redis_client.scard(client_set_key) or 0

                        current_bitrate_bps = 0.0
                        try:
                            client_ids = context.redis_client.smembers(client_set_key)
                            for client_id_bytes in client_ids:
                                try:
                                    client_id = client_id_bytes.decode('utf-8') if isinstance(client_id_bytes, bytes) else client_id_bytes
                                    client_key = f"{CHANNEL_KEY_PREFIX}:channel:{channel_uuid}:clients:{client_id}"
                                    client_data = context.redis_client.hgetall(client_key)
                                    if client_data and 'current_rate_KBps' in client_data:
                                        current_rate_kb = float(client_data['current_rate_KBps'])
                                        if current_rate_kb > 50000:
                                            current_bitrate_bps += current_rate_kb * 8
                                        else:
                                            current_bitrate_bps += current_rate_kb * 8000
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        state = get_metadata(ChannelMetadataField.STATE, 'unknown')

                        try:
                            stream = Stream.objects.select_related('m3u_account').get(id=stream_id)
                            stream_name = stream.name
                            provider = stream.m3u_account.name if stream.m3u_account else "Unknown"
                            stream_type = stream.m3u_account.account_type if stream.m3u_account else "Unknown"

                            stream_index = 0
                            try:
                                from apps.channels.models import ChannelStream
                                channel_stream = ChannelStream.objects.get(channel_id=channel.id, stream_id=stream_id)
                                stream_index = channel_stream.order
                            except Exception:
                                pass

                            profile_id = None
                            profile_name = "Unknown"
                            profile_connections = 0
                            profile_max = 0

                            m3u_profile_id = get_metadata(ChannelMetadataField.M3U_PROFILE, None)
                            if not m3u_profile_id or m3u_profile_id == '0':
                                try:
                                    raw = context.redis_client.get(f"stream_profile:{stream_id}")
                                    if raw:
                                        m3u_profile_id = raw.decode('utf-8') if isinstance(raw, bytes) else str(raw)
                                except Exception:
                                    pass
                            if m3u_profile_id and m3u_profile_id != '0':
                                try:
                                    profile_id = int(m3u_profile_id)
                                    active_profile = M3UAccountProfile.objects.get(id=profile_id)
                                    profile_name = active_profile.name
                                    profile_connections = int(context.redis_client.get(f"profile_connections:{profile_id}") or 0)
                                    profile_max = active_profile.max_streams
                                except Exception as e:
                                    logger.debug(f"Error getting M3U profile {profile_id}: {e}")

                            base_labels = [
                                ("type", "live"),
                                ("channel_uuid", channel_uuid),
                                ("channel_number", channel_number),
                            ]

                            try:
                                channel_number_value = float(channel_number)
                            except (ValueError, TypeError):
                                channel_number_value = 0.0

                            metadata_labels = base_labels + [
                                ("channel_name", channel_name),
                                ("channel_group", channel_group),
                                ("stream_id", stream_id),
                                ("stream_name", stream_name),
                                ("provider", provider),
                                ("provider_type", stream_type),
                                ("state", state),
                                ("logo_url", logo_url),
                                ("profile_id", profile_id if profile_id else "none"),
                                ("profile_name", profile_name),
                                ("stream_profile", stream_profile_name),
                                ("video_codec", video_codec),
                                ("resolution", resolution),
                            ]

                            families["dispatcharr_stream_index"].add(stream_index, labels(base_labels))
                            families["dispatcharr_stream_available_streams"].add(channel.streams.count(), labels(base_labels))
                            families["dispatcharr_stream_channel_number"].add(channel_number_value, labels(base_labels))
                            families["dispatcharr_stream_id"].add(stream_id, labels(base_labels))

                            families["dispatcharr_stream_uptime_seconds"].add(uptime_seconds, labels(base_labels))
                            families["dispatcharr_stream_active_clients"].add(active_clients, labels(base_labels))

                            if source_fps and source_fps != '0':
                                families["dispatcharr_stream_fps"].add(source_fps, labels(base_labels))

                            if ffmpeg_speed and ffmpeg_speed != '0':
                                try:
                                    speed_value = float(ffmpeg_speed.rstrip('x'))
                                    families["dispatcharr_stream_buffering_speed"].add(speed_value, labels(base_labels))
                                except (ValueError, AttributeError):
                                    pass

                            if video_bitrate and video_bitrate != '0':
                                families["dispatcharr_stream_video_bitrate_bps"].add(float(video_bitrate) * 1000, labels(base_labels))
                            if ffmpeg_output_bitrate and ffmpeg_output_bitrate != '0':
                                families["dispatcharr_stream_transcode_bitrate_bps"].add(float(ffmpeg_output_bitrate) * 1000, labels(base_labels))
                            if avg_bitrate_bps > 0:
                                families["dispatcharr_stream_avg_bitrate_bps"].add(avg_bitrate_bps, labels(base_labels))
                            if current_bitrate_bps > 0:
                                families["dispatcharr_stream_current_bitrate_bps"].add(current_bitrate_bps, labels(base_labels))
                            if total_mb > 0:
                                families["dispatcharr_stream_total_transfer_mb"].add(total_mb, labels(base_labels))

                            if profile_id:
                                families["dispatcharr_stream_profile_connections"].add(profile_connections, labels(base_labels))
                                families["dispatcharr_stream_profile_max_connections"].add(profile_max, labels(base_labels))

                            families["dispatcharr_stream_metadata"].add(1, labels(metadata_labels))

                            # EPG program data
                            if hasattr(channel, 'epg_data') and channel.epg_data:
                                try:
                                    from apps.epg.models import ProgramData
                                    from django.utils import timezone as django_timezone

                                    now = django_timezone.now()

                                    current_program = ProgramData.objects.filter(
                                        epg=channel.epg_data,
                                        start_time__lte=now,
                                        end_time__gte=now,
                                    ).first()
                                    previous_program = ProgramData.objects.filter(
                                        epg=channel.epg_data,
                                        end_time__lt=now,
                                    ).order_by('-end_time').first()
                                    next_program = ProgramData.objects.filter(
                                        epg=channel.epg_data,
                                        start_time__gt=now,
                                    ).order_by('start_time').first()

                                    def format_program_data(program, prefix):
                                        if not program:
                                            return [
                                                (f"{prefix}_title", ""),
                                                (f"{prefix}_subtitle", ""),
                                                (f"{prefix}_description", ""),
                                                (f"{prefix}_start_time", ""),
                                                (f"{prefix}_end_time", ""),
                                            ]

                                        return [
                                            (f"{prefix}_title", program.title),
                                            (f"{prefix}_subtitle", program.sub_title),
                                            (f"{prefix}_description", program.description),
                                            (f"{prefix}_start_time", program.start_time.isoformat()),
                                            (f"{prefix}_end_time", program.end_time.isoformat()),
                                        ]

                                    if previous_program or current_program or next_program:
                                        epg_labels = base_labels.copy()
                                        epg_labels.extend(format_program_data(previous_program, 'previous'))
                                        epg_labels.extend(format_program_data(current_program, 'current'))
                                        epg_labels.extend(format_program_data(next_program, 'next'))

                                        progress = 0.0
                                        if current_program:
                                            total_duration = (current_program.end_time - current_program.start_time).total_seconds()
                                            elapsed = (now - current_program.start_time).total_seconds()
                                            progress = min(1.0, max(0.0, elapsed / total_duration)) if total_duration > 0 else 0.0

                                        families["dispatcharr_stream_programming"].add(progress, labels(epg_labels))
                                except Exception as e:
                                    logger.debug(f"Error fetching EPG program for channel {channel_id}: {e}")

                        except Stream.DoesNotExist:
                            logger.debug(f"Stream {stream_id} not found in database")

                    except Channel.DoesNotExist:
                        logger.debug(f"Channel {channel_id} not found in database")

            except Exception as e:
                logger.debug(f"Error processing stream key {key}: {e}")

    except Exception as e:
        logger.debug(f"Error scanning stream keys: {e}")
