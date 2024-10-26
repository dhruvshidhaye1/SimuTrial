import polars as pl
import json

# Load JSON mapping
with open('column_mapping.json', 'r') as f:
    column_mapping = json.load(f)

# Load your dataset
df = pl.read_csv('diabetes_dataset.csv')

# Function to rename columns based on mapping
def normalize_columns(df, mapping):
    for standard_name, possible_names in mapping.items():
        for col in possible_names:
            if col in df.columns:
                df = df.rename({col: standard_name})
                break
    return df

# Apply the normalization
df_normalized = normalize_columns(df, column_mapping)

# Display normalized DataFrame
print(df_normalized)