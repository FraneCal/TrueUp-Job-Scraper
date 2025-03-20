from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
import time
import csv
import re

EMAIL = "EMAIL"
PASSWORD = "PASSWORD"
CSV_FILENAME = "company_open_jobs.csv"
OUTPUT_FILENAME = "job_listings_by_company_2.csv"

class CompanyScraper():
    def __init__(self):
        self.options = Options()
        self.options.add_argument('--headless=new')  # Enable headless mode
        self.driver = None

    def selenium_initialization(self):
        """Initialize Selenium WebDriver"""
        print("Initializing Selenium WebDriver...")
        self.driver = webdriver.Chrome(options=self.options)
        print("Selenium WebDriver initialized.")
        self.selenium_log_in()

    def selenium_log_in(self):
        """Logs into the website"""
        print("Opening website...")
        self.driver.get("https://trueup.io")  # Open homepage
        self.driver.maximize_window()

        print("Clicking login button...")
        # Click the login button
        self.log_in_button = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="main-nav"]/nav/div[2]/div[2]/button[1]'))
        )
        self.log_in_button.click()

        print("Entering login credentials...")
        # Enter email
        self.email = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="username"]'))
        )
        self.email.send_keys(EMAIL)

        # Enter password
        self.password = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]'))
        )
        self.password.send_keys(PASSWORD)

        print("Clicking continue button...")
        # Click continue
        self.continue_button = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div[2]/main/section/div/div/div/form/div[2]/button'))
        )
        self.continue_button.click()

        time.sleep(3)
        print("Login complete.")

    def extract_company_name(self, url):
        """Extracts the company name from the URL"""
        print(f"Extracting company name from URL: {url}")
        match = re.search(r"https://trueup\.io/co/([^/]+)/jobs", url)
        company_name = match.group(1).capitalize() if match else "Unknown"
        print(f"Extracted company name: {company_name}")
        return company_name

    def selenium_show_all_jobs(self):
        """Loads all job postings by scrolling and clicking 'Show More'"""
        print("Clicking job category 'Engineering (Software)'...")
        self.job_picker = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//a[contains(@class, 'ais-HierarchicalMenu-link') and span[contains(text(), 'Engineering (Software)')]]")
            )
        )
        self.job_picker.click()

        time.sleep(2)
        print("Scrolling and loading more jobs...")
        while True:
            try:
                # Scroll to the bottom to trigger lazy loading
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Allow time for content to load

                print("Searching for 'Show More' button...")
                # Try to find the "Show More" button
                show_more_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'ais-InfiniteHits-loadMore')]"))
                )

                # Scroll to the button before clicking it
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                time.sleep(1)

                try:
                    print("Clicking 'Show More' button...")
                    # Attempt clicking the button
                    show_more_button.click()
                except ElementClickInterceptedException:
                    print("Click intercepted! Trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", show_more_button)

                time.sleep(1)  # Allow content to load

                # Scroll down again to ensure new jobs are visible
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            except (NoSuchElementException, TimeoutException):
                print("No more 'Show More' button found. Exiting loop.")
                break

            except ElementNotInteractableException:
                print("Element not interactable. Retrying...")
                time.sleep(2)
                break

            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                break

    def scrape_jobs_for_company(self, company_name, company_url):
        """Scrapes job listings for a given company"""
        print(f"Scraping jobs for {company_name} from {company_url}...")
        self.driver.get(company_url)
        time.sleep(3)  # Allow page to load

        # Load all jobs before scraping
        self.selenium_show_all_jobs()

        # Initialize BeautifulSoup
        print("Parsing page with BeautifulSoup...")
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Find all job names and locations
        job_names = soup.find_all("div", class_="font-bold mb-1")
        locations = soup.find_all("div", class_="overflow-hidden text-gray-500 dark:text-gray-400 mb-2 font-medium")

        print(f"Found {len(job_names)} job listings. Saving to CSV...")
        # Open CSV to save data
        with open(OUTPUT_FILENAME, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Write header if file is empty
            if file.tell() == 0:
                writer.writerow(["Company Name", "Job Name", "Location", "Job Link"])

            # Iterate over job listings
            for job, location in zip(job_names, locations):
                job_text = job.getText().strip() if job else "-"
                location_text = location.getText().strip() if location else "-"
                job_link = job.find("a", href=True)["href"] if job.find("a", href=True) else "-"

                # Write job details with company name
                writer.writerow([company_name, job_text, location_text, job_link])

        print(f"Scraped jobs for {company_name}.")

    def read_company_links_and_scrape(self):
        """Reads company links from CSV and scrapes jobs for each"""
        print(f"Reading company links from {CSV_FILENAME} and starting scrape...")
        with open(CSV_FILENAME, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header

            for row in reader:
                if row:
                    company_url = row[0]
                    company_name = self.extract_company_name(company_url)
                    self.scrape_jobs_for_company(company_name, company_url)

    def close(self):
        """Closes the browser"""
        print("Closing the browser...")
        if self.driver:
            self.driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    print("Starting scraper...")
    scraper = CompanyScraper()
    scraper.selenium_initialization()
    scraper.read_company_links_and_scrape()
    scraper.close()
    print("Scraping completed.")
