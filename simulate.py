import streamlit as st
import pandas as pd
import polars as pl
import json
from mesa import Agent, Model
from mesa.time import RandomActivation
import random

# Load JSON mapping
with open('column_mapping.json', 'r') as f:
    column_mapping = json.load(f)

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
        # Simple logic to decide if patient consents based on model parameters
        consent_probability = self.model.consent_rate
        self.consented = random.random() < consent_probability

class RecruitmentModel(Model):
    def __init__(self, num_agents, consent_rate):
        self.num_agents = num_agents
        self.consent_rate = consent_rate
        self.schedule = RandomActivation(self)

        # Create agents
        for i in range(self.num_agents):
            age = random.randint(18, 80)  # Example attribute assignment
            gender = random.choice(['Male', 'Female'])
            race = random.choice(['White', 'Black', 'Asian', 'Hispanic'])
            region = random.choice(['North', 'South', 'East', 'West'])
            health_issues = random.choice(['Diabetes', 'Hypertension', 'None'])
            agent = PatientAgent(i, self, age, gender, race, region, health_issues)
            self.schedule.add(agent)

    def step(self):
        self.schedule.step()

st.title("Patient Recruitment Simulation")

# File uploader
data_file = st.file_uploader("Upload Data File", type=["csv", "tsv"])

if data_file is not None:
    df = pl.read_csv(data_file)
    df_normalized = normalize_columns(df, column_mapping)
    st.write("Data Preview:", df_normalized.head().to_pandas())

    # Inputs for simulation
    study_size = st.number_input("Study Size", min_value=1, max_value=10000, value=100)
    consent_rate = st.slider("Consent Rate", 0.0, 1.0, 0.5)
    num_simulations = st.number_input("Number of Simulations", min_value=1, max_value=100, value=10)

    if st.button("Run Simulation"):
        st.write(f"Running simulation with {study_size} agents and consent rate of {consent_rate}...")
        model = RecruitmentModel(num_agents=study_size, consent_rate=consent_rate)
        for i in range(num_simulations):
            model.step()
        st.write("Simulation completed.")