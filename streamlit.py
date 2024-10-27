import streamlit as st
import pandas as pd
import polars as pl
import json
from mesa import Agent, Model
from mesa.time import RandomActivation
import random
import numpy as np
import time

# Load JSON mapping
column_mapping = {
  "age": ["Age", "age", "dob"],
  "gender": ["Gender", "sex", "Sex"],
  "race_ethnicity": ["Race", "Ethnicity", "race_ethnicity", "race", "race:AfricanAmerican", "race:Asian", "race:Caucasian", "race:Hispanic", "race:Other"],
  "region": ["Location", "region", "Region"],
  "health_issues": ["Conditions", "health_conditions", "Issues", "hypertension", "heart_disease"]
}

# Function to normalize columns
def normalize_columns(df, mapping):
    for standard_name, possible_names in mapping.items():
        for col in possible_names:
            if col in df.columns:
                df = df.rename({col: standard_name})
                break
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
    for i in range(num_simulations):
        model = RecruitmentModel(df, consent_rate_min, consent_rate_max)
        for _ in range(1):  # Run for 1 step (as we only need to determine consent)
            model.step()
        consented_agents = sum([1 for agent in model.schedule.agents if agent.consented])
        consent_results.append(consented_agents)
        
        # Update progress bar
        st.session_state.progress.progress((i + 1) / num_simulations)
    
    # Calculate statistics
    mean_consent = np.mean(consent_results)
    confidence_interval = np.std(consent_results) * 1.96 / np.sqrt(num_simulations)
    
    return {
        "mean_consent": mean_consent,
        "confidence_interval": confidence_interval,
        "consent_results": consent_results
    }

# Streamlit App Configuration
st.set_page_config(page_title="Patient Recruitment Simulation", layout="wide")

# Add a place for the logo
st.image("backtgroundSimuTrial.png", use_column_width=True)

# File uploader for EMR connection
data_file = st.file_uploader("Upload Data File", type=["csv", "tsv"])

if data_file is not None:
    df = pl.read_csv(data_file)
    df_normalized = normalize_columns(df, column_mapping)
    st.write("Data Preview:", df_normalized.head().to_pandas())

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

    # Demographic targeting checkboxes
    st.subheader("Demographic Targeting")
    age_group = st.checkbox("Target by Age Group")
    gender = st.checkbox("Target by Gender")
    ethnicity = st.checkbox("Target by Ethnicity")
    if ethnicity:
        st.text('Select Targeted Demographics')
        include_african = st.checkbox('African American')
        include_caucasian = st.checkbox('Caucasian')
        include_hispanic = st.checkbox('Hispanic')
        include_asian = st.checkbox('Asian')
        include_other = st.checkbox('Other')

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
        st.write(f"Mean Consent: {simulation_results['mean_consent']}")
        st.write(f"Confidence Interval: +/- {simulation_results['confidence_interval']}")
        
        # Clear progress bar
        st.session_state.progress.empty()
