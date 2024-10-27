import streamlit as st
import pandas as pd

# Set the background color to #04668D
st.markdown(
    """
    <style>
    .stApp {
        background-color: #04668D;
    }
    .title {
        color: white;
        font-size: 50px;
        text-align: center;
    }
    .subtitle {
        color: white;
        font-size: 30px;
        text-align: center;
        margin-top: -20px;
    }
    .button {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .connect-button button {
        font-size: 20px;
        padding: 15px;
    }
    .logo {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Add a place for the logo
st.markdown('<div class="logo"><img src="https://via.placeholder.com/150" alt="Logo" width="150"></div>', unsafe_allow_html=True)

# Title and subtitle
st.markdown('<div class="title">Simu<span style="color: #00274D;">Trial</span></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Pre-Trial Simulations and Analysis</div>', unsafe_allow_html=True)

# File uploader for EMR connection
emr_connected = False

st.markdown('<div class="button connect-button">', unsafe_allow_html=True)
connect_emr = st.button("Connect to EMR")
st.markdown('</div>', unsafe_allow_html=True)

if connect_emr:
    data_file = st.file_uploader("Upload Data File", type=["csv", "tsv"])
    if data_file is not None:
        df = pd.read_csv(data_file)
        st.write("Data Preview:")
        st.write(df.head())
        emr_connected = True

# Move the recruitment settings outside the button press block
if emr_connected:
    # Input elements for recruitment settings
    st.subheader("Recruitment Settings")

    # Sliders for consent rate
    consent_rate_min = st.slider("Consent Rate - Min", 0.0, 1.0, 0.2)
    consent_rate_max = st.slider("Consent Rate - Max", 0.0, 1.0, 0.8)

    # Number of simulations
    num_simulations = st.number_input("Number of Simulations", min_value=1, max_value=100, value=10)

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
        st.write(f"Running simulation with study size: {study_size}, consent rate range: {consent_rate_min}-{consent_rate_max}, disease area: {disease_area}, location: {location}, targeting: {'Age' if age_group else ''} {'Gender' if gender else ''} {'Ethnicity' if ethnicity else ''}")
        # Placeholder for simulation code
