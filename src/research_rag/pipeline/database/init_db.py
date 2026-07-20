from sqlalchemy import text
from research_rag.pipeline.database.db import Base, engine
from research_rag.pipeline.database import models  # noqa: F401


def init_db() -> None:
    print("Testing PostgreSQL connection...")

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("PostgreSQL connection successful.")

    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully.")


def main() -> None:
    init_db()


if __name__ == "__main__":
    main()