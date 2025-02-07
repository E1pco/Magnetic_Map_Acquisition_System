import pandas as pd
import matplotlib.pyplot as plt

# Load the modified time differences CSV file
modified_time_diffs = pd.read_csv('test_data/modified_time_diffs_3.csv')

# Plot the Base_Time_Diff
plt.figure(figsize=(10, 6))
plt.plot(modified_time_diffs['Base_Time_Diff'],  linestyle='-', color='b')
plt.title('Base Time Difference Plot')
plt.xlabel('Index')
plt.ylabel('Base Time Difference (s)')
plt.grid(True)
plt.savefig('test_data/base_time_diff_plot_3.png')
plt.show()

print('Plot saved as test_data/base_time_diff_plot.png')
