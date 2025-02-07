import pandas as pd
import numpy as np
from scipy import interpolate
from datetime import datetime
from scipy.signal import savgol_filter

class SensorDataSynchronizer:
    def __init__(self, window_size=100, max_time_diff_ms=3):
        self.window_size = window_size
        self.max_time_diff_ms = max_time_diff_ms
        
    def load_data(self, mag_file, ins_file):

        self.mag_data = pd.read_csv(mag_file)
        self.ins_data = pd.read_csv(ins_file)
        
        # Convert timestamps to datetime and get seconds since start
        for df in [self.mag_data, self.ins_data]:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df['seconds'] = (df['Timestamp'] - df['Timestamp'].min()).dt.total_seconds()
    
    def detect_time_drift(self, data, window_size=50):
        
        timestamps = pd.to_datetime(data['Timestamp'])
        time_diffs = timestamps.diff().dt.total_seconds()
        rolling_mean = time_diffs.rolling(window=window_size).mean()
        rolling_std = time_diffs.rolling(window=window_size).std()
        drift_points = np.where(np.abs(time_diffs - rolling_mean) > 3 * rolling_std)[0]
        
        return drift_points, rolling_mean, rolling_std
    
    def interpolate_sensor_data(self, data, time_points):
        """Interpolate sensor data to specified time points"""
        interpolated_data = {}
        
        # Get numeric columns for interpolation
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col != 'seconds':  # Skip the time column
                # Create interpolation function
                f = interpolate.interp1d(data['seconds'], data[col],
                                       kind='cubic', bounds_error=False,
                                       fill_value='extrapolate')
                
                # Interpolate data
                interpolated_data[col] = f(time_points)
        
        return pd.DataFrame(interpolated_data)
    
    def calculate_quality_metrics(self, window_data):
        """Calculate data quality metrics for a window of data"""
        metrics = {
            'variance': np.var(window_data),
            'missing_data': np.sum(np.isnan(window_data)),
            'signal_noise_ratio': np.mean(window_data) / np.std(window_data) if np.std(window_data) != 0 else 0
        }
        return metrics
    
    def sync_with_sliding_window(self):
        """Synchronize data using sliding window approach"""
        synchronized_data = []
        start_time = max(self.mag_data['seconds'].min(), self.ins_data['seconds'].min())
        end_time = min(self.mag_data['seconds'].max(), self.ins_data['seconds'].max())
        
        time_points = np.arange(start_time, end_time, 0.01)
        mag_interp = self.interpolate_sensor_data(self.mag_data, time_points)
        ins_interp = self.interpolate_sensor_data(self.ins_data, time_points)
        mag_drift, mag_roll_mean, mag_roll_std = self.detect_time_drift(self.mag_data)
        ins_drift, ins_roll_mean, ins_roll_std = self.detect_time_drift(self.ins_data)
        for i in range(0, len(time_points) - self.window_size, self.window_size // 2):
            window_slice = slice(i, i + self.window_size)
            mag_window = mag_interp.iloc[window_slice]
            ins_window = ins_interp.iloc[window_slice]
            mag_quality = self.calculate_quality_metrics(mag_window['Magnitude'])
            ins_quality = self.calculate_quality_metrics(ins_window['Acceleration X (g)'])
            for j in range(len(mag_window)):
                combined_data = {
                    'Timestamp': pd.Timestamp(self.mag_data['Timestamp'].min()) + 
                                pd.Timedelta(seconds=time_points[i + j]),
                    'Time_Point': time_points[i + j],
                    'Mag_X': mag_window['X'].iloc[j],
                    'Mag_Y': mag_window['Y'].iloc[j],
                    'Mag_Z': mag_window['Z'].iloc[j],
                    'Mag_Magnitude': mag_window['Magnitude'].iloc[j],
                    'Mag_Filtered_Magnitude': savgol_filter(mag_window['Magnitude'], 
                                                          window_length=min(11, len(mag_window)), 
                                                          polyorder=3)[j],
                    'INS_Accel_X': ins_window['Acceleration X (g)'].iloc[j],
                    'INS_Accel_Y': ins_window['Acceleration Y (g)'].iloc[j],
                    'INS_Accel_Z': ins_window['Acceleration Z (g)'].iloc[j],
                    'INS_Gyro_X': ins_window['Angular_velocity_X (dps)'].iloc[j],
                    'INS_Gyro_Y': ins_window['Angular_velocity_Y (dps)'].iloc[j],
                    'INS_Gyro_Z': ins_window['Angular_velocity_Z (dps)'].iloc[j],
                    'INS_Temperature': ins_window['Temperature (°C)'].iloc[j],
                    'INS_Longitude': ins_window['Longitude'].iloc[j],
                    'INS_Latitude': ins_window['Latitude'].iloc[j],
                    'Mag_Quality_Score': mag_quality['signal_noise_ratio'],
                    'INS_Quality_Score': ins_quality['signal_noise_ratio'],
                    'Window_Index': i // (self.window_size // 2)
                }
                synchronized_data.append(combined_data)
        
        return pd.DataFrame(synchronized_data)

def main():
    synchronizer = SensorDataSynchronizer(window_size=100, max_time_diff_ms=3)
    synchronizer.load_data('test_data/mag_data.csv', 'test_data/ins_data.csv')

    synced_data = synchronizer.sync_with_sliding_window()
    output_file = 'test_data/synchronized_data.csv'
    synced_data.to_csv(output_file, index=False)
    
    print(f"synchronized data saved to {output_file}")
    print(f"Total synchronized points: {len(synced_data)}")
    print("\nData quality statistics:")
    print(f"Magnetic data quality (mean): {synced_data['Mag_Quality_Score'].mean():.2f}")
    print(f"INS data quality (mean): {synced_data['INS_Quality_Score'].mean():.2f}")

if __name__ == "__main__":
    main()
