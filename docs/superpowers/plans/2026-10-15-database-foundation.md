# Issue #18 Database Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use TDD task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add migration-managed reference MIDI and lesson summary data structures after the existing 006 schema without breaking the current course creation flow.

**Architecture:** Extend the canonical student learning models in `backend/models/student.py`. Migration 007 follows the backend branch's `006_message_client_id`, creates the new tables, and backfills legacy `courses.reference_midi_path`; the course service dual-writes during the expand-contract transition. PostgreSQL integration tests exercise real Alembic upgrade/downgrade behavior.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-15-database-foundation-design.md`

## Global Constraints

- Do not modify Alembic revisions 001 through 006.
- Use the glossary terms `參考 MIDI` and `課前摘要`.
- Preserve `courses.reference_midi_path` during this phase.
- Do not add another teacher-table migration in this phase; keep `Base.metadata.create_all()`.
- Every PostgreSQL integration test must refuse a database whose name does not end in `_test`.
- Do not use practice scores to derive course recommendation level or lesson summary level.

## Review Focus

- A legacy MIDI path with nested directories or only a filename backfills a non-empty `original_filename`.
- Migration downgrade leaves the legacy course MIDI path untouched.
- A failed course transaction removes only the file created by that request.
- An invalid MIDI extension creates neither a course row nor a file.
- A first lesson can have a summary with `window_started_at = NULL` without violating time constraints.

---

### Task 1: PostgreSQL Migration Contract

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `tests/database/conftest.py`
- Create: `tests/database/test_migrations.py`
- Create: `alembic/versions/007_database_foundation.py`
- Modify: `backend/models/student.py`

**Interfaces:**
- Consumes: Alembic revision `006_message_client_id`, `DATABASE_URL`, and a disposable `TEST_DATABASE_URL` ending in `_test`.
- Produces: Alembic revision `007_database_foundation`; SQLAlchemy models `ReferenceMidi` and `LessonSummary`.

- [ ] **Step 1: Add pytest as a development dependency**

Add a `dev` dependency group containing `pytest>=8.3,<9`, then update `uv.lock` with `uv lock`.

- [ ] **Step 2: Create the guarded PostgreSQL test fixture**

`tests/database/conftest.py` must parse `TEST_DATABASE_URL`, refuse non-PostgreSQL URLs and database names not ending in `_test`, and expose an Alembic `Config` using that URL without reading the developer `.env`.

- [ ] **Step 3: Write the failing 006→007 migration test**

`test_upgrade_backfills_reference_midi_and_creates_lesson_summaries` must:

1. Upgrade to `006_message_client_id`.
2. Insert one teacher, one student, one course with a legacy MIDI path, and one lesson session.
3. Upgrade to `head`.
4. Assert `reference_midis` and `lesson_summaries` exist.
5. Assert the reference row preserves course, teacher, storage key and filename.
6. Assert unique/check/FK constraints and required indexes exist by name.

- [ ] **Step 4: Write the failing downgrade preservation test**

`test_downgrade_to_006_keeps_legacy_midi_path` upgrades through head, downgrades to 006, asserts both new tables are absent, and asserts `courses.reference_midi_path` is unchanged.

- [ ] **Step 5: Run the migration tests and verify RED**

Run: `TEST_DATABASE_URL=postgresql+psycopg://aipe04:aipe04@127.0.0.1:55433/aipe04_test .venv/bin/pytest tests/database/test_migrations.py -v`

Expected: FAIL because revision 007 and the new models do not exist.

- [ ] **Step 6: Add the SQLAlchemy models**

Add to `backend/models/student.py`:

- `ReferenceMidi` with one-to-one `course_id`, teacher ownership, storage metadata, SHA-256, size, and timestamps.
- `LessonSummary` with lesson/course/teacher/student ownership, optional previous lesson, time window, source count, text, generation status, and timestamps.

Use named constraints and indexes matching the design spec.

- [ ] **Step 7: Implement migration 007**

Create both tables, indexes and named constraints. Backfill every non-null legacy path using Python-generated UUIDs and the path basename. Downgrade drops only the two new tables in dependency-safe order.

- [ ] **Step 8: Run migration tests and verify GREEN**

Run the Step 5 command.

Expected: 2 passed.

- [ ] **Step 9: Commit the migration slice**

```bash
git add pyproject.toml uv.lock tests/database/conftest.py tests/database/test_migrations.py \
  alembic/versions/007_database_foundation.py backend/models/student.py
git commit -m "feat(db): add reference MIDI and lesson summaries"
```

### Task 2: Course Reference MIDI Dual Write

**Files:**
- Create: `tests/database/test_course_reference_midi.py`
- Modify: `backend/services/student.py`

**Interfaces:**
- Consumes: `create_course(...)`, `ReferenceMidi`, a migrated PostgreSQL session, and a temporary upload directory.
- Produces: one `Course` and, when MIDI is supplied, one matching `ReferenceMidi`; raises `StudentBusinessError` for unsupported extensions.

- [ ] **Step 1: Write the failing successful-upload service test**

`test_create_course_with_midi_dual_writes_reference_metadata` calls `create_course(...)` with `song.mid` and known bytes, then asserts:

- the course legacy path equals `ReferenceMidi.storage_key`;
- `original_filename == "song.mid"`;
- `content_sha256` equals the independently calculated literal digest;
- `file_size_bytes` equals the known byte length;
- exactly one file exists under the temporary upload root.

- [ ] **Step 2: Write the failing invalid-extension test**

`test_create_course_rejects_non_midi_file_without_side_effects` supplies `notes.txt`, expects `StudentBusinessError`, and asserts no course, metadata row or file was created.

- [ ] **Step 3: Run the service tests and verify RED**

Run: `TEST_DATABASE_URL=postgresql+psycopg://aipe04:aipe04@127.0.0.1:55433/aipe04_test .venv/bin/pytest tests/database/test_course_reference_midi.py -v`

Expected: FAIL because the service does not create `ReferenceMidi` or reject the extension.

- [ ] **Step 4: Implement dual-write behavior**

Update `create_course(...)` to validate `.mid`/`.midi`, calculate SHA-256 and byte size, create the course and reference metadata in one transaction, preserve the legacy path, and unlink the newly written file if the transaction fails.

- [ ] **Step 5: Run the service tests and verify GREEN**

Run the Step 3 command.

Expected: 2 passed.

- [ ] **Step 6: Run both database test modules**

Run: `TEST_DATABASE_URL=postgresql+psycopg://aipe04:aipe04@127.0.0.1:55433/aipe04_test .venv/bin/pytest tests/database -v`

Expected: 4 passed.

- [ ] **Step 7: Commit the service slice**

```bash
git add tests/database/test_course_reference_midi.py backend/services/student.py
git commit -m "feat(db): persist reference MIDI metadata"
```

### Task 3: Alembic Metadata and Maintainer Documentation

**Files:**
- Modify: `alembic/env.py`
- Modify: `backend/models/__init__.py`
- Create: `tests/database/test_metadata.py`
- Create: `docs/database/data-dictionary.md`
- Create: `docs/database/migration-runbook.md`

**Interfaces:**
- Consumes: shared SQLAlchemy `Base.metadata` and the canonical student learning models.
- Produces: Alembic autogenerate visibility for canonical tables; maintainer instructions for safe schema changes.

- [ ] **Step 1: Write the failing metadata visibility test**

`test_alembic_metadata_contains_database_foundation_tables` imports the Alembic model-loading module and asserts `courses`, `reference_midis`, and `lesson_summaries` are present in `Base.metadata.tables`.

- [ ] **Step 2: Run the metadata test and verify RED**

Run: `.venv/bin/pytest tests/database/test_metadata.py -v`

Expected: FAIL because Alembic does not explicitly load student learning models.

- [ ] **Step 3: Export and load the canonical models**

Export the student learning models from `backend/models/__init__.py` and explicitly import the canonical student model module in `alembic/env.py`. Do not remove teacher legacy model imports from application startup.

- [ ] **Step 4: Run the metadata test and verify GREEN**

Run the Step 2 command.

Expected: 1 passed.

- [ ] **Step 5: Document the new tables and migration workflow**

`data-dictionary.md` records columns, ownership, constraints, indexes and legacy fields. `migration-runbook.md` documents revision creation, clean upgrade, existing-data upgrade, rollback cautions, backup requirements, test database safety and the rule against editing applied migrations.

- [ ] **Step 6: Verify Alembic has one head and generates offline SQL**

Run:

```bash
.venv/bin/alembic heads
DATABASE_URL=postgresql+psycopg://aipe04:aipe04@127.0.0.1:55433/aipe04_test \
  .venv/bin/alembic upgrade 006_message_client_id:head --sql > /tmp/aipe04-007.sql
```

Expected: exactly `007_database_foundation (head)` and a non-empty 007 SQL file. Full base-to-head offline SQL is blocked by the pre-existing 005 revision's runtime introspection.

- [ ] **Step 7: Run the complete relevant test suite**

Run:

```bash
TEST_DATABASE_URL=postgresql+psycopg://aipe04:aipe04@127.0.0.1:55433/aipe04_test \
  .venv/bin/pytest tests/database -v
```

Expected: all database tests pass.

- [ ] **Step 8: Commit the metadata and documentation slice**

```bash
git add alembic/env.py backend/models/__init__.py tests/database/test_metadata.py docs/database
git commit -m "docs(db): add migration maintenance runbook"
```

### Task 4: ERD and Final Review

**Files:**
- Create: `.archify/erd-database-foundation-*/candidate.json`
- Create: `.archify/erd-database-foundation-*/database-foundation.html`

**Interfaces:**
- Consumes: repository-backed SQLAlchemy models and Alembic revisions 001 through 007.
- Produces: validated interactive ERD showing canonical auth, course, learning, reference MIDI and lesson summary tables.

- [ ] **Step 1: Generate the repository-backed ERD**

Use the `archify` ERD workflow with complete physical columns, key roles, cardinalities and repository source evidence. Mark legacy teacher module tables outside the canonical Issue #18 domain or omit them with an explicit scope note.

- [ ] **Step 2: Finalize and validate the ERD**

Run Archify `finalize erd ... --repo-root /Users/olliehu/iSpan/AIPE04_group3 --quality standard --json` and repair any failed gate within the documented repair limit.

- [ ] **Step 3: Review the complete branch diff**

Check that only the approved conservative scope changed, migrations 001-006 are untouched, pre-existing untracked `.impeccable/` and `frontend/` remain untouched, and no secrets or generated test data are tracked.

- [ ] **Step 4: Report completion**

Provide links to the design, plan, data dictionary, migration runbook and ERD; report test commands and any remaining integration work without marking Issue #18 complete.
