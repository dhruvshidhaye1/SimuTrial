import streamlit as st
import pandas as pd
import polars as pl
import json
from mesa import Agent, Model
from mesa.time import RandomActivation
import random
import numpy as np

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
    for _ in range(num_simulations):
        model = RecruitmentModel(df, consent_rate_min, consent_rate_max)
        for _ in range(1):  # Run for 1 step (as we only need to determine consent)
            model.step()
        consented_agents = sum([1 for agent in model.schedule.agents if agent.consented])
        consent_results.append(consented_agents)
    
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

st.title("Patient Recruitment Simulation")

# File uploader
data_file = st.file_uploader("Upload Data File", type=["csv", "tsv"])

if data_file is not None:
    df = pl.read_csv(data_file)
    df_normalized = normalize_columns(df, column_mapping)
    st.write("Data Preview:", df_normalized.head().to_pandas())

    # Inputs for simulation
    consent_rate_min = st.slider("Consent Rate Minimum", 0.0, 1.0, 0.4)
    consent_rate_max = st.slider("Consent Rate Maximum", 0.0, 1.0, 0.7)
    num_simulations = st.number_input("Number of Simulations", min_value=1, max_value=500, value=100)

    if st.button("Run Simulation"):
        # Convert Polars DataFrame to Pandas for compatibility with Mesa
        df_normalized_pd = df_normalized.to_pandas()
        
        # Run the simulations
        simulation_results = run_simulations(df_normalized_pd, consent_rate_min, consent_rate_max, num_simulations)
        
        # Display results
        st.write(f"Mean Consent: {simulation_results['mean_consent']}")
        st.write(f"Confidence Interval: +/- {simulation_results['confidence_interval']}")