import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(
    filename=r"C:\Users\HP\Desktop\web_scraping\logs\Ml.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

logging.info("Starting ML pipeline for Avito warehouse...")

# Database connection
load_dotenv()

def get_engine():
    try:
        engine = create_engine(
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )

        logging.info("Database connection created successfully")
        return engine

    except Exception as e:
        logging.error(f"Error creating database connection: {e}")
        raise
engine = get_engine()

# Create ml_schema
with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS ml_schema"))

# Create OBT table inside ml_schema
with engine.begin() as conn:
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS ml_schema.obt_avito_annonce(
            annonce_id SERIAL PRIMARY KEY,
            title TEXT,
            price BIGINT,
            location TEXT,
            surface INTEGER,
            rooms INTEGER,
            baths INTEGER,
            link TEXT,
            city VARCHAR,
            neighborhood VARCHAR,
            price_meter BIGINT,
            price_category VARCHAR
        )
    '''))

# Load cleaned data from CSV
df = pd.read_csv(r"C:\Users\HP\Desktop\web_scraping\clean\avito_data_clean.csv")

# Select OBT columns for ml_schema
df_obt_avito_annonce = df[[
    "title",
    "price",
    "location",
    "surface",
    "rooms",
    "baths",
    "link",
    "city",
    "neighborhood",
    "price_meter",
    "price_category"
]]

# Load OBT data into PostgreSQL ml_schema
df_obt_avito_annonce.to_sql(
    "obt_avito_annonce",
    engine,
    if_exists="append",
    schema="ml_schema",
    index=False,
    method="multi",
    chunksize=500
)

logging.info(
    f"ML schema loaded successfully - {len(df_obt_avito_annonce)} rows inserted"
)