import pandas as pd
ins_data = pd.read_csv('test_data/ins_data_seconds.csv')
mag_data = pd.read_csv('test_data/mag_data_seconds.csv')

ins_data['Timestamp'] = pd.to_datetime(ins_data['Timestamp']).dt.strftime('%S.%f').astype(float)
mag_data['Timestamp'] = pd.to_datetime(mag_data['Timestamp']).dt.strftime('%S.%f').astype(float)

results = []
for _, ins_row in ins_data.iterrows():
    ins_timestamp = ins_row['Timestamp']
    ins_base_time = ins_row['Base_Time']
    for _, mag_row in mag_data.iterrows():
        mag_timestamp = mag_row['Timestamp']
        mag_base_time = mag_row['Base_Time']
        if abs(ins_timestamp - mag_timestamp) < 0.003:
            base_time_diff = ins_base_time - mag_base_time
            base_time_diff = round(base_time_diff, 3)
            
            results.append((ins_row['Base_Time'], mag_row['Base_Time'],ins_row['Timestamp'],mag_row['Timestamp'], base_time_diff))

results_df = pd.DataFrame(results, columns=['INS_Base_Time', 'MAG_Base_Time', 'INS_Timestamp', 'MAG_Timestamp', 'Base_Time_Diff'])
results_df.to_csv('test_data/modified_time_diffs_3.csv', index=False)

print('Modified time differences calculated and saved to test_data/modified_time_diffs.csv')
