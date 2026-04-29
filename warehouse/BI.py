import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(
    filename=r"C:\Users\HP\Desktop\web_scraping\warehouse\BI.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

# connection with db
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

# create tables for BI
with engine.begin() as conn:
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS dim_location(
                    location_id SERIAL PRIMARY KEY,
                    city VARCHAR(50),
                    neighborhood VARCHAR(50)
        )
    '''))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS dim_price_category(
                    price_category_id SERIAL PRIMARY KEY,
                    price_category VARCHAR(10)
        )
    '''))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS dim_property(
                    property_id SERIAL PRIMARY KEY,
                    title TEXT,
                    link TEXT
        )
    '''))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS fact_annonce(
                    annonce_id SERIAL PRIMARY KEY,
                    location_id INTEGER,
                    price_category_id INTEGER,
                    property_id INTEGER,
                    price INTEGER,
                    surface INTEGER,
                    rooms INTEGER,
                    baths INTEGER,
                    price_meter INTEGER,
                    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
                    FOREIGN KEY (property_id) REFERENCES dim_property(property_id),
                    FOREIGN KEY (price_category_id) REFERENCES dim_price_category(price_category_id)
        )
    '''))

# load data from csv
df = pd.read_csv(r"C:\Users\HP\Desktop\web_scraping\clean\avito_data_clean.csv")

# reapartition the data
df_dim_location = df[["city", "neighborhood"]].drop_duplicates()
df_dim_price_category = df[["price_category"]].drop_duplicates()
df_dim_property = df[["title", "link"]].drop_duplicates()

with engine.begin() as conn:
    conn.execute(text("""
        TRUNCATE TABLE fact_annonce, dim_property, dim_price_category, dim_location RESTART IDENTITY CASCADE
    """))

# to sql
df_dim_location.to_sql("dim_location", engine, if_exists="append", index=False)
df_dim_price_category.to_sql("dim_price_category", engine, if_exists="append", index=False)
df_dim_property.to_sql("dim_property", engine, if_exists="append", index=False)

# read sql
df_dim_location = pd.read_sql("SELECT * FROM dim_location", engine)
df_dim_price_category = pd.read_sql("SELECT * FROM dim_price_category", engine)
df_dim_property = pd.read_sql("SELECT * FROM dim_property", engine)

# merge
df = df.merge(df_dim_location, on=["city", "neighborhood"], how="left")
df = df.merge(df_dim_price_category, on=["price_category"], how="left")
df = df.merge(df_dim_property, on=["title", "link"], how="left")

df_fact_annonce = df[[
    "location_id",
    "price_category_id",
    "property_id",
    "price",
    "surface",
    "rooms",
    "baths",
    "price_meter"
]]

df_fact_annonce.to_sql(
    "fact_annonce",
    engine,
    if_exists="append",
    index=False,
    method="multi"
)