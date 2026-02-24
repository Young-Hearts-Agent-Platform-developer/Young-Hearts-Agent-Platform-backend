from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DB_URL, future=True)

# Enable foreign key constraints for SQLite
if "sqlite" in settings.DB_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # attempt to import models to ensure metadata is registered
    try:
        from app.models import Base
        Base.metadata.create_all(bind=engine)
    except Exception:
        import traceback
        print("[init_db] Exception occurred while creating tables:")
        print(traceback.format_exc())
        # if no models defined yet, ignore
        pass
