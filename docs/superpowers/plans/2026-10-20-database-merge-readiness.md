# Database Merge Readiness Implementation Plan

**Goal:** Make database revision 010 reviewable against current main and reproducibly validate PostgreSQL setup for other feature developers.

**Architecture:** Keep existing FastAPI JSON APIs and Alembic 001→010. Merge latest main into an isolated database branch; do not include recommendation revision 011 or rewrite applied migrations.

**Tech Stack:** Python 3.12, PostgreSQL 16, SQLAlchemy 2, Alembic, pytest.

**Spec:** `docs/superpowers/specs/2026-10-18-database-transition-integration-design.md`

## Constraints and review focus

- Preserve ADR 0006's API-only backend and main's current documentation.
- Exercise fresh install, legacy backfill, downgrade/re-upgrade and a single head.
- Destructive tests must only use an independent PostgreSQL database ending in `_test`.
- Failed metadata writes must remove the new file and preserve existing MIDI data.
- Other features use the shared courses and lesson_preparation_summaries tables.

## Tasks

- [x] Merge current main and resolve `docs/資料表設計.md` using 010 plus main's current field descriptions.
- [x] Run existing tests against isolated PostgreSQL 16; investigate failures before changing code.
- [x] Add regression coverage for fresh install and any integration failures; fix the underlying causes.
- [x] Add reproducible PostgreSQL CI and update setup/migration handoff documentation.
- [x] Run complete backend tests, inspect diff and commit the validated result.
- [x] Attempt publication and record access requirement: gh is not authenticated, and the connected GitHub account receives HTTP 404 when writing this repository. No remote branch or PR was created.

## Validation evidence (2026-10-20)

- Base merged: `origin/main` at `2fa1a28`; conflict resolved in the table design document.
- PostgreSQL 16 isolated container: fresh `alembic upgrade head` succeeded; `current` and `heads` both report `010_reference_midis`.
- First full run reproduced 10 failures after a migration downgrade left the schema at 009. Migration fixtures now restore head and avoid API transactions.
- Added regression reproducing leaked MIDI files when the metadata query fails; query and commit failures now both clean the new file and preserve old metadata.
- Final full backend suite: **58 passed**, no skips, 22 existing dependency deprecation warnings.
- `git diff --check` passed. GitHub Actions configuration added; remote CI has not run because publication is blocked by authentication/access.

## Publish after authenticating an account with repository write access

From this worktree, with `codex/database-merge-ready` checked out:

```bash
gh auth login
gh auth setup-git
git push -u origin codex/database-merge-ready
gh pr create --base main --head codex/database-merge-ready --title "整合資料庫 010 並加入 PostgreSQL 回歸驗證" --body-file docs/database/database-pr-description.md
```

The local merge simulation succeeds without conflicts. The workflow's remote result and any repository-required reviews remain to be checked before merging main.
