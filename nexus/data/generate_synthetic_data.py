import pandas as pd
import numpy as np
import datetime

def generate_synthetic_data(output_path='historical_process_data.csv'):
    """
    Generates 5 years of synthetic hourly data for an integrated biorefinery process.

    This function simulates a variety of process variables, operational scenarios,
    and market conditions to create a realistic dataset for developing and testing
    a digital twin.
    """
    # Define the time range: 5 years of hourly data
    total_hours = 365 * 24 * 5
    date_rng = pd.date_range(start='2020-01-01', periods=total_hours, freq='H')
    df = pd.DataFrame(date_rng, columns=['timestamp'])
    df.set_index('timestamp', inplace=True)

    # --- Simulate Operational Scenarios ---
    # 70% Normal, 20% Transient, 8% Abnormal, 2% Extreme
    df['operational_mode'] = 'Normal'
    transient_periods = int(0.20 * total_hours)
    abnormal_periods = int(0.08 * total_hours)
    extreme_periods = int(0.02 * total_hours)

    # Assign transient events (e.g., startup/shutdown)
    for _ in range(50): # 50 startup/shutdown cycles over 5 years
        start_idx = np.random.randint(0, total_hours - 200)
        df.iloc[start_idx:start_idx+100, df.columns.get_loc('operational_mode')] = 'Transient'

    # Assign abnormal events (e.g., equipment failure)
    for _ in range(100): # 100 random abnormal events
        start_idx = np.random.randint(0, total_hours - 50)
        df.iloc[start_idx:start_idx+24, df.columns.get_loc('operational_mode')] = 'Abnormal'

    # --- Feedstock Processing Unit ---
    # Biomass composition with seasonal variation
    df['feed_cellulose'] = 40 + 5 * np.sin(2 * np.pi * df.index.dayofyear / 365) + np.random.normal(0, 1, total_hours)
    df['feed_hemicellulose'] = 25 + 3 * np.sin(2 * np.pi * df.index.dayofyear / 365) + np.random.normal(0, 1, total_hours)
    df['feed_lignin'] = 20 + 2 * np.sin(2 * np.pi * df.index.dayofyear / 365) + np.random.normal(0, 0.5, total_hours)
    df['feed_flow_rate'] = 1000 + 50 * np.sin(2 * np.pi * df.index.dayofyear / 365) + np.random.normal(0, 20, total_hours)

    # --- Reaction Network (Fermentation) ---
    df['reactor_temp'] = 35.0 + np.random.normal(0, 0.2, total_hours)
    df['reactor_ph'] = 5.0 + np.random.normal(0, 0.05, total_hours)
    df['agitator_speed'] = 150 + np.random.normal(0, 5, total_hours)
    # Simulate a fault in the pH sensor
    fault_start = np.random.randint(0, total_hours - 500)
    df.loc[df.index[fault_start:fault_start+500], 'reactor_ph'] += 0.5
    df.loc[df.index[fault_start:fault_start+500], 'operational_mode'] = 'Abnormal'

    # --- Separation Complex (Distillation) ---
    df['distillation_temp'] = 102.0 + np.random.normal(0, 0.5, total_hours)
    df['distillation_pressure'] = 1.2 + np.random.normal(0, 0.02, total_hours)
    df['reflux_ratio'] = 2.5 + np.random.normal(0, 0.1, total_hours)

    # --- Utility Systems ---
    df['steam_pressure'] = 10.0 + np.random.normal(0, 0.1, total_hours)
    df['cooling_water_temp'] = 25.0 + 5 * np.sin(2 * np.pi * df.index.dayofyear / 365) + np.random.normal(0, 0.5, total_hours)

    # --- Product Portfolio ---
    # Product concentration depends on multiple factors
    base_concentration = 120 * (df['feed_cellulose'] / 40) * (df['reactor_temp'] / 35)
    df['product_bioethanol_concentration'] = base_concentration + np.random.normal(0, 2, total_hours)
    # Introduce a process drift over time (equipment aging)
    drift = np.linspace(0, -10, total_hours) # 10 g/L drop over 5 years
    df['product_bioethanol_concentration'] += drift

    # --- Market and Economic Data ---
    df['feedstock_price'] = 50 + 10 * np.sin(2 * np.pi * df.index.dayofyear / 365) + np.random.normal(0, 3, total_hours)
    df['bioethanol_price'] = 0.8 + 0.15 * np.sin(2 * np.pi * df.index.month / 12) + np.random.normal(0, 0.05, total_hours)

    # --- Save the data to a CSV file ---
    df.to_csv(output_path)
    print(f"Synthetic data generated and saved to {output_path}")
    print(f"Generated {len(df)} data points with {len(df.columns)} variables.")
    print("Operational mode distribution:")
    print(df['operational_mode'].value_counts(normalize=True))

if __name__ == "__main__":
    generate_synthetic_data()

