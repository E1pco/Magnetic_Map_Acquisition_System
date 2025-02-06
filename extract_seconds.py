import pandas as pd

# Load the CSV files into dataframes
ins_data = pd.read_csv('test_data/ins_data.csv')
mag_data = pd.read_csv('test_data/mag_data.csv')

# Extract the full seconds part of Base_Time including fractional seconds
ins_data['Base_Time'] = pd.to_datetime(ins_data['Base_Time']).dt.strftime('%S.%f').astype(float)
mag_data['Base_Time'] = pd.to_datetime(mag_data['Base_Time']).dt.strftime('%S.%f').astype(float)

# Save the modified dataframes back to CSV
ins_data.to_csv('test_data/ins_data_seconds.csv', index=False)
mag_data.to_csv('test_data/mag_data_seconds.csv', index=False)

print('Base_Time seconds extracted and saved to new CSV files.')
