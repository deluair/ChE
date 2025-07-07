import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from nexus.digital_twin.rt_interface.data_interface import CSVDataReader
from nexus.digital_twin.adaptation.model_adaptation import ParameterEstimator
from nexus.nexus_core.models.unit_operations import CSTR
from nexus.nexus_core.properties.property_models import PropertyPackage, Component
from nexus.nexus_core.kinetics.kinetics import PowerLawReaction

def run_and_visualize_adaptation(timestamp_str, data_path):
    """Runs the full adaptation and validation cycle and plots the results."""
    # --- 1. Setup --- 
    reader = CSVDataReader(file_path=data_path)
    if reader.data.empty:
        return

    water = Component('Water', 'H2O')
    ethanol = Component('Ethanol', 'C2H6O')
    prop_pkg = PropertyPackage(components=[water, ethanol])
    stoich = {'Ethanol': -1, 'Product': 1}
    initial_A = 0.005
    def arrhenius_k_initial(T): return initial_A * np.exp(5000 * (1/310 - 1/T))
    reactants = {'Ethanol': 1}
    reaction = PowerLawReaction('Ethanol_Conversion', stoich, arrhenius_k_initial, reactants)
    reactor = CSTR(name='R-101', volume=50, prop_pkg=prop_pkg, reaction=reaction)

    target_map = {'model': 'Product', 'data': 'product_bioethanol_concentration'}
    estimator = ParameterEstimator(model=reactor, data_reader=reader, target_variable_map=target_map)

    # --- 2. Tune the model --- 
    tune_time = pd.Timestamp(timestamp_str)
    tuned_A = estimator.tune_parameter(tune_time, 'arrhenius_A', initial_A)
    if tuned_A is None:
        print("Could not generate plot as tuning failed.")
        return

    # --- 3. Get results before and after tuning ---
    # Before tuning
    actual_data = reader.get_data_at_timestamp(tune_time)
    reactor.reaction.rate_constant_func = arrhenius_k_initial
    estimator._objective_function([initial_A], 'arrhenius_A', tune_time) # Reruns model
    pred_before = reactor.outlets[0]['composition']['Product']

    # After tuning
    def arrhenius_k_tuned(T): return tuned_A * np.exp(5000 * (1/310 - 1/T))
    reactor.reaction.rate_constant_func = arrhenius_k_tuned
    estimator._objective_function([tuned_A], 'arrhenius_A', tune_time) # Reruns model
    pred_after = reactor.outlets[0]['composition']['Product']

    actual_value = actual_data[target_map['data']] / 1000

    # --- 4. Plotting --- 
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    time_range = pd.date_range(end=tune_time, periods=24*7, freq='H')
    ax.plot(reader.data.loc[time_range, target_map['data']] / 1000, label='Historical Data', alpha=0.7)
    
    ax.axhline(y=actual_value, color='green', linestyle='--', label=f'Actual Value at {tune_time.date()}')
    ax.plot(tune_time, pred_before, 'o', color='red', markersize=10, label='Initial Prediction')
    ax.plot(tune_time, pred_after, 'o', color='blue', markersize=10, label='Tuned Prediction')

    ax.set_title('Digital Twin Model Adaptation')
    ax.set_ylabel('Product Concentration')
    ax.set_xlabel('Timestamp')
    ax.legend()
    plt.tight_layout()
    
    # Save the plot to a file
    plot_filename = 'model_adaptation_visualization.png'
    plt.savefig(plot_filename)
    print(f"\nVisualization saved to {plot_filename}")

if __name__ == '__main__':
    import os
    # Construct the absolute path to the data file to resolve pathing issues when run as a module
    script_dir = os.path.dirname(__file__)
    data_path = os.path.abspath(os.path.join(script_dir, '..', '..', 'data', 'historical_process_data.csv'))
    validation_timestamp = '2023-01-10 12:00:00'
    run_and_visualize_adaptation(validation_timestamp, data_path)
