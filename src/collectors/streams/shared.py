"""Shared stream metric families and label helpers."""

import logging

try:
    from apps.proxy.live_proxy.constants import ChannelMetadataField
    CHANNEL_KEY_PREFIX = "live"
except ImportError:
    from apps.proxy.ts_proxy.constants import ChannelMetadataField
    CHANNEL_KEY_PREFIX = "ts_proxy"

logger = logging.getLogger(__name__)


def stream_families(writer):
    families = {
        "dispatcharr_active_streams": writer.gauge("dispatcharr_active_streams", 'Total number of active streams (live, VOD, and timeshift)'),
        "dispatcharr_stream_channel_number": writer.gauge("dispatcharr_stream_channel_number", 'Channel number for active stream (live only)'),
        "dispatcharr_stream_id": writer.gauge("dispatcharr_stream_id", 'Active stream ID for channel or session ID for VOD'),
        "dispatcharr_stream_index": writer.gauge("dispatcharr_stream_index", 'Active stream index for channel (0=primary, >0=fallback) (live only)'),
        "dispatcharr_stream_available_streams": writer.gauge("dispatcharr_stream_available_streams", 'Total number of streams configured for channel (live only)'),
        "dispatcharr_stream_metadata": writer.gauge("dispatcharr_stream_metadata", 'Stream metadata (type: live/vod/timeshift, state values: active, paused, waiting_for_clients, buffering, stopping, error, unknown)'),
        "dispatcharr_stream_programming": writer.gauge("dispatcharr_stream_programming", 'Current EPG program information for active streams (live and timeshift; timeshift current_title is prefixed \"Catchup-MM-DD-HH:MM: \")'),
        "dispatcharr_stream_uptime_seconds": writer.counter("dispatcharr_stream_uptime_seconds", 'Stream uptime in seconds since stream started'),
        "dispatcharr_stream_active_clients": writer.gauge("dispatcharr_stream_active_clients", 'Number of active clients connected to stream'),
        "dispatcharr_stream_video_bitrate_bps": writer.gauge("dispatcharr_stream_video_bitrate_bps", 'Video bitrate in bits per second'),
        "dispatcharr_stream_transcode_bitrate_bps": writer.gauge("dispatcharr_stream_transcode_bitrate_bps", 'Transcode output bitrate in bits per second'),
        "dispatcharr_stream_avg_bitrate_bps": writer.gauge("dispatcharr_stream_avg_bitrate_bps", 'Average bitrate in bits per second'),
        "dispatcharr_stream_current_bitrate_bps": writer.gauge("dispatcharr_stream_current_bitrate_bps", 'Current bitrate in bits per second (sum of all client rates)'),
        "dispatcharr_stream_total_transfer_mb": writer.counter("dispatcharr_stream_total_transfer_mb", 'Total data transferred in megabytes'),
        "dispatcharr_stream_fps": writer.gauge("dispatcharr_stream_fps", 'Stream frames per second'),
        "dispatcharr_stream_buffering_speed": writer.gauge("dispatcharr_stream_buffering_speed", 'Stream buffering speed multiplier (e.g., 1.0 = realtime, 2.0 = 2x speed)'),
        "dispatcharr_stream_profile_connections": writer.gauge("dispatcharr_stream_profile_connections", 'Current connections for the M3U profile used by this stream'),
        "dispatcharr_stream_profile_max_connections": writer.gauge("dispatcharr_stream_profile_max_connections", 'Maximum connections allowed for the M3U profile'),
    }
    return families


def labels(labels):
    """Return explicitly ordered label pairs for a stream sample."""
    return labels
