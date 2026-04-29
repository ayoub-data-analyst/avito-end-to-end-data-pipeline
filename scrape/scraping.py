import time
import csv
import logging as log
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options

log.basicConfig(
    filename="scrape_avito.log",
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)

logger = log.getLogger()

# setup driver
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=options)
driver.get("https://www.avito.ma/fr/maroc/appartements-%C3%A0_vendre?price=100000-&rooms=1&bathrooms=1&has_price=true&size=20-")

wait = WebDriverWait(driver, 10)

results = []

# pagination loop
for page in range(100):

    logger.info(f"Page {page+1} start")

    # scroll
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1)

    # get cards
    cards = driver.find_elements(By.XPATH, "//a[contains(@href,'/appartements/')]")
    logger.info(f"Cards found: {len(cards)}")

    for card in cards:
        try:
            link = card.get_attribute("href")

            # title
            try:
                title = card.find_element(By.XPATH, ".//p[@title]").text
            except:
                title = card.text.split("\n")[0]

            # location
            try:
                location = card.find_element(By.XPATH, ".//p[contains(text(),'dans')]").text
            except:
                location = None

            # price
            try:
                price_text = card.find_element(By.XPATH, ".//span[contains(@class,'3286ebc5-2')]").text
                price = int(price_text.replace("\u202f", "").replace(" ", ""))
            except:
                price = None

            # details
            surface = rooms = baths = None
            lines = card.text.lower().split("\n")

            for l in lines:
                if "m²" in l:
                    surface = l
                elif "chambre" in l:
                    rooms = l
                elif "sdb" in l or "bain" in l:
                    baths = l

            results.append({
                "title": title,
                "price": price,
                "location": location,
                "surface": surface,
                "rooms": rooms,
                "baths": baths,
                "link": link
            })

        except Exception as e:
            logger.warning(f"Error parsing card: {e}")
            continue

    # next page
    try:
        next_buttons = driver.find_elements(By.XPATH, "//a[contains(@href,'?o=')]")
        next_btn = next_buttons[-1]

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
        next_btn.click()

        time.sleep(3)

    except Exception as e:
        logger.info("Last page reached")
        break

driver.quit()

# save CSV
if results:
    with open(r"C:\Users\HP\Desktop\web_scraping\staging\staging_avito_raw.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "title", "price", "location", "surface", "rooms", "baths", "link"
        ])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"CSV saved with {len(results)} rows")
    print("CSV saved")
else:
    logger.warning("No data collected")
    print("No data")