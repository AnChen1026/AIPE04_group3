# Database Transition Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reference MIDI metadata after backend Migration 009 without creating a second lesson-summary schema or breaking existing readers.

**Architecture:** `courses` remains the course authority and `lesson_preparation_summaries` remains the summary authority. A new `reference_midis` table is introduced with backfill and temporary dual writes from the course service; existing reads continue through `courses.reference_midi_path` until a later contract migration.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16, pytest

**Spec:** `docs/superpowers/specs/2026-10-18-database-transition-integration-design.md`

## Global Constraints

- The new revision must directly follow `009_images_profile` and leave one Alembic head.
- Existing `lesson_preparation_summaries` is the only lesson-summary table.
- Shared or applied migrations are not rewritten.
- Existing MIDI readers continue to work during the dual-write period.
- Destructive migration tests run only against a PostgreSQL database whose name ends in `_test`.

## Review Focus

- A Windows-style legacy path must backfill the basename correctly.
- Replacing a MIDI must update one metadata row rather than insert a duplicate.
- A database commit failure must remove only the newly written file.
- Invalid files must not create metadata or change the current MIDI path.
- Downgrading to 009 must preserve `courses.reference_midi_path`.

---

### Task 1: Migration contract

**Files:**
- Create: `alembic/versions/010_reference_midis.py`
- Create: `tests/database/conftest.py`
- Create: `tests/database/test_reference_midi_migration.py`

**Interfaces:**
- Consumes: Alembic revision `009_images_profile` and legacy `courses.reference_midi_path`.
- Produces: revision `010_reference_midis` and the `reference_midis` table.

- [ ] Write a migration test that upgrades to 009, inserts a legacy course, upgrades to head, and verifies the backfilled metadata and constraints.
- [ ] Run the test and verify it fails because revision 010 does not exist.
- [ ] Implement `010_reference_midis` with table, index, backfill, and downgrade.
- [ ] Verify upgrade, backfill, downgrade, and single-head checks pass.
- [ ] Commit the migration slice.

### Task 2: Course upload dual write

**Files:**
- Modify: `backend/models/student.py`
- Modify: `backend/services/course.py`
- Modify: `tests/test_courses.py`
- Modify: `alembic/env.py`

**Interfaces:**
- Consumes: `save_reference_midi(db, teacher_user_id, course_id, filename, content)`.
- Produces: `ReferenceMidi` metadata synchronized with `Course.reference_midi_path`.

- [ ] Extend the public API test to assert path, filename, SHA-256, size, and one-row replacement behavior.
- [ ] Run the test and verify it fails because `ReferenceMidi` is absent.
- [ ] Add the SQLAlchemy model and dual-write logic with failed-commit cleanup.
- [ ] Run the course tests and the complete backend suite.
- [ ] Commit the service slice.

### Task 3: Operations documentation and repository hygiene

**Files:**
- Create: `docs/database/data-dictionary.md`
- Create: `docs/database/migration-runbook.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: the tested 010 schema and dual-write behavior.
- Produces: maintainer guidance for schema ownership, deployment, backup, rollback, and the later contract step.

- [ ] Document the current 001→010 chain and the reference MIDI transition.
- [ ] Document safe migration, backup, restore, verification, and rollback commands.
- [ ] Ignore generated frontend and local design-tool artifacts.
- [ ] Run all tests, inspect the final diff, and commit the documentation slice.

