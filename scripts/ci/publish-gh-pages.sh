#!/usr/bin/env bash
# Publish files to the gh-pages branch. Used only by GitHub Actions
# (deploy.yml and daily.yml); humans never push to gh-pages.
#
# Usage: scripts/ci/publish-gh-pages.sh <mode> <source_dir> <commit_message>
#
#   mode=site  Replace everything on gh-pages with <source_dir>, EXCEPT the
#              data/ folder, which holds the pipeline output and is preserved.
#   mode=data  Copy <source_dir> into gh-pages/data/ (adds and overwrites,
#              never deletes), e.g. gold/ and diamond/ from the daily run.
#
# The repository must be checked out with push access to gh-pages: the
# workflows use the GH_PAGES_DEPLOY_KEY deploy key, the only actor allowed to
# bypass the gh-pages ruleset. Creates gh-pages on first use.
set -euo pipefail

mode="${1:?usage: publish-gh-pages.sh <site|data> <source_dir> <message>}"
src="${2:?source directory required}"
message="${3:?commit message required}"
worktree="${GH_PAGES_WORKTREE:-.gh-pages}"

src="$(cd "$src" && pwd)"
rm -rf "$worktree"
git worktree prune

if git ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
  git fetch --depth=1 origin gh-pages
  git worktree add -B gh-pages "$worktree" FETCH_HEAD
else
  echo "gh-pages does not exist yet: creating it."
  git worktree add --orphan -b gh-pages "$worktree"
fi

case "$mode" in
  site)
    # Delete the previous site but keep data/ and git metadata.
    find "$worktree" -mindepth 1 -maxdepth 1 ! -name .git ! -name data -exec rm -rf {} +
    rsync -a --exclude '/data' "$src"/ "$worktree"/
    touch "$worktree/.nojekyll"
    ;;
  data)
    mkdir -p "$worktree/data"
    rsync -a "$src"/ "$worktree/data"/
    ;;
  *)
    echo "unknown mode '$mode' (expected 'site' or 'data')" >&2
    exit 2
    ;;
esac

cd "$worktree"
git add -A
if git diff --cached --quiet; then
  echo "gh-pages is already up to date."
  exit 0
fi
git -c user.name="github-actions[bot]" \
    -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
    commit --quiet -m "$message"
git push origin HEAD:refs/heads/gh-pages
echo "Published to gh-pages: $message"
