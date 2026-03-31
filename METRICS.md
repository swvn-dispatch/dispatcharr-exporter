# Dispatcharr Exporter Metrics Reference

Complete reference for all metrics exposed by the Dispatcharr Prometheus Exporter plugin.

## Table of Contents

- [Core Metrics](#core-metrics)
- [Exporter Metrics](#exporter-metrics)
- [M3U Account Metrics](#m3u-account-metrics)
- [EPG Source Metrics](#epg-source-metrics)
- [Channel Metrics](#channel-metrics)
- [Stream Metrics](#stream-metrics)
- [Profile Metrics](#profile-metrics)
- [Client Connection Metrics](#client-connection-metrics)
- [User Metrics](#user-metrics)
- [Legacy Metrics](#legacy-metrics)

---

## Core Metrics

### `dispatcharr_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `version` - Dispatcharr version (includes timestamp for dev builds)

**Description:** Provides version information about the Dispatcharr instance.

**Example:**
```
dispatcharr_info{version="v0.1.0-20251222123417"} 1
```

---

## Exporter Metrics

### `dispatcharr_exporter_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `version` - Exporter plugin version

**Description:** Provides version information about the exporter plugin.

**Example:**
```
dispatcharr_exporter_info{version="1.2.0"} 1
```

### `dispatcharr_exporter_settings_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:** All plugin settings as labels (for debugging/support)
- `auto_start` - Auto-start enabled (true/false)
- `suppress_access_logs` - Access log suppression (true/false)
- `disable_update_notifications` - Update notifications disabled (true/false)
- `port` - Metrics server port
- `host` - Metrics server host
- `base_url` - Dispatcharr base URL
- `include_m3u_stats` - M3U stats included (true/false)
- `include_epg_stats` - EPG stats included (true/false)
- `include_client_stats` - Client stats included (true/false)
- `include_source_urls` - Source URLs included (true/false)
- `include_user_stats` - User stats included (true/false)
- `include_legacy_metrics` - Legacy metrics included (true/false)

**Description:** Info metric showing all exporter configuration settings.

**Example:**
```
dispatcharr_exporter_settings_info{auto_start="true",suppress_access_logs="true",disable_update_notifications="false",port="9192",host="0.0.0.0",base_url="",include_m3u_stats="true",include_epg_stats="false",include_client_stats="false",include_source_urls="false",include_user_stats="false",include_legacy_metrics="false"} 1
```

### `dispatcharr_exporter_port`
**Type:** gauge  
**Value:** The configured port number  
**Labels:** None

**Description:** The port number the metrics server is configured to run on.

**Example:**
```
dispatcharr_exporter_port 9192
```

---

## M3U Account Metrics

*Optional metrics - enabled by default via `include_m3u_stats` setting*

### `dispatcharr_m3u_accounts`
**Type:** gauge  
**Value:** Account count  
**Labels:**
- `status` - "total" or "active"

**Description:** Total number of M3U accounts and active M3U accounts.

**Example:**
```
dispatcharr_m3u_accounts{status="total"} 5
dispatcharr_m3u_accounts{status="active"} 4
```

### `dispatcharr_m3u_account_status`
**Type:** gauge  
**Value:** Count of accounts with this status  
**Labels:**
- `status` - Account status (idle, fetching, parsing, error, success, etc.)

**Description:** Breakdown of M3U account counts by status.

**Example:**
```
dispatcharr_m3u_account_status{status="success"} 3
dispatcharr_m3u_account_status{status="error"} 1
dispatcharr_m3u_account_status{status="idle"} 1
```

### `dispatcharr_m3u_account_stream_count`
**Type:** gauge  
**Value:** Number of streams configured for this account  
**Labels:**
- `account_id` - Account database ID
- `account_name` - Account name
- `account_type` - Account type (XC, STD, etc.)
- `status` - Account status
- `is_active` - Active state (true/false)
- `username` - XC username (optional, only if `include_source_urls=true`)
- `server_url` - Server URL (optional, only if `include_source_urls=true`)

**Description:** Number of streams configured for each M3U account.

**Example:**
```
dispatcharr_m3u_account_stream_count{account_id="1",account_name="Provider A",account_type="XC",status="success",is_active="true"} 150
```

---

## EPG Source Metrics

*Optional metrics - disabled by default via `include_epg_stats` setting*

### `dispatcharr_epg_sources`
**Type:** gauge  
**Value:** Source count  
**Labels:**
- `status` - "total" or "active"

**Description:** Total number of EPG sources and active EPG sources.

**Example:**
```
dispatcharr_epg_sources{status="total"} 3
dispatcharr_epg_sources{status="active"} 2
```

### `dispatcharr_epg_source_status`
**Type:** gauge  
**Value:** Count of sources with this status  
**Labels:**
- `status` - EPG source status

**Description:** Breakdown of EPG source counts by status.

**Example:**
```
dispatcharr_epg_source_status{status="success"} 2
dispatcharr_epg_source_status{status="error"} 1
```

### `dispatcharr_epg_source_priority`
**Type:** gauge  
**Value:** Priority value (lower is higher priority)  
**Labels:**
- `source_id` - EPG source database ID
- `source_name` - EPG source name
- `source_type` - Source type (xmltv, m3u, etc.)
- `status` - Source status
- `is_active` - Active state (true/false)
- `url` - Source URL (optional, only if `include_source_urls=true`)

**Description:** Priority value for each EPG source.

**Example:**
```
dispatcharr_epg_source_priority{source_id="1",source_name="EPG Source 1",source_type="xmltv",status="success",is_active="true"} 1
```

---

## Channel Metrics

### `dispatcharr_channels`
**Type:** gauge  
**Value:** Channel count  
**Labels:**
- `status` - "total"

**Description:** Total number of channels.

**Example:**
```
dispatcharr_channels{status="total"} 250
```

### `dispatcharr_channel_groups`
**Type:** gauge  
**Value:** Channel group count  
**Labels:** None

**Description:** Total number of channel groups.

**Example:**
```
dispatcharr_channel_groups 15
```

---

## Stream Metrics

**Important:** All stream metrics include both live channel streams and VOD streams, differentiated by the `type` label:
- `type="live"` - Live channel streams
- `type="vod"` - VOD streams

Both types use the same base label structure:
- `channel_uuid` - Unique stream identifier (channel UUID for live, full session_id for VOD)
- `channel_number` - Stream number (channel number for live, numeric timestamp for VOD)

VOD streams include additional metadata labels:
- `channel_name` - Content title (movie/episode name)
- `channel_group` - Content category (Action, Comedy, etc.)
- `content_uuid` - Content database UUID
- `content_type` - "movie" or "episode"
- For episodes: `season_number`, `episode_number`, `series_name`

Some metrics are only available for live streams (stream index, available streams, EPG programming). VOD streams do not populate stream_profile (transcode profile) as this data is not stored in Redis.

### Value Metrics (Minimal Labels)

All value metrics use minimal identifying labels (`type` plus stream-specific identifiers) for efficient querying and joining.

#### `dispatcharr_active_streams`
**Type:** gauge  
**Value:** Count of active streams  
**Labels:** None

**Description:** Total number of currently active streams (live and VOD combined).

**Example:**
```
dispatcharr_active_streams 12
```

#### `dispatcharr_stream_uptime_seconds`
**Type:** counter  
**Value:** Seconds since stream started  
**Labels:**
- `type` - Stream type: "live" or "vod"
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)

**Description:** Stream uptime in seconds. Resets when stream restarts.

**Example:**
```
dispatcharr_stream_uptime_seconds{type="live",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 3847
dispatcharr_stream_uptime_seconds{type="vod",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474"} 1234
```

#### `dispatcharr_stream_active_clients`
**Type:** gauge  
**Value:** Number of connected clients  
**Labels:**
- `type` - Stream type: "live" or "vod"
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)

**Description:** Number of active clients connected to this stream.

**Example:**
```
dispatcharr_stream_active_clients{type="live",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 1
dispatcharr_stream_active_clients{type="vod",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474"} 2
```

#### `dispatcharr_stream_fps`
**Type:** gauge  
**Value:** Frames per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Current stream frames per second.

**Example:**
```
dispatcharr_stream_fps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 59.94
```

#### `dispatcharr_stream_buffering_speed`
**Type:** gauge  
**Value:** Speed multiplier (e.g., 1.0 for realtime, 2.0 for 2x speed)  
**Labels:**
- `type` - Stream type ("live" or "vod")
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Stream buffering speed multiplier indicating how fast the stream is being processed relative to real-time. Available for live channels only (VOD streams do not report this metric). Values like 1.0 indicate realtime processing, values greater than 1.0 indicate the stream is buffering faster than realtime (good), and values less than 1.0 indicate the stream is falling behind (potential buffering issues).

**Example:**
```
dispatcharr_stream_buffering_speed{type="live",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 1.02
```

#### `dispatcharr_stream_video_bitrate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Source video bitrate in bits per second. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_stream_video_bitrate_bps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 8500000
```

#### `dispatcharr_stream_transcode_bitrate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Transcode output bitrate in bits per second. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_stream_transcode_bitrate_bps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 5383400
```

#### `dispatcharr_stream_avg_bitrate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Calculated average bitrate in bits per second (total bytes * 8 / uptime). Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_stream_avg_bitrate_bps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 5200500
```

#### `dispatcharr_stream_current_bitrate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Current bitrate in bits per second (sum of all connected client transfer rates). Matches the "current bitrate" shown in Dispatcharr UI. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_stream_current_bitrate_bps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 4820000
```

#### `dispatcharr_stream_total_transfer_mb`
**Type:** counter  
**Value:** Total megabytes transferred  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Total data transferred by this stream in megabytes.

**Example:**
```
dispatcharr_stream_total_transfer_mb{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 4096.25
```

### Context Metrics

All context metrics use minimal labels (`channel_uuid`, `channel_number`) for consistency.

#### `dispatcharr_stream_channel_number`
**Type:** gauge  
**Value:** The channel number  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Channel number as a numeric value for sorting and filtering.

**Example:**
```
dispatcharr_stream_channel_number{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 1001.0
```

#### `dispatcharr_stream_id`
**Type:** gauge  
**Value:** The stream database ID (live) or 0 (VOD)  
**Labels:**
- `type` - Stream type: "live" or "vod"
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)

**Description:** Database ID of the currently active stream (live only). Value changes indicate stream switched. VOD always reports 0.

**Example:**
```
dispatcharr_stream_id{type="live",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 2954
dispatcharr_stream_id{type="vod",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474"} 0
```

#### `dispatcharr_stream_index`
**Type:** gauge  
**Value:** The stream index (0-based)  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Position of active stream in channel's stream list. 0 = primary stream, >0 = fallback/backup stream.

**Example:**
```
dispatcharr_stream_index{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 0
```

#### `dispatcharr_stream_available_streams`
**Type:** gauge  
**Value:** Total number of streams configured  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Total number of streams configured for this channel.

**Example:**
```
dispatcharr_stream_available_streams{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 3
```

**Example queries:**
```promql
# Remaining backup streams available
dispatcharr_stream_available_streams - dispatcharr_stream_index - 1

# Alert when on last stream
dispatcharr_stream_index >= dispatcharr_stream_available_streams - 1
```

#### `dispatcharr_stream_metadata`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `type` - Stream type: "live" or "vod"
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)
- `channel_name` - Channel/content name
- `channel_group` - Channel group or content category (empty string if none)
- `provider` - M3U account/provider name
- `provider_type` - Provider type (XC, STD, etc.)
- `state` - Stream state (active, waiting_for_clients, buffering, error, etc.)
- `logo_url` - Logo URL (empty string if none)
- `profile_id` - M3U profile database ID
- `profile_name` - M3U profile name
- `stream_profile` - Transcode profile name (empty string for VOD)
- `video_codec` - Video codec (empty string if unknown)
- `resolution` - Video resolution (empty string if unknown)
- Live-specific: `stream_id`, `stream_name`
- VOD-specific: `content_uuid`, `content_type` (movie/episode)
- Episode-specific: `season_number`, `episode_number`, `series_name`

**Description:** Full metadata for the active stream. Unknown/unavailable values are empty strings, not "unknown".

**Example (Live):**
```
dispatcharr_stream_metadata{type="live",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0",channel_name="CBC Toronto",channel_group="News",stream_id="2954",stream_name="CBC Toronto",provider="Provider A",provider_type="XC",state="active",logo_url="/api/channels/logos/1/cache/",profile_id="3",profile_name="Default",stream_profile="ffmpeg Clean",video_codec="h264",resolution="1920x1080"} 1
```

**Example (VOD Movie):**
```
dispatcharr_stream_metadata{type="vod",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474",content_uuid="d6ec6373-dbd2-4a35-a851-712f88e4768c",channel_name="1660 Vine (2022)",channel_group="Action",content_type="movie",provider="Provider A",provider_type="XC",state="active",logo_url="http://example.com/api/vod/vodlogos/74201/cache/",profile_id="24",profile_name="Default",stream_profile="",video_codec="h264",resolution="1920x1080"} 1
```

**Example (VOD Episode):**
```
dispatcharr_stream_metadata{type="vod",channel_uuid="vod_1771265648475_8156",channel_number="1771265648475",content_uuid="abc123-def456",channel_name="The Big Episode",channel_group="Drama",content_type="episode",season_number="3",episode_number="5",series_name="Great Show",provider="Provider A",provider_type="XC",state="active",logo_url="http://example.com/api/vod/vodlogos/12345/cache/",profile_id="24",profile_name="Default",stream_profile="",video_codec="h264",resolution="1920x1080"} 1
```

#### `dispatcharr_stream_programming`
**Type:** gauge  
**Value:** Current program/content progress (0.0 to 1.0), or 0.0 if no current program  
**Labels:**
- `type` - Stream type: "live" or "vod"
- `channel_uuid` - Channel UUID (or VOD session ID for VOD content)
- `channel_number` - Channel number (or VOD session timestamp)
- `previous_title` - Previous program title (empty string if none; not used for VOD)
- `previous_subtitle` - Previous program subtitle/episode (empty string if none; not used for VOD)
- `previous_description` - Previous program description (empty string if none; not used for VOD)
- `previous_start_time` - Previous program start time in ISO format (empty string if none; not used for VOD)
- `previous_end_time` - Previous program end time in ISO format (empty string if none; not used for VOD)
- `current_title` - Current program title (empty string if none)
  - **Live TV**: EPG program title
  - **VOD Movies**: Movie name
  - **VOD Episodes**: Series name
- `current_subtitle` - Current program subtitle/episode (empty string if none)
  - **Live TV**: EPG episode/subtitle
  - **VOD Movies**: "Year - Genre" (e.g., "1999 - Action, Sci-Fi")
  - **VOD Episodes**: "S02E05 - Episode Name"
- `current_description` - Current program description (empty string if none)
  - **Live TV**: EPG program description
  - **VOD**: Movie or episode description
- `current_start_time` - Current program start time in ISO format (empty string if none)
  - **Live TV**: EPG program start time
  - **VOD**: Connection start time (when viewing began)
- `current_end_time` - Current program end time in ISO format (empty string if none)
  - **Live TV**: EPG program end time
  - **VOD**: Estimated completion time (start time + duration)
- `next_title` - Next program title (empty string if none; not used for VOD)
- `next_subtitle` - Next program subtitle/episode (empty string if none; not used for VOD)
- `next_description` - Next program description (empty string if none; not used for VOD)
- `next_start_time` - Next program start time in ISO format (empty string if none; not used for VOD)
- `next_end_time` - Next program end time in ISO format (empty string if none; not used for VOD)

**Description:** 
- **Live TV**: EPG program schedule information for the active stream. Only present if channel has EPG data assigned. The metric value represents how far into the current program we are (0.0 = just started, 1.0 = about to end). Labels provide previous, current, and next program information.
- **VOD**: Rich content metadata including title, description, year, genre, rating, and viewing progress. The metric value represents how far into the content the viewer is (based on elapsed time vs. duration).

> **Note for Live TV:** This metric only works with actual EPG data. Channels using placeholder or dummy EPG sources will not have this metric.

**Example (Live TV with EPG):**
```
dispatcharr_stream_programming{type="live",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0",previous_title="Afternoon News",previous_subtitle="",previous_description="Local and national news coverage",previous_start_time="2026-01-02T17:00:00+00:00",previous_end_time="2026-01-02T18:00:00+00:00",current_title="The Evening News",current_subtitle="Special Report",current_description="Breaking news and analysis",current_start_time="2026-01-02T18:00:00+00:00",current_end_time="2026-01-02T19:00:00+00:00",next_title="Prime Time Drama",next_subtitle="Season 3 Episode 5",next_description="An exciting episode",next_start_time="2026-01-02T19:00:00+00:00",next_end_time="2026-01-02T20:00:00+00:00"} 0.5833
```

**Example (VOD Movie):**
```
dispatcharr_stream_programming{type="vod",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474",previous_title="",previous_subtitle="",previous_description="",previous_start_time="",previous_end_time="",current_title="The Matrix",current_subtitle="1999 - Action, Sci-Fi",current_description="A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",current_start_time="2026-02-16T19:30:45+00:00",current_end_time="2026-02-16T21:46:45+00:00",next_title="",next_subtitle="",next_description="",next_start_time="",next_end_time=""} 0.4200
```

**Example (VOD Episode):**
```
dispatcharr_stream_programming{type="vod",channel_uuid="vod_1771265648475_8156",channel_number="1771265648475",previous_title="",previous_subtitle="",previous_description="",previous_start_time="",previous_end_time="",current_title="Breaking Bad",current_subtitle="S03E05 - Más",current_description="Gus increases his efforts to lure Walt back into business, forcing a rift between Walt and Jesse.",current_start_time="2026-02-16T20:15:22+00:00",current_end_time="2026-02-16T21:02:22+00:00",next_title="",next_subtitle="",next_description="",next_start_time="",next_end_time=""} 0.1852
```

**Example queries:**
```promql
# Time remaining in current program/content (minutes) - Live TV
(1 - dispatcharr_stream_programming{type="live"}) * 
  (timestamp(dispatcharr_stream_programming{type="live",current_end_time!=""}) - 
   timestamp(dispatcharr_stream_programming{type="live",current_start_time!=""})) / 60

# Time remaining in VOD content (minutes)
(1 - dispatcharr_stream_programming{type="vod"}) * 
  (timestamp(dispatcharr_stream_programming{type="vod",current_end_time!=""}) - 
   timestamp(dispatcharr_stream_programming{type="vod",current_start_time!=""})) / 60

# Combine title and subtitle for display (works for both live and VOD)
label_join(
  dispatcharr_stream_programming,
  "program_full",
  " ",
  "current_title",
  "current_subtitle"
)

# Filter VOD by genre (from current_subtitle for movies)
dispatcharr_stream_programming{type="vod",current_subtitle=~".*Action.*"}

# Join with stream metadata for enriched dashboard
dispatcharr_stream_programming
* on(type, channel_uuid, channel_number) group_left(channel_name, logo_url, state)
  dispatcharr_stream_metadata
```

---

## Client Connection Metrics

*Optional metrics - disabled by default via `include_client_stats` setting*

### `dispatcharr_active_clients`
**Type:** gauge  
**Value:** Count of active client connections  
**Labels:** None

**Description:** Total number of currently active client connections across all streams.

**Example:**
```
dispatcharr_active_clients 15
```

### `dispatcharr_client_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number
- `ip_address` - Client IP address
- `user_agent` - Client user agent string
- `worker_id` - Dispatcharr worker ID handling the connection

**Description:** Metadata for each connected client. Join with `dispatcharr_stream_metadata` on `channel_uuid` to get channel name.

**Example:**
```
dispatcharr_client_info{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0",ip_address="192.168.1.100",user_agent="VLC/3.0.16 LibVLC/3.0.16",worker_id="worker_1"} 1
```

### `dispatcharr_client_connection_duration_seconds`
**Type:** gauge  
**Value:** Duration in seconds since client connected  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** How long this client has been connected to the stream.

**Example:**
```
dispatcharr_client_connection_duration_seconds{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 3847
```

### `dispatcharr_client_bytes_sent`
**Type:** counter  
**Value:** Total bytes sent to client  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Cumulative bytes transferred to this client connection.

**Example:**
```
dispatcharr_client_bytes_sent{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 524288000
```

### `dispatcharr_client_avg_transfer_rate_bps`
**Type:** gauge  
**Value:** Average transfer rate in bits per second  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Average data transfer rate to this client over the connection lifetime. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_client_avg_transfer_rate_bps{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 41604000
```

### `dispatcharr_client_current_transfer_rate_bps`
**Type:** gauge  
**Value:** Current transfer rate in bits per second  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Current/recent data transfer rate to this client. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_client_current_transfer_rate_bps{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 43201600
```

---

## Profile Metrics

*Optional metrics - enabled by default via `include_m3u_stats` setting*

### `dispatcharr_profile_connections`
**Type:** gauge  
**Value:** Current connection count  
**Labels:**
- `profile_id` - Profile database ID
- `profile_name` - Profile name
- `account_name` - M3U account name

**Description:** Current number of connections for this M3U profile.

**Example:**
```
dispatcharr_profile_connections{profile_id="3",profile_name="Default",account_name="Provider A"} 5
```

### `dispatcharr_profile_max_connections`
**Type:** gauge  
**Value:** Maximum allowed connections  
**Labels:**
- `profile_id` - Profile database ID
- `profile_name` - Profile name
- `account_name` - M3U account name

**Description:** Maximum allowed connections for this M3U profile (0 = unlimited).

**Example:**
```
dispatcharr_profile_max_connections{profile_id="3",profile_name="Default",account_name="Provider A"} 10
```

### `dispatcharr_profile_connection_usage`
**Type:** gauge  
**Value:** Usage ratio (0.0 to 1.0)  
**Labels:**
- `profile_id` - Profile database ID
- `profile_name` - Profile name
- `account_name` - M3U account name

**Description:** Connection usage ratio (current/max). Only present if max_connections > 0.

**Example:**
```
dispatcharr_profile_connection_usage{profile_id="3",profile_name="Default",account_name="Provider A"} 0.5
```

### `dispatcharr_stream_profile_connections`
**Type:** gauge  
**Value:** Current connection count  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Current connections for the M3U profile used by this specific stream.

**Example:**
```
dispatcharr_stream_profile_connections{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 0
```

### `dispatcharr_stream_profile_max_connections`
**Type:** gauge  
**Value:** Maximum allowed connections  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Maximum allowed connections for the M3U profile used by this stream.

**Example:**
```
dispatcharr_stream_profile_max_connections{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 0
```

---

## Client Connection Metrics

*Optional metrics - disabled by default via `include_client_stats` setting*

**Important:** All client metrics include both live channel clients and VOD session clients, differentiated by the `type` label:
- `type="live"` - Clients streaming live channels
- `type="vod"` - Clients streaming VOD content

### `dispatcharr_active_clients`
**Type:** gauge  
**Value:** Client count  
**Labels:** None

**Description:** Total number of active client connections across both live and VOD streams.

**Example:**
```
dispatcharr_active_clients 5
```

### `dispatcharr_client_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `type` - Connection type: "live" or "vod"
- `client_id` - Unique client identifier
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)
- `ip_address` - Client IP address
- `user_agent` - Client user agent string
- `worker_id` - Dispatcharr worker ID
- VOD-specific: `content_uuid`, `channel_name`, `content_type`

**Description:** Metadata about each active client connection. Note: VOD sessions are counted as single clients even if they have multiple active HTTP streams.

**Example:**
```
dispatcharr_client_info{type="live",client_id="client_1771267188580_6007",channel_uuid="8c9d9b93-b626-42ce-a82f-2509fd8e606d",channel_number="101.0",ip_address="192.168.1.100",user_agent="VLC/3.0.21 LibVLC/3.0.21",worker_id="7a98b87ad2e3:164"} 1
dispatcharr_client_info{type="vod",client_id="vod_1771265648474_7145",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474",content_uuid="d6ec6373-dbd2-4a35-a851-712f88e4768c",channel_name="1660 Vine (2022)",content_type="movie",ip_address="192.168.1.121",user_agent="Mozilla/5.0",worker_id="7a98b87ad2e3-164"} 1
```

### `dispatcharr_client_connection_duration_seconds`
**Type:** gauge  
**Value:** Duration in seconds  
**Labels:**
- `type` - Connection type: "live" or "vod"
- `client_id` - Unique client identifier
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)

**Description:** How long the client has been connected.

**Example:**
```
dispatcharr_client_connection_duration_seconds{type="live",client_id="client_1771267188580_6007",channel_uuid="8c9d9b93-b626-42ce-a82f-2509fd8e606d",channel_number="101.0"} 22
dispatcharr_client_connection_duration_seconds{type="vod",client_id="vod_1771265648474_7145",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474"} 13
```

### `dispatcharr_client_bytes_sent`
**Type:** counter  
**Value:** Total bytes sent  
**Labels:**
- `type` - Connection type: "live" or "vod"
- `client_id` - Unique client identifier
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)

**Description:** Total bytes transferred to the client.

**Example:**
```
dispatcharr_client_bytes_sent{type="live",client_id="client_1771267188580_6007",channel_uuid="8c9d9b93-b626-42ce-a82f-2509fd8e606d",channel_number="101.0"} 16887288
dispatcharr_client_bytes_sent{type="vod",client_id="vod_1771265648474_7145",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474"} 35635200
```

### `dispatcharr_client_avg_transfer_rate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `type` - Connection type: "live" or "vod"
- `client_id` - Unique client identifier
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)

**Description:** Average transfer rate to the client.

**Example:**
```
dispatcharr_client_avg_transfer_rate_bps{type="live",client_id="client_1771267188580_6007",channel_uuid="8c9d9b93-b626-42ce-a82f-2509fd8e606d",channel_number="101.0"} 6634400.0
dispatcharr_client_avg_transfer_rate_bps{type="vod",client_id="vod_1771265648474_7145",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474"} 21929353.84
```

### `dispatcharr_client_current_transfer_rate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `type` - Connection type: "live" or "vod"
- `client_id` - Unique client identifier
- `channel_uuid` - Stream identifier
- `channel_number` - Stream number (numeric)

**Description:** Current transfer rate to the client. For live channels, this is the real-time rate from Redis. For VOD, this uses the average rate (since VOD bitrate is typically stable).

**Example:**
```
dispatcharr_client_current_transfer_rate_bps{type="live",client_id="client_1771267188580_6007",channel_uuid="8c9d9b93-b626-42ce-a82f-2509fd8e606d",channel_number="101.0"} 9025062.4
dispatcharr_client_current_transfer_rate_bps{type="vod",client_id="vod_1771265648474_7145",channel_uuid="vod_1771265648474_7145",channel_number="1771265648474"} 21929353.84
```

---

## User Metrics

*Optional metrics - disabled by default via `include_user_stats` setting*

These metrics expose user account information. Only enable on private networks.

### `dispatcharr_user_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `user_id` - Dispatcharr user ID
- `username` - Username
- `user_level` - Role: `"streamer"` (0), `"standard"` (1), or `"admin"` (10+)
- `is_staff` - Django staff flag (`"true"` / `"false"`)
- `date_joined` - Unix timestamp when the account was created

**Description:** Per-user static information. Join with other user metrics on `user_id`.

**Example:**
```
dispatcharr_user_info{user_id="1",username="alice",user_level="admin",is_staff="true",date_joined="1700000000"} 1
dispatcharr_user_info{user_id="2",username="bob",user_level="streamer",is_staff="false",date_joined="1710000000"} 1
```

### `dispatcharr_user_stream_limit`
**Type:** gauge  
**Value:** Configured concurrent stream limit (0 = unlimited)  
**Labels:**
- `user_id` - Dispatcharr user ID
- `username` - Username

**Description:** The maximum number of concurrent streams configured for each user. A value of `0` means no limit is enforced.

**Example:**
```
dispatcharr_user_stream_limit{user_id="1",username="alice"} 0
dispatcharr_user_stream_limit{user_id="2",username="bob"} 2
```

### `dispatcharr_user_active_streams`
**Type:** gauge  
**Value:** Current active stream count  
**Labels:**
- `user_id` - Dispatcharr user ID
- `username` - Username

**Description:** Number of streams currently active for each user, counting both live channel clients and active VOD sessions.

**Example:**
```
dispatcharr_user_active_streams{user_id="1",username="alice"} 1
dispatcharr_user_active_streams{user_id="2",username="bob"} 2
```

### `dispatcharr_user_last_login_timestamp`
**Type:** gauge  
**Value:** Unix timestamp of last login (0 if the user has never logged in)  
**Labels:**
- `user_id` - Dispatcharr user ID
- `username` - Username

**Description:** Unix timestamp of each user's last login. 0 if the user has never logged in.

**Example:**
```
dispatcharr_user_last_login_timestamp{user_id="1",username="alice"} 1743400000
dispatcharr_user_last_login_timestamp{user_id="2",username="bob"} 0
```

**Example queries:**
```promql
# Stream usage ratio per user (requires stream_limit > 0)
dispatcharr_user_active_streams / dispatcharr_user_stream_limit > 0

# Users at or over their stream limit
dispatcharr_user_active_streams >= dispatcharr_user_stream_limit
  and dispatcharr_user_stream_limit > 0

# Users who have never logged in
dispatcharr_user_last_login_timestamp == 0

# Users inactive for more than 30 days
(time() - dispatcharr_user_last_login_timestamp) / 86400 > 30
  and dispatcharr_user_last_login_timestamp > 0
```

---

## Legacy Metrics

*Deprecated metrics - disabled by default via `include_legacy_metrics` setting*

**Warning:** These metrics are from v1.1.0 and earlier. They are NOT recommended as they create new time series whenever any value changes. Use the new layered metrics instead.

### `dispatcharr_stream_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:** ALL stream information as labels (values and metadata mixed)

**Description:** Legacy format with all stream statistics as labels. Creates high cardinality and new series on every value change.

**Migration:** Use the new layered metrics:
- Use `dispatcharr_stream_metadata` for static metadata
- Use separate value metrics (`dispatcharr_stream_fps`, `dispatcharr_stream_uptime_seconds`, etc.) for dynamic values
- Join metrics using `channel_uuid` and `channel_number`

### `dispatcharr_m3u_account_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:** Account information with `stream_count` as a label

**Description:** Legacy format with stream count as a label.

**Migration:** Use `dispatcharr_m3u_account_stream_count` for the stream count as a proper gauge value.

### `dispatcharr_epg_source_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:** EPG source information with `priority` as a label

**Description:** Legacy format with priority as a label.

**Migration:** Use `dispatcharr_epg_source_priority` for the priority as a proper gauge value.

---

## Common PromQL Query Patterns

### Basic Queries
```promql
# All active streams (live + VOD)
dispatcharr_active_streams

# Only live streams
count(dispatcharr_stream_active_clients{type="live"})

# Only VOD streams
count(dispatcharr_stream_active_clients{type="vod"})

# All active clients (live + VOD)
dispatcharr_active_clients

# FPS for specific channel
dispatcharr_stream_fps{channel_uuid="..."}

# Detect fallback (backup stream active) - live only
dispatcharr_stream_index > 0

# Sort channels by number
sort(dispatcharr_stream_channel_number)

# Client connection durations
dispatcharr_client_connection_duration_seconds

# Clients connected for over 1 hour
dispatcharr_client_connection_duration_seconds > 3600
```

### Working with Live + VOD Unified Metrics
```promql
# Total active streams across both types
sum(dispatcharr_stream_active_clients)

# Total active streams by type
sum by (type) (dispatcharr_stream_active_clients)

# Total bitrate across all streams (live + VOD)
sum(dispatcharr_stream_avg_bitrate_bps)

# Average bitrate by type
avg by (type) (dispatcharr_stream_avg_bitrate_bps)

# Profile connections including both live and VOD
dispatcharr_profile_connections

# Join VOD metadata to get content name
dispatcharr_stream_uptime_seconds{type="vod"}
  * on(channel_uuid, channel_number) group_left(channel_name, content_type)
  dispatcharr_stream_metadata
```

### Client Queries
```promql
# Total bytes sent to all clients (live + VOD)
sum(dispatcharr_client_bytes_sent)

# Total bytes sent per stream
sum by (type, channel_uuid, channel_number) (dispatcharr_client_bytes_sent)

# Average transfer rate across all clients (in bps)
avg(dispatcharr_client_avg_transfer_rate_bps)

# Average transfer rate in Mbps for display
avg(dispatcharr_client_avg_transfer_rate_bps) / 1000000

# Client connection duration with IP and user agent
dispatcharr_client_connection_duration_seconds
  * on(type, client_id, channel_uuid, channel_number) group_left(ip_address, user_agent)
  dispatcharr_client_info

# Client info with stream metadata (double join)
dispatcharr_client_info
  * on(type, channel_uuid, channel_number) group_left(channel_name, provider, content_type)
  dispatcharr_stream_metadata

# VOD client connections with content name
dispatcharr_client_info{type="vod"}
  * on(channel_uuid, channel_number) group_left(channel_name)
  dispatcharr_stream_metadata
```

### Enriched Queries (with joins)
```promql
# FPS with provider information (live only)
dispatcharr_stream_fps
  * on(channel_uuid, channel_number) group_left(provider, stream_name)
  dispatcharr_stream_metadata{type="live"}

# Total transfer with full metadata
dispatcharr_stream_total_transfer_mb
  * on(type, channel_uuid, channel_number) group_left(logo_url, resolution, video_codec, channel_name)
  dispatcharr_stream_metadata

# Stream uptime with index (live only)
dispatcharr_stream_uptime_seconds{type="live"}
  + on(channel_uuid, channel_number)
  dispatcharr_stream_index

# VOD streams with category
dispatcharr_stream_uptime_seconds{type="vod"}
  * on(channel_uuid, channel_number) group_left(channel_group, content_type)
  dispatcharr_stream_metadata
```

### Alerts
```promql
# Alert on stream fallback
dispatcharr_stream_index > 0

# Alert on high profile usage
dispatcharr_profile_connection_usage > 0.9

# Alert on M3U account errors
dispatcharr_m3u_account_status{status="error"} > 0
```
