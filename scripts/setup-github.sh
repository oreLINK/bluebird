#!/usr/bin/env bash
# One-time (and idempotent) GitHub setup for Bluebird. Run it yourself, from
# the repository root, after pushing `main` to GitHub:
#
#   scripts/setup-github.sh
#
# Requires the GitHub CLI (`gh auth login`) with admin rights on the repo.
# It performs these steps, each skipped when already done:
#
#   0. Makes `main` the default branch and removes a fully merged `dev`.
#   1. Creates a write deploy key and stores its private half in the
#      GH_PAGES_DEPLOY_KEY secret (used by deploy.yml and refresh.yml).
#   2. Creates or updates two branch rulesets:
#        "Protect main":     no direct push, no force push, no deletion,
#                            changes only through pull requests with the
#                            "CI result" check passing.
#        "Protect gh-pages": nobody may push, merge or delete; only deploy
#                            keys bypass (i.e. GitHub Actions).
#   2b. Allows workflows to open pull requests (reference.yml opens one to main).
#   3. Builds the site once if gh-pages does not exist yet (deploy.yml).
#   4. Configures GitHub Pages to serve the gh-pages branch.
#   5. Runs the data refresh workflow once so the site has data.
#
# Options:
#   --rotate-key   replace the deploy key and secret
#   --no-runs      do not trigger workflows (steps 3 and 5)
set -euo pipefail

ROTATE_KEY=false
TRIGGER_RUNS=true
for arg in "$@"; do
  case "$arg" in
    --rotate-key) ROTATE_KEY=true ;;
    --no-runs) TRIGGER_RUNS=false ;;
    -h | --help) sed -n '2,24p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

KEY_TITLE="bluebird gh-pages publisher"
SECRET_NAME="GH_PAGES_DEPLOY_KEY"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

command -v gh >/dev/null || { echo "GitHub CLI 'gh' is required: https://cli.github.com" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Run 'gh auth login' first." >&2; exit 1; }

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
VISIBILITY="$(gh repo view --json visibility -q .visibility)"
say "Repository: $REPO ($VISIBILITY)"
if [ "$VISIBILITY" != "PUBLIC" ]; then
  echo "Warning: rulesets and GitHub Pages on a private repository need a paid plan (GitHub Pro or higher)."
fi

for branch in main; do
  if ! gh api "repos/$REPO/branches/$branch" >/dev/null 2>&1; then
    echo "Branch '$branch' is missing on GitHub. Push it first: git push -u origin $branch" >&2
    exit 1
  fi
done
gh api -X PATCH "repos/$REPO" -f default_branch=main >/dev/null
echo "Default branch: main."

# `main` is the only long-lived branch. Remove a leftover `dev` branch, but
# only when it has no commit that main lacks.
if gh api "repos/$REPO/branches/dev" >/dev/null 2>&1; then
  ahead="$(gh api "repos/$REPO/compare/main...dev" -q .ahead_by)"
  if [ "$ahead" = "0" ]; then
    gh api -X DELETE "repos/$REPO/git/refs/heads/dev" >/dev/null
    echo "Deleted the legacy 'dev' branch (fully merged into main)."
  else
    echo "Branch 'dev' has $ahead commit(s) missing from main: left untouched."
  fi
fi

# --------------------------------------------------------------- 1. deploy key
say "1. Deploy key and $SECRET_NAME secret"
has_secret=false
if gh secret list --repo "$REPO" --json name -q '.[].name' | grep -qx "$SECRET_NAME"; then
  has_secret=true
fi
if $has_secret && ! $ROTATE_KEY; then
  echo "Secret already present (use --rotate-key to replace it)."
else
  for id in $(gh api "repos/$REPO/keys" -q ".[] | select(.title == \"$KEY_TITLE\") | .id"); do
    gh api -X DELETE "repos/$REPO/keys/$id" >/dev/null
    echo "Removed previous deploy key $id."
  done
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  ssh-keygen -t ed25519 -N "" -C "$KEY_TITLE" -f "$tmp/key" -q
  gh repo deploy-key add "$tmp/key.pub" --repo "$REPO" --allow-write --title "$KEY_TITLE"
  gh secret set "$SECRET_NAME" --repo "$REPO" < "$tmp/key"
  rm -rf "$tmp"
  echo "Deploy key created and secret stored."
fi

# ---------------------------------------------------------------- 2. rulesets
upsert_ruleset() {
  local name="$1" body="$2" id
  id="$(gh api "repos/$REPO/rulesets" -q ".[] | select(.name == \"$name\") | .id" | head -n1)"
  if [ -n "$id" ]; then
    gh api -X PUT "repos/$REPO/rulesets/$id" --input - <<<"$body" >/dev/null
    echo "Updated ruleset '$name'."
  else
    gh api -X POST "repos/$REPO/rulesets" --input - <<<"$body" >/dev/null
    echo "Created ruleset '$name'."
  fi
}

say "2. Branch rulesets"
upsert_ruleset "Protect main" '{
  "name": "Protect main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "bypass_actors": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false } },
    { "type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": false,
        "required_status_checks": [ { "context": "CI result" } ] } }
  ]
}'
upsert_ruleset "Protect gh-pages" '{
  "name": "Protect gh-pages",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/gh-pages"], "exclude": [] } },
  "bypass_actors": [ { "actor_id": null, "actor_type": "DeployKey", "bypass_mode": "always" } ],
  "rules": [
    { "type": "creation" },
    { "type": "update" },
    { "type": "deletion" },
    { "type": "non_fast_forward" }
  ]
}'

say "2b. Workflow permissions"
gh api -X PUT "repos/$REPO/actions/permissions/workflow" \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true >/dev/null
echo "Workflows may open pull requests (default token stays read-only)."

# ------------------------------------------------------- 3. first site build
latest_run_id() {
  gh run list --repo "$REPO" --workflow "$1" --limit 1 --json databaseId -q '.[0].databaseId // empty'
}

# Trigger a workflow on main and wait for that new run (not an older one).
run_and_wait() {
  local workflow="$1" before run_id=""
  before="$(latest_run_id "$workflow")"
  gh workflow run "$workflow" --repo "$REPO" --ref main
  for _ in $(seq 1 40); do
    sleep 3
    run_id="$(latest_run_id "$workflow")"
    [ -n "$run_id" ] && [ "$run_id" != "$before" ] && break
    run_id=""
  done
  [ -n "$run_id" ] || { echo "Could not find the new $workflow run." >&2; return 1; }
  gh run watch "$run_id" --repo "$REPO" --exit-status
}

say "3. First site build"
if gh api "repos/$REPO/branches/gh-pages" >/dev/null 2>&1; then
  echo "gh-pages already exists."
elif $TRIGGER_RUNS; then
  run_and_wait deploy.yml
else
  echo "Skipped (--no-runs). Run the 'Deploy site' workflow, then re-run this script."
fi

# ------------------------------------------------------------- 4. Pages
say "4. GitHub Pages"
if ! gh api "repos/$REPO/branches/gh-pages" >/dev/null 2>&1; then
  echo "gh-pages does not exist yet; re-run this script once 'Deploy site' has succeeded."
else
  pages_body='{"build_type":"legacy","source":{"branch":"gh-pages","path":"/"}}'
  if gh api "repos/$REPO/pages" >/dev/null 2>&1; then
    gh api -X PUT "repos/$REPO/pages" --input - <<<"$pages_body" >/dev/null
  else
    gh api -X POST "repos/$REPO/pages" --input - <<<"$pages_body" >/dev/null
  fi
  echo "Pages serves gh-pages: $(gh api "repos/$REPO/pages" -q .html_url)"
fi

# ------------------------------------------------------- 5. first data run
say "5. First data run"
if $TRIGGER_RUNS && gh api "repos/$REPO/branches/gh-pages" >/dev/null 2>&1; then
  run_and_wait refresh.yml
else
  echo "Skipped. Run the 'Data refresh' workflow from the Actions tab when ready."
fi

say "Done."
