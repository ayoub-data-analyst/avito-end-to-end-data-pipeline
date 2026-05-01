import pandas as pd

# Load raw staging data
df = pd.read_csv(r"C:\Users\HP\Desktop\web_scraping\staging\staging_avito_raw.csv")

# Remove duplicate listings
df = df.drop_duplicates()

# Extract city and neighborhood from location column
df["city"] = df["location"].str.replace("Appartements dans", "").str.split(",").str[0].str.strip()
df["neighborhood"] = df["location"].str.replace("Appartements dans", "").str.split(",").str[1].str.strip()

# Convert structured columns to numeric
df["surface"] = df["surface"].str.replace("m²", "").str.strip().astype(int)
df["rooms"] = df["rooms"].str.replace(r"chambres|chambre", "", regex=True).str.strip().astype(int)
df["baths"] = df["baths"].str.replace(r"sdbs|sdb", "", regex=True).str.strip().astype(int)

# Remove unrealistic surface outliers
df = df[df["surface"] <= 500]

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
df.to_csv(r"C:\Users\HP\Desktop\web_scraping\clean\avito_data_clean.csv", index=False)