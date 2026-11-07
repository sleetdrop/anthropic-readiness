#!/usr/bin/env bash
# Publish the current npm package, with npm handling interactive login and OTP.
set -euo pipefail

fail() { printf 'error: %s\n' "$*" >&2; exit 1; }

DRY_RUN=false
DIST_TAG=""
for argument in "$@"; do
  case "$argument" in
    --dry-run) DRY_RUN=true ;;
    latest|next) [[ -z "$DIST_TAG" ]] || fail "Specify one npm dist-tag."; DIST_TAG="$argument" ;;
    -h|--help) echo "Usage: ./scripts/publish.sh [--dry-run] [latest|next]"; exit 0 ;;
    *) fail "Unknown argument: $argument" ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

is_node24() {
  command -v node >/dev/null 2>&1 && [[ "$(node -p 'process.versions.node.split(".")[0]')" == 24 ]]
}
if ! is_node24 && command -v brew >/dev/null 2>&1; then
  node_prefix="$(brew --prefix node@24 2>/dev/null || true)"
  if [[ -n "$node_prefix" && -x "$node_prefix/bin/node" ]]; then export PATH="$node_prefix/bin:$PATH"; fi
fi
is_node24 || fail "Node 24 LTS is required. Activate it and run this script again."
command -v npm >/dev/null 2>&1 || fail "npm is required."

REGISTRY="https://registry.npmjs.org/"
export npm_config_registry="$REGISTRY"
export npm_config_cache="$REPO_ROOT/artifacts/npm-cache"
PACKAGE="$(node -p 'require("./package.json").name')"
VERSION="$(node -p 'require("./package.json").version')"
[[ "$PACKAGE" == '@sleetdrop/anthropic-readiness' ]] || fail "Unexpected package: $PACKAGE"
if [[ -z "$DIST_TAG" ]]; then
  case "$VERSION" in *-*) DIST_TAG=next ;; *) DIST_TAG=latest ;; esac
fi
if [[ "$DIST_TAG" == latest && "$VERSION" == *-* ]]; then
  fail "Prerelease $VERSION must use next, not latest."
fi

scope_registry="$(npm config get @sleetdrop:registry)"
case "${scope_registry%/}" in
  ""|undefined|null|"${REGISTRY%/}") ;;
  *) fail "The @sleetdrop scope overrides npmjs.org. Check npm registry configuration before publishing." ;;
esac

if [[ "$DRY_RUN" == false ]]; then
  if ! identity="$(npm whoami --registry "$REGISTRY" 2>/dev/null)"; then
    echo "Sign in to npm to continue..."
    npm login --registry "$REGISTRY"
    identity="$(npm whoami --registry "$REGISTRY")"
  fi
  [[ "$identity" == sleetdrop ]] || fail "Expected npm account sleetdrop, got $identity."
fi

echo "Checking $PACKAGE@$VERSION (npm tag: $DIST_TAG)..."
npm ci --ignore-scripts --registry "$REGISTRY"
npm run check

publish_tmp="$(mktemp -d "${TMPDIR:-/tmp}/anthropic-readiness-publish.XXXXXX")"
trap 'rm -rf "$publish_tmp"' EXIT
RELEASE_DIR="$REPO_ROOT/artifacts/releases/$VERSION"
mkdir -p "$RELEASE_DIR"
npm pack "$REPO_ROOT" --ignore-scripts --json --pack-destination "$RELEASE_DIR" > "$publish_tmp/pack.json"
archive_name="$(node -p 'JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8"))[0].filename' "$publish_tmp/pack.json")"
integrity="$(node -p 'JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8"))[0].integrity' "$publish_tmp/pack.json")"
[[ "$archive_name" == "sleetdrop-anthropic-readiness-$VERSION.tgz" && "$integrity" == sha512-* ]] ||
  fail "Unexpected npm archive metadata."
archive="$RELEASE_DIR/$archive_name"
publish_args=("$archive" --access public --registry "$REGISTRY" --tag "$DIST_TAG")

if [[ "$DRY_RUN" == true ]]; then
  npm publish "${publish_args[@]}" --dry-run
  echo "Dry run complete. Archive: $archive"
  exit 0
fi

echo "Publishing $PACKAGE@$VERSION as $identity. Complete npm's verification prompt."
# Keep stdin and stdout attached so npm can request OTP or browser verification.
npm publish "${publish_args[@]}"

echo "Verifying the published version, archive integrity, and npm tag..."
verified=false
for attempt in 1 2 3; do
  registry_version="$(npm view "$PACKAGE@$VERSION" version --registry "$REGISTRY" 2>/dev/null || true)"
  registry_integrity="$(npm view "$PACKAGE@$VERSION" dist.integrity --registry "$REGISTRY" 2>/dev/null || true)"
  registry_tag="$(npm view "$PACKAGE" "dist-tags.$DIST_TAG" --registry "$REGISTRY" 2>/dev/null || true)"
  if [[ "$registry_version" == "$VERSION" && "$registry_integrity" == "$integrity" && "$registry_tag" == "$VERSION" ]]; then
    verified=true
    break
  fi
  if [[ "$attempt" != 3 ]]; then sleep 2; fi
done
[[ "$verified" == true ]] || fail "Publication may have succeeded, but registry verification failed. Check npm before retrying."

echo "Checking workbench creation from the registry package..."
(
  cd "$publish_tmp"
  npm exec --yes --registry "$REGISTRY" --package "$PACKAGE@$VERSION" -- \
    anthropic-readiness init "$publish_tmp/workbench"
)
[[ -f "$publish_tmp/workbench/AGENTS.md" && -f "$publish_tmp/workbench/.agents/skills/anthropic-readiness/SKILL.md" ]] ||
  fail "Published package did not create the expected workbench."
echo "Published and verified $PACKAGE@$VERSION ($DIST_TAG)."
