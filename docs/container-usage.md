# Containers

The development image is Linux/Python 3.12 with the pinned uv tool. Reopen the
repository in its Dev Container; `postCreateCommand` prepares locked dependencies.
Use a private configuration outside the build context. The runtime image contains
an installed wheel and runtime dependencies, with a non-root user and no source
checkout, uv, Git or development tools.

```sh
docker buildx build --platform linux/arm64 --target runtime --load \
  --build-arg VCS_REF=LOCAL_COMMIT -t anthropic-readiness:local .
mkdir -p artifacts/container-output
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,noexec,size=64m \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/artifacts/container-output:/output" \
  -v "$PWD/examples:/input:ro" \
  anthropic-readiness:local validate --target /input/target.yaml
```

Choose `linux/amd64` on x86 hosts; emulated execution must be labeled as such.
The optional user override gives bind-mounted output files the host owner's ID;
the image defaults to UID 10001. Output directories must be writable and each run
must select a new, absent `--out` directory. Mount private target files read-only.
Real calls additionally need an explicit network, `--allow-live`, a finite budget
and the named credential variable. Pure replay works with `--network none`.
Avoid putting credentials in command arguments or image build arguments.

## Maintainer acceptance

From a host with Python 3.11+ and Docker (or the Dev Container with a deliberately
provided Docker CLI/socket), run the stdlib-only image orchestrator:

```sh
python3 scripts/check_images.py --platform linux/amd64
python3 scripts/check_images.py --platform linux/arm64
```

These commands build dev/runtime, verify ordinary-user/read-only offline replay,
output retention, failure exit codes, signals and an isolated synthetic peer.
They use disposable containers and a private internal Docker network; they never
modify daemon configuration or publish images. On Docker Desktop, optional
`--host-url http://host.docker.internal:PORT` checks a separately prepared generic
synthetic server. Linux can use an explicitly routable host URL. This optional
path is reported separately from the internal peer result.

Build logs, image IDs, architecture/native-or-emulated classification, source
fingerprint and verdicts are retained under ignored `artifacts/images/`.
Preparation can download pinned dependencies; verification inside the images is
offline. Slow downloads use extended timeouts. GitHub runs the same script on
native architecture runners. No registry login/push is configured. Docker Hub
credentials and publishing can be configured with the owner in a later stage.

The full image job prepares dev dependencies, disconnects that disposable dev
container from its external network, verifies the empty network attachment list,
and only then runs the offline full graph. Synthetic HTTP tests still use that
container's loopback; the runtime peer uses a separate internal Docker network.
