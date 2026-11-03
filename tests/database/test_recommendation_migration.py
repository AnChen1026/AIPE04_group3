"""首頁推薦對談的 Migration 合約。"""

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect


UPSTREAM_REVISION = "010_reference_midis"
RECOMMENDATION_REVISION = "011_recommendations"


def _names(items: list[dict[str, object]]) -> set[str]:
    return {str(item["name"]) for item in items if item.get("name")}


def test_010_to_head_creates_recommendation_tables(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, UPSTREAM_REVISION)
    command.upgrade(config, "head")

    inspector = inspect(engine)
    assert {"recommendation_sessions", "recommendation_items"} <= set(inspector.get_table_names())
    assert _names(inspector.get_check_constraints("recommendation_sessions")) == {
        "ck_recommendation_sessions_question_count",
        "ck_recommendation_sessions_status",
    }
    assert _names(inspector.get_foreign_keys("recommendation_items")) == {
        "fk_recommendation_items_course_id_courses",
        "fk_recommendation_items_session_id_recommendation_sessions",
    }
    assert _names(inspector.get_unique_constraints("recommendation_items")) == {
        "uq_recommendation_items_session_course",
        "uq_recommendation_items_session_position",
    }
    with engine.connect() as connection:
        revision = connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
    assert revision == ScriptDirectory.from_config(config).get_current_head()


def test_downgrade_to_010_only_removes_recommendation_tables(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "head")
    command.downgrade(config, UPSTREAM_REVISION)

    tables = set(inspect(engine).get_table_names())
    assert "recommendation_sessions" not in tables
    assert "recommendation_items" not in tables
    assert "courses" in tables
    assert "reference_midis" in tables
