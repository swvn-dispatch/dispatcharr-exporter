# Dispatcharr Prometheus Exporter

A [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) plugin that exposes metrics in Prometheus format for monitoring and alerting.

## Support

This project is maintained in my spare time. If it's saved you some headaches, a tip is always appreciated.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/sethwv)

## Installation

1. Download the latest release zip from the [releases page](https://github.com/sethwv/dispatcharr-exporter/releases).
2. In Dispatcharr, go to **Plugins** and upload the zip.
3. Approve the requested capabilities and restart Dispatcharr for the network listener capability.
4. Enable the plugin and configure settings.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Suppress Access Logs | `true` | Suppress HTTP access logs for /metrics requests |
| Metrics Server Port | `9192` | Port for the HTTP metrics server |
| Metrics Server Host | `0.0.0.0` | Bind address (`0.0.0.0` for all interfaces, `127.0.0.1` for local only) |
| Dispatcharr Base URL | _(empty)_ | Base URL for absolute logo URLs (e.g. `http://localhost:5656`). Leave empty for relative paths |
| Include M3U Account Metrics | `true` | Include M3U account and profile connection metrics |
| Include EPG Source Metrics | `false` | Include EPG source status metrics |
| Include Client Statistics | `false` | Include individual client connection info (may expose sensitive data) |
| Include Source URLs | `false` | Include server URLs and XC usernames in metrics. Disable before sharing output for troubleshooting |
| Include User Statistics | `false` | Include per-user metrics (user info, stream limits, active streams) |
| Include Speedtest Statistics | `false` | Include the latest speedtest from the [Packet Slapper](https://github.com/write-erase/packet-slapper) plugin (turn on its "Publish results for Prometheus" setting) |
| Include Stream Usage Statistics | `false` | Include sampled traffic from the Stream Usage plugin (enable its "Publish for Exporter" setting) |

## External integrations

External metrics are disabled by default and require their producer to be enabled
separately. See [INTEGRATIONS.md](INTEGRATIONS.md) for the integration model and
the Packet Slapper Redis contract.

## Usage

The elected plugin leader starts the metrics server automatically. Stats and integration settings take effect on the next scrape after saving. Save and reload the plugin to apply server settings. Disabling the plugin stops the server. On upgrades from older versions, restart Dispatcharr after approving capabilities to ensure the old server has stopped.

Metrics are available at:

```
http://your-dispatcharr-host:9192/metrics
http://your-dispatcharr-host:9192/health
```

You may need to map port 9192 if running in Docker.

## Metrics Reference

See [METRICS.md](METRICS.md) for all available metrics, labels, and example PromQL queries.

## Grafana Examples

See [EXAMPLES.md](EXAMPLES.md) for sample Grafana panels and dashboards.

## Requirements

- Dispatcharr v0.34.0 or later

## Building from Source

```bash
./package.sh
```
