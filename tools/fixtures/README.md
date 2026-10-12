# Administrative API fixtures

These offline fixtures preserve observed endpoint shapes without storing credentials. They do not replace a fresh read of live policy before administration.

`main-protection-2026-10-12.json` is the complete public-policy JSON body captured on 2026-10-12 using a read-only GET to `repos/HodeTech/Tyrne/branches/main/protection`, GitHub API version `2022-11-28`. Only JSON formatting changed; all values, URL metadata and context ordering are retained. The corresponding GraphQL classic-rule baseline is versioned separately in `.github/branch-protection/main.json`.

The test requires normalization of this actual response to preserve the full committed policy. Unknown extensions still fail closed. In particular, review dismissal/bypass actors and enforcement scope are policy, so this fixture does not authorize discarding them. `name` and `protection_url` from a branch-summary response do not widen the protection endpoint's supported schema. An API shape outside this capture needs explicit endpoint/semantic review before use; no administration write is attempted to infer it.

Primary references: [Get branch protection](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection), [Get a branch](https://docs.github.com/en/rest/branches/branches#get-a-branch).
