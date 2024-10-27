from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import re

def scrape_with_selenium(url):
    # Set up Selenium with Chrome
    options = Options()
    options.headless = True  # Run in headless mode (no UI)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Open the URL
    driver.get(url)

    # Get the page source
    page_source = driver.page_source

    # Close the driver
    driver.quit()

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract all text content from the HTML
    all_text = soup.get_text(separator='\n', strip=True)

    return all_text

import re  # Add this import for regular expressions

def extract_data(raw_data):
    lines = raw_data.strip().split('\n')
    results = []
    
    # Initialize the index
    i = 0

    # Extract age categories
    age_data = {}
    while i < len(lines):
        if 'Age, Categorical' in lines[i]:
            i += 5  # Skip to data section
            for _ in range(3):  # Three age groups
                if i >= len(lines): break
                age_group = lines[i].strip()
                count = lines[i + 1].strip()
                percentage = lines[i + 2].strip()

                # Extract numeric values using regex
                count_value = int(re.search(r'\d+', count).group())
                percentage_value = float(re.search(r'\d+', percentage).group()) / 100

                age_data[age_group] = {
                    'Count': count_value, 
                    'Percentage': percentage_value
                }
                i += 3  # Move to the next age group
            break
        i += 1

    results.append(('Age', age_data))

    # Reset index for extracting sex data
    i = 0

    # Extract sex data
    sex_data = {}
    while i < len(lines):
        if 'Sex: Female, Male' in lines[i]:
            i += 5  # Skip to data section
            for _ in range(2):  # Two sex categories
                if i >= len(lines): break
                sex_group = lines[i].strip()
                count = lines[i + 1].strip()
                percentage = lines[i + 2].strip()

                # Extract numeric values using regex
                count_value = int(re.search(r'\d+', count).group())
                percentage_value = float(re.search(r'\d+', percentage).group()) / 100

                sex_data[sex_group] = {
                    'Count': count_value, 
                    'Percentage': percentage_value
                }
                i += 3  # Move to the next sex group
            break
        i += 1

    results.append(('Sex', sex_data))

    # Reset index for extracting height data
    i = 0

    # Extract height data
    while i < len(lines):
        if 'Height (cm)' in lines[i]:
            i += 5  # Skip to mean data
            mean_height = lines[i].strip()
            std_dev_height = lines[i + 1].strip().strip('()')

            # Extract numeric values using regex
            mean_value = float(re.search(r'\d+(\.\d+)?', mean_height).group())
            std_dev_value = float(re.search(r'\d+(\.\d+)?', std_dev_height).group())

            height_data = {
                'Mean': mean_value, 
                'Standard Deviation': std_dev_value
            }
            results.append(('Height', height_data))
            break
        i += 1

    return results



# URL of the study page you want to scrape
url = 'https://clinicaltrials.gov/study/NCT03653091?tab=results#baseline-characteristics'  # Replace with the actual URL
data = scrape_with_selenium(url)

# Call the function and create a DataFrame
extracted_data = extract_data(data)
df = pd.DataFrame({
    'Category': [category for category, _ in extracted_data],
    'Data': [data for _, data in extracted_data]
})

# Display the DataFrame
print(df)
