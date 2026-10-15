# PR49 evidence archive and citation migration

This records the actual archive/recovery gates, bounded local history adoption and lossless navigation migration under Accepted ADR-0044. It preserves the initial generator failure and its reproducible correction; both fresh complementary migration review rounds and the prevention/final hosted unit remain pending.

## Verified boundaries

- Original executed tip: `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4`; main anchor: `c16997e003fbd1726d1205734380394781c52002`.
- Governance-inclusive archival tip: `6c84f0d51820f858b31789ad51ecb612ed74e186`; trial/adopted local tip: `32bdc16e4f19a654fda19abc202d3b4ad496d406`.
- [Immutable evidence release](https://github.com/HodeTech/Tyrne/releases/tag/evidence-pr-49-2026-10-16), release ID414293393, nine assets. GitHub reports immutable:true, draft:false, prerelease:true; the evidence tag points only to clean main. Product release/version/signature claims remain outside this archive profile.
- Complete draft download and a separate post-publication download from all browser asset URLs without credentials/cookies/Authorization headers pass published-size and SHA-256 checks. Each downloaded bundle independently clones/restores the governance-inclusive tip, passes full Git integrity checks and recovers original97; all804 tar members and recovered payload files match the original manifest,134293614 bytes. Original local bundle and independent local copies remain outside Git.
- Isolated filtering covered151 commits (145 original plus six governance);150 retained mapped trees equal the original tree minus only804 approved paths. Messages/authors/committers are unchanged. One evidence-only commit `2b62391386c7d0d90e41abb86348c2d1d1506eb6` became empty; main's object/tree remains unchanged. No candidate path is reachable through filtered development.
- Only after verified immutable publication/public recovery was filtered development adopted locally. Other local heads/tags remain unchanged; remote development remains original97. No reflog expiry, aggressive GC, remote backup ref or hidden GitHub object-purge claim.

## Citation preservation

The [catalog](2026-10-16-pr49-evidence-catalog.md) and [machine catalog](2026-10-16-pr49-evidence-catalog.json) provide asset IDs/digests, all151 mappings, ten dataset groups and exact-member recovery. Production Markdown-reader enumeration identifies348 links in46 documents. Every destination now reaches its catalog group; link titles retain the complete original member path. Each document has a dated migration notice.

All46 documents were reversed by removing exactly that notice and replacing the new destination/title on its original line; every original byte is recovered. Original verdicts, severities, measurements, limitations and SHA literals are unchanged. No performance-review narrative or Accepted ADR body is part of those46 files. The six existing checker/fixture blobs and both Rust doc-comment files remain byte-equal to original97. The [recovery guide](../../guides/review-evidence.md) and guide/review indexes make recovery discoverable. The catalog pair totals26796 bytes before later reviewed corrections, below128KiB; the full804-file inventory stays external.

## Generator correction and reproducibility

The archived initial `migrate-citations.py` used the ordinary local-target resolver after approved payload removal. That resolver correctly rejected a now-missing archived path, so the helper stopped before changing any document. The pre-migration full checker reported348 missing local targets; its tool output was truncated, so only the reported count is retained here, not a claim to have independently read a complete initial diagnostic stream. No broken intermediate source was pushed.

The corrected generator uses the ordinary resolver first. On its missing-target error, it lexically normalizes the destination and permits only exact membership in the already-approved804-path inventory; any other failure is re-raised. This only identifies citations for migration; it does not alter or bypass the delivered documentation checker. The complete patch below also makes generator provenance honest: original archived source plus this committed correction, each digest-bound in the machine catalog.

- Original archived script SHA-256: `3954232d9e7c06f1e04bc89b13d126409f34eb235514383c7764822c28375630`.
- Corrected script SHA-256: `337ace0b3dba02eca903e9e357865eef232ec2733650c76efe138fb0544a4308`.

The patch was generated with Python difflib and applied to an independent original-script copy with the system patch tool; the reconstructed bytes exactly equal the executed corrected script. The archive remains immutable; its original script was not overwritten. This report contains the full correction, not a new source-tree export.

````diff
--- migrate-citations.py
+++ migrate-citations.py
@@ -7,6 +7,7 @@
 import hashlib
 import json
 import os
+import posixpath
 from pathlib import Path
 import re
 import subprocess
@@ -54,7 +55,15 @@
             continue
         target = value.partition("#")[0].partition("?")[0]
         if target:
-            resolved = resolve_path(ROOT, source, unquote(target)).as_posix()
+            try:
+                resolved = resolve_path(ROOT, source, unquote(target)).as_posix()
+            except ValueError:
+                # Only the exact approved missing archival paths are eligible.
+                decoded = unquote(target)
+                resolved = posixpath.normpath(decoded.lstrip("/") if decoded.startswith("/")
+                    else posixpath.join(posixpath.dirname(source), decoded))
+                if resolved not in paths:
+                    raise
             if resolved in paths:
                 assert link.kind == "markdown"
                 links[(source, link.line, value, resolved)] += 1
@@ -99,7 +108,9 @@
 mapping = dict(line.split() for line in (ARCHIVE / "commit-map.txt").read_text().splitlines()[1:])
 catalog = {"schema_version": 1, "purpose": "PR49 immutable evidence archive",
     "generated_by": {"asset": "provenance.tar.gz", "member": "migrate-citations.py",
-        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
+        "original_script_sha256": hashlib.sha256((ARCHIVE / "migrate-citations.py").read_bytes()).hexdigest(),
+        "correction_record": "docs/analysis/reports/2026-10-16-pr49-evidence-migration.md",
+        "corrected_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
     "release": {"id": release["id"], "tag": TAG, "url": release["html_url"], "immutable": True,
         "main_anchor": "c16997e003fbd1726d1205734380394781c52002"},
     "original_executed_tip": ORIGINAL, "pre_rewrite_tip": PRE, "trial_filtered_tip": FILTERED,
@@ -125,7 +136,7 @@
 text += "\n## Find an archived member\n\nEach migrated link title gives its full original repository member path. The [full per-file manifest](" + asset_rows["candidate-files.json"]["url"] + ") contains all paths, sizes and SHA-256 values. Download payloads.tar.gz and inspect that member with the recovery guide. Older revisions remain in the Git bundle.\n\n"
 for dataset, group in sorted(groups.items()):
     text += '<a id="' + group["anchor"] + '"></a>\n\n### ' + dataset + "\n\n" + str(group["files"]) + " archived files, " + str(group["bytes"]) + " bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.\n\n"
-text += "## Generation and policy\n\nGenerated by `migrate-citations.py`, retained as an inspectable member of provenance.tar.gz and digest-bound in the machine catalog. It used the production Markdown reader, changed 348 recognized destinations in 46 documents, added exact member titles and dated notices, and verified exact reversal to each original document. No historical SHA or verdict text was replaced. [ADR-0044](../../decisions/0044-review-evidence-retention.md) governs storage; [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md) retains corpus/attribution authority.\n"
+text += "## Generation and policy\n\nGenerated by the archived `migrate-citations.py` plus the [reproducible correction](2026-10-16-pr49-evidence-migration.md); both original and corrected script digests are bound in the machine catalog. It used the production Markdown reader, changed 348 recognized destinations in 46 documents, added exact member titles and dated notices, and verified exact reversal to each original document. No historical SHA or verdict text was replaced. [ADR-0044](../../decisions/0044-review-evidence-retention.md) governs storage; [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md) retains corpus/attribution authority.\n"
 (ROOT / catalog_path).write_text(text, encoding="utf-8")
 assert (ROOT / catalog_path).stat().st_size + (ROOT / catalog_json_path).stat().st_size <= 128 * 1024
 guide = """# Recover archived review evidence
````

## Pending review and delivery

The current source is the adopted filtered tip plus this committed migration. Archive/citation review R1 and different fresh R2, validated corrections and their canonical record follow. T-049/T-056 remain In Progress. The separate footprint guard, final clean clone, exact lease publication and final hosted source are still pending; no Done or merge is claimed.
