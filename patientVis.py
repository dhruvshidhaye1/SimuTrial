import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Define the mapping for CENSREG (region)
state_to_censreg = {
    'Northeast': ['Connecticut', 'Maine', 'Massachusetts', 'New Hampshire', 'New Jersey', 'New York', 'Pennsylvania', 'Rhode Island', 'Vermont'],
    'Midwest': ['Illinois', 'Indiana', 'Iowa', 'Kansas', 'Michigan', 'Minnesota', 'Missouri', 'Nebraska', 'North Dakota', 'Ohio', 'South Dakota', 'Wisconsin'],
    'South': ['Alabama', 'Arkansas', 'Delaware', 'District of Columbia', 'Florida', 'Georgia', 'Kentucky', 'Louisiana', 'Maryland', 'Mississippi', 'North Carolina', 'Oklahoma', 'South Carolina', 'Tennessee', 'Texas', 'Virginia', 'West Virginia'],
    'West': ['Alaska', 'Arizona', 'California', 'Colorado', 'Hawaii', 'Idaho', 'Montana', 'Nevada', 'New Mexico', 'Oregon', 'Utah', 'Washington', 'Wyoming']
}

# Define the mapping for race
race_mapping = {
    'Hispanic': 1,
    'Caucasian': 2,
    'AfricanAmerican': 3,
    'Asian': 4,
    'Other': -9
}

# Assumption rates for willingness based on race
assumption_rates = {
    1: 0.123,  # Hispanic
    2: 0.440,  # Caucasian
    3: 0.164,  # African American
    4: 0.231,  # Asian
    -9: 0.0    # Other, assume least likely to participate
}

# Function to determine CENSREG based on location
def map_location_to_censreg(location):
    for region, states in state_to_censreg.items():
        if location in states:
            return {
                'Northeast': 1,
                'Midwest': 2,
                'South': 3,
                'West': 4
            }[region]
    return None  # Unknown region

# Function to preprocess patient data and predict willingness scores
def predict_willingness_scores(csv_path, X_train, y_train):
    # Load the patient data
    patient_data = pd.read_csv(csv_path)
    
    # Preprocess the patient data
    patient_data['CENSREG'] = patient_data['location'].apply(map_location_to_censreg)
    
    # Extract race/ethnicity information
    patient_data['RaceEthn'] = patient_data[[col for col in patient_data.columns if 'race:' in col]].apply(
        lambda x: [race_mapping[col.split(':')[1]] for col in x.index if x[col] == 1], axis=1
    ).apply(lambda x: x[0] if x else -9)  # Default to -9 if no races are found
    
    patient_data['BirthGender'] = patient_data['gender'].apply(lambda x: 1 if x == 'Male' else 0)  # Mapping gender
    patient_data['Age'] = patient_data['age']

    # Filter columns to match model input
    model_input = patient_data[['Age', 'CENSREG', 'BirthGender', 'RaceEthn']]
    
    # Check for missing values and drop rows with NaN values
    model_input = model_input.dropna()

    # Scale the features
    scaler = StandardScaler()
    model_input_scaled = scaler.fit_transform(model_input)

    # Initialize and fit the Logistic Regression model
    model = LogisticRegression(max_iter=1000)  # Increase max_iter to avoid convergence issues
    model.fit(X_train, y_train)  # Use the passed training data to fit the model

    # Make predictions using the trained model
    willingness_scores = model.predict_proba(model_input_scaled)[:, 1]

    # Adjust willingness scores based on race and age assumptions
    for model_idx, orig_idx in enumerate(model_input.index):
        race = patient_data.loc[orig_idx, 'RaceEthn']
        willingness_scores[model_idx] *= assumption_rates[race] * 1.5  # Increase the impact of the race assumption

        # Boost score for younger participants
        if patient_data.loc[orig_idx, 'Age'] < 30:
            age_boost = 1 + (30 - patient_data.loc[orig_idx, 'Age']) / 100 * 2  # Increase the boost effect
            willingness_scores[model_idx] *= age_boost

    # Add a constant boost or apply a scaling factor
    willingness_scores += 0.01  # Add a constant boost
    # willingness_scores *= 1.5  # Or use a scaling factor instead

    # Scale the scores to be within [0, 0.5]
    scaling_factor = 0.5 / willingness_scores.max() if willingness_scores.max() > 0 else 1
    willingness_scores *= scaling_factor

    # Clip scores to ensure they are within the specified range
    willingness_scores = np.clip(willingness_scores, 0.0, 0.5)

    # Add predictions to the DataFrame
    patient_data['WillingnessScore'] = np.nan  # Initialize the column
    patient_data.loc[model_input.index, 'WillingnessScore'] = willingness_scores  # Assign scores only where predictions were made

    # Plot the distribution of willingness scores
    plt.figure(figsize=(10, 6))
    sns.histplot(willingness_scores, bins=30, kde=True)
    plt.axvline(x=0.5, color='red', linestyle='--', label='Threshold (0.5)')
    plt.title('Distribution of Willingness Scores')
    plt.xlabel('Willingness Score')
    plt.ylabel('Frequency')
    plt.legend()
    plt.show()

    return patient_data[['Age', 'CENSREG', 'BirthGender', 'RaceEthn', 'WillingnessScore']]

# Example usage
training_data = pd.read_csv('editedclinicaltrial_copy.csv')  # Replace with your actual training data path
X_train = training_data[['Age', 'CENSREG', 'BirthGender', 'RaceEthn']]  # Features
y_train = training_data['ParticipatedClinTrial']  # Target variable

csv_path = 'diabetes_dataset.csv'  # Path to your patient data CSV
results_df = predict_willingness_scores(csv_path, X_train, y_train)

print(results_df)
results_df.to_csv('patient_willingness_scores.csv', index=False)  # Save to CSV if needed
