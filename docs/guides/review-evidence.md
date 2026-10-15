# Recover archived review evidence

This guide helps reviewers retrieve the exact raw evidence and original source behind historical Tyrne review records, verify their integrity, and keep old development history separate from the cleaned branch.

## Goal

Recover a specified archived member or original source revision from the immutable PR49 archive, with its published digest verified.

## Prerequisites

- Git, tar and a SHA-256 command (`shasum` on macOS or `sha256sum` on Linux).
- An empty download directory and a separate new recovery directory; do not overwrite an existing checkout.
- The [archive catalog](../analysis/reports/2026-10-16-pr49-evidence-catalog.md) and the exact member path in the migrated link title.
- Network access for downloading the public assets; inspection and recovery work offline afterward. No account or downloaded-script execution is required.

## Steps

1. **Download all nine attachments** from the release linked in the catalog into the empty download directory. Use attached pre-rewrite-development.bundle for the old source; the automatic GitHub source ZIP/tar is the clean-main tag anchor.
2. **Verify the downloads.** Compare SHA256SUMS with its digest pinned in the catalog, then verify the assets. On macOS:

   ```sh
   shasum -a 256 SHA256SUMS
   shasum -a 256 -c SHA256SUMS
   ```

   On Linux:

   ```sh
   sha256sum SHA256SUMS
   sha256sum -c SHA256SUMS
   ```

3. **Recover original source into a new directory**, then verify the complete bundle from inside that Git repository:

   ```sh
   git clone --single-branch --branch development pre-rewrite-development.bundle recovered-pr49
   git -C recovered-pr49 bundle verify ../pre-rewrite-development.bundle
   git -C recovered-pr49 fsck --full --no-reflogs
   ```

4. **Inspect the exact historical source**, replacing the placeholders with the original SHA and repository path. The bundle tip includes governance commits; use the original execution identity for the historical run:

   ```sh
   git -C recovered-pr49 show '<original-sha>:<repository-path>'
   ```

5. **Read a final raw payload without extracting scripts.** Copy its full member path from the link title and verify it against candidate-files.json. For example:

   ```sh
   tar -tzf payloads.tar.gz
   tar -xOf payloads.tar.gz docs/analysis/reports/2026-10-13-t045-architecture-evidence/metadata.json
   ```

6. **Interpret the commit map.** commit-map.txt and the compact catalog map the 151 pre-rewrite commits; the original PR had145 commits and six governance commits followed. One evidence-only commit became empty and maps to zeros. Mapped hashes do not assert historical execution. Later maintenance commits are authored after rewriting.

## Verifying it worked

Every listed checksum reports OK, the recovered bundle reports complete history, Git integrity checks succeed, and the requested original SHA/path resolves. Compare an individual member's bytes and SHA-256 against candidate-files.json. The migration verified all 804 members from both the published tar and recovered source. Digests establish byte integrity; this archive makes no maintainer-key signature claim.

## Troubleshooting

- **Need a repository to verify a bundle:** clone into the new recovery directory first, then run the shown `git -C` verification command.
- **Member absent:** use the full original repository member path, including docs/analysis/reports/. Older revisions may exist only at the original SHA in the Git bundle.
- **Checksum mismatch or unavailable asset:** stop using that copy, download the pinned asset again and compare its identity. Do not substitute an expiring Actions artifact or claim a different source was executed.
- **Old local development history:** retain any uncommitted work in an independent safe copy before synchronizing. A fresh ordinary clone is the clearest starting point. Do not merge the old development ancestry back into cleaned development. Original work remains recoverable from the bundle; reconcile any separate commits deliberately.

## References

- [PR49 evidence catalog](../analysis/reports/2026-10-16-pr49-evidence-catalog.md).
- [ADR-0044 — Review evidence retention and delivery](../decisions/0044-review-evidence-retention.md).
- [Git bundle documentation](https://git-scm.com/docs/git-bundle).
