import pandas as pd

#------------
# export csv
#------------
df = pd.read_csv(r"C:\Users\HP\Desktop\web_scraping\staging\staging_avito_raw.csv")

#----------------
# drop duplicates
#----------------
df = df.drop_duplicates()

#------------------------------------------
# extract city & neighborhood from location 
#------------------------------------------
df["city"] = df["location"].str.replace("Appartements dans", "").str.split(",").str[0].str.strip()

df["neighborhood"] = df["location"].str.replace("Appartements dans", "").str.split(",").str[1].str.strip()

#-----------------------
# from string to integer
#-----------------------
df["surface"] = df["surface"].str.replace("m²", "").str.strip().astype(int)

df["rooms"] = df["rooms"].str.replace(r"chambres|chambre", "", regex=True).str.strip().astype(int)

df["baths"] = df["baths"].str.replace(r"sdbs|sdb", "", regex=True).str.strip().astype(int)

#----------------
# price per meter
#----------------
df["price_meter"] = (df["price"] / df["surface"]).astype(int)

#-----------------------------------------------------
# drop nulls of the neighborhood column {0.5% = nulls}
#-----------------------------------------------------
df = df.dropna()

#-------------
# KPIs
#----------------
def price_category(price):
    if price <= 500000:
        return "Low"
    elif price >= 1000000:
        return "High"
    else:
        return "Medium"

df["price_category"] = df["price"].apply(price_category)

#---------------
# import to csv
#---------------
df.to_csv("avito_data_clean.csv", index=False)