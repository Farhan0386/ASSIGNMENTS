import pandas as pd
import numpy as np
import os

print("--- 1. DataFrames Creation ---")
data = {
    'ID': [101, 102, 103, 104, 105, 106],
    'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank'],
    'Department': ['HR', 'IT', 'IT', 'Finance', 'HR', 'Finance'],
    'Salary': [50000, 70000, np.nan, 65000, 52000, np.nan],
    'Age': [25, np.nan, 30, 35, 28, 40]
}
df = pd.DataFrame(data)
print("Initial DataFrame:")
print(df)
print("\nDataFrame Info:")
print(df.info())

print("\n--- 2. Cleaning Missing Values ---")
print("Missing values count per column:")
print(df.isnull().sum())

# Fill missing values
df_cleaned = df.copy()
df_cleaned['Salary'] = df_cleaned['Salary'].fillna(df_cleaned['Salary'].mean())
df_cleaned['Age'] = df_cleaned['Age'].fillna(df_cleaned['Age'].median())
print("\nDataFrame after filling missing values:")
print(df_cleaned)

print("\n--- 3. Filtering ---")
# Filter employees in IT department or salary > 60000
filtered_df = df_cleaned[(df_cleaned['Department'] == 'IT') | (df_cleaned['Salary'] > 60000)]
print("Filtered DataFrame (Department == IT or Salary > 60000):")
print(filtered_df)

print("\n--- 4. Groupby ---")
# Group by Department and calculate average Salary and Age
grouped_df = df_cleaned.groupby('Department')[['Salary', 'Age']].mean().reset_index()
print("Grouped by Department (Mean Salary & Age):")
print(grouped_df)

print("\n--- 5. Merge ---")
# Create another DataFrame for Department details
dept_info = pd.DataFrame({
    'Department': ['HR', 'IT', 'Finance', 'Marketing'],
    'Location': ['Building A', 'Building B', 'Building C', 'Building D'],
    'Manager': ['Sarah', 'Mike', 'Karen', 'John']
})
merged_df = pd.merge(df_cleaned, dept_info, on='Department', how='inner')
print("Merged DataFrame with Department Details:")
print(merged_df)

print("\n--- 6. Reading and Writing CSV ---")
csv_file = "sample_data.csv"
output_file = "output_cleaned_data.csv"

# Write DataFrame to CSV
merged_df.to_csv(csv_file, index=False)
print(f"Data saved to {csv_file}")

# Read DataFrame back from CSV
df_from_csv = pd.read_csv(csv_file)
print("Data read back from CSV:")
print(df_from_csv)

# Clean up created files if needed, or keep for demonstration
if os.path.exists(csv_file):
    os.remove(csv_file)
    print(f"Cleaned up {csv_file}")

print("\nPandas code executed successfully!")
