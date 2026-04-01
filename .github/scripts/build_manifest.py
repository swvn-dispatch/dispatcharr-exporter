#!/usr/bin/env python3
"""
Build the Dispatcharr plugin repo manifests from GitHub Releases.

Configuration is read from .github/workflows/manifest-config.json.
Outputs are written to _manifest_out/.

Required environment variables:
  REPO          e.g. "owner/repo-name"
  GH_TOKEN      GitHub token (used by the `gh` CLI)
  GITHUB_OUTPUT path to the GitHub Actions step-output file
"""

import hashlib
import io
import json
import os
import subprocess
import sys
import urllib.request
import zipfile

CONFIG_FILE = ".github/workflows/manifest-config.json"
OUT_DIR = "_manifest_out"


def gh(*args):
    """Run a `gh` CLI command and return parsed JSON output."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def set_output(key, value):
    gho = os.environ.get("GITHUB_OUTPUT", "")
    if gho:
        with open(gho, "a") as f:
            f.write(f"{key}={value}\n")


def resolve_commit(repo, tag):
    """Return (commit_sha, commit_sha_short) for a tag, following annotated tags."""
    try:
        raw = gh("api", f"repos/{repo}/git/refs/tags/{tag}", "--jq", ".object | {sha, type}")
        obj = json.loads(raw)
        sha = obj["sha"]
        if obj["type"] == "tag":
            # Annotated tag – dereference to the commit
            sha = gh("api", f"repos/{repo}/git/tags/{sha}", "--jq", ".object.sha")
        return sha, sha[:7]
    except Exception as exc:
        print(f"  Warning: could not resolve commit for {tag}: {exc}", flush=True)
        return None, None


def fetch_zip(url):
    """Download a zip from url and return raw bytes, or None on failure."""
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except Exception as exc:
        print(f"  Warning: download failed ({url}): {exc}", flush=True)
        return None


def min_ver_from_zip(data):
    """Extract min_dispatcharr_version from plugin.json inside a zip."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            matches = [n for n in zf.namelist() if n.endswith("plugin.json")]
            if matches:
                pj = json.loads(zf.read(matches[0]))
                return pj.get("min_dispatcharr_version")
    except Exception as exc:
        print(f"  Warning: could not read plugin.json from zip: {exc}", flush=True)
    return None


def main():
    repo = os.environ["REPO"]

    # Load config
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    SLUG = config["slug"]
    plugin_json_path = config.get("plugin_json", "src/plugin.json")
    logo_path = config.get("logo", "src/logo.png")

    set_output("slug", SLUG)
    set_output("logo", logo_path)

    # Load current plugin metadata (used for display fields)
    with open(plugin_json_path) as f:
        meta = json.load(f)

    # Fetch all releases (paginated)
    print("Fetching releases...", flush=True)
    releases = json.loads(gh("api", "--paginate", f"repos/{repo}/releases"))

    # Process releases newest-first, skipping drafts and prereleases
    versions = []
    for rel in sorted(releases, key=lambda r: r["published_at"], reverse=True):
        if rel["draft"] or rel["prerelease"]:
            continue

        tag = rel["tag_name"]
        version = tag.lstrip("v")

        # Find the release zip, skipping any pre-release assets
        asset = next(
            (
                a
                for a in rel["assets"]
                if a["name"].endswith(".zip") and "-pre" not in a["name"]
            ),
            None,
        )
        if not asset:
            print(f"  {tag}: no zip asset – skipping")
            continue

        url = asset["browser_download_url"]
        print(f"Processing {version}: {url}", flush=True)

        data = fetch_zip(url)
        if data is None:
            continue

        sha256 = hashlib.sha256(data).hexdigest()
        min_ver = min_ver_from_zip(data)
        commit_sha, commit_short = resolve_commit(repo, tag)

        entry = {
            "version": version,
            "url": url,
            "checksum_sha256": sha256,
            "build_timestamp": rel["published_at"],
        }
        if commit_sha:
            entry["commit_sha"] = commit_sha
            entry["commit_sha_short"] = commit_short
        if min_ver:
            entry["min_dispatcharr_version"] = min_ver

        versions.append(entry)
        print(f"  -> ok  sha256={sha256[:16]}...", flush=True)

    if not versions:
        print("\nNo qualifying releases found – nothing to publish.")
        set_output("has_releases", "false")
        sys.exit(0)

    latest = versions[0]
    latest_ver = latest["version"]

    registry_url = f"https://github.com/{repo}"
    root_url = f"https://raw.githubusercontent.com/{repo}/manifest"

    # Build the plugin entry for the root manifest
    plugin_entry = {
        "slug": SLUG,
        "name": meta.get("name", "Dispatcharr Exporter"),
        "description": meta.get("description", ""),
        "author": meta.get("author", ""),
        "license": meta.get("license", "MIT"),
        "latest_version": latest_ver,
        "last_updated": latest.get("build_timestamp"),
        "manifest_url": f"plugins/{SLUG}/manifest.json",
        "latest_url": latest["url"],
        "latest_sha256": latest["checksum_sha256"],
        "icon_url": f"plugins/{SLUG}/logo.png",
        "min_dispatcharr_version": latest.get("min_dispatcharr_version"),
        "discord_thread": meta.get("discord_thread"),
        "help_url": meta.get("help_url"),
    }
    # Drop keys with no value
    plugin_entry = {k: v for k, v in plugin_entry.items() if v is not None}

    root_manifest = {
        "registry_name": meta.get("name", "Dispatcharr Exporter"),
        "registry_url": registry_url,
        "root_url": root_url,
        "plugins": [plugin_entry],
    }

    per_plugin_manifest = {
        "slug": SLUG,
        "name": meta.get("name", "Dispatcharr Exporter"),
        "description": meta.get("description", ""),
        "author": meta.get("author", ""),
        "license": meta.get("license", "MIT"),
        "latest_version": latest_ver,
        "versions": versions,
        "latest": {**latest},
    }

    # Write output files
    plugin_out = os.path.join(OUT_DIR, "plugins", SLUG)
    os.makedirs(plugin_out, exist_ok=True)

    with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
        json.dump(root_manifest, f, indent=2)
        f.write("\n")

    with open(os.path.join(plugin_out, "manifest.json"), "w") as f:
        json.dump(per_plugin_manifest, f, indent=2)
        f.write("\n")

    print(f"\nDone – {len(versions)} version(s), latest {latest_ver}")
    set_output("has_releases", "true")


if __name__ == "__main__":
    main()
