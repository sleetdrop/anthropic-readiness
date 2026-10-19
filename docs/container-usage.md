# Containers

## Personal local Web workspace

```sh
docker compose up --build -d
```

Open [http://localhost:8765](http://localhost:8765). Compose selects the `web` target,
publishes `127.0.0.1:8765:8765`, and runs UID/GID 10001 with a read-only root,
dropped capabilities, no-new-privileges and a bounded temporary filesystem. One
named volume stores the index, immutable plans, progress, evidence and exports.
No Docker socket, runtime Node/browser, source checkout or host Python is needed.
The container listens on `0.0.0.0` internally; its published port remains local.
The service is intended for one person's computer, not shared remote hosting.

Stopping or replacing the service retains history. A replacement reconciles saved
jobs into terminal states and never automatically resumes work or restores keys.
The 15-second stop grace period permits bounded worker cancellation and durable
finalization. Keep a backup of the stopped service's data volume before moving
between software versions; an older binary may reject a newer index schema.
`docker compose down` retains the volume; `down --volumes` deliberately deletes it.

Configuration/preview, history, reconnects and exports send no model request.
Start explicitly admits the frozen 15-minute plan. One assessment executes at a
time with eight waiting slots. Budget and capture limits still apply to internal
models. Cancellation preserves completed evidence and labels incomplete records.
Web exports are on demand; CLI execution continues to write reports automatically.

Browser-entered credentials are start-only task memory, not saved preset values.
Server credential references are optional: explicitly pass `--credential-env NAME`
and inject that variable into the container at runtime through private deployment
configuration. The checked-in Compose file sets no credential variables. Do not
put credentials in image arguments, command values, public overrides or reports.
A report/evidence export can still contain business content; review it before sharing.

## Host endpoints and custom ports

`127.0.0.1` inside a container means that container. For a proxy on the Docker
Desktop host, explicitly enter `http://host.docker.internal:PORT/v1/messages`.
The application never rewrites localhost. On Linux, add the following to a private
Compose override when host access is intended:

```yaml
services:
  readiness:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

The target must actually listen on an interface reachable from that gateway; a
host process restricted to loopback is not universally reachable this way on
Linux. Test routing using an owned synthetic server before sending credentials.
These are container routing rules, not a claim that a particular model is compatible.

If port 8765 is occupied, keep the server port, host mapping and browser origin in
agreement. For example, change both published/container ports to 8766 and supply
`serve --host 0.0.0.0 --port 8766 --data-dir /data` as the service command. Forwarding
a different external port without updating the server settings fails its strict
Host/Origin checks. Do not publish on all host interfaces for the local deployment.

## CLI image

Build the `runtime` target for your architecture (`linux/amd64` on x86 hosts):

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

The default UID is 10001. A host-user override gives bind-mounted output the host
owner's ID; the output directory must be writable, and every run needs a fresh
absent `--out` path. Mount private configuration read-only outside the build context.
Replay can run with `--network none`; real calls require an explicit network,
`--allow-live`, finite budgets and the configured credential variable. Web and CLI
images share the same engine and source contract; their dependencies stay separate.

## Maintainer acceptance

The product is built and tested in Linux containers. The stdlib-only Docker
orchestrator runs on a host/CI runner with Python 3.11+ and Docker; it imports no
product package and needs no Docker socket in the default Dev Container:

```sh
python3 scripts/check_images.py --platform linux/arm64 --targets runtime,web
python3 scripts/check_images.py --platform linux/amd64 --targets runtime,web
```

Full acceptance builds both runtime targets plus dev, prepares Python/npm/Chromium,
disconnects the disposable dev container's external network, and runs the complete
offline graph. Development tooling uses the Docker engine's native architecture;
the requested `--platform` still selects both actual CLI/Web runtime images. For
example, an arm64 engine tests its complete native Linux developer/browser baseline
and separately executes requested amd64 CLI/Web images under emulation. A runtime
image contains no browser, and this does not certify an emulated amd64 developer
browser. Native GitHub runners select their own matching developer architecture.
Separate CLI checks cover nonroot/read-only operation, replay and
signals. Web checks exercise installed pages/assets, four synthetic cases, hash-
verified exports, cancellation, persistent-volume replacement with active/queued
jobs, preserved history and an owned synthetic Docker-host route. No real endpoint
is used. On Docker Desktop the owned host peer is published on loopback. On Linux,
the controller resolves and validates Docker's private bridge gateway and publishes
only the synthetic peer on that interface, with an explicit host-gateway alias.
Public, loopback, multicast and unspecified gateway addresses are rejected. This
accounts for Docker's [host-only loopback publication](https://docs.docker.com/engine/network/port-publishing/);
the user's Web listener always remains on host loopback. Owned containers, networks
and run-data volumes are cleaned up. Local Desktop results do not establish that
the Linux-host CI route has executed.

Disposable development containers reuse public browser tools in named volumes
`anthropic-readiness-playwright-ARCH-REVISION`, labelled with the platform and
npm-locked Chromium revision. The locked installer still runs before network
disconnection, followed by actual browser launch/version and full-suite checks;
cache presence alone cannot pass acceptance. These caches contain no target data
and are never mounted in runtime images. They persist separately from disposable
run volumes; remove an unused named cache explicitly to reclaim disk space.

`--scope smoke` checks both selected runtime targets without the complete dev/
restart/host-route matrix; it cannot substitute for full acceptance. `--targets
runtime` or `web` selects that image explicitly. `--skip-build` is debug-only and
cannot produce a passing acceptance result. Missing tools/platforms are BLOCKED,
not PASS. Native and emulated observations are labeled separately.

Version 2.1 image records separately identify the observed Docker engine, development
platform/execution and runtime platform/execution, alongside selected targets,
required-check gaps, context hashes and inspected image identities. Version 2.0
records remain readable without adding facts they did not record; Stage A 1.0
records remain historical artifacts. All observations stay under ignored
`artifacts/images`. Browser prerequisites check numeric fidelity, and a black/white
contrast calibration joins the full suite. An invalid browser measurement environment
cannot pass by suppressing contrast rules or skipping tests. Network preparation may be
slow; keep original locked sources and extended timeouts rather than silently
switching versions. Weekly/manual GitHub jobs run the same two-architecture full
matrix without registry publication. Docker Hub setup/pushing is a later explicitly
authorized operation, not part of these local checks.

## Portable diagnosis in a local Web volume

The workbench imports a ZIP through an explicit checked preview/activation flow;
importing or opening it sends no model request. A baseline is a retained read-only
source, not a credential or reusable arbitrary request template. Configure this
computer's endpoint/key, review the full original scope and conditions, then start
an explicit retest. Select that baseline in Compare before exporting if the new
report should include the paired checks. Closing/restarting never starts a job.

New exports use presentation 3.0, explicit Chinese/English and light/dark/system
choices, a document-view and agent guide. An export preview is invalidated by a
presentation change. Standalone files read offline; full ZIPs also retain original
source/evidence and are not anonymized. Review endpoint/model/business context
before sharing. Legacy/partial/evidence-omitted imports cannot establish verified
repair; hashes are not signatures or provider authentication.

The existing full image controller now requires `web-diagnostic-import`,
`web-diagnostic-retest` and `web-import-persistence` observations. It transfers only
the source ZIP to a separate receiver volume, supplies an ephemeral receiver key,
executes all four cases, exports the comparison and restarts that receiver. Exact
archive/export bytes and unchanged request counts are checked after restart.
Old JSON export compatibility is checked separately from current presentation.
The installed-template probe compiles the current template inventory. These are
synthetic observations of the selected image, not endpoint certification.
