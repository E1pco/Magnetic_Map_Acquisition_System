import pandas as pd

# Read the CSV file
csv_path = 'test_data/modified_time_diffs_3.csv'
df = pd.read_csv(csv_path)

# Get the last column and calculate the sum
last_column = df.iloc[:, -1]
total_sum = last_column.sum()

print(f"Sum of values in the last column: {total_sum}")
