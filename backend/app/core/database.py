from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Determine async database URL and connection options
async_db_url = settings.get_async_database_url()

if "postgresql+asyncpg" in async_db_url:
    engine = create_async_engine(
        async_db_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args={"statement_cache_size": 0}
    )
else:
    engine = create_async_engine(
        async_db_url,
        echo=False,
        future=True
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def run_schema_migrations(async_engine):
    """
    Safely inspects existing tables in SQLite or PostgreSQL and adds any missing
    columns that were introduced in recent schema updates without dropping existing data.
    """
    from sqlalchemy import inspect, text

    def _apply_migrations(sync_conn):
        inspector = inspect(sync_conn)
        tables = set(inspector.get_table_names())

        if "recovery_workflows" in tables:
            cols = {c["name"] for c in inspector.get_columns("recovery_workflows")}
            if "recovery_type" not in cols:
                sync_conn.execute(text("ALTER TABLE recovery_workflows ADD COLUMN recovery_type VARCHAR(32) DEFAULT 'PAYMENT'"))
            if "reference_id" not in cols:
                sync_conn.execute(text("ALTER TABLE recovery_workflows ADD COLUMN reference_id VARCHAR(64)"))
            if "execution_mode" not in cols:
                sync_conn.execute(text("ALTER TABLE recovery_workflows ADD COLUMN execution_mode VARCHAR(32) DEFAULT 'SIMULATED'"))

        if "users" in tables:
            cols = {c["name"] for c in inspector.get_columns("users")}
            if "role" not in cols:
                sync_conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'OPERATIONS_AGENT'"))

    async with async_engine.begin() as conn:
        await conn.run_sync(_apply_migrations)
