import os
import time
import csv
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import chromedriver_autoinstaller

# === CONFIGURATION ===
BASE_URL = "https://indiankanoon.org"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "indiankanoon-case-dump")
YEARS = list(range(1946, 2025))  # For year-wise scraping
USERNAME = __Your EmailID __ 
PASSWORD = __Your Password__
USE_DATE_RANGE = False  # Set True for range search, False for year-wise
FROM_DATE = "1-01-1946"
TO_DATE = "30-12-2024"
COURT_FILTER = ['Supreme Court of India', 'Supreme Court - Daily Orders', 'Allahabad High Court', 'Andhra HC (Pre-Telangana)', 'Andhra Pradesh High Court - Amravati', 'Bombay High Court', 'Calcutta High Court', 'Calcutta High Court (Appellete Side)', 'Chattisgarh High Court', 'Delhi High Court', 'Delhi High Court - Orders', 'Gauhati High Court', 'Gujarat High Court', 'Himachal Pradesh High Court', 'Jammu & Kashmir High Court', 'Jammu & Kashmir High Court - Srinagar Bench', 'Jharkhand High Court', 'Karnataka High Court', 'Kerala High Court', 'Madhya Pradesh High Court', 'Manipur High Court', 'Meghalaya High Court', 'Madras High Court', 'Orissa High Court', 'Patna High Court', 'Patna High Court - Orders', 'Punjab-Haryana High Court', 'Rajasthan High Court - Jaipur', 'Rajasthan High Court - Jodhpur', 'Sikkim High Court', 'Uttarakhand High Court', 'Tripura High Court', 'Telangana High Court', 'Delhi District Court', 'Bangalore District Court', 'Appellate Tribunal For Electricity', 'Authority Tribunal', 'Central Administrative Tribunal', 'Customs, Excise and Gold Tribunal', 'Central Electricity Regulatory Commission', 'Central Information Commission', 'Company Law Board', 'Consumer Disputes Redressal', 'Copyright Board', 'Debt Recovery Appellate Tribunal', 'National Green Tribunal', 'Competition Commission of India', 'Intellectual Property Appellate Board', 'Income Tax Appellate Tribunal', 'Monopolies and Restrictive Trade Practices Commission', 'Securities Appellate Tribunal', 'State Taxation Tribunal', 'Telecom Disputes Settlement Tribunal', 'Trademark Tribunal', 'Custom, Excise & Service Tax Tribunal', 'National Company Law Appellate Tribunal', 'Law Commission Report', 'Constituent Assembly Debates', 'Lok Sabha Debates', 'Rajya Sabha Debates'] # Set to list like ['Supreme Court of India'] or None for all

# === Setup ===
chromedriver_autoinstaller.install()
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--headless=new")
options.add_experimental_option("prefs", {"download.default_directory": DOWNLOAD_DIR})
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# === Functions ===
def login():
    driver.get(f"{BASE_URL}/members/login/?nextpage=/")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(USERNAME)
    driver.find_element(By.NAME, "passwd").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//input[@type='submit']").click()
    time.sleep(2)

def get_court_category_links():
    driver.get(f"{BASE_URL}/browse/")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    info_blocks = soup.find_all('div', class_='info_indian_kanoon')
    court_links = {}
    for block in info_blocks:
        for link in block.find_all('a'):
            label = link.text.strip()
            if COURT_FILTER is None or label in COURT_FILTER:
                court_links[label] = BASE_URL + link['href']
    return court_links

def get_case_text(url):
    try:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        content = soup.find('div', class_='judgments') or soup.find('pre')
        return content.get_text(separator='\n', strip=True) if content else "N/A"
    except Exception:
        return "N/A"

def get_cases_by_year(court_url, year):
    all_cases = []
    page = 0
    while True:
        paginated_url = f"{court_url}?year={year}&p={page}"
        driver.get(paginated_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = soup.find_all('div', class_='result')
        if not results:
            break
        for div in results:
            title_tag = div.find("a")
            if not title_tag:
                continue
            title = title_tag.text.strip()
            url = BASE_URL + title_tag['href']
            snippet = div.find("p", class_="snippet")
            snippet_text = snippet.text.strip() if snippet else ""
            date_span = div.find("span", class_="result_date")
            date_text = date_span.text.strip() if date_span else ""
            print(f"   📄 {year} | {title}")
            full_text = get_case_text(url)
            all_cases.append({
                "Title": title,
                "URL": url,
                "Snippet": snippet_text,
                "Date": date_text,
                "Full_Text": full_text
            })
        page += 1
        time.sleep(0.5)
    return all_cases

def get_cases_by_date_range(court_type):
    query = f"doctypes:{court_type} fromdate:{FROM_DATE} todate:{TO_DATE}"
    search_url = f"{BASE_URL}/search/?formInput={query}"
    all_cases = []
    page = 0
    while True:
        driver.get(f"{search_url}&p={page}")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = soup.find_all('div', class_='result')
        if not results:
            break
        for div in results:
            title_tag = div.find("a")
            if not title_tag:
                continue
            title = title_tag.text.strip()
            url = BASE_URL + title_tag['href']
            snippet = div.find("p", class_="snippet")
            snippet_text = snippet.text.strip() if snippet else ""
            date_span = div.find("span", class_="result_date")
            date_text = date_span.text.strip() if date_span else ""
            print(f"   📄 {date_text} | {title}")
            full_text = get_case_text(url)
            all_cases.append({
                "Title": title,
                "URL": url,
                "Snippet": snippet_text,
                "Date": date_text,
                "Full_Text": full_text
            })
        page += 1
        time.sleep(0.5)
    return all_cases

def save_to_csv(name, cases):
    if not cases:
        return
    safe_name = name.replace(" ", "_").replace("/", "-")
    file_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.csv")
    with open(file_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "URL", "Snippet", "Date", "Full_Text"])
        writer.writeheader()
        writer.writerows(cases)

# === Main Execution ===
def main():
    login()
    court_links = get_court_category_links()
    print("✅ Courts found:", list(court_links.keys()))

    for court_name, court_url in court_links.items():
        print(f"\n📂 Scraping {court_name}...")
        if USE_DATE_RANGE:
            cases = get_cases_by_date_range(court_name)
        else:
            cases = []
            for year in YEARS:
                yearly_cases = get_cases_by_year(court_url, year)
                cases.extend(yearly_cases)
        print(f"   ✅ Total {len(cases)} cases fetched.")
        save_to_csv(court_name, cases)

# === Run Script ===
if __name__ == "__main__":
    main()
    driver.quit()
