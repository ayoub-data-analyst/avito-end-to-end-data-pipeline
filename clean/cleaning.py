import pandas as pd

# Load raw staging data
df = pd.read_csv("/app/staging/staging_avito_raw_1.csv")

# Remove duplicate listings
df = df.drop_duplicates()

# Extract city and neighborhood from location column
df["city"] = df["location"].str.replace("Appartements dans", "").str.split(",").str[0].str.strip()
df["neighborhood"] = df["location"].str.replace("Appartements dans", "").str.split(",").str[1].str.strip()

# Convert structured columns to numeric
df["surface"] = df["surface"].str.replace("m²", "").str.strip().astype(int)
df["rooms"] = df["rooms"].str.replace("chambres?", "", regex=True).str.strip().astype(int)
df["baths"] = df["baths"].str.replace("sdbs?", "", regex=True).str.strip().astype(int)

# Feature engineering: price per m²
df["price_meter"] = (df["price"] / df["surface"]).astype(int)

# Remove rows with missing neighborhood values (~0.5% nulls)
df = df.dropna()

# KPI segmentation: price categories
def price_category(price):
    if price <= 500000:
        return "Low"
    elif price >= 1000000:
        return "High"
    else:
        return "Medium"

df["price_category"] = df["price"].apply(price_category)

# Export cleaned dataset
df.to_csv("/app/clean/avito_data_clean_1.csv", index=False)