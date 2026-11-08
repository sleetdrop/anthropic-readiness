#!/usr/bin/env bash
# Publish an existing Git tag to npm, with interactive login and OTP.
set -euo pipefail

fail() { printf 'error: %s\n' "$*" >&2; exit 1; }

DRY_RUN=false
VERIFY_ONLY=false
DIST_TAG=""
for argument in "$@"; do
  case "$argument" in
    --dry-run) DRY_RUN=true ;;
    --verify-only) VERIFY_ONLY=true ;;
    latest|next) [[ -z "$DIST_TAG" ]] || fail "Specify one npm dist-tag."; DIST_TAG="$argument" ;;
    -h|--help) echo "Usage: ./scripts/publish.sh [--dry-run | --verify-only] [latest|next]"; exit 0 ;;
    *) fail "Unknown argument: $argument" ;;
  esac
done
if [[ "$DRY_RUN" == true && "$VERIFY_ONLY" == true ]]; then
  fail "Choose either --dry-run or --verify-only."
fi

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
VERSION_TAG="v$VERSION"
SOURCE_COMMIT="$(git rev-parse --verify "refs/tags/$VERSION_TAG^{commit}" 2>/dev/null)" ||
  fail "Prepare the $VERSION_TAG source tag separately. This helper does not create Git tags."
git diff --quiet "$SOURCE_COMMIT" -- package.json package-lock.json bin templates README.md LICENSE ||
  fail "Package inputs differ from $VERSION_TAG. Review the intended source release first."

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

RELEASE_DIR="$REPO_ROOT/artifacts/releases/$VERSION"
archive="$RELEASE_DIR/sleetdrop-anthropic-readiness-$VERSION.tgz"

if [[ "$VERIFY_ONLY" == true ]]; then
  [[ -f "$archive" ]] || fail "Saved publish archive is missing: $archive. Use --dry-run to recreate it from the source tag."
  integrity="$(node -p '"sha512-" + require("node:crypto").createHash("sha512").update(require("node:fs").readFileSync(process.argv[1])).digest("base64")' "$archive")"
  echo "Verifying the published version, archive integrity, and npm tag..."
  fetch_args=(--registry "$REGISTRY" --prefer-online --fetch-retries=0 --fetch-timeout=15000)
  registry_version="$(npm view "$PACKAGE@$VERSION" version "${fetch_args[@]}" 2>/dev/null || true)"
  registry_integrity="$(npm view "$PACKAGE@$VERSION" dist.integrity "${fetch_args[@]}" 2>/dev/null || true)"
  registry_tag="$(npm view "$PACKAGE" "dist-tags.$DIST_TAG" "${fetch_args[@]}" 2>/dev/null || true)"
  if [[ -z "$registry_version" || -z "$registry_integrity" || -z "$registry_tag" ]]; then
    echo "Verification pending: registry metadata is unavailable. npm may still be processing the package."
    echo "Try ./scripts/publish.sh --verify-only $DIST_TAG later. Do not republish."
    exit 2
  fi
  [[ "$registry_version" == "$VERSION" ]] || fail "Version mismatch: expected $VERSION, found $registry_version. Do not republish."
  [[ "$registry_integrity" == "$integrity" ]] || fail "Archive integrity mismatch. Check the published package; do not republish."
  [[ "$registry_tag" == "$VERSION" ]] || fail "npm tag $DIST_TAG points to $registry_tag, not $VERSION. Check the registry tag; do not republish."

  echo "Checking workbench creation from the registry package..."
  publish_tmp="$(mktemp -d "${TMPDIR:-/tmp}/anthropic-readiness-verify.XXXXXX")"
  trap 'rm -rf "$publish_tmp"' EXIT
  (
    cd "$publish_tmp"
    npm exec --yes "${fetch_args[@]}" --package "$PACKAGE@$VERSION" -- \
      anthropic-readiness init "$publish_tmp/workbench"
  ) || fail "Registry installation could not be verified. Rerun --verify-only later; do not republish."
  [[ -f "$publish_tmp/workbench/AGENTS.md" && -f "$publish_tmp/workbench/.agents/skills/anthropic-readiness/SKILL.md" ]] ||
    fail "Registry package did not create the expected workbench."
  echo "Verified $PACKAGE@$VERSION ($DIST_TAG)."
  exit 0
fi

if [[ "$DRY_RUN" == false ]]; then
  if ! identity="$(npm whoami --registry "$REGISTRY" 2>/dev/null)"; then
    echo "Sign in to npm to continue..."
    npm login --registry "$REGISTRY"
    identity="$(npm whoami --registry "$REGISTRY")"
  fi
  [[ "$identity" == sleetdrop ]] || fail "Expected npm account sleetdrop, got $identity."
fi

echo "Checking $PACKAGE@$VERSION ($VERSION_TAG, npm tag: $DIST_TAG)..."
npm ci --ignore-scripts --registry "$REGISTRY"
npm run check

publish_tmp="$(mktemp -d "${TMPDIR:-/tmp}/anthropic-readiness-publish.XXXXXX")"
trap 'rm -rf "$publish_tmp"' EXIT
mkdir "$publish_tmp/source"
git archive "$SOURCE_COMMIT" | tar -x -C "$publish_tmp/source"
mkdir -p "$RELEASE_DIR"
npm pack "$publish_tmp/source" --ignore-scripts --json --pack-destination "$RELEASE_DIR" > "$publish_tmp/pack.json"
archive_name="$(node -p 'JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8"))[0].filename' "$publish_tmp/pack.json")"
integrity="$(node -p 'JSON.parse(require("node:fs").readFileSync(process.argv[1], "utf8"))[0].integrity' "$publish_tmp/pack.json")"
[[ "$archive_name" == "sleetdrop-anthropic-readiness-$VERSION.tgz" && "$integrity" == sha512-* ]] ||
  fail "Unexpected npm archive metadata."
publish_args=("$archive" --access public --registry "$REGISTRY" --tag "$DIST_TAG")

if [[ "$DRY_RUN" == true ]]; then
  npm publish "${publish_args[@]}" --dry-run
  echo "Dry run complete. Archive: $archive"
  exit 0
fi

echo "Publishing $PACKAGE@$VERSION as $identity. Complete npm's verification prompt."
# Keep stdin and stdout attached so npm can request OTP or browser verification.
npm publish "${publish_args[@]}"

echo "Publication submitted: $PACKAGE@$VERSION ($DIST_TAG). npm may take a few minutes to make it available."
echo "Registry verification has not run. Later, run: ./scripts/publish.sh --verify-only $DIST_TAG"
