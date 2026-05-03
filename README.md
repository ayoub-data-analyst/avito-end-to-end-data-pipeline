# Avito End-to-End Data Pipeline

A fully automated data engineering pipeline that scrapes real estate listings from [Avito.ma](https://www.avito.ma/), cleans and enriches the data, and loads it into a PostgreSQL data warehouse — with two separate schemas optimized for **Business Intelligence** and  **Machine Learning** .

---

## Table of Contents

* [Overview](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#overview)
* [Architecture](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#architecture)
* [Project Structure](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#project-structure)
* [Pipeline Stages](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#pipeline-stages)
  * [1. Scraping](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#1-scraping)
  * [2. Cleaning](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#2-cleaning)
  * [3. Warehousing](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#3-warehousing)
* [Data Model](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#data-model)
* [Getting Started](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#getting-started)
  * [Prerequisites](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#prerequisites)
  * [Environment Variables](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#environment-variables)
  * [Running with Docker](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#running-with-docker)
  * [Running Locally](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#running-locally)
* [Sample Data](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#sample-data)
* [Tech Stack](https://claude.ai/chat/48f60e0e-b334-4f41-8aa5-ba18b1ae3fcd#tech-stack)

---

## Overview

This project implements a complete **ETL pipeline** for Moroccan apartment listings scraped from Avito.ma. It targets apartments for sale with at least 1 bedroom, 1 bathroom, and a minimum surface of 20 m².

The pipeline runs end-to-end across three stages:

| Stage               | Input               | Output                                   |
| ------------------- | ------------------- | ---------------------------------------- |
| **Scrape**    | Avito.ma (live web) | `staging/staging_avito_raw.csv`        |
| **Clean**     | Raw CSV             | `clean/avito_data_clean.csv`           |
| **Warehouse** | Clean CSV           | PostgreSQL (`bi_schema`+`ml_schema`) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Avito.ma (Web Source)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │  Selenium scraper (100 pages)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│             staging/staging_avito_raw.csv                    │
│        title | price | location | surface | rooms | baths   │
└──────────────────────────┬──────────────────────────────────┘
                           │  Pandas cleaning & feature engineering
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               clean/avito_data_clean.csv                     │
│   + city | neighborhood | price_meter | price_category       │
└──────────────┬────────────────────────────┬─────────────────┘
               │                            │
               ▼                            ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│  PostgreSQL          │      │  PostgreSQL                  │
│  bi_schema           │      │  ml_schema                   │
│  (Star Schema)       │      │  (One Big Table)             │
│                      │      │                              │
│  dim_location        │      │  obt_avito_annonce           │
│  dim_price_category  │      │  (flat, ML-ready)            │
│  dim_property        │      └──────────────────────────────┘
│  fact_annonce        │
└──────────────────────┘
```

---

## Project Structure

```
avito-end-to-end-data-pipeline/
│
├── scrape/
│   └── scraping.py            # Selenium-based web scraper
│
├── clean/
│   ├── cleaning.py            # Data cleaning & feature engineering
│   └── avito_data_clean.csv   # Cleaned dataset (output)
│
├── staging/
│   └── staging_avito_raw.csv  # Raw scraped data (output)
│
├── warehouse/
│   ├── bi_pipeline.py         # Star schema loader (BI)
│   ├── ml_pipeline.py         # OBT loader (ML)
│   └── main.py                # Orchestrator — runs both pipelines
│
├── docker/
│   ├── Dockerfile.scraper
│   ├── Dockerfile.cleaner
│   ├── Dockerfile.warehouse
│   └── docker-compose.yml
│
├── requirements.txt
└── README.md
```

---

## Pipeline Stages

### 1. Scraping

**File:** `scrape/scraping.py`

Uses **Selenium** with Chrome to scrape apartment listings from Avito.ma across up to 100 pages. The scraper:

* Scrolls each page to trigger lazy-loaded listing cards
* Extracts: `title`, `price`, `location`, `surface`, `rooms`, `baths`, `link`
* Navigates to the next page via URL pagination
* Logs progress and errors to `logs/scrape_avito.log`
* Exports raw results to `staging/staging_avito_raw.csv`

**Target URL:**

```
https://www.avito.ma/fr/maroc/appartements-à_vendre?price=100000-&rooms=1&bathrooms=1&has_price=true&size=20-
```

---

### 2. Cleaning

**File:** `clean/cleaning.py`

Transforms the raw staging CSV into an analysis-ready dataset using  **pandas** :

| Step                | Description                                                          |
| ------------------- | -------------------------------------------------------------------- |
| Deduplication       | Removes exact duplicate rows                                         |
| Location parsing    | Splits `location`into `city`and `neighborhood`                 |
| Type casting        | Converts `surface`,`rooms`,`baths`from text to integers        |
| Feature engineering | Computes `price_meter = price / surface`                           |
| Null handling       | Drops rows with missing `neighborhood`(~0.5%)                      |
| Segmentation        | Assigns `price_category`:`Low`(≤500K),`Medium`,`High`(≥1M) |

Output: `clean/avito_data_clean.csv`

---

### 3. Warehousing

**File:** `warehouse/main.py` (orchestrates both sub-pipelines)

#### BI Pipeline — `warehouse/bi_pipeline.py`

Loads data into a **star schema** under `bi_schema` in PostgreSQL, optimized for BI dashboards and OLAP queries:

```
bi_schema
├── dim_location       (location_id, city, neighborhood)
├── dim_price_category (price_category_id, price_category)
├── dim_property       (property_id, title, link)
└── fact_annonce       (annonce_id, location_id, price_category_id,
                        property_id, price, surface, rooms, baths, price_meter)
```

#### ML Pipeline — `warehouse/ml_pipeline.py`

Loads data into a flat **One Big Table (OBT)** under `ml_schema`, optimized for machine learning feature extraction:

```
ml_schema
└── obt_avito_annonce  (annonce_id, title, price, location, surface,
                        rooms, baths, link, city, neighborhood,
                        price_meter, price_category)
```

Both pipelines use `TRUNCATE ... RESTART IDENTITY CASCADE` before loading to ensure idempotent, repeatable runs.

---

## Data Model

### Star Schema (`bi_schema`)

```
         dim_location
         ┌───────────────┐
         │ location_id PK│◄──┐
         │ city          │   │
         │ neighborhood  │   │
         └───────────────┘   │
                             │
dim_price_category           │    fact_annonce
┌──────────────────┐         │   ┌─────────────────────┐
│ price_category_id│◄────────┼───│ annonce_id PK        │
│ price_category   │         │   │ location_id FK        │
└──────────────────┘         └───│ price_category_id FK  │
                                 │ property_id FK        │
         dim_property        ┌───│ price                 │
         ┌───────────────┐   │   │ surface               │
         │ property_id PK│◄──┘   │ rooms                 │
         │ title         │       │ baths                 │
         │ link          │       │ price_meter           │
         └───────────────┘       └─────────────────────┘
```

---

## Getting Started

### Prerequisites

* Python 3.10+
* Google Chrome + ChromeDriver (for scraping)
* PostgreSQL (local or remote)
* Docker & Docker Compose (optional, for containerized run)

### Environment Variables

Create a `.env` file at the project root:

```env
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=avito_db
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### Running with Docker

The project includes three Dockerfiles and a Compose file that run the pipeline stages in order, with dependency management:

```bash
cd docker
docker-compose up --build
```

Services run in sequence: `scraper` → `cleaner` → `warehouse`.

Shared CSV files are exchanged via mounted volumes (`staging/` and `clean/`).

### Running Locally

**Step 1 — Install dependencies:**

```bash
pip install -r requirements.txt
```

**Step 2 — Scrape listings:**

```bash
python scrape/scraping.py
```

**Step 3 — Clean the data:**

```bash
python clean/cleaning.py
```

**Step 4 — Load to PostgreSQL:**

```bash
python warehouse/main.py
```

---

## Sample Data

Preview of `clean/avito_data_clean.csv`:

| title                                     | price     | city       | neighborhood | surface | rooms | baths | price_meter | price_category |
| ----------------------------------------- | --------- | ---------- | ------------ | ------- | ----- | ----- | ----------- | -------------- |
| Appartement à vendre 61 m² à Marrakech | 1,530,000 | Marrakech  | Guéliz      | 61      | 1     | 1     | 25,081      | High           |
| Appartement 95m2 vendables - Palmier      | 1,750,000 | Casablanca | Palmier      | 95      | 2     | 2     | 18,421      | High           |
| Vente Appartement 4 pièces de 190 m2     | 3,800,000 | Casablanca | Racine       | 190     | 3     | 2     | 20,000      | High           |

---

## Tech Stack

| Layer              | Tool                           |
| ------------------ | ------------------------------ |
| Scraping           | Python, Selenium, ChromeDriver |
| Data Processing    | pandas                         |
| Data Warehouse     | PostgreSQL                     |
| ORM / DB Connector | SQLAlchemy                     |
| Containerization   | Docker, Docker Compose         |
| Logging            | Python `logging`module       |
| Config Management  | `python-dotenv`              |
