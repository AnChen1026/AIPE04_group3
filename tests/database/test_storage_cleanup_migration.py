from sqlalchemy import inspect

from alembic import command


def test_storage_cleanup_upgrade_downgrade(migration_database):
    config, engine = migration_database
    command.upgrade(config, "016_storage_cleanup")
    assert "storage_cleanup_jobs" in inspect(engine).get_table_names()
    command.downgrade(config, "015_studios")
    assert "storage_cleanup_jobs" not in inspect(engine).get_table_names()
    assert "teacher_studios" in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    assert "storage_cleanup_jobs" in inspect(engine).get_table_names()
