# Dispatcharr Prometheus Exporter

A [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) plugin that exposes metrics in Prometheus format for monitoring and alerting.

## Support

This project is maintained in my spare time. If it's saved you some headaches, a tip is always appreciated.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/sethwv)

## Installation

1. Download the latest release zip from the [releases page](https://github.com/sethwv/dispatcharr-exporter/releases).
2. In Dispatcharr, go to **Plugins** and upload the zip.
3. Restart Dispatcharr.
4. Enable the plugin and configure settings.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Auto-start Server | `false` | Automatically start metrics server when Dispatcharr starts |
| Suppress Access Logs | `true` | Suppress HTTP access logs for /metrics requests |
| Metrics Server Port | `9192` | Port for the HTTP metrics server |
| Metrics Server Host | `0.0.0.0` | Bind address (`0.0.0.0` for all interfaces, `127.0.0.1` for local only) |
| Dispatcharr Base URL | _(empty)_ | Base URL for absolute logo URLs (e.g. `http://localhost:5656`). Leave empty for relative paths |
| Include M3U Account Metrics | `true` | Include M3U account and profile connection metrics |
| Include EPG Source Metrics | `false` | Include EPG source status metrics |
| Include Client Statistics | `false` | Include individual client connection info (may expose sensitive data) |
| Include Source URLs | `false` | Include server URLs and XC usernames in metrics. Disable before sharing output for troubleshooting |
| Include User Statistics | `false` | Include per-user metrics (user info, stream limits, active streams) |

## Usage

Once the server is started, metrics are available at:

```
http://your-dispatcharr-host:9192/metrics
http://your-dispatcharr-host:9192/health
```

You may need to map port 9192 if running in Docker.

## Plugin Actions

- **Start Metrics Server** - Start the HTTP server on the configured port
- **Stop Metrics Server** - Stop the HTTP server
- **Restart Metrics Server** - Restart the server (useful after changing settings)
- **Server Status** - Check if the server is running

## Metrics Reference

See [METRICS.md](METRICS.md) for all available metrics, labels, and example PromQL queries.

## Grafana Examples

See [EXAMPLES.md](EXAMPLES.md) for sample Grafana panels and dashboards.

## Requirements

- Dispatcharr v0.19.0 or later

## Building from Source

```bash
./package.sh
```