# Development history

These records preserve earlier implementation work and verification evidence.
They describe the paths, commands, and scope of the checkout at the time;
use the referenced commit when reproducing an old result.

- [Verification record](verification.md)
- [2026-11-05 implementation review](reviews/2026-11-05-current-implementation.md)

The standalone Python/Web application and early Skill prototype are retained
at commit `8048934`. For example:

```sh
git show 8048934:docs/harness/progress.md
git show 8048934:docs/reviews/2026-11-02-llm-comply-maturity.md
```

Earlier package numbers and local archives were internal exploration, not
public releases. The current design is in [architecture](../architecture.md)
and the current release state is in [maintainer status](../CONTINUE.md).
