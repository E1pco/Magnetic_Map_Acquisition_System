import pandas as pd
from datetime import datetime, timedelta


ins_data = pd.read_csv('test_data/ins_data.csv')
mag_data = pd.read_csv('test_data/mag_data.csv')

ins_data['Timestamp'] = pd.to_datetime(ins_data['Timestamp']).apply(lambda x: x.timestamp())
mag_data['Timestamp'] = pd.to_datetime(mag_data['Timestamp']).apply(lambda x: x.timestamp())
ins_data['Base_Time'] = pd.to_datetime(ins_data['Base_Time']).apply(lambda x: x.timestamp())
mag_data['Base_Time'] = pd.to_datetime(mag_data['Base_Time']).apply(lambda x: x.timestamp())

results = []
for _, ins_row in ins_data.iterrows():
    ins_timestamp = ins_row['Timestamp']
    ins_base_time = ins_row['Base_Time']
    
    for _, mag_row in mag_data.iterrows():
        mag_timestamp = mag_row['Timestamp']
        mag_base_time = mag_row['Base_Time']
        if abs(ins_timestamp - mag_timestamp) < 0.003:
            base_time_diff = ins_base_time - mag_base_time
            base_time_diff = str(timedelta(seconds=base_time_diff))
            results.append((ins_timestamp, mag_timestamp, base_time_diff))

# Convert the results to a DataFrame
results_df = pd.DataFrame(results, columns=['INS_Timestamp', 'MAG_Timestamp', 'Base_Time_Diff'])

# Save the results to a new CSV file
results_df.to_csv('test_data/time_diffs.csv', index=False)

print('Time differences calculated and saved to test_data/time_diffs.csv')
