"""Vod stream metric collection."""

import logging

from .shared import CHANNEL_KEY_PREFIX, ChannelMetadataField, labels

logger = logging.getLogger(__name__)

def collect(context, families, totals):
    from apps.m3u.models import M3UAccountProfile

    settings = context.settings
    try:
        from apps.vod.models import Movie, Episode
        import re as _re

        for key in context.redis_client.scan_iter(match="vod_persistent_connection:*"):
            try:
                connection_data = context.redis_client.hgetall(key)
                if not connection_data:
                    continue

                if isinstance(list(connection_data.keys())[0], bytes):
                    def get_vod_field(field_name, default=''):
                        val = connection_data.get(
                            field_name.encode('utf-8') if isinstance(field_name, str) else field_name,
                            b'',
                        )
                        return val.decode('utf-8') if isinstance(val, bytes) else default
                else:
                    def get_vod_field(field_name, default=''):
                        return connection_data.get(field_name, default)

                active_stream_count = int(get_vod_field('active_streams', '0'))
                if active_stream_count == 0:
                    continue

                totals["all"] += 1
                totals["vod"] += 1

                session_id = key.decode('utf-8') if isinstance(key, bytes) else key
                session_id = session_id.replace('vod_persistent_connection:', '')

                try:
                    session_parts = session_id.split('_')
                    vod_channel_number = session_parts[1] if len(session_parts) >= 2 else session_id
                except Exception:
                    vod_channel_number = session_id

                content_type = get_vod_field('content_obj_type', 'unknown')
                content_uuid = get_vod_field('content_uuid', '')
                content_name = get_vod_field('content_name', 'Unknown')
                m3u_profile_id_str = get_vod_field('m3u_profile_id', '')

                logo_url = ""
                video_codec = ""
                resolution = ""
                stream_profile_name = ""
                season_number = None
                episode_number = None
                series_name = None
                channel_group = ""

                prog_title = ""
                prog_subtitle = ""
                prog_description = ""
                prog_year = ""
                prog_genre = ""
                prog_duration_secs = 0

                try:
                    if content_type == 'movie':
                        from apps.vod.models import M3UMovieRelation
                        content_obj = Movie.objects.select_related('logo').get(uuid=content_uuid)
                        if hasattr(content_obj, 'logo') and content_obj.logo:
                            logo_url = f"/api/vod/vodlogos/{content_obj.logo.id}/cache/"
                            base_url = settings.get('base_url', '').strip() if settings else ''
                            if base_url:
                                logo_url = f"{base_url.rstrip('/')}{logo_url}"
                        if content_obj.custom_properties:
                            video_info = content_obj.custom_properties.get('video', {})
                            if video_info:
                                video_codec = video_info.get('codec_name', '')
                                width = video_info.get('width')
                                height = video_info.get('height')
                                if width and height:
                                    resolution = f"{width}x{height}"
                        content_name = content_obj.name
                        prog_title = content_obj.name
                        prog_description = content_obj.description or ""
                        prog_year = str(content_obj.year) if content_obj.year else ""
                        prog_genre = content_obj.genre or ""
                        prog_duration_secs = content_obj.duration_secs or 0
                        if prog_year:
                            for pattern in [f" ({prog_year})", f" - {prog_year}", f" {prog_year}"]:
                                if prog_title.endswith(pattern):
                                    prog_title = prog_title[:-len(pattern)].strip()
                                    break
                        subtitle_parts = []
                        if prog_year:
                            subtitle_parts.append(prog_year)
                        if prog_genre:
                            subtitle_parts.append(prog_genre)
                        prog_subtitle = " - ".join(subtitle_parts)
                        if m3u_profile_id_str:
                            try:
                                relation = M3UMovieRelation.objects.select_related('category').filter(
                                    movie=content_obj,
                                    m3u_account__profiles__id=int(m3u_profile_id_str),
                                ).first()
                                if relation and relation.category:
                                    channel_group = relation.category.name
                            except Exception:
                                pass

                    elif content_type == 'episode':
                        from apps.vod.models import M3USeriesRelation
                        content_obj = Episode.objects.select_related('series', 'series__logo').get(uuid=content_uuid)
                        season_number = content_obj.season_number
                        episode_number = content_obj.episode_number
                        if content_obj.series:
                            content_name = content_obj.series.name
                            series_name = content_obj.series.name
                        if hasattr(content_obj.series, 'logo') and content_obj.series.logo:
                            logo_url = f"/api/vod/vodlogos/{content_obj.series.logo.id}/cache/"
                            base_url = settings.get('base_url', '').strip() if settings else ''
                            if base_url:
                                logo_url = f"{base_url.rstrip('/')}{logo_url}"
                        if content_obj.custom_properties:
                            video_info = content_obj.custom_properties.get('video', {})
                            if video_info:
                                video_codec = video_info.get('codec_name', 'unknown')
                                width = video_info.get('width')
                                height = video_info.get('height')
                                if width and height:
                                    resolution = f"{width}x{height}"
                        prog_title = content_obj.series.name if content_obj.series else ""
                        prog_description = content_obj.description or ""
                        prog_duration_secs = content_obj.duration_secs or 0
                        prog_subtitle = content_obj.name
                        if prog_title and prog_subtitle.startswith(prog_title):
                            prog_subtitle = prog_subtitle[len(prog_title):].lstrip(' -')
                        series_name_no_year = prog_title
                        if prog_title:
                            match = _re.search(r'\s*\(\d{4}\)$', prog_title)
                            if match:
                                series_name_no_year = prog_title[:match.start()].strip()
                        if series_name_no_year and prog_subtitle.startswith(series_name_no_year):
                            prog_subtitle = prog_subtitle[len(series_name_no_year):].lstrip(' -')
                        logger.debug(f"VOD Episode programming: title='{prog_title}', subtitle='{prog_subtitle}', duration={prog_duration_secs}")
                        if m3u_profile_id_str and content_obj.series:
                            try:
                                relation = M3USeriesRelation.objects.select_related('category').filter(
                                    series=content_obj.series,
                                    m3u_account__profiles__id=int(m3u_profile_id_str),
                                ).first()
                                if relation and relation.category:
                                    channel_group = relation.category.name
                            except Exception:
                                pass

                except (Movie.DoesNotExist, Episode.DoesNotExist):
                    logger.debug(f"VOD content {content_type} {content_uuid} not found in database")
                except Exception as e:
                    logger.error(f"Error querying VOD content metadata for {content_uuid}: {e}", exc_info=True)

                content_name = content_name
                logo_url = logo_url

                profile_id = None
                profile_name = ""
                profile_connections = 0
                profile_max = 0
                provider_name = ""
                provider_type = ""

                if m3u_profile_id_str:
                    try:
                        profile_id = int(m3u_profile_id_str)
                        active_profile = M3UAccountProfile.objects.get(id=profile_id)
                        profile_name = active_profile.name
                        provider_name = active_profile.m3u_account.name
                        provider_type = active_profile.m3u_account.account_type
                        profile_connections = int(context.redis_client.get(f"profile_connections:{profile_id}") or 0)
                        profile_max = active_profile.max_streams
                    except Exception as e:
                        logger.debug(f"Error getting VOD M3U profile {m3u_profile_id_str}: {e}")

                created_at = float(get_vod_field('created_at', '0'))
                uptime_seconds = int(context.timestamp - created_at) if created_at > 0 else 0
                bytes_sent = int(get_vod_field('bytes_sent', '0'))
                total_mb = round(bytes_sent / 1024 / 1024, 2)
                avg_bitrate_bps = round((bytes_sent * 8 / uptime_seconds), 2) if uptime_seconds > 0 else 0
                active_clients = active_stream_count

                base_labels = [
                    ("type", "vod"),
                    ("channel_uuid", session_id),
                    ("channel_number", vod_channel_number),
                ]

                metadata_labels = base_labels + [
                    ("content_uuid", content_uuid),
                    ("channel_name", content_name),
                    ("channel_group", channel_group),
                    ("content_type", content_type),
                    ("provider", provider_name),
                    ("provider_type", provider_type),
                    ("state", "active"),
                    ("logo_url", logo_url),
                    ("profile_id", profile_id if profile_id else "none"),
                    ("profile_name", profile_name),
                    ("stream_profile", stream_profile_name),
                    ("video_codec", video_codec),
                    ("resolution", resolution),
                ]

                if content_type == 'episode' and season_number is not None and episode_number is not None:
                    metadata_labels.append(("season_number", season_number))
                    metadata_labels.append(("episode_number", episode_number))
                    if series_name:
                        metadata_labels.append(("series_name", series_name))

                families["dispatcharr_stream_id"].add(0, labels(base_labels))
                families["dispatcharr_stream_metadata"].add(1, labels(metadata_labels))
                families["dispatcharr_stream_uptime_seconds"].add(uptime_seconds, labels(base_labels))
                families["dispatcharr_stream_active_clients"].add(active_clients, labels(base_labels))

                if avg_bitrate_bps > 0:
                    families["dispatcharr_stream_avg_bitrate_bps"].add(avg_bitrate_bps, labels(base_labels))
                if total_mb > 0:
                    families["dispatcharr_stream_total_transfer_mb"].add(total_mb, labels(base_labels))
                if profile_id:
                    families["dispatcharr_stream_profile_connections"].add(profile_connections, labels(base_labels))
                    families["dispatcharr_stream_profile_max_connections"].add(profile_max, labels(base_labels))

                # VOD programming metric
                logger.debug(f"VOD Programming check for {session_id}: prog_title='{prog_title}', prog_description='{prog_description[:50] if prog_description else ''}'")
                if prog_title or prog_description:
                    try:
                        from datetime import datetime, timezone, timedelta

                        logger.debug(f"Entering programming metric generation for {session_id}")

                        prog_title_safe = prog_title
                        prog_subtitle_safe = prog_subtitle
                        prog_description_safe = prog_description

                        prog_start_time = ""
                        prog_end_time = ""
                        if created_at > 0:
                            start_dt = datetime.fromtimestamp(created_at, tz=timezone.utc)
                            prog_start_time = start_dt.isoformat()
                            if prog_duration_secs > 0:
                                prog_end_time = (start_dt + timedelta(seconds=prog_duration_secs)).isoformat()

                        programming_labels = base_labels + [
                            ("previous_title", ""),
                            ("previous_subtitle", ""),
                            ("previous_description", ""),
                            ("previous_start_time", ""),
                            ("previous_end_time", ""),
                            ("current_title", prog_title_safe),
                            ("current_subtitle", prog_subtitle_safe),
                            ("current_description", prog_description_safe),
                            ("current_start_time", prog_start_time),
                            ("current_end_time", prog_end_time),
                            ("next_title", ""),
                            ("next_subtitle", ""),
                            ("next_description", ""),
                            ("next_start_time", ""),
                            ("next_end_time", ""),
                        ]

                        progress = 0.0
                        if prog_duration_secs > 0 and uptime_seconds > 0:
                            progress = min(1.0, max(0.0, uptime_seconds / prog_duration_secs))

                        families["dispatcharr_stream_programming"].add(progress, labels(programming_labels))
                        logger.debug(f"Programming metric appended for {session_id}")
                    except Exception as prog_e:
                        logger.error(f"Error generating programming metric for {session_id}: {prog_e}", exc_info=True)

            except Exception as e:
                logger.debug(f"Error processing VOD connection key {key}: {e}")

    except Exception as e:
        logger.debug(f"Error scanning VOD connection keys: {e}")
