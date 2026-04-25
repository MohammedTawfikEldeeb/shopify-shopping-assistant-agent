from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, Session

def create_session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)

@contextmanager
def get_session(session_factory) -> Session:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()