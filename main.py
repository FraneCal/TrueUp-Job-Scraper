from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
import time
import csv

SEARCH_TERM = "software engineer"
EMAIL = "EMAIL"
PASSWORD = "PASSWORD"

class TwitterScraper:
    def __init__(self):
        self.options = Options()
        # self.options.add_argument('--headless=new')
        self.driver = None

    def selenium_initialization(self, URL):
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get(URL)
        # self.driver.maximize_window()

        self.selenium_log_in()

    def selenium_log_in(self):
        self.log_in_button = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="main-nav"]/nav/div[2]/div[2]/button[1]'))
        )
        self.log_in_button.click()

        self.email = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="username"]'))
        )
        self.email.click()
        self.email.send_keys(EMAIL)

        self.password = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]'))
        )
        self.password.click()
        self.password.send_keys(PASSWORD)

        self.continue_button = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div[2]/main/section/div/div/div/form/div[2]/button'))
        )
        self.continue_button.click()

        time.sleep(3)

        self.selenium_search_bar()

    def selenium_search_bar(self):
        self.search_bar = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/main/main/div/div[2]/div/div/div/div/div/div/div/div/div[1]/div/div/div[1]/form/input'))
        )
        self.search_bar.click()
        self.search_bar.send_keys(SEARCH_TERM)
        self.search_bar.send_keys(Keys.ENTER)

        time.sleep(2)

        self.selenium_show_all_jobs()

    def selenium_show_all_jobs(self):
        while True:
            try:
                # Step 1: Scroll down gradually to load initial jobs
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Give the page time to load content

                # Step 2: Try to find the "Show More" button
                show_more_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(@class, 'ais-InfiniteHits-loadMore')]"))
                )

                # Step 3: Scroll to the button before clicking it to ensure it's in view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                time.sleep(1)  # Allow UI to settle

                try:
                    # Try clicking the button
                    show_more_button.click()
                except ElementClickInterceptedException:
                    print("Click intercepted! Trying JavaScript click...")
                    # Fallback: click using JavaScript if the normal click fails
                    self.driver.execute_script("arguments[0].click();", show_more_button)

                time.sleep(1)  # Allow new content to load

                # Step 4: Scroll down again to make sure new jobs are visible
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Give it time to load more content

            except (NoSuchElementException, TimeoutException):
                print("No more 'Show More' button found or timeout. Exiting loop.")
                break

            except ElementNotInteractableException:
                print("Element not interactable. Trying again...")
                time.sleep(2)  # Wait before retrying
                break

            except Exception as e:
                print(f"Unexpected error occurred: {str(e)}")
                break

        self.beautiful_soup_initialization()

    def beautiful_soup_initialization(self):
        # Get the page source and initialize BeautifulSoup
        self.page_source = self.driver.page_source
        self.soup = BeautifulSoup(self.page_source, "html.parser")

        # Find all job names, company names, and locations
        self.job_names = self.soup.find_all("div", class_="font-bold mb-1")
        self.company_names = self.soup.find_all("a",
                                                class_="text-foreground font-medium text-base hover:underline hover:underline-offset-2")
        self.locations = self.soup.find_all("div",
                                            class_="overflow-hidden text-gray-500 dark:text-gray-400 mb-2 font-medium")

        # Open a CSV file to save the data
        with open("job_listings.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Write the header if the file is empty
            if file.tell() == 0:
                writer.writerow(["Job Name", "Company Name", "Location", "Job Link"])

            # Iterate over the job listings and extract the relevant information
            for job, company_name, location in zip(self.job_names, self.company_names, self.locations):
                job_text = job.getText().strip() if job else "-"
                company_text = company_name.getText().strip() if company_name else "-"
                location_text = location.getText().strip() if location else "-"

                # Find the link for the job
                job_link = job.find("a", href=True)["href"] if job.find("a", href=True) else "-"

                # Write the row of job details to the CSV file
                writer.writerow([job_text, company_text, location_text, job_link])

            print("Job listings saved to CSV.")

if __name__ == "__main__":
    URL = "https://trueup.io/jobs"

    scraper = TwitterScraper()
    scraper.selenium_initialization(URL)
