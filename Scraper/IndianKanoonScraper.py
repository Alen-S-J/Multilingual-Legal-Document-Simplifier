import os
import time
import chromedriver_autoinstaller
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup


# === CONFIGURATION === #
BASE_URL = "https://indiankanoon.org"
BROWSE_URL = BASE_URL + "/browse/"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "indiankanoon-all-cases")
USERNAME = "sabu.s.alan@gmail.com"
PASSWORD = "Alan@123"
MAX_WAIT = 20


# === CHROME DRIVER SETUP === #
chromedriver_autoinstaller.install()
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

chrome_options = Options()
chrome_options.add_experimental_option("prefs", {"download.default_directory": DOWNLOAD_DIR})
chrome_options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, MAX_WAIT)


# === LOGIN === #
def login():
    login_url = "https://indiankanoon.org/members/login/?nextpage=/"
    driver.get(login_url)
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(USERNAME)
    driver.find_element(By.NAME, "passwd").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//input[@type='submit']").click()
    time.sleep(2)


# === FETCH COURT CATEGORY LINKS === #
def get_court_category_links():
    driver.get(BROWSE_URL)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    info_blocks = soup.find_all('div', class_='info_indian_kanoon')
    court_links = {}

    for block in info_blocks:
        for link in block.find_all('a'):
            label = link.text.strip()
            court_links[label] = BASE_URL + link['href']
    
    return court_links


# === PAGINATE AND COLLECT CASE LINKS === #
def get_all_case_links(category_url):
    all_links = []
    page = 0
    while True:
        paginated_url = f"{category_url}?p={page}&sortby=mostrecent"
        driver.get(paginated_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = soup.find_all('div', class_='result')

        if not results:
            break  # No more pages

        for div in results:
            case_link = BASE_URL + div.a['href']
            all_links.append(case_link)
        page += 1
        time.sleep(1)

    return all_links


# === DOWNLOAD DOCUMENT PDF === #
def download_documents(links, court_copy=False):
    button_text = "Download Court Copy" if court_copy else "Get this document in PDF"
    for idx, url in enumerate(links):
        driver.get(url)
        print(f"[{idx+1}/{len(links)}] Visiting: {url}")
        try:
            download_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(),'{button_text}')]"))
            )
            download_button.click()
            time.sleep(3)
        except TimeoutException:
            print(f"⛔ Timeout: Download button not found for {url}")
        except Exception as e:
            print(f"⚠️ Error downloading from {url}: {e}")


# === MAIN FUNCTION === #
def download_all_cases(court_copy=False):
    if court_copy:
        login()

    court_links = get_court_category_links()
    print("✅ Found court categories:", list(court_links.keys()))

    for court_name, court_url in court_links.items():
        print(f"\n📂 Scraping category: {court_name}")
        case_links = get_all_case_links(court_url)
        print(f"   - Found {len(case_links)} cases.")
        download_documents(case_links, court_copy=court_copy)


# === EXECUTE === #
download_all_cases(court_copy=False)
driver.quit()
