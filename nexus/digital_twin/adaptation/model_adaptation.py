import pandas as pd
import numpy as np
from scipy.optimize import minimize
from nexus.digital_twin.rt_interface.data_interface import CSVDataReader
from nexus.nexus_core.models.unit_operations import CSTR
from nexus.nexus_core.properties.property_models import PropertyPackage, Component
from nexus.nexus_core.kinetics.kinetics import PowerLawReaction

class ParameterEstimator:
    """Tunes model parameters to minimize the error against historical data."""
    def __init__(self, model, data_reader, target_variable_map):
        self.model = model
        self.data_reader = data_reader
        self.target_variable_map = target_variable_map

    def _objective_function(self, param_value, param_name, timestamp):
        """The function to minimize: the error between prediction and actual data."""
        # Temporarily set the new parameter value in the model
        # This is a simple approach; a more robust way would be needed for complex models
        # e.g., self.model.set_parameter(param_name, param_value)
        # For this example, we'll assume the parameter is the pre-exponential factor 'A'
        # in the reaction's rate constant function.
        original_k_func = self.model.reaction.rate_constant_func
        self.model.reaction.rate_constant_func = lambda T: param_value[0] * np.exp(5000 * (1/310 - 1/T))
        
        # Run the model and get the prediction
        actual_data = self.data_reader.get_data_at_timestamp(timestamp)
        inlet_stream = {
            'flow_rate': actual_data['feed_flow_rate'] / 3600,
            'temperature': actual_data['reactor_temp'] + 273.15,
            'pressure': 101325,
            'composition': {
                'Ethanol': actual_data['feed_cellulose'] / 100,
                'Water': 1 - (actual_data['feed_cellulose'] / 100),
                'Product': 0.0
            }
        }
        self.model.inlets = [inlet_stream]
        self.model.outlets = [inlet_stream.copy()]
        self.model.solve()
        predicted_outlet = self.model.outlets[0]

        # Restore original function
        self.model.reaction.rate_constant_func = original_k_func

        # Calculate error
        predicted_value = predicted_outlet['composition'][self.target_variable_map['model']]
        actual_value = actual_data[self.target_variable_map['data']] / 1000
        return (predicted_value - actual_value) ** 2

    def tune_parameter(self, timestamp, param_name, initial_guess):
        """Uses optimization to find the best value for a model parameter."""
        result = minimize(
            self._objective_function,
            x0=[initial_guess],
            args=(param_name, timestamp),
            method='Nelder-Mead'
        )
        if result.success:
            return result.x[0]
        else:
            print("Parameter tuning failed:", result.message)
            return None

# Example Usage:
if __name__ == '__main__':
    import os
    # Construct the absolute path to the data file to resolve pathing issues when run as a module
    script_dir = os.path.dirname(__file__)
    data_path = os.path.abspath(os.path.join(script_dir, '..', '..', 'data', 'historical_process_data.csv'))
    reader = CSVDataReader(file_path=data_path)

    water = Component('Water', 'H2O')
    ethanol = Component('Ethanol', 'C2H6O')
    prop_pkg = PropertyPackage(components=[water, ethanol])
    stoich = {'Ethanol': -1, 'Product': 1}
    # Initial guess for Arrhenius pre-exponential factor 'A'
    initial_A = 0.005 
    def arrhenius_k(T): return initial_A * np.exp(5000 * (1/310 - 1/T))
    reactants = {'Ethanol': 1}
    reaction = PowerLawReaction('Ethanol_Conversion', stoich, arrhenius_k, reactants)
    reactor = CSTR(name='R-101', volume=50, prop_pkg=prop_pkg, reaction=reaction)

    target_map = {'model': 'Product', 'data': 'product_bioethanol_concentration'}
    estimator = ParameterEstimator(model=reactor, data_reader=reader, target_variable_map=target_map)

    if not reader.data.empty:
        tune_time = pd.Timestamp('2023-01-10 12:00:00')
        print(f"Initial Arrhenius 'A' factor: {initial_A}")
        
        tuned_A = estimator.tune_parameter(tune_time, 'arrhenius_A', initial_A)

        if tuned_A is not None:
            print(f"Tuned Arrhenius 'A' factor: {tuned_A:.6f}")
