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
        return sha, sha[:8]
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


def _plugin_json_from_zip(data):
    """Return parsed plugin.json from inside a zip, or {}."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            matches = [n for n in zf.namelist() if n.endswith("plugin.json")]
            if matches:
                return json.loads(zf.read(matches[0]))
    except Exception as exc:
        print(f"  Warning: could not read plugin.json from zip: {exc}", flush=True)
    return {}


def min_ver_from_zip(data):
    """Extract min_dispatcharr_version from plugin.json inside a zip."""
    return _plugin_json_from_zip(data).get("min_dispatcharr_version")


def version_from_zip(data):
    """Extract version string from plugin.json inside a zip."""
    return _plugin_json_from_zip(data).get("version")


def main():
    repo = os.environ["REPO"]

    # Load config
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    SLUG = config["slug"]
    plugin_json_path = config.get("plugin_json", "src/plugin.json")
    logo_path = config.get("logo", "src/logo.png")
    registry_name_override = config.get("registry_name")
    dev_tag = config.get("dev_tag")
    dev_tag_prefix = config.get("dev_tag_prefix")

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

    # Optionally include a dev build from a rolling pre-release
    dev_entry = None
    _dev_source = dev_tag or dev_tag_prefix
    if _dev_source:
        if dev_tag:
            # Fixed tag name
            print(f"\nLooking for dev pre-release '{dev_tag}'...", flush=True)
            try:
                candidates = [json.loads(gh("api", f"repos/{repo}/releases/tags/{dev_tag}"))]
            except subprocess.CalledProcessError:
                candidates = []
        else:
            # Find the latest pre-release whose tag starts with the prefix
            print(f"\nSearching for dev pre-release with prefix '{dev_tag_prefix}'...", flush=True)
            all_releases = json.loads(gh("api", "--paginate", f"repos/{repo}/releases"))
            candidates = [
                r for r in all_releases
                if r.get("prerelease") and r["tag_name"].startswith(dev_tag_prefix)
            ]
            candidates.sort(key=lambda r: r["published_at"], reverse=True)

        if not candidates:
            print(f"  No matching dev pre-release found – skipping", flush=True)
        else:
            dev_rel = candidates[0]
            if not dev_rel.get("prerelease"):
                print(f"  Release '{dev_rel['tag_name']}' is not a pre-release – skipping", flush=True)
            else:
                dev_asset = next(
                    (a for a in dev_rel["assets"] if a["name"].endswith(".zip")),
                    None,
                )
                if not dev_asset:
                    print(f"  No zip asset in dev release '{dev_rel['tag_name']}' – skipping", flush=True)
                else:
                    dev_url = dev_asset["browser_download_url"]
                    print(f"  Found '{dev_rel['tag_name']}': {dev_url}", flush=True)
                    dev_data = fetch_zip(dev_url)
                    if dev_data:
                        dev_sha256 = hashlib.sha256(dev_data).hexdigest()
                        dev_ver_str = version_from_zip(dev_data) or dev_rel["tag_name"]
                        dev_min_ver = min_ver_from_zip(dev_data)
                        dev_commit_sha, dev_commit_short = resolve_commit(repo, dev_rel["tag_name"])
                        dev_entry = {
                            "version": dev_ver_str,
                            "url": dev_url,
                            "checksum_sha256": dev_sha256,
                            "build_timestamp": dev_rel["published_at"],
                            "prerelease": True,
                        }
                        if dev_commit_sha:
                            dev_entry["commit_sha"] = dev_commit_sha
                            dev_entry["commit_sha_short"] = dev_commit_short
                        if dev_min_ver:
                            dev_entry["min_dispatcharr_version"] = dev_min_ver
                        print(f"  -> ok  sha256={dev_sha256[:16]}...", flush=True)

    if not versions and not dev_entry:
        print("\nNo qualifying releases found – nothing to publish.")
        set_output("has_releases", "false")
        sys.exit(0)

    # Root manifest always points to the latest stable release.
    # If no stable releases exist, omit the latest_* fields entirely.
    latest = versions[0] if versions else None
    latest_ver = latest["version"] if latest else None

    registry_url = f"https://github.com/{repo}"
    root_url = f"https://raw.githubusercontent.com/{repo}/manifest"

    # Build the plugin entry for the root manifest
    plugin_entry = {
        "slug": SLUG,
        "name": meta.get("name", SLUG),
        "description": meta.get("description", ""),
        "author": meta.get("author", ""),
        "license": meta.get("license", "MIT"),
        "latest_version": latest_ver,
        "last_updated": latest.get("build_timestamp") if latest else None,
        "manifest_url": f"plugins/{SLUG}/manifest.json",
        "latest_url": latest["url"] if latest else None,
        "latest_sha256": latest["checksum_sha256"] if latest else None,
        "icon_url": f"plugins/{SLUG}/logo.png",
        "min_dispatcharr_version": latest.get("min_dispatcharr_version") if latest else None,
        "discord_thread": meta.get("discord_thread"),
        "help_url": meta.get("help_url"),
    }
    # Drop keys with no value
    plugin_entry = {k: v for k, v in plugin_entry.items() if v is not None}

    root_manifest = {
        "registry_name": registry_name_override or meta.get("name", SLUG),
        "registry_url": registry_url,
        "root_url": root_url,
        "plugins": [plugin_entry],
    }

    per_plugin_manifest = {
        "slug": SLUG,
        "name": meta.get("name", SLUG),
        "description": meta.get("description", ""),
        "author": meta.get("author", ""),
        "license": meta.get("license", "MIT"),
        "latest_version": latest_ver,
        "versions": versions + ([dev_entry] if dev_entry else []),
        "latest": {**latest} if latest else None,
    }
    # Drop top-level keys with no value
    per_plugin_manifest = {k: v for k, v in per_plugin_manifest.items() if v is not None}

    # Write output files
    plugin_out = os.path.join(OUT_DIR, "plugins", SLUG)
    os.makedirs(plugin_out, exist_ok=True)

    with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
        json.dump(root_manifest, f, indent=2)
        f.write("\n")

    with open(os.path.join(plugin_out, "manifest.json"), "w") as f:
        json.dump(per_plugin_manifest, f, indent=2)
        f.write("\n")

    total = len(versions) + (1 if dev_entry else 0)
    print(f"\nDone – {total} version(s) ({len(versions)} stable{', 1 dev' if dev_entry else ''}), latest stable {latest_ver}")
    set_output("has_releases", "true")


if __name__ == "__main__":
    main()
