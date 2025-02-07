import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import savgol_filter, medfilt
from sklearn.metrics import r2_score
from scipy.interpolate import CubicSpline

def apply_savgol_filter(series, window_length=11, polyorder=3):
    if window_length % 2 == 0:
        window_length += 1
    series = series.fillna(method='ffill').fillna(method='bfill')
    filtered = savgol_filter(series.values, window_length, polyorder)
    return pd.Series(filtered, index=series.index)

def interpolate_angular_velocity(data, target_index):
    """对角速度数据进行插值处理，使用三次样条保持平滑性"""
    angular_cols = [col for col in data.columns if 'angular_velocity' in col.lower()]
    if not angular_cols:
        return data
    
    angular_data = data[angular_cols].copy()
    
    for col in angular_cols:
        mean_val = angular_data[col].mean()
        std_val = angular_data[col].std()
        mask = (angular_data[col] - mean_val).abs() <= 3 * std_val
        clean_data = angular_data[col][mask]
        
        if len(clean_data) < 2:
            angular_data[col] = angular_data[col].interpolate(method='linear')
            continue
        
        try:
            valid_data = clean_data.dropna()
            if len(valid_data) >= 4:
                t_valid = np.arange(len(valid_data))
                spline = CubicSpline(t_valid, valid_data.values, bc_type='natural')
                t_all = np.linspace(0, len(valid_data)-1, len(angular_data))
                interpolated = spline(t_all)
                interpolated = medfilt(interpolated, kernel_size=3)
                angular_data[col] = interpolated
            else:
                angular_data[col] = angular_data[col].interpolate(method='linear')
        except:
            angular_data[col] = angular_data[col].interpolate(method='linear')
    
    resampled = angular_data.reindex(target_index)
    resampled = resampled.interpolate(method='linear')
    
    return resampled

def dynamic_window_interpolation(data, window_size=5):
    """使用动态窗口进行数据插值，对角速度采用特殊处理"""
    if not data.index.is_monotonic_increasing:
        data = data.sort_index()
    
    start_time = data.index.min()
    end_time = data.index.max()
    target_index = pd.date_range(start=start_time, end=end_time, freq='10ms')
    
    angular_cols = [col for col in data.columns if 'angular_velocity' in col.lower()]
    other_cols = [col for col in data.columns if col not in angular_cols]
    
    if angular_cols:
        angular_data = interpolate_angular_velocity(data[angular_cols], target_index)
    else:
        angular_data = pd.DataFrame(index=target_index)
    
    other_data = pd.DataFrame(index=target_index)
    if other_cols:
        for col in other_cols:
            series = data[col]
            if pd.api.types.is_numeric_dtype(series):
                resampled = series.reindex(target_index)
                
                for i in range(len(resampled)):
                    if pd.isna(resampled.iloc[i]):
                        current_time = resampled.index[i]
                        window_data = series[
                            (series.index >= current_time - pd.Timedelta(milliseconds=10*window_size)) &
                            (series.index <= current_time + pd.Timedelta(milliseconds=10*window_size))
                        ]
                        
                        if not window_data.empty:
                            time_diff = abs((window_data.index - current_time).total_seconds())
                            weights = 1 / (time_diff + 1e-6)
                            resampled.iloc[i] = np.average(window_data, weights=weights)
                        else:
                            resampled.iloc[i] = np.nan
                
                resampled = resampled.interpolate(method='linear')
                other_data[col] = resampled
    
    result = pd.concat([angular_data, other_data], axis=1)
    
    for col in data.columns:
        if col not in result.columns:
            result[col] = np.nan
    
    return result[data.columns]

def format_with_precision(value, precision=8, pad_zeros=False):
    """确保数值保持指定的小数位数"""
    try:
        if pd.isna(value):
            return ''
        rounded = round(float(value), precision)
        format_str = '{:0.%df}' % precision if pad_zeros else '{:.%df}' % precision
        return format_str.format(rounded)
    except:
        return ''

def validate_columns(df, required_cols):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"缺少必需的列: {missing}")

def remove_trailing_nulls(df):
    last_valid_idx = -1
    for idx in range(len(df) - 1, -1, -1):
        if not df.iloc[idx].isna().all():
            last_valid_idx = idx
            break
    return df.iloc[:last_valid_idx + 1] if last_valid_idx >= 0 else df.iloc[0:0]

def synchronize_and_merge(ins_path, mag_path, output_path):
    ins_df = pd.read_csv(ins_path)
    mag_df = pd.read_csv(mag_path)
    ins_df.columns = ins_df.columns.str.lower()
    mag_df.columns = mag_df.columns.str.lower()
    
    for df in [ins_df, mag_df]:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(how='all', inplace=True)
    
    validate_columns(ins_df, ['acceleration x (g)', 'acceleration y (g)', 'acceleration z (g)'])
    validate_columns(mag_df, ['x', 'y', 'z'])
    
    start_time = max(ins_df.index.min().ceil('10ms'), mag_df.index.min().ceil('10ms'))
    end_time = min(ins_df.index.max().floor('10ms'), mag_df.index.max().floor('10ms'))
    overlap_duration = (end_time - start_time).total_seconds()
    if overlap_duration < 1.0:
        raise ValueError("传感器时间同步异常：有效重叠时段不足1秒")
    
    ins_numeric = ins_df.select_dtypes(include=[np.number])
    mag_numeric = mag_df.select_dtypes(include=[np.number])
    
    ins_resampled = dynamic_window_interpolation(ins_numeric)
    mag_resampled = mag_numeric.reindex(ins_resampled.index, method='nearest')
    
    merged = pd.concat([ins_resampled, mag_resampled], axis=1)
    merged = merged.loc[:, ~merged.columns.str.contains('base_time', case=False)]
    
    if 'longitude' in merged.columns and 'latitude' in merged.columns:
        for col in ['longitude', 'latitude']:
            merged[col] = pd.to_numeric(merged[col], errors='coerce').round(8)
    
    merged = remove_trailing_nulls(merged)
    merged.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    formatted_data = merged.reset_index()
    formatted_data.index = formatted_data['index'].apply(
        lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    )
    
    for col in formatted_data.columns:
        if col == 'index':
            continue
        col_lower = col.lower()
        if col_lower in ['longitude', 'latitude']:
            formatted_data[col] = formatted_data[col].apply(lambda x: format_with_precision(x, 8, pad_zeros=True))
        elif col_lower in ['x', 'y', 'z', 'magnitude', 'filtered magnitude']:
            formatted_data[col] = formatted_data[col].apply(lambda x: format_with_precision(x, 6))
        elif col_lower != 'timestamp':
            formatted_data[col] = formatted_data[col].apply(lambda x: format_with_precision(x, 4))
    
    formatted_data = formatted_data.rename(columns={'index': 'timestamp'})
    formatted_data.to_csv(output_path, index=False)
    print(f"数据处理完成，已保存到 {output_path}")

if __name__ == '__main__':
    ins_path = 'test_data/ins_data.csv'
    mag_path = 'test_data/mag_data.csv'
    output_path = 'merged_sensor_data.csv'
    synchronize_and_merge(ins_path, mag_path, output_path)
