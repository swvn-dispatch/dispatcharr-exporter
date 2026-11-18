# Changelog

All notable changes to this project are documented in this file.

## [v3.4.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v3.4.0) - 2026-11-18

### Added

- Add an optional integration with the Stream Usage plugin to export sampled traffic totals, including breakdowns by user, channel, and time period. Contributed by @funkasaur in [#19](https://github.com/swvn-dispatch/dispatcharr-exporter/pull/19).

### Changed

- Require Dispatcharr v0.34.0 or later. Approve the requested plugin capabilities and restart Dispatcharr when upgrading from an older exporter version.
- Start and stop the metrics server automatically with the enabled plugin. Save server settings and reload the plugin to apply them.
- Apply saved metric and integration settings on the next scrape without a plugin reload. Organize settings into server, metric, and individual integration sections.

### Removed

- Remove the auto-start setting and server control actions. Reload the plugin to restart the server, or disable it to stop the server.

## [v3.3.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v3.3.0) - 2026-11-14

### Added

- Added Packet Slapper metrics for download and upload loaded latency and the last scheduled speedtest skipped while someone was watching. Contributed by @write-erase in [#15](https://github.com/swvn-dispatch/dispatcharr-exporter/pull/15).

## [v3.2.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v3.2.0) - 2026-11-04

### Added

- Added opt-in Packet Slapper speedtest metrics, including recent test status, connection performance, and test-server information. Contributed by HaraldRuppert in [#13](https://github.com/swvn-dispatch/dispatcharr-exporter/pull/13).

## [v3.1.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v3.1.0) - 2026-07-18

### Added
- Catch-up (timeshift) streams now show up alongside live and VOD everywhere: `dispatcharr_active_streams{type="timeshift"}`, `dispatcharr_stream_metadata`, `dispatcharr_stream_active_clients`, `dispatcharr_stream_uptime_seconds`, `dispatcharr_stream_avg_bitrate_bps`, and per-viewer `dispatcharr_client_*` connection metrics (client stats setting).
- Catch-up sessions report EPG program info just like live TV, anchored to the position being watched rather than real time; the current program title is prefixed `Catchup-MM-DD-HH:MM:` to distinguish it from a live view.
- Active M3U provider and profile (`provider`, `provider_type`, `profile_id`, `profile_name`) and connection limits are now reported for catch-up streams, matching live.
- New per-channel info metrics (`dispatcharr_channel_info`, `dispatcharr_channel_source_count`, `dispatcharr_channel_catchup_days`) covering channel group, source/stream count, and catch-up configuration, behind a new "Include Channel Info Statistics" setting.
- New plugin health metrics (`dispatcharr_plugins`, `dispatcharr_plugin_info`, `dispatcharr_plugin_repos`, `dispatcharr_plugin_repo_info`, `dispatcharr_plugin_repo_last_fetch_timestamp`) behind a new "Include Plugin Statistics" setting.

### Fixed
- The metrics server now releases its database connection after every scrape. Previously it could leave connections open indefinitely, which under sustained load could exhaust the database's connection limit and make Dispatcharr unresponsive.

## [v3.0.1](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v3.0.1) - 2026-05-10

### Fixed

- Compatible with Dispatcharr versions that renamed `ts_proxy` to `live_proxy` - the plugin now tries the new module path first and falls back to the old one, so both old and new Dispatcharr installs are supported

## [v3.0.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v3.0.0) - 2026-04-18

### Added
- User metrics: `dispatcharr_user_info`, `dispatcharr_user_date_joined_timestamp`, `dispatcharr_user_stream_limit`, and `dispatcharr_user_active_streams` (opt-in via new `Include User Statistics` setting)
- `dispatcharr_m3u_account_info` gauge providing metadata for each M3U account
- Per-type breakdown on `dispatcharr_active_streams` with `type="live"` and `type="vod"` labels
- `type` label added to `dispatcharr_stream_fps`, `dispatcharr_stream_video_bitrate_bps`, `dispatcharr_stream_transcode_bitrate_bps`, `dispatcharr_stream_current_bitrate_bps`, `dispatcharr_stream_channel_number`, `dispatcharr_stream_index`, and `dispatcharr_stream_available_streams`
- `user_id` and `username` labels on `dispatcharr_client_info`
- Manual stop flag - stopping the server now prevents auto-start from restarting it until explicitly started again

### Changed
- Minimum Dispatcharr version raised to v0.22.0
- "Start Server" and "Restart Server" action buttons merged into a single "Start / Restart Metrics Server" button

### Removed
- Legacy metrics (`dispatcharr_stream_info`, legacy `dispatcharr_m3u_account_info` with `stream_count` label, legacy `dispatcharr_epg_source_info` with `priority` label) and the `Include Legacy Metric Formats` setting
- `Disable Update Notifications` setting and the `Check for Updates` action button

## [v2.4.2](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v2.4.2) - 2026-03-30

### Fixed
- Prevent exporter auto-start from being blocked by stale state left behind after a failed upgrade or ungraceful shutdown by clearing prior Redis keys and removing the stale auto-start lock file on startup.

## [v2.4.1](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v2.4.1) - 2026-03-26

### Added
- Modified plugin metadata to support upcoming [plugin repo](https://github.com/Dispatcharr/Plugins).
- Added stronger server stop reliability:
  - `MetricsServer._verify_stopped()` to confirm the port is actually free after stopping.
  - Stop-signal monitor now:
    - reuses a Redis client instead of reacquiring every loop iteration,
    - retries Redis acquisition if missing,
    - logs periodic “heartbeat” and escalates some logs to `info/warning`,
    - calls `server.stop(timeout=5)` and verifies shutdown.

### Changed
- Auto-start lock handling tightened and made safer:
  - lock file permissions changed from `0666` to `0600` (owner-only).
  - explicit handling of `BlockingIOError` to exit cleanly when another worker owns the lock.
  - improved cleanup on exceptions (best-effort unlock/close).
  - removed the early `_auto_start_attempted = True` assignment (was being set before lock/auto-start logic ran).
- `stop_server` / `restart_server` actions improved for cross-worker scenarios:
  - more explicit logging when sending stop signals via Redis.
  - if shutdown isn’t confirmed within 5 seconds, force-cleans Redis keys (`server_running`, `server_host`, `server_port`, `stop_requested`) and removes the lock file so a restart can proceed.
- General code cleanup:
  - Removed unused `typing` import.
  - Replaced many silent `pass` blocks with commented `pass` explaining why an exception is ignored.
  - Minor trimming of unused local variables in VOD programming (removed unused rating/air_date vars).

## [v2.4.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v2.4.0) - 2026-03-01

### Added
- Unified **live + VOD stream coverage** for stream metrics via a new `type` label (`type="live"` / `type="vod"`), so the same metric families can represent both.
- Added VOD-aware stream enrichment:
  - `dispatcharr_stream_metadata` now includes VOD labels like `content_uuid`, `content_type` (movie/episode), and episode labels (`season_number`, `episode_number`, `series_name`) when available.
  - `dispatcharr_stream_programming` now supports VOD by emitting content title/description + a time-based progress value (elapsed/duration).
- Added `dispatcharr_stream_buffering_speed` gauge (live-only) derived from ffmpeg “speed” (e.g., `1.0x` → `1.0`).
- Added per-type active stream counts:
  - `dispatcharr_active_streams{type="live"}` and `dispatcharr_active_streams{type="vod"}`.
- Expanded client connection metrics to include **VOD sessions as clients** (with `type="vod"`), including:
  - `dispatcharr_client_info`
  - `dispatcharr_client_connection_duration_seconds`
  - `dispatcharr_client_bytes_sent`
  - `dispatcharr_client_avg_transfer_rate_bps`
  - `dispatcharr_client_current_transfer_rate_bps`

### Changed
- Removed the separate “VOD Metrics” section/setting:
  - Dropped `include_vod_stats` setting and the `dispatcharr_vod_*` metrics.
  - VOD is now represented through the same stream/client metrics with `type="vod"`.
- Updated profile connection counting logic to include both:
  - live channel streams (`channel_stream:*`)
  - VOD persistent connections (`vod_persistent_connection:*` with `active_streams > 0`)
- Improved MetricsServer host handling and diagnostics:
  - Normalizes empty/whitespace host values to default host
  - Logs exact bind target and validates host resolution (`getaddrinfo`) before binding, with clearer Docker guidance (`0.0.0.0`).
- Updated docs and samples:
  - `METRICS.md` reorganized (VOD section replaced with Client Connection Metrics) and updated queries/joins to include `type`.
  - Grafana dashboard + sample panels updated for Grafana `12.3.3`, new `Type` column, and refreshed table options/layout.

### Fixed
- Improved label escaping for VOD programming strings (ensures backslashes, quotes, and newlines are escaped in a safe order).
- Minor JSON formatting/EOF newline fixes in sample dashboard/panels.

**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v2.3.0...v2.4.0

## [v2.3.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v2.3.0) - 2026-02-12

## **This release requires >= v0.19.0 of Dispatcharr to run**
### Added
- Added a **pre-built Grafana dashboard** for quick import:
  - `samples/dashboards/Dispatcharr-1767806789544.json` (+ screenshot in `samples/dashboards/images/Dispatcharr.png`)
- Added `src/plugin.json` (plugin manifest) and `src/logo.png` to support **Dispatcharr v0.19.0+ plugin system** expectations.
- Release workflow now updates the version in **both** `src/plugin.py` and `src/plugin.json`.

### Changed
- Moved plugin metadata/config to `src/plugin.json` and updated `src/plugin.py` to load config from that file (with a safe fallback config if loading fails).
- Updated packaging script to enforce/validate presence of `src/plugin.json` and to keep its version in sync during packaging.
- README now highlights **dashboards** (instead of individual example panels) and includes dashboard import instructions.
- Updated sample panel JSON (`samples/panels/active-streams.json`) to a newer table layout:
  - Adds “Program” and “Progress” (gauge) columns via merged Prometheus queries
  - Improves table styling (centered logos, stronger state row highlighting, column sizing)

### Fixed
- Fixed Prometheus label escaping for program metadata (escape order corrected; now also escapes newlines), reducing the chance of producing invalid metrics output.
- Centralized Dispatcharr version detection into a single helper to keep version reporting and minimum-version checks consistent.
- Removed background auto-update notification thread logic; updates are now checked via the existing **“Check for Updates”** action button (reduces startup noise/side effects).

**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v2.2.0...v2.3.0

## [v2.2.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v2.2.0) - 2026-01-05

**NOTICE:** If you are running Dispatcharr in Docker, add `PYTHONDONTWRITEBYTECODE=1` to your container's environment variables to prevent root-owned cache files from blocking plugin updates.  This is a workaround for a Dispatcharr startup behavior that runs migrations as root.

### Added
- Added `dispatcharr_stream_programming` to expose current EPG program context (previous/current/next program details) and current-program progress for active streams.

- ---
**Installing**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#installation
**Upgrading**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#updating-the-plugin
**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v2.1.1...v2.2.0

## [v2.1.1](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v2.1.1) - 2025-12-31

## NOTICE

**Important:** If you are running Dispatcharr in Docker, add `PYTHONDONTWRITEBYTECODE=1` to your container's environment variables to prevent root-owned cache files from blocking plugin updates.  This is a workaround for a Dispatcharr startup behavior that runs migrations as root.

## Added
- **(v2.1.1 HOTFIX)** New stream metric:  
  - `dispatcharr_stream_current_bitrate_bps` — Current bitrate in bits per second (sum of all connected client transfer rates). Matches the "current bitrate" shown in Dispatcharr UI. 
- Minimum Dispatcharr version check:  
  - Plugin now verifies that Dispatcharr meets the minimum required version (`v0.14.0`) at startup. 
  - Skips version check for dev builds (with timestamp suffix).
  - Logs warning if version cannot be determined and proceeds anyway. 
- Profile expiry metric:
  - New `dispatcharr_profile_days_to_expiry` gauge showing days remaining until XC profile expiry.
  - Value is 0 if expired, -1 if no expiry is set. 
  - Calculated from `custom_properties['user_info']['exp_date']` Unix timestamp. 
- Root-owned `__pycache__` detection:
  - Plugin detects root-owned `__pycache__` directories at startup (caused by Dispatcharr running migrations as root).
  - Logs a warning with remediation instructions (add `PYTHONDONTWRITEBYTECODE=1` or manually delete).

## Changed
- **(v2.1.1 HOTFIX)** Client transfer rate unit auto-detection: 
  - Client metrics now auto-detect whether Redis fields contain bytes/s or KB/s (field names suggest KB/s but currently contain bytes/s in some Dispatcharr versions).
  - Auto-detection logic:  if value > 50000, assume bytes/s; otherwise assume KB/s.
  - Applied to both `avg_rate_KBps` and `current_rate_KBps` fields.
- Bitrate metrics now use bits per second (bps) instead of kilobits per second (kbps):
  - Stream metrics:  `dispatcharr_stream_video_bitrate_bps`, `dispatcharr_stream_transcode_bitrate_bps`, `dispatcharr_stream_avg_bitrate_bps` (previously `*_kbps`).
  - Client metrics: `dispatcharr_client_avg_transfer_rate_bps`, `dispatcharr_client_current_transfer_rate_bps` (previously `*_kbps`).
  - All bitrate values are now in bits per second for consistency with Prometheus/Grafana best practices.   
  - Use Grafana's "bits/sec" unit for automatic formatting (auto-converts to Kbps, Mbps, Gbps).
  - Legacy metrics also updated to use `*_bps` naming and values. 
- Profile connection counting improved: 
  - Profile connection metrics now calculate actual active connections by scanning active streams.  
  - More accurate than Redis counters which don't update during stream fallback/failover.
- METRICS.md documentation updated: 
  - All bitrate metric names and examples updated to reflect bps units.
  - Added PromQL examples for converting bps to Mbps for display. 

## Fixed
- **(v2.1.1 HOTFIX)** Client transfer rates now correctly handle Dispatcharr versions that store bytes/s instead of KB/s in Redis fields (previously multiplied by 8000 unconditionally, causing 1000x inflation).
- Profile connection metrics now reflect reality during stream fallback (previously used stale Redis counters).
---
**Installing**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#installation
**Upgrading**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#updating-the-plugin
**Hotfix Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v2.1.0...v2.1.1
**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v2.0.0...v2.1.1

## [v2.1.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v2.1.0) - 2025-12-31

## NOTICE

**Important:** If you are running Dispatcharr in Docker, add `PYTHONDONTWRITEBYTECODE=1` to your container's environment variables to prevent root-owned cache files from blocking plugin updates.  This is a workaround for a Dispatcharr startup behavior that runs migrations as root.

## Added
- Minimum Dispatcharr version check: 
  - Plugin now verifies that Dispatcharr meets the minimum required version (`v0.14.0`) at startup. 
  - Skips version check for dev builds (with timestamp suffix).
  - Logs warning if version cannot be determined and proceeds anyway. 
- Profile expiry metric:
  - New `dispatcharr_profile_days_to_expiry` gauge showing days remaining until XC profile expiry.
  - Value is 0 if expired, -1 if no expiry is set. 
  - Calculated from `custom_properties['user_info']['exp_date']` Unix timestamp. 
- Root-owned `__pycache__` detection:
  - Plugin detects root-owned `__pycache__` directories at startup (caused by Dispatcharr running migrations as root).
  - Logs a warning with remediation instructions (add `PYTHONDONTWRITEBYTECODE=1` or manually delete).

## Changed
- Bitrate metrics now use bits per second (bps) instead of kilobits per second (kbps):
  - Stream metrics:  `dispatcharr_stream_video_bitrate_bps`, `dispatcharr_stream_transcode_bitrate_bps`, `dispatcharr_stream_avg_bitrate_bps` (previously `*_kbps`).
  - Client metrics: `dispatcharr_client_avg_transfer_rate_bps`, `dispatcharr_client_current_transfer_rate_bps` (previously `*_kbps`).
  - All bitrate values are now in bits per second for consistency with Prometheus/Grafana best practices.  
  - Use Grafana's "bits/sec" unit for automatic formatting (auto-converts to Kbps, Mbps, Gbps).
  - Legacy metrics also updated to use `*_bps` naming and values. 
- Profile connection counting improved: 
  - Profile connection metrics now calculate actual active connections by scanning active streams. 
  - More accurate than Redis counters which don't update during stream fallback/failover.
- METRICS.md documentation updated: 
  - All bitrate metric names and examples updated to reflect bps units.
  - Added PromQL examples for converting bps to Mbps for display. 

## Fixed
- Profile connection metrics now reflect reality during stream fallback (previously used stale Redis counters).
---
**Installing**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#installation
**Upgrading**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#updating-the-plugin
**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v2.0.0...v2.1.0

## [v2.0.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v2.0.0) - 2025-12-29

## Added
- Comprehensive metrics documentation: 
  - New METRICS. md file documenting all available Prometheus metrics, their types, labels, and usage patterns. 
  - Includes PromQL query examples and best practices for joining metrics.
- Client connection metrics (optional, disabled by default):
  - New `dispatcharr_active_clients` gauge showing total active client connections.
  - New `dispatcharr_client_info` gauge with client metadata (IP address, user agent, worker ID).
  - New `dispatcharr_client_connection_duration_seconds` gauge tracking connection duration.
  - New `dispatcharr_client_bytes_sent` counter for total bytes transferred to each client.
  - New `dispatcharr_client_avg_transfer_rate_kbps` and `dispatcharr_client_current_transfer_rate_kbps` gauges for transfer rates.
  - Controlled via new `include_client_stats` setting (privacy-focused, off by default).
- Improved stream metrics structure:
  - New layered metric design separating static metadata from dynamic values to avoid creating new time series on value changes.
  - New `dispatcharr_stream_metadata` gauge with all enrichment labels (channel name, provider, state, logo, codec, resolution).
  - New separate value gauges:  `dispatcharr_stream_channel_number`, `dispatcharr_stream_id`, `dispatcharr_stream_index`, `dispatcharr_stream_available_streams`.
  - New `dispatcharr_stream_uptime_seconds` counter, `dispatcharr_stream_active_clients` gauge, `dispatcharr_stream_fps` gauge, and bitrate/transfer metrics.
  - All metrics use minimal `channel_uuid` and `channel_number` labels for efficient joining.
- Improved M3U and EPG metrics:
  - New `dispatcharr_m3u_account_stream_count` gauge (stream count as a value, not a label).
  - New `dispatcharr_epg_source_priority` gauge (priority as a value, not a label).
  - Separate info metrics (`dispatcharr_m3u_account_info`, `dispatcharr_epg_source_info`) for static metadata.
- Exporter metadata improvements:
  - New `dispatcharr_exporter_port` gauge showing the configured port number.
  - Renamed `dispatcharr_exporter_settings` to `dispatcharr_exporter_settings_info` for clarity.
- Root endpoint landing page:
  - New HTML landing page at `/` showing plugin name, version, description, and links to `/metrics` and `/health`.

## Changed
- Stream metrics now detect and report the actual active stream ID from Redis metadata (handles fallback/failover correctly).
- Stream metrics include channel group information in metadata labels. 
- Legacy metric formats (v1.1.0 and earlier) are now opt-in via the new `include_legacy_metrics` setting (disabled by default).
- Plugin configuration updated to include `include_client_stats` and `include_legacy_metrics` settings.
- README updated to reference the new METRICS.md documentation and clarify privacy-focused client metrics.

## Deprecated
- Legacy metric formats (`dispatcharr_stream_info` with all values as labels, `dispatcharr_m3u_account_info` with stream_count as label, `dispatcharr_epg_source_info` with priority as label) are deprecated and disabled by default.
  - Only enable via `include_legacy_metrics=true` if you need time to migrate existing dashboards.
  - Use the new layered metrics instead (static metadata + separate value gauges).
---
**Installing**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#installation
**Upgrading**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#updating-the-plugin
**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v1.1.0...v2.0.0

## [v1.1.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v1.1.0) - 2025-12-22

## Added
- Exporter metadata metrics:
  - New Prometheus metrics `dispatcharr_exporter_info` and `dispatcharr_exporter_settings` expose the plugin/exporter version and current settings as metrics.
  - Settings are emitted as labeled gauge(s) so exporter configuration can be inspected via Prometheus.
- New plugin settings:
  - `base_url` — optional Dispatcharr base URL; when set, channel logo URLs emitted by the exporter are absolute (e.g., https://dispatcharr.example.com/api/...). Leave empty to use relative paths.
  - `suppress_access_logs` — boolean to suppress HTTP access logs for the metrics server.
  - `disable_update_notifications` — boolean to disable automatic update notification broadcasts.
- Update-checking and notifications:
  - Background check against the GitHub releases API to detect newer plugin releases; when an update is available the plugin can publish a notification (rate-limited via Redis).
  - Exposes a manual action `check_for_updates` to query GitHub and return update status and download URL.

## Changed
- Metrics collection:
  - Stream metrics collection now accepts plugin settings so emitted stream-related fields (e.g., absolute logo URLs) may reflect the `base_url` setting.
  - The plugin now includes exporter/version info near the top of the metrics output.
- Metrics server runtime and logging:
  - Gevent WSGI server startup now supports suppressing access logs when `suppress_access_logs` is enabled.
  - Several startup/auto-start messages have been shifted from info → debug to reduce log noise by default.
- Release workflow robustness:
  - Release artifact upload step was made more resilient: it tolerates immutable releases, checks for existing assets, and handles prerelease asset removal more gracefully.
- Plugin metadata:
  - Internal PLUGIN_CONFIG version string was updated and `repo_url` was added to the config for use by update checks.
---
**Installing**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#installation
**Upgrading**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#updating-the-plugin
**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v1.0.1...v1.1.0

## [v1.0.1](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v1.0.1) - 2025-12-18

Listed below are the main changes featured in this release.
See README for installation & more information.

- `d400463` XC usernames are now hidden when the "Include Provider/Source Information" is FALSE.
- `41775ff` Dummy EPG entries are now suppressed from EPG Info.
- `213bb85` Fixed auto-start functionality, this was previously not working.

**Installing**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#installation
**Upgrading**: https://github.com/sethwv/dispatcharr-exporter?tab=readme-ov-file#updating-the-plugin
**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/compare/v1.0.0...v1.0.1

## [v1.0.0](https://github.com/swvn-dispatch/dispatcharr-exporter/releases/tag/v1.0.0) - 2025-12-18

**Initial Release, work-in-progress.**
See README for installation & more information.

**Full Changelog**: https://github.com/sethwv/dispatcharr-exporter/commits/v1.0.0
