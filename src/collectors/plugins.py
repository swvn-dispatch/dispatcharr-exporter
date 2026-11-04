"""Dispatcharr plugin and plugin-repository metric collection."""

import logging

logger = logging.getLogger(__name__)


def collect_plugin_metrics(context, writer) -> None:
    """Write installed plugin and repository health metrics."""
    try:
        from apps.plugins.models import PluginConfig, PluginRepo
    except ImportError:
        return

    include_urls = context.settings.get("include_source_urls", False)
    try:
        plugins = PluginConfig.objects.all()
        totals = writer.gauge("dispatcharr_plugins", "Total number of installed plugins")
        totals.add(plugins.count(), [("status", "total")])
        totals.add(plugins.filter(enabled=True).count(), [("status", "enabled")])
        totals.add(plugins.filter(deprecated=True).count(), [("status", "deprecated")])
        totals.add(plugins.filter(source_repo__isnull=False).count(), [("status", "managed")])
        plugin_info = writer.info("dispatcharr_plugin_info", "Installed plugin metadata")
        for plugin in plugins:
            plugin_info.add([
                ("key", plugin.key),
                ("name", plugin.name),
                ("version", plugin.version),
                ("enabled", str(plugin.enabled).lower()),
                ("deprecated", str(plugin.deprecated).lower()),
                ("is_managed", str(plugin.is_managed).lower()),
            ])

        repos = PluginRepo.objects.all()
        repo_totals = writer.gauge("dispatcharr_plugin_repos", "Total number of configured plugin repositories")
        repo_totals.add(repos.count(), [("status", "total")])
        repo_totals.add(repos.filter(enabled=True).count(), [("status", "enabled")])
        repo_totals.add(repos.filter(is_official=True).count(), [("status", "official")])
        repo_info = writer.info("dispatcharr_plugin_repo_info", "Plugin repository metadata")
        last_fetch = writer.gauge(
            "dispatcharr_plugin_repo_last_fetch_timestamp",
            "Unix timestamp of the last manifest fetch for this plugin repository",
        )
        for repo in repos:
            labels = [
                ("name", repo.name),
                ("is_official", str(repo.is_official).lower()),
                ("enabled", str(repo.enabled).lower()),
                ("signature_verified", str(repo.signature_verified).lower()),
                ("last_fetch_status", repo.last_fetch_status),
            ]
            if include_urls:
                labels.append(("url", repo.url))
            repo_info.add(labels)
            if repo.last_fetched:
                last_fetch.add(repo.last_fetched.timestamp(), [
                    ("name", repo.name),
                    ("is_official", str(repo.is_official).lower()),
                ])
    except Exception as exc:
        logger.error("Error collecting plugin metrics: %s", exc)
    writer.separator()
