import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Fetch log directory from environment variable
log_dir = os.getenv('Logs', 'E:\\scripts\\Logs')  # Default to 'E:\\scripts\\Logs' if not set
log_file = os.path.join(log_dir, 'steamdb_crawler.log')

# Ensure the log directory exists
os.makedirs(log_dir, exist_ok=True)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels

# File handler for logging to file
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Add file handler to the logger (no console handler to avoid logging to the terminal)
logger.addHandler(file_handler)

logger.info("Starting the SteamDB Crawler script")

# Configure Chrome WebDriver
chrome_driver_path = 'D:\\chromedriver-win64\\chromedriver.exe'
service = Service(chrome_driver_path)
options = Options()
options.headless = False  # Set to True if you want to run in headless mode
driver = webdriver.Chrome(service=service, options=options)

try:
    # Navigate to the SteamDB page
    url = 'https://steamdb.info/depot/1091501/'
    logger.info(f"Navigating to {url}")
    driver.get(url)

    # Wait until the "Manifests" tab is clickable, then click it
    try:
        manifests_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'tab-manifests'))
        )
        logger.info("Found the Manifests tab. Clicking it.")
        manifests_tab.click()
    except TimeoutException:
        logger.error("Timed out waiting for the Manifests tab.")
        raise

    # Wait for the manifest table to appear
    try:
        manifest_table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//table[contains(@class, "table-responsive-flex")]/tbody'))
        )
        logger.info("Found the manifest table.")
    except TimeoutException:
        logger.error("Timed out waiting for the manifest table.")
        raise

    # Find all rows in the table body
    manifest_rows = manifest_table.find_elements(By.TAG_NAME, 'tr')

    # Log each manifest ID from the third column
    logger.info("Listing manifest IDs:")
    for index, row in enumerate(manifest_rows):
        try:
            # Log the entire row's HTML to the file for debugging
            row_html = row.get_attribute('outerHTML')
            logger.debug(f"Row {index + 1} HTML content: {row_html}")

            # Find the columns (td elements) in the row
            tds = row.find_elements(By.TAG_NAME, 'td')

            # Check if there are at least three columns and fetch the Manifest ID from the third column
            if len(tds) >= 3:
                manifest_id = tds[2].text.strip()  # Third column contains the Manifest ID
                if manifest_id.isdigit():
                    print(manifest_id)  # Output to terminal
                    logger.info(f"Manifest ID {index + 1}: {manifest_id}")
                else:
                    logger.warning(f"Row {index + 1} does not contain a valid Manifest ID. HTML: {row_html}")
            else:
                logger.warning(f"Row {index + 1} has fewer than 3 columns. HTML: {row_html}")

        except NoSuchElementException:
            logger.warning(f"Row {index + 1} has no <a> elements. HTML: {row_html}")
        except Exception as e:
            # Log an exception if anything else goes wrong
            logger.warning(f"Error processing row {index + 1}: {str(e)}")

except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
finally:
    logger.info("Closing the browser.")
    driver.quit()

logger.info("Script finished.")
