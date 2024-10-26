import kagglehub

# Download latest version
path = kagglehub.dataset_download("priyamchoksi/100000-diabetes-clinical-dataset")

print("Path to dataset files:", path)