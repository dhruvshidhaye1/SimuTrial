Patient Recruitment Simulation App

This repository contains a Streamlit-based web application for simulating patient recruitment for clinical trials. The app leverages the Mesa framework to create artificial intelligence (AI) agents that simulate the willingness of patients to participate in clinical trials. It uses patient demographic and health data to predict their likelihood of consenting to participate in a study based on various factors such as region, health conditions, and other attributes. The primary goal is to help clinical trial managers estimate patient consent rates, as well as staffing and site requirements.

Features

Data Upload and Normalization:

The app allows users to connect to an Electronic Medical Record (EMR) system by uploading patient data in CSV or TSV formats.

The uploaded data is normalized using a JSON-based mapping to standardize column names and aggregate race/ethnicity information.

Targeted Patient Selection:

Users can filter the patient data based on age, gender, ethnicity, and other demographic information using Streamlit's interactive UI components.

Recruitment Simulation:

The app creates patient agents using the Mesa framework, simulating their willingness to participate in a study based on a defined consent rate range.

Users can specify recruitment settings such as consent rate range, disease area focus, location, and study size.

The simulation runs multiple trials to estimate mean consent rates, confidence intervals, and staff/site requirements for patient recruitment.

Progress Tracking and Visualization:

A progress bar is included to visually indicate the progress of simulations.

The app displays the results of the simulations, including consent rate statistics, staff requirements, and site recommendations.

Web Scraping for Staff and Site Requirements:

The app attempts to scrape staff and site requirement information from external sources if needed.

Usage

Running the App Locally

To run the app locally, you will need Python 3.7 or later and the following libraries:

Streamlit

Pandas

Polars

Mesa

Requests

BeautifulSoup

NumPy

To install all dependencies, run:

pip install -r requirements.txt

Once installed, you can start the Streamlit app by running:

streamlit run app.py

Using the App

Upload a CSV or TSV file containing patient data via the "Connect to EMR" button.

Use the filtering options to target specific patient demographics.

Configure the recruitment settings such as consent rate, study size, disease area, and location.

Click on "Run Simulation" to start the recruitment simulation.

Review the results, including the mean consent rate, confidence interval, average staff needed, and average sites required.

Scaling the App with AWS EC2 and S3

To scale the application for larger datasets and increased computational needs, the following approach can be used:

Deploying to EC2:

Deploy the Streamlit app on an Amazon EC2 instance. Choose an instance type suitable for the required processing power, such as a t3.medium or m5.large instance for moderate workloads.

Configure the EC2 instance to serve the app via a public IP address or domain name. You can use a load balancer to handle incoming requests if you expect a high volume of users.

Using S3 for Data Storage:

Store patient data and simulation results in an AWS S3 bucket to handle large datasets efficiently. Instead of uploading patient data through the Streamlit UI, users can specify an S3 bucket URL to load the data directly from S3.

This reduces the need to store large files locally on the EC2 instance and ensures data persistence.

Autoscaling and Monitoring:

Use AWS Auto Scaling to add more EC2 instances if there is a spike in user activity or if large datasets are being processed.

CloudWatch can be used to monitor the performance of the EC2 instances, keeping track of CPU utilization, memory usage, and other performance metrics.

S3 and EC2 Integration:

Use AWS Identity and Access Management (IAM) to create roles and policies for securely accessing S3 from EC2.

Mount the S3 bucket to the EC2 instance using S3FS-FUSE, which will make it easy to read and write data to S3 as if it were part of the local file system.

Future Improvements

Enhanced Model Complexity: Implement more sophisticated agent behaviors and decision-making to better simulate real-world scenarios.

Integration with Clinical Trial Management Systems: Integrate the simulation app with existing platforms like Medidata, Veeva, or Salesforce to streamline workflows.

User Authentication: Add authentication to ensure that only authorized users can access patient data and run simulations.

Batch Processing: Allow for batch simulations to be run asynchronously, using task queues like Celery or Amazon SQS.
