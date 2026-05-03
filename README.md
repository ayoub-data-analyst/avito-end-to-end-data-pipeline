
# Avito End-to-End Data Pipeline

A fully containerized data pipeline that scrapes real estate listings from [Avito.ma](https://www.avito.ma/), cleans and enriches the data, and loads it into a PostgreSQL data warehouse with two schemas — one optimized for BI/analytics and one for machine learning.

---

## Architecture Overview

```
[Avito.ma] ──scrape──> [Staging CSV] ──clean──> [Clean CSV] ──load──> [PostgreSQL]
                                                                      ├── bi_schema  (Star Schema)
                                                                      └── ml_schema  (OBT)
```

The pipeline runs as three sequential Docker services:

| Stage | Service       | Script                 | Description                                         |
| ----- | ------------- | ---------------------- | --------------------------------------------------- |
| 1     | `scraper`   | `scrape/scraping.py` | Headless Selenium scraper, paginates Avito listings |
| 2     | `cleaner`   | `clean/cleaning.py`  | Cleans, parses, and feature-engineers the raw data  |
| 3     | `warehouse` | `warehouse/main.py`  | Loads data into PostgreSQL via BI and ML pipelines  |

---

## Project Structure

```
avito-end-to-end-data-pipeline/
├── scrape/
│   └── scraping.py          # Selenium scraper → staging CSV
├── clean/
│   ├── cleaning.py          # Pandas cleaning → clean CSV
│   └── avito_data_clean.csv # Sample clean output
├── staging/
│   └── staging_avito_raw.csv # Sample raw output
├── warehouse/
│   ├── main.py              # Orchestrator (runs BI + ML pipelines)
│   ├── bi_pipeline.py       # Star schema loader (bi_schema)
│   └── ml_pipeline.py       # OBT loader (ml_schema)
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.scraper
│   ├── Dockerfile.cleaner
│   └── Dockerfile.warehouse
└── requirements.txt
```

---

## Pipeline Stages

### Stage 1 — Scraping (`scrape/scraping.py`)

Uses **Selenium** in headless Chrome mode to scrape apartment-for-sale listings from Avito.ma.

* Filters: price 100k–1M MAD, 1 bedroom, 1 bathroom, surface 20–1000 m²
* Paginates across multiple pages with scroll-to-load behavior
* Extracts per listing: `title`, `price`, `location`, `surface`, `rooms`, `baths`, `link`
* Outputs to: `staging/staging_avito_raw_1.csv`
* Logs to: `/app/logs/scrape_avito.log`

### Stage 2 — Cleaning (`clean/cleaning.py`)

Uses **Pandas** to transform raw staging data into an analysis-ready dataset.

* Removes duplicate listings
* Parses `location` into `city` and `neighborhood`
* Converts `surface`, `rooms`, `baths` from text to integers
* Engineers `price_meter` (price per m²)
* Adds `price_category` segmentation: `Low` (≤500k), `Medium`, `High` (≥1M)
* Drops rows with null `neighborhood` (~0.5% of data)
* Outputs to: `clean/avito_data_clean_1.csv`

### Stage 3 — Warehouse (`warehouse/`)

Connects to PostgreSQL via **SQLAlchemy** and loads data into two schemas:

**`bi_schema` — Star Schema** (for dashboards / BI tools)

```
fact_annonce
 ├── dim_location       (city, neighborhood)
 ├── dim_property       (title, link)
 └── dim_price_category (Low / Medium / High)
```

**`ml_schema` — One Big Table** (for model training)

```
obt_avito_annonce
  title, price, location, surface, rooms, baths,
  city, neighborhood, price_meter, price_category
```

---

## Getting Started

### Prerequisites

* [Docker](https://www.docker.com/) and Docker Compose
* A running PostgreSQL instance reachable by the `warehouse` container

### 1. Configure Environment Variables

Create a `.env` file in the project root:

```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
```

### 2. Run the Full Pipeline

```bash
cd docker
docker-compose up --build
```

Docker Compose will run the three services in order: `scraper` → `cleaner` → `warehouse`.

### 3. Run Stages Individually

```bash
# Scraper only
docker build -f docker/Dockerfile.scraper -t avito-scraper .
docker run --rm -v $(pwd)/staging:/app/staging avito-scraper

# Cleaner only
docker build -f docker/Dockerfile.cleaner -t avito-cleaner .
docker run --rm -v $(pwd)/staging:/app/staging -v $(pwd)/clean:/app/clean avito-cleaner

# Warehouse only (requires .env)
docker build -f docker/Dockerfile.warehouse -t avito-warehouse .
docker run --rm --env-file .env -v $(pwd)/clean:/app/clean avito-warehouse
```

---

## Dependencies

Key packages (see `requirements.txt` for pinned versions):

| Package           | Purpose                          |
| ----------------- | -------------------------------- |
| `selenium`      | Browser automation for scraping  |
| `pandas`        | Data cleaning and transformation |
| `sqlalchemy`    | PostgreSQL ORM / connection      |
| `python-dotenv` | Environment variable loading     |
| `numpy`         | Numeric operations               |
| `psycopg2`      | PostgreSQL driver                |

---

## Data Schema Reference

### Raw Staging Schema

| Column       | Type   | Description                       |
| ------------ | ------ | --------------------------------- |
| `title`    | string | Listing title                     |
| `price`    | int    | Price in MAD                      |
| `location` | string | Raw location string from Avito    |
| `surface`  | string | Surface area (e.g.`"85 m²"`)   |
| `rooms`    | string | Room count (e.g.`"3 chambres"`) |
| `baths`    | string | Bathroom count (e.g.`"2 sdb"`)  |
| `link`     | string | URL to the listing                |

### Clean Schema (adds)

| Column             | Type   | Description                   |
| ------------------ | ------ | ----------------------------- |
| `city`           | string | Parsed city name              |
| `neighborhood`   | string | Parsed neighborhood name      |
| `surface`        | int    | Surface area in m² (numeric) |
| `rooms`          | int    | Number of bedrooms (numeric)  |
| `baths`          | int    | Number of bathrooms (numeric) |
| `price_meter`    | int    | Price per m²                 |
| `price_category` | string | `Low`/`Medium`/`High`   |

---

## Notes

* The scraper targets apartment listings with `has_price=true`, so all records in staging have a valid price.
* The warehouse pipelines use `TRUNCATE ... RESTART IDENTITY CASCADE` before each load, making every run a full refresh.
* Log files are written inside the container at `/app/logs/`. Mount a volume there to persist them on the host.
* The `bi_pipeline.py` and `ml_pipeline.py` files currently contain hardcoded Windows paths for local log files — these are overridden in the Docker environment by the container paths set in `logging.basicConfig`. When running locally outside Docker, update those paths to match your system.
