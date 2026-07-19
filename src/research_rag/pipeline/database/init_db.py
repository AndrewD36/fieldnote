from research_rag.pipeline.database.db import Base, engine

# Important:
# importing models registers the SQLAlchemy models
# with Base.metadata.
from research_rag.pipeline.database import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    print("Database tables created.")


def main() -> None:
    init_db()


if __name__ == "__main__":
    main()