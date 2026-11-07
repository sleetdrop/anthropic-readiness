# Releasing

The first public release is being prepared as `0.1.0`. Earlier package numbers
and local archives were exploratory. They are not a published release history.
Probe-contract and fixture versions identify rules and evidence independently
of the npm package version.

1. Set the package version in `package.json`, update `package-lock.json`, and
   move the relevant changelog entries under that version.
2. Run `npm ci` and `npm run check` on Node 24. Try the packed archive in a new
   workbench and record the tested scope in `docs/history/verification.md`.
3. Merge the validated changes into `main` with a clean working tree. Create
   an annotated `v<version>` tag on that commit. Do not move a published tag.
4. From the tagged checkout, run `npm pack --pack-destination /tmp`. Inspect
   the archive. Its version and contents must match the validated source;
   it must contain no targets, credentials, captures, tests, or local artifacts.
5. With explicit authorization, push `main` and the version tag, then publish
   the inspected archive with `npm publish /path/to/package.tgz --access public`.
6. Create a fresh directory from the registry package and verify initialization
   before announcing the release. Record registry verification separately from
   local archive testing.

Local commits, merges, and tags do not publish the package. Do not contact a
real diagnostic endpoint as part of release checks without authorization and
request/time bounds.
