#!/usr/bin/env bash
# Copy the data already published on gh-pages (gold history, diamond payloads
# and status) into a storage folder. Used by refresh.yml so a KPI that cannot
# be recomputed keeps its last valid values (shown as stale), and so the status
# job sees what visitors see. Read-only: never writes to gh-pages.
#
# Usage: scripts/ci/fetch-gh-pages-data.sh <storage_dir>
#
# No-op when gh-pages or its data/ folder does not exist yet.
set -euo pipefail

dest="${1:?usage: fetch-gh-pages-data.sh <storage_dir>}"
mkdir -p "$dest"

if ! git ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
  echo "gh-pages does not exist yet: nothing to restore."
  exit 0
fi
git fetch --depth=1 --no-tags origin gh-pages
if ! git cat-file -e FETCH_HEAD:data 2>/dev/null; then
  echo "gh-pages has no data/ folder yet: nothing to restore."
  exit 0
fi
git archive FETCH_HEAD data | tar -x -C "$dest" --strip-components=1
echo "Restored published data into $dest:"
find "$dest" -maxdepth 2 -mindepth 1 -type d | sort
