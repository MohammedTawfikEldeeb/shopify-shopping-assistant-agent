from src.config import settings
from sqlalchemy import create_engine, text, inspect

engine = create_engine(settings.postgres.url)

with engine.connect() as conn:
    # Get all tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Drop all tables
    for table in tables:
        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
    
    # Clear migration history
    conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    
    conn.commit()
    print(f"Dropped tables: {tables}")
    print("Ready for fresh migration!")

exit()