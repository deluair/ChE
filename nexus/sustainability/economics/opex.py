import numpy as np

class Opex:
    """Estimates the operating cost of the process."""

    # Standard utility and raw material costs (can be customized)
    UTILITY_COSTS = {
        'CoolingWater': 0.25,  # $/m^3
        'Steam': 15.0,        # $/tonne
        'Electricity': 0.12,  # $/kWh
    }

    RAW_MATERIAL_COSTS = {
        'Ethanol': 0.7, # $/kg
        'Water': 0.001, # $/kg (process water)
    }

    def __init__(self, flowsheet, operating_hours_per_year=8000):
        self.flowsheet = flowsheet
        self.operating_hours = operating_hours_per_year

    def calculate_utility_costs(self):
        """Calculates the total annual utility costs based on flowsheet duties."""
        total_utility_cost = 0
        # This is a placeholder. A real implementation would query heat exchangers,
        # pumps, etc., for their energy consumption.
        # For now, let's assume a fixed electricity cost per unit.
        for unit in self.flowsheet.unit_ops:
            # Simplified: assume 10 kW for each unit op
            power_kw = 10 
            annual_kwh = power_kw * self.operating_hours
            total_utility_cost += annual_kwh * self.UTILITY_COSTS['Electricity']
        return total_utility_cost

    def calculate_raw_material_costs(self):
        """Calculates the total annual raw material costs from all source units."""
        total_rm_cost = 0
        
        # Find feed streams by identifying units with no inlets
        feed_streams = []
        for unit in self.flowsheet.unit_ops.values():
            if not unit.inlets:
                feed_streams.extend(unit.outlets)

        if not feed_streams:
            print("Warning: Could not find any feed streams in the flowsheet.")
            return 0.0

        for feed_stream in feed_streams:
            # A simple assumption: flow_rate is in m^3/s, density is 1000 kg/m^3
            flow_rate_kg_s = feed_stream.get('flow_rate', 0) * 1000 
            
            for component, fraction in feed_stream.get('composition', {}).items():
                if component in self.RAW_MATERIAL_COSTS:
                    mass_flow_kg_s = flow_rate_kg_s * fraction
                    annual_kg = mass_flow_kg_s * 3600 * self.operating_hours
                    total_rm_cost += annual_kg * self.RAW_MATERIAL_COSTS.get(component, 0)
                    
        return total_rm_cost

    def calculate_total_opex(self):
        """Calculates the total annual operating expenditure."""
        utility_cost = self.calculate_utility_costs()
        rm_cost = self.calculate_raw_material_costs()

        # Other costs (labor, maintenance) are often estimated as a % of Capex
        # This requires a Capex result, so we'll omit it for now but mention it.
        # For example: labor = 0.10 * capex, maintenance = 0.05 * capex
        
        total_opex = utility_cost + rm_cost
        return {
            'TotalOpex': total_opex,
            'UtilityCost': utility_cost,
            'RawMaterialCost': rm_cost
        }

# Example Usage:
if __name__ == '__main__':
    # Mock objects for demonstration
    class MockUnitOp:
        def __init__(self, name):
            self.name = name

    class MockFlowsheet:
        def __init__(self):
            self.unit_ops = [MockUnitOp('R-101'), MockUnitOp('C-101')]
            self.streams = [
                {
                    'flow_rate': 0.1, # m^3/s
                    'composition': {'Ethanol': 0.8, 'Water': 0.2}
                }
            ]

    flowsheet = MockFlowsheet()
    opex_estimator = Opex(flowsheet)
    total_opex_details = opex_estimator.calculate_total_opex()

    print(f"--- Opex Estimation Example ---")
    print(f"Annual Utility Cost: ${total_opex_details['UtilityCost']:,.2f}")
    print(f"Annual Raw Material Cost: ${total_opex_details['RawMaterialCost']:,.2f}")
    print(f"Total Annual Operating Cost (Opex): ${total_opex_details['TotalOpex']:,.2f}")
