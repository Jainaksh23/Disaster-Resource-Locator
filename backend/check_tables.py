import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not found")
    exit(1)

engine = create_engine(database_url)
inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tables in database:", tables)
