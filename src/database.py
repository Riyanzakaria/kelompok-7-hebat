import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

DATABASE_URL = os.getenv("AIVEN_DATABASE_URL")

def get_engine():
    """Membuat dan mengembalikan SQLAlchemy engine untuk PostgreSQL."""
    if not DATABASE_URL:
        raise ValueError("AIVEN_DATABASE_URL is not set in .env")
    return create_engine(DATABASE_URL)

def fetch_data(query="SELECT * FROM fact_ultimate_impact"):
    """Mengambil data dari database PostgreSQL di Aiven Cloud."""
    print("Mengambil data dari database PostgreSQL Aiven...")
    engine = get_engine()
    df = pd.read_sql(query, engine)
    return df
