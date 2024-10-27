import streamlit as st
import pandas as pd
import polars as pl
from mesa import Agent, Model
from mesa.time import RandomActivation
import random
import numpy as np
import requests
from patientVis import predict_willingness_scores  # Import the willingness score function

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
    for standard_name, possible_names in mapping.items():
        for col in possible_names:
            if col in df.columns:
                df = df.rename({col: standard_name})
                break

    race_cols = [col for col in df.columns if col.startswith("race:")]
    if race_cols:
        df = df.with_columns(
            pl.concat_list([df[col] for col in race_cols]).alias("race_ethnicity")
        )
        df = df.drop(race_cols)
    
    return df

class PatientAgent(Agent):
    def __init__(self, unique_id, model, age, gender, race, region, health_issues, willingness_score):
        super().__init__(unique_id, model)
        self.age = age
        self.gender = gender
        self.race = race
        self.region = region
        self.health_issues = health_issues
        self.willingness_score = willingness_score
        self.consented = False

    def step(self):
        self.consented = random.random() < self.willingness_score

class RecruitmentModel(Model):
    def __init__(self, df, consent_rate_min, consent_rate_max):
        self.df = df
        self.consent_rate_min = consent_rate_min
        self.consent_rate_max = consent_rate_max
        self.schedule = RandomActivation(self)

        for i, row in df.iterrows():
            age = row.get('age', None)
            gender = row.get('gender', None)
            race = row.get('race_ethnicity', None)
            region = row.get('region', None)
            health_issues = row.get('health_issues', None)
            willingness_score = row.get('WillingnessScore', None)
            
            agent = PatientAgent(i, self, age, gender, race, region, health_issues, willingness_score)
            self.schedule.add(agent)

    def step(self):
        self.schedule.step()

def run_simulations(df, consent_rate_min, consent_rate_max, num_simulations):
    consent_results = []
    staff_requirements = []
    site_recommendations = []

    for i in range(num_simulations):
        model = RecruitmentModel(df, consent_rate_min, consent_rate_max)
        for _ in range(1):
            model.step()
        consented_agents = sum([1 for agent in model.schedule.agents if agent.consented])
        consent_results.append(min(consented_agents, len(df)))

        staff_needed = max(1, int(consented_agents / 50))
        sites_needed = max(1, int(consented_agents / 100))
        staff_requirements.append(staff_needed)
        site_recommendations.append(sites_needed)

        st.session_state.progress.progress((i + 1) / num_simulations)
    
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

# Streamlit App Configuration
st.set_page_config(page_title="Patient Recruitment Simulation", layout="wide")
st.image("backtgroundSimuTrial.png", width=150)

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
    st.subheader("Recruitment Settings") 

    consent_rate_min = st.slider("Consent Rate - Min", 0.0, 1.0, 0.2)
    consent_rate_max = st.slider("Consent Rate - Max", 0.0, 1.0, 0.8)

    if st.checkbox("Target by Age Group"):
        st.write("Filtering by age group greater than 18...")
        df_normalized = df_normalized.filter(pl.col("age") > 18)  # Example filter
    
    if st.checkbox("Target by Gender"):
        if st.checkbox('Female'):
            df_normalized = df_normalized.filter(pl.col("gender") == "Female")  # Example filter
        if st.checkbox("Male"):
            df_normalized = df_normalized.filter(pl.col("gender") == "Male")  # Example filter
    
    if st.checkbox("Target by Ethnicity"):
        ethnicity_conditions = []

        if st.checkbox('African American'):
            ethnicity_conditions.append(pl.col("race_ethnicity") == 1)

        if st.checkbox('Caucasian'):
            ethnicity_conditions.append(pl.col("race_ethnicity") == 1)

        if st.checkbox('Hispanic'):
            ethnicity_conditions.append(pl.col("race_ethnicity") == 1)

        if st.checkbox('Asian'):
            ethnicity_conditions.append(pl.col("race_ethnicity") == 1)

        # Apply combined ethnicity filter only if there are conditions selected
        if ethnicity_conditions:
            df_normalized = df_normalized.filter(pl.any(ethnicity_conditions))

    # Display filtered DataFrame
    st.write("Filtered Data Preview:", df_normalized.head().to_pandas())

    num_simulations = st.number_input("Number of Simulations", min_value=1, max_value=500, value=100)

    training_data = pd.read_csv('editedclinicaltrial_copy.csv')
    X_train = training_data[['Age', 'CENSREG', 'BirthGender', 'RaceEthn']]
    y_train = training_data['ParticipatedClinTrial']

    # Predict willingness scores for patients
    csv_path = data_file.name  # Use the uploaded file as input
    results_df = predict_willingness_scores(csv_path, X_train, y_train)

    df_normalized_pd = df_normalized.to_pandas()
    df_normalized_pd['WillingnessScore'] = results_df['WillingnessScore']

    if st.button("Run Simulation"):
        st.session_state.progress = st.progress(0)

        simulation_results = run_simulations(df_normalized_pd, consent_rate_min, consent_rate_max, num_simulations)
        
        st.write(f"Mean Consent Rate: {simulation_results['mean_consent_rate']}%")
        st.write(f"Confidence Interval: +/- {simulation_results['confidence_interval']}")
        st.write(f"Average Staff Needed: {simulation_results['mean_staff']}")
        st.write(f"Average Sites Needed: {simulation_results['mean_sites']}")

        st.subheader("Calculated Willingness Scores")
        st.dataframe(results_df[['Age', 'CENSREG', 'BirthGender', 'RaceEthn', 'WillingnessScore']], height=500)  # Show top 10 entries for brevity

        mean_will = (results_df["WillingnessScore"].sum())/len(results_df)

        mean_will_perc = mean_will * 100

        st.write(f"Mean Willingness Score Across Agents: {mean_will_perc}%")
        
        st.session_state.progress.empty()
