import pandas as pd

# Load the modified CSV files into dataframes
ins_data = pd.read_csv('test_data/ins_data_seconds.csv')
mag_data = pd.read_csv('test_data/mag_data_seconds.csv')

# Extract seconds and milliseconds from Timestamp
ins_data['Timestamp'] = pd.to_datetime(ins_data['Timestamp']).dt.strftime('%S.%f').astype(float)
mag_data['Timestamp'] = pd.to_datetime(mag_data['Timestamp']).dt.strftime('%S.%f').astype(float)

# Initialize a list to store the results
results = []

# Iterate over each row in ins_data
for _, ins_row in ins_data.iterrows():
    ins_timestamp = ins_row['Timestamp']
    ins_base_time = ins_row['Base_Time']
    
    # Find matching timestamps in mag_data
    for _, mag_row in mag_data.iterrows():
        mag_timestamp = mag_row['Timestamp']
        mag_base_time = mag_row['Base_Time']
        
        # Check if the timestamps are within 3ms
        if abs(ins_timestamp - mag_timestamp) < 0.005:
            # Calculate the difference in Base_Time
            base_time_diff = ins_base_time - mag_base_time
            
            # Round the Base_Time_Diff to three decimal places
            base_time_diff = round(base_time_diff, 3)
            
            # Append the result as a tuple (ins_timestamp, mag_timestamp, base_time_diff)
            results.append((ins_row['Base_Time'], mag_row['Base_Time'],ins_row['Timestamp'],mag_row['Timestamp'], base_time_diff))

# Convert the results to a DataFrame
results_df = pd.DataFrame(results, columns=['INS_Base_Time', 'MAG_Base_Time', 'INS_Timestamp', 'MAG_Timestamp', 'Base_Time_Diff'])

# Save the results to a new CSV file
results_df.to_csv('test_data/modified_time_diffs.csv', index=False)

print('Modified time differences calculated and saved to test_data/modified_time_diffs.csv')
