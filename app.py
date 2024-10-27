import streamlit as st
import pandas as pd
import polars as pl
import json
from mesa import Agent, Model
from mesa.time import RandomActivation
import random
import numpy as np
import time
import requests
from bs4 import BeautifulSoup

# Load JSON mapping
column_mapping = {
  "age": ["Age", "age", "dob"],
  "gender": ["Gender", "sex", "Sex"],
  "race_ethnicity": ["Race", "Ethnicity", "race_ethnicity", "race", "race:AfricanAmerican", "race:Asian", "race:Caucasian", "race:Hispanic", "race:Other"],
  "region": ["Location", "region", "Region"],
  "health_issues": ["Conditions", "health_conditions", "Issues", "hypertension", "heart_disease"]
}

# Function to normalize columns with race aggregation
def normalize_columns(df, mapping):
    # Iterate through mapping dictionary to rename columns
    for standard_name, possible_names in mapping.items():
        for col in possible_names:
            if col in df.columns:
                df = df.rename({col: standard_name})
                break

    # Handle race/ethnicity columns separately by aggregating into one
    race_cols = [col for col in df.columns if col.startswith("race:")]
    if race_cols:
        df = df.with_columns(
            pl.concat_list([df[col] for col in race_cols]).alias("race_ethnicity")
        )
        df = df.drop(race_cols)
    
    return df

class PatientAgent(Agent):
    def __init__(self, unique_id, model, age, gender, race, region, health_issues):
        super().__init__(unique_id, model)
        self.age = age
        self.gender = gender
        self.race = race
        self.region = region
        self.health_issues = health_issues
        self.consented = False

    def step(self):
        # Determine consent based on consent rate range
        consent_probability = random.uniform(self.model.consent_rate_min, self.model.consent_rate_max)
        self.consented = random.random() < consent_probability

class RecruitmentModel(Model):
    def __init__(self, df, consent_rate_min, consent_rate_max):
        self.df = df
        self.consent_rate_min = consent_rate_min
        self.consent_rate_max = consent_rate_max
        self.schedule = RandomActivation(self)

        # Create agents based on the DataFrame
        for i, row in df.iterrows():
            age = row.get('age', None)
            gender = row.get('gender', None)
            race = row.get('race_ethnicity', None)
            region = row.get('region', None)
            health_issues = row.get('health_issues', None)
            
            agent = PatientAgent(i, self, age, gender, race, region, health_issues)
            self.schedule.add(agent)

    def step(self):
        self.schedule.step()

# Function to run multiple simulations and calculate scores
def run_simulations(df, consent_rate_min, consent_rate_max, num_simulations):
    consent_results = []
    staff_requirements = []
    site_recommendations = []

    for i in range(num_simulations):
        model = RecruitmentModel(df, consent_rate_min, consent_rate_max)
        for _ in range(1):  # Run for 1 step (as we only need to determine consent)
            model.step()
        consented_agents = sum([1 for agent in model.schedule.agents if agent.consented])
        consent_results.append(min(consented_agents, len(df)))
        
        # Use a simple heuristic to estimate staff and sites
        staff_needed = max(1, int(consented_agents / 50))  # Assume 1 staff per 50 consenting patients
        sites_needed = max(1, int(consented_agents / 100))  # Assume 1 site per 100 consenting patients
        staff_requirements.append(staff_needed)
        site_recommendations.append(sites_needed)

        # Update progress bar
        st.session_state.progress.progress((i + 1) / num_simulations)
    
    # Calculate statistics
    mean_consent_rate = (np.mean(consent_results) / len(df)) * 100
    confidence_interval = (np.std(consent_results) * 1.96 / np.sqrt(num_simulations)) / len(df) * 100
    mean_staff = np.mean(staff_requirements)
    mean_sites = np.mean(site_recommendations)
    
    return {
        "mean_consent_rate": mean_consent_rate,
        "confidence_interval": confidence_interval,
        "staff_requirements": staff_requirements,
        "site_recommendations": site_recommendations,
        "mean_staff": mean_staff,
        "mean_sites": mean_sites
    }

# Function to scrape staff and sites requirements
def webscrape_staff_sites():
    try:
        # Example webscraping to get staff and sites requirements
        response = requests.get("https://example.com/staff_sites")
        soup = BeautifulSoup(response.text, "html.parser")

        # Assuming the data is in some table format
        staff_data = soup.find("span", {"id": "staff_needed"}).text
        sites_data = soup.find("span", {"id": "sites_needed"}).text

        return int(staff_data), int(sites_data)
    
    except Exception as e:
        # Fallback if scraping fails
        st.warning("Unable to retrieve staff and sites requirements via webscraping.")
        return None, None

# Streamlit App Configuration
st.set_page_config(page_title="Patient Recruitment Simulation", layout="wide")

# Display logo using Streamlit's st.image()
st.image("backtgroundSimuTrial.png", width=150)

# Set background color to dark gray and reset input colors to default
st.markdown(
    """
    <style>
    .stApp {
        background-color: #333333;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Single button for EMR connection
data_file = st.file_uploader("Connect to EMR", type=["csv", "tsv"], label_visibility='collapsed')

if data_file is not None:
    df = pl.read_csv(data_file)
    df_normalized = normalize_columns(df, column_mapping)

    # Filtering based on inputs from Streamlit
    if st.checkbox("Target by Age Group"):
        df_normalized = df_normalized.filter(pl.col("age") > 18)  # Example filter
    
    if st.checkbox("Target by Gender"):
        df_normalized = df_normalized.filter(pl.col("gender") == "Female")  # Example filter
    
    if st.checkbox("Target by Ethnicity"):
        ethnicity_conditions = []
        if st.checkbox('African American'):
            ethnicity_conditions.append(pl.col("race_ethnicity") == "AfricanAmerican")
        if st.checkbox('Caucasian'):
            ethnicity_conditions.append(pl.col("race_ethnicity") == "Caucasian")
        if st.checkbox('Hispanic'):
            ethnicity_conditions.append(pl.col("race_ethnicity") == "Hispanic")
        if st.checkbox('Asian'):
            ethnicity_conditions.append(pl.col("race_ethnicity") == "Asian")
        
        # Apply combined ethnicity filter
        if ethnicity_conditions:
            df_normalized = df_normalized.filter(
                pl.any([cond for cond in ethnicity_conditions])
            )
    
    # Display filtered DataFrame
    st.write("Filtered Data Preview:", df_normalized.head().to_pandas())

    # Input elements for recruitment settings
    st.subheader("Recruitment Settings")

    # Sliders for consent rate
    consent_rate_min = st.slider("Consent Rate - Min", 0.0, 1.0, 0.2)
    consent_rate_max = st.slider("Consent Rate - Max", 0.0, 1.0, 0.8)

    # Number of simulations
    num_simulations = st.number_input("Number of Simulations", min_value=1, max_value=500, value=100)

    # Dropdown for disease area
    disease_area = st.selectbox(
        "Disease Area Focus",
        ["Cardiology", "Oncology", "Neurology", "Endocrinology", "Infectious Diseases", "Other"]
    )

    # Dropdown search for location
    location = st.selectbox("Enter Location (State)", ['Alabama','Alaska','American Samoa','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','District of Columbia','Florida','Georgia','Guam','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Marshall Islands','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Northern Mariana Islands','Ohio','Oklahoma','Oregon','Palau','Pennsylvania','Puerto Rico','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virgin Island','Virginia','Washington','West Virginia','Wisconsin','Wyoming'])

    # Number input for study size
    study_size = st.number_input("Study Size", min_value=1, max_value=10000, value=100)

    # Run Simulation button
    if st.button("Run Simulation"):
        # Initialize progress bar
        st.session_state.progress = st.progress(0)
        
        # Convert Polars DataFrame to Pandas for compatibility with Mesa
        df_normalized_pd = df_normalized.to_pandas()
        
        # Run the simulations
        simulation_results = run_simulations(df_normalized_pd, consent_rate_min, consent_rate_max, num_simulations)
        
        # Display results
        st.write(f"Mean Consent Rate: {simulation_results['mean_consent_rate']}%")
        st.write(f"Confidence Interval: +/- {simulation_results['confidence_interval']}")
        st.write(f"Average Staff Needed: {simulation_results['mean_staff']}")
        st.write(f"Average Sites Needed: {simulation_results['mean_sites']}")
        
        # Clear progress bar
        st.session_state.progress.empty()
