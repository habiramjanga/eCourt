from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

# Use consistent names for globals
driver = None
wait = None

def get_driver():
    global driver, wait  # ensure we modify the globals
    if driver is None:
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")  # optional
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)

        # Navigate to main page and click Case Status link
        driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "a[href*='casestatus/index']"))
        driver.find_element(By.CSS_SELECTOR, "a[href*='casestatus/index']").click()

    return driver, wait

def close_driver():
    global driver, wait  # fix the globals here too
    if driver:
        driver.quit()
        driver = None
        wait = None
