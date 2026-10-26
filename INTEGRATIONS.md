# External Metrics Integrations

`src/integrations/` contains opt-in metrics that are produced by other plugins
or external services. Native Dispatcharr model and Redis collections stay in
`src/collector.py`, even when their exporter setting is optional.

## Available integrations

### Packet Slapper

[Packet Slapper](https://github.com/write-erase/packet-slapper) runs scheduled
or on-demand Ookla speedtests from Dispatcharr. Enable its **Publish results for
Prometheus** setting, then enable this exporter's **Include Speedtest
Statistics** setting (`include_speedtest_stats`). Nothing is emitted until
Packet Slapper has published a run.

Packet Slapper writes its latest state to `packet_slapper:prometheus:latest`.
A failed speedtest updates only the `last_attempt_*` metrics. Result metrics
retain the values from the last successful run.

| Metric | Type | Description |
| --- | --- | --- |
| `dispatcharr_speedtest_last_attempt_timestamp_seconds` | gauge | Unix timestamp of the latest attempted speedtest. |
| `dispatcharr_speedtest_last_attempt_success` | gauge | `1` after a successful attempt, `0` after a failed attempt. |
| `dispatcharr_speedtest_last_success_timestamp_seconds` | gauge | Unix timestamp of the latest successful speedtest. |
| `dispatcharr_speedtest_download_mbps` | gauge | Download speed in megabits per second. |
| `dispatcharr_speedtest_upload_mbps` | gauge | Upload speed in megabits per second. |
| `dispatcharr_speedtest_latency_ms` | gauge | Idle ping latency in milliseconds. |
| `dispatcharr_speedtest_jitter_ms` | gauge | Idle ping jitter in milliseconds. |
| `dispatcharr_speedtest_packet_loss_percent` | gauge | Packet loss percentage. Omitted when Ookla does not report it. |
| `dispatcharr_speedtest_server_info` | gauge | Always `1`, with `isp`, `server_name`, `server_location`, `server_country`, and `server_host` labels. |

```promql
# Alert when the latest speedtest failed
dispatcharr_speedtest_last_attempt_success == 0

# Alert when no successful speedtest has occurred for three hours
time() - dispatcharr_speedtest_last_success_timestamp_seconds > 3 * 3600
```

## Integrating

### Adding an integration

1. Add a module under `src/integrations/` that exports a setting ID and a
   `collect_metrics(redis_client)` function returning Prometheus text lines.
2. Register it in `src/integrations/__init__.py`.
3. Add a boolean `include_*` setting to `src/config.py`, defaulting to `False`.
4. Document its setting in `README.md` and its full metric reference here.

The registry invokes only enabled integrations and isolates their failures so a
bad external payload cannot fail the `/metrics` response or another integration.

### Producer contract

Producers should publish a stable, namespaced Redis key and a JSON object. The
integration must tolerate an absent key, bytes or decoded string values,
malformed data, unavailable Redis, and producer upgrades. Add a schema version
before making incompatible changes to an established payload.

Do not assume a key has a TTL. If values survive restarts, publish timestamps so
Prometheus users can alert on stale data. Producers and consumers must both be
explicitly enabled when the data is optional.

### Prometheus requirements

Emit HELP and TYPE lines for every metric family. Reject non-finite numeric
values, escape all label values with `utils.escape_label`, and avoid labels that
expose credentials or other sensitive data. Keep producer-specific Redis keys,
payload parsing, and metric formatting in that producer's module.
