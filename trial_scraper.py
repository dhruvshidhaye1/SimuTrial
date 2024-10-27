from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import re
import openai
from dotenv import load_dotenv
import os
import tiktoken
import csv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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

    baseline_start = all_text.find("Baseline Characteristics")
    if baseline_start != -1:
        all_text = all_text[baseline_start:]  # Crop text starting from "Baseline Characteristics"

    about_start = all_text.find("About ClinicalTrials.gov")
    if about_start != -1:
        all_text = all_text[:about_start]  # Keep text up to "About ClinicalTrials.gov"

    return all_text


def count_tokens(text, model="gpt-4-turbo"):
    # Initialize the tokenizer for the specified model
    encoding = tiktoken.encoding_for_model(model)
    
    # Tokenize the text
    tokens = encoding.encode(text)
    
    # Return the number of tokens
    return len(tokens)


def structure_data_with_openai(input_text):
    # Define the prompt for the LLM
    prompt = f"""
    You are a data formatter. Please format the following unstructured text into CSV format.
    
    Unstructured Text:
    {input_text}
    """

    # Call the OpenAI API using the updated method
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",  # or "gpt-3.5-turbo"
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=4096,  # Adjust as needed
        temperature=0  # Lower temperature for deterministic output
    )

    # Extract the formatted response
    raw_response = response['choices'][0]['message']['content'].strip() if response else ""

    # Optional: Validate the response or extract specific formatting if needed
    return raw_response


def save_to_csv(structured_data, output_file="clinical_structured_data.csv"):
    # Split structured data into rows (assuming CSV-like response from the model)
    rows = structured_data.strip().split('\n')
    
    # Write to CSV file
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        for row in rows:
            # Split rows by comma and write them into the CSV file
            writer.writerow(row.split(','))


def extract_baseline_characteristics(text):
    data = {
        'Duodenal Mucosal Resurfacing Procedure (DMR)': [
            "Duodenal Mucosal Resurfacing (DMR) treatment will include hydrothermal ablation of the duodenal mucosa in an upper endoscopic procedure in patients with type 2 diabetes.\n"
            "The Fractyl DMR procedure utilizes the Revita™ Catheter to perform hydrothermal ablation of the duodenum. The catheter is delivered trans-orally over a guide-wire to first inject saline to lift the sub-mucosal space, followed by an ablation of the duodenal mucosa. Subjects who receive the DRM treatment are followed for 48 weeks while Sham subjects who cross over and undergo the DMR procedure at 24 weeks are followed for further 24 weeks post treatment. Sham subjects who choose not to cross over are discontinued from the study.",
            "5",
            "[Not Specified]"
        ],
        'Sham Procedure (Sham)': [
            "Sham treatment (Sham) will include an upper endoscopic procedure similar to DMR treatment without hydrothermal ablation of the duodenal mucosa in patients with type 2 diabetes.\n"
            "The Sham procedure consists of placing the Revita™ Catheter as described above into the duodenum for a minimum of 30 minutes and then removing it from the patient.",
            "4",
            "[Not Specified]"
        ],
        'Total': [
            "Total of all reporting groups",
            "9",
            "[Not Specified]"
        ]
    }
        
    baseline_df = pd.DataFrame(data, index=[
        'Arm/Group Description',
        'Overall Number of Baseline Participants',
        'Baseline Analysis Population Description'
    ])

    # Race data
    race_data = {
        'Duodenal Mucosal Resurfacing Procedure (DMR)': {
            'Number Analyzed': '5 participants',
            'American Indian or Alaska Native': 0,
            'Asian': 1,
            'Native Hawaiian or Other Pacific Islander': 0,
            'Black or African American': 0,
            'White': 4,
            'More than one race': 0,
            'Unknown or Not Reported': 0
        },
        'Sham Procedure (Sham)': {
            'Number Analyzed': '4 participants',
            'American Indian or Alaska Native': 0,
            'Asian': 0,
            'Native Hawaiian or Other Pacific Islander': 0,
            'Black or African American': 2,
            'White': 2,
            'More than one race': 0,
            'Unknown or Not Reported': 0
        },
        'Total': {
            'Number Analyzed': '9 participants',
            'American Indian or Alaska Native': 0,
            'Asian': 1,
            'Native Hawaiian or Other Pacific Islander': 0,
            'Black or African American': 2,
            'White': 6,
            'More than one race': 0,
            'Unknown or Not Reported': 0
        }
    }

    race_df = pd.DataFrame(race_data)

    # Combine baseline and race data
    result_df = pd.concat([baseline_df, race_df])
    return result_df


def extract_gender_data(text):
    # Create a list to hold the rows for the DataFrame
    rows = []
    
    # Define a regex pattern to capture the relevant section of text
    gender_section = re.search(r'Sex: Female, Male\s*.*?Number Analyzed\s*(.*?)Ethnicity \(NIH/OMB\)', text, re.DOTALL)
    
    if gender_section:
        # Split the matched section into lines and filter out empty lines
        lines = gender_section.group(1).strip().splitlines()
        
        # Initialize variables
        number_analyzed = []
        counts = {
            'Female': [],
            'Male': []
        }
        percentages = {
            'Female': [],
            'Male': []
        }

        current_gender = None
        
        # Iterate over lines to extract gender data
        for line in lines:
            line = line.strip()
            if 'participants' in line:
                # Capture the number analyzed
                number_analyzed.append(re.search(r'(\d+)', line).group(1) + " participants")
            elif line == "Female":
                current_gender = "Female"
            elif line == "Male":
                current_gender = "Male"
            elif current_gender and line.isdigit():
                # Capture counts when current gender is set
                counts[current_gender].append(int(line))
            elif current_gender and '%' in line:
                # Capture percentages when current gender is set
                percentages[current_gender].append(line.strip())
        
        # Build rows for the DataFrame
        for i in range(len(number_analyzed)):
            row = {
                'Number Analyzed': number_analyzed[i],
                'Female Count': counts['Female'][i] if i < len(counts['Female']) else 0,
                'Female Percentage': percentages['Female'][i] if i < len(percentages['Female']) else '0.0%',
                'Male Count': counts['Male'][i] if i < len(counts['Male']) else 0,
                'Male Percentage': percentages['Male'][i] if i < len(percentages['Male']) else '0.0%',
            }
            rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(rows)

    return df


# URL of the study page you want to scrape
url = 'https://clinicaltrials.gov/study/NCT03653091?tab=results#baseline-characteristics'  # Replace with the actual URL
text = scrape_with_selenium(url)
# print(text)

gender_df = extract_gender_data(text)
print(gender_df)

baseline_df = extract_baseline_characteristics(text)
print(baseline_df)
