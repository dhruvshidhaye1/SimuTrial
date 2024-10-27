import requests
import pandas as pd
import tkinter as tk
from tkinter import ttk
import webbrowser

# Define the base URL for the studies endpoint
base_url = "https://clinicaltrials.gov/api/v2/studies"

# Set up query parameters for CSV
params = {
    "format": "csv",  # Request format as CSV
    "query.cond": "diabetes",  # Condition to filter studies
    "filter.overallStatus": "COMPLETED",  # Status filter
    "pageSize": 100,  # Adjust the number of studies per page as needed
    "countTotal": "true"  # Include total count in response
}

# Make the GET request
response = requests.get(base_url, params=params)

# Check response
if response.status_code == 200:
    # Save the response content to a CSV file
    with open('clinical_trials.csv', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    # Read the saved CSV file into a DataFrame
    df = pd.read_csv('clinical_trials.csv')

    # Filter out studies without patient information in "Study Documents"
    filtered_df = df[df['Study Documents'].notna()]

    # Create a popup window to display the filtered DataFrame
    root = tk.Tk()
    root.title("Clinical Trials with Patient Information")

    # Create a Treeview to display the DataFrame
    tree = ttk.Treeview(root)
    tree.pack(expand=True, fill='both')

    # Define columns
    tree["columns"] = list(filtered_df.columns)
    tree["show"] = "headings"

    # Create a scrollbar for vertical scrolling
    scrollbar_y = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar_y.set)
    scrollbar_y.pack(side='right', fill='y')

    # Create a scrollbar for horizontal scrolling
    scrollbar_x = ttk.Scrollbar(root, orient="horizontal", command=tree.xview)
    tree.configure(xscroll=scrollbar_x.set)
    scrollbar_x.pack(side='bottom', fill='x')

    # Set column widths and headings
    for col in filtered_df.columns:
        tree.heading(col, text=col)  # Set the column headings
        tree.column(col, anchor="center", width=150)  # Center the column content and set fixed width

    # Insert rows into the treeview
    for index, row in filtered_df.iterrows():
        # Prepare row data, making the Study URL clickable
        row_data = list(row)
        if 'Study URL' in filtered_df.columns:  # Check if the Study URL column exists
            row_data[filtered_df.columns.get_loc('Study URL')] = f"{row['Study URL']}"  # Convert URL to string
        tree.insert("", "end", values=row_data)

    # Function to open URL in a web browser when a cell is double-clicked
    def open_url(event):
        item = tree.selection()
        if item:
            selected_item = tree.item(item)
            url = selected_item['values'][filtered_df.columns.get_loc('Study URL')]
            if url:
                webbrowser.open(url)  # Open URL in the default web browser

    # Bind double-click event to the Treeview
    tree.bind("<Double-1>", open_url)

    # Start the GUI event loop
    root.mainloop()
else:
    print(f"Error: {response.status_code} - {response.text}")
