from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRESQL_PW = os.getenv('POSTGRESQL_PW')
POSTGRESQL_DB = os.getenv('POSTGRESQL_DB')

# Test connection
def check_postgresql():
    with PostgresSaver.from_conn_string(
        f"postgresql://postgres:{POSTGRESQL_PW}@localhost:5432/{POSTGRESQL_DB}"
    ) as checkpointer:
        checkpointer.setup()  # Creates checkpoint tables
        print("✓ PostgreSQL connection successful!")
        print(f"✓ Connected to database: {POSTGRESQL_DB}")
        print("✓ Checkpoint tables created!")

# Do a init so it can be called from other files

check_postgresql()
