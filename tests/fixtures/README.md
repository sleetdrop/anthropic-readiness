# Protocol fixtures

The captures under `contracts/` are synthetic normal and faulty controls.
They test specific protocol and task rules. The directory version identifies
that fixture set, not an npm release.

Preserve exact bytes, including SSE frame delimiters and trailing newlines.
Git text conversion is disabled for these files. Keep a passing comparison
when adding a fault, and keep private service captures out of this directory.
