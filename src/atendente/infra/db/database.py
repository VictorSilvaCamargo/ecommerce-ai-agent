import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from atendente.infra.db.models import Base

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://novaloja:novalojapass@localhost:5432/novaloja_db"
)


class DatabaseManager:
    """Gerenciador central do ciclo de vida de conexões com o PostgreSQL / SQLite."""

    def __init__(self, db_url: str = DEFAULT_DATABASE_URL):
        self.db_url = db_url
        self.engine: AsyncEngine = create_async_engine(
            self.db_url,
            echo=False,
            future=True
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession
        )

    async def create_all_tables(self) -> None:
        """Cria todas as tabelas mapeadas no Base (útil para testes em memória)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all_tables(self) -> None:
        """Remove todas as tabelas (limpeza de testes)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependência assíncrona geradora de sessões."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
