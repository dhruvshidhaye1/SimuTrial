import streamlit as st
import pandas as pd
import polars as pl
import json
from mesa import Agent, Model
from mesa.time import RandomActivation
import random
import numpy

df = pd.read_csv('editedclinical copy.csv')

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
        # Consent based on model's consent rate range
        consent_probability = random.uniform(self.model.consent_rate_min, self.model.consent_rate_max)
        self.consented = random.random() < consent_probability

class RecruitmentModel(Model):
    def __init__(self, num_agents, consent_rate_min, consent_rate_max, targeted_demographics):
        self.num_agents = num_agents
        self.consent_rate_min = consent_rate_min
        self.consent_rate_max = consent_rate_max
        self.targeted_demographics = targeted_demographics
        self.schedule = RandomActivation(self)
        self.num_consented = 0

        # Create agents
        for i in range(self.num_agents):
            age = random.randint(18, 80)
            gender = random.choice(['Male', 'Female'])
            race = random.choice(['Caucasian', 'African American', 'Asian', 'Hispanic', 'Other'])
            region = random.choice(['North', 'South', 'East', 'West'])
            health_issues = random.choice(['Diabetes', 'Hypertension', 'None'])
            agent = PatientAgent(i, self, age, gender, race, region, health_issues)
            self.schedule.add(agent)

    def step(self):
        self.schedule.step()
        # Filter consented agents based on targeted demographics
        self.num_consented = sum(agent.consented for agent in self.schedule.agents if self.is_targeted(agent))

    def is_targeted(self, agent):
        # Check if agent matches targeted demographics
        if 'age' in self.targeted_demographics and not (18 <= agent.age <= 80):
            return False      
        if 'gender' in self.targeted_demographics and agent.gender not in self.targeted_demographics['gender']:
            return False
        if 'race' in self.targeted_demographics and agent.race not in self.targeted_demographics['race']:
            return False
        return True

st.title("Patient Recruitment Simulation")

# File uploader (optional)
data_file = st.file_uploader("Upload Data File", type=["csv", "tsv"])

# Use default data if no file is uploaded
if data_file is not None:
    df = pl.read_csv(data_file)
else:
    # Sample data for testing
    data = {
        "age": [32, 29, 18, 41, 52],
        "gender": ["Female", "Female", "Male", "Male", "Female"],
        "race": ["White", "Asian", "Black", "White", "Hispanic"],
        "region": ["North", "South", "East", "West", "North"],
        "health_issues": ["Diabetes", "None", "Hypertension", "None", "Diabetes"]
    }
    df = pl.DataFrame(data)
    
df_normalized = normalize_columns(df, column_mapping)
st.write("Data Preview:", df_normalized.head().to_pandas())

# Inputs for simulation
study_size = st.number_input("Study Size", min_value=1, max_value=10000, value=100)
consent_rate_min = st.slider("Consent Rate - Min", 0.0, 1.0, 0.2)
consent_rate_max = st.slider("Consent Rate - Max", 0.0, 1.0, 0.8)
num_simulations = st.number_input("Number of Simulations", min_value=1, max_value=100, value=10)

# Targeted Demographics
targeted_demographics = {}
if st.checkbox("Target by Age Group"):
    targeted_demographics['age'] = True
if st.checkbox("Target by Gender"):
    gender_options = st.multiselect("Select Genders", ["Male", "Female"])
    if gender_options:
        targeted_demographics['gender'] = gender_options
if st.checkbox("Target by Ethnicity"):
    ethnicity_options = st.multiselect("Select Ethnicities", ["African American", "Caucasian", "Hispanic", "Asian", "Other"])
    if ethnicity_options:
        targeted_demographics['race'] = ethnicity_options

if st.button("Run Simulation"):
    st.write(f"Running simulation with study size: {study_size}, consent rate range: {consent_rate_min}-{consent_rate_max}...")
    total_consented = 0

    for i in range(num_simulations):
        model = RecruitmentModel(num_agents=study_size, consent_rate_min=consent_rate_min, consent_rate_max=consent_rate_max, targeted_demographics=targeted_demographics)
        model.step()
        total_consented += model.num_consented
        st.write(f"Simulation {i + 1}: {model.num_consented} out of {study_size} agents consented.")

    avg_consented = total_consented / num_simulations
    st.write("Simulation completed.")
    st.write(f"Average number of consented agents per simulation: {avg_consented:.2f}")
