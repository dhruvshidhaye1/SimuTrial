import pandas as pd
import matplotlib.pyplot as plt


# Load the data from the CSV file
data = pd.read_csv("editedclinicaltrial copy.csv")


# Display the first few rows of the dataframe to understand its structure
print(data.head())


# Define the participation column (consent)
consent_col = 'ParticipatedClinTrial'  # Adjust based on your column name


# List of demographic columns to analyze
demographics = ['BirthGender', 'Occupation_Employed', 'Occupation_1YUnemployed',
               'Occupation_Less1YUnemployed', 'Occupation_Student', 'Occupation_Retired',
               'Occupation_Disabled', 'MaritalStatus', 'IncomeRanges', 'RaceEthn']


# Exclude rows where any of the demographic columns contain -9
filtered_data = data[~data[demographics].isin([-9]).any(axis=1)]


# Create bar plots for each demographic variable
plt.figure(figsize=(20, 15))


for i, demographic in enumerate(demographics):
   plt.subplot(4, 3, i + 1)


   # Calculate participation rate by demographic category
   participation_rate = filtered_data.groupby(demographic)[consent_col].mean().reset_index()


   # Bar plot
   plt.bar(participation_rate[demographic].astype(str), participation_rate[consent_col], alpha=0.7)
  
   # Set the title and labels
   plt.title(f'Participation Rate by {demographic}')
   plt.xlabel(demographic)
   plt.ylabel('Participation Rate (0 = No, 1 = Yes)')
   plt.xticks(rotation=45)


plt.tight_layout()
plt.show()

