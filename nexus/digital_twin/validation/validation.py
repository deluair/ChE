import pandas as pd
import numpy as np
from nexus.digital_twin.rt_interface.data_interface import CSVDataReader
from nexus.nexus_core.models.unit_operations import CSTR
from nexus.nexus_core.properties.property_models import PropertyPackage, Component
from nexus.nexus_core.kinetics.kinetics import PowerLawReaction

class ValidationEngine:
    """Compares simulation model outputs with historical data to assess accuracy."""
    def __init__(self, model, data_reader):
        self.model = model
        self.data_reader = data_reader

    def validate_at_timestamp(self, timestamp):
        """
        Performs validation for a single point in time.

        Args:
            timestamp (pd.Timestamp): The timestamp to validate against.

        Returns:
            dict: A dictionary containing the model's prediction, the actual data,
                  and the calculated error.
        """
        # 1. Get historical data for the specified timestamp
        actual_data = self.data_reader.get_data_at_timestamp(timestamp)
        if actual_data is None:
            print(f"No data available for timestamp {timestamp}")
            return None

        # 2. Configure the model's inlet stream based on historical data
        # This mapping depends on the data column names
        inlet_stream = {
            'flow_rate': actual_data['feed_flow_rate'] / 3600,  # Convert from hourly to m^3/s
            'temperature': actual_data['reactor_temp'] + 273.15, # Convert C to K
            'pressure': 101325, # Assume atmospheric pressure
            'composition': {
                'Ethanol': actual_data['feed_cellulose'] / 100, # Simplified mapping
                'Water': 1 - (actual_data['feed_cellulose'] / 100),
                'Product': 0.0
            }
        }
        self.model.inlets = [inlet_stream]
        self.model.outlets = [inlet_stream.copy()] # Reset outlet

        # 3. Solve the model
        self.model.solve()
        predicted_outlet = self.model.outlets[0]

        # 4. Compare predicted vs. actual
        # We are comparing the concentration of 'Product' (mapped from bioethanol)
        predicted_value = predicted_outlet['composition']['Product']
        # This mapping is a simplification for the example
        actual_value = actual_data['product_bioethanol_concentration'] / 1000 # g/L to kg/m^3 (approx)
        
        error = abs(predicted_value - actual_value)

        return {
            'timestamp': timestamp,
            'predicted_product_conc': predicted_value,
            'actual_product_conc': actual_value,
            'absolute_error': error
        }

# Example Usage:
if __name__ == '__main__':
    # 1. Setup the data reader
    import os
    # Construct the absolute path to the data file to resolve pathing issues when run as a module
    script_dir = os.path.dirname(__file__)
    data_path = os.path.abspath(os.path.join(script_dir, '..', '..', 'data', 'historical_process_data.csv'))
    reader = CSVDataReader(file_path=data_path)

    # 2. Setup the model to be validated (CSTR)
    water = Component('Water', 'H2O')
    ethanol = Component('Ethanol', 'C2H6O')
    prop_pkg = PropertyPackage(components=[water, ethanol])
    stoich = {'Ethanol': -1, 'Product': 1}
    def arrhenius_k(T): return 0.005 * np.exp(5000 * (1/310 - 1/T))
    reactants = {'Ethanol': 1}
    reaction = PowerLawReaction('Ethanol_Conversion', stoich, arrhenius_k, reactants)
    reactor = CSTR(name='R-101', volume=50, prop_pkg=prop_pkg, reaction=reaction)

    # 3. Create the validation engine
    validator = ValidationEngine(model=reactor, data_reader=reader)

    # 4. Perform validation at a specific time
    if not reader.data.empty:
        validation_time = pd.Timestamp('2023-01-10 12:00:00')
        result = validator.validate_at_timestamp(validation_time)

        if result:
            print("\n--- Validation Result ---")
            print(f"Timestamp: {result['timestamp']}")
            print(f"Predicted Product Concentration: {result['predicted_product_conc']:.4f}")
            print(f"Actual Product Concentration:    {result['actual_product_conc']:.4f}")
            print(f"Absolute Error:                {result['absolute_error']:.4f}")
