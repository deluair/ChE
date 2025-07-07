import numpy as np

class LCI:
    """Generates a Life Cycle Inventory (emissions) from a flowsheet."""

    # Emission factors for utilities (kg of substance per unit of utility)
    # Source: Simplified from ecoinvent and other LCI databases
    UTILITY_EMISSION_FACTORS = {
        'Electricity': { # per kWh
            'CO2': 0.4, # kg CO2/kWh
            'CH4': 0.00002, # kg CH4/kWh
        },
        'Steam': { # per kg of steam
            'CO2': 0.1, # kg CO2/kg steam
        }
    }

    def __init__(self, flowsheet, operating_hours_per_year=8000):
        self.flowsheet = flowsheet
        self.operating_hours = operating_hours_per_year

    def generate_inventory(self):
        """Generates the complete LCI for the process.
        
        Returns:
            dict: A dictionary where keys are substance names (e.g., 'CO2')
                  and values are the total mass emitted per year (in kg).
        """
        inventory = {}

        # 1. Emissions from utility consumption (placeholder logic)
        # A real implementation would get energy usage from each unit op.
        for unit in self.flowsheet.unit_ops:
            power_kw = 10 # Simplified: assume 10 kW per unit
            annual_kwh = power_kw * self.operating_hours
            
            for substance, factor in self.UTILITY_EMISSION_FACTORS['Electricity'].items():
                emission_kg = annual_kwh * factor
                inventory[substance] = inventory.get(substance, 0) + emission_kg

        # 2. Fugitive emissions from the process (e.g., leaks)
        # This is highly dependent on the process and equipment type.
        # Let's assume a small fugitive emission for each component in the feed.
        feed_streams = []
        for unit in self.flowsheet.unit_ops.values():
            if not unit.inlets:
                feed_streams.extend(unit.outlets)

        if not feed_streams:
            print("Warning: Could not find any feed streams for fugitive emission calculation.")
        else:
            for feed_stream in feed_streams:
                flow_rate_kg_s = feed_stream.get('flow_rate', 0) * 1000 # Assume density 1000 kg/m3
                for comp, fraction in feed_stream.get('composition', {}).items():
                    # Assume 0.01% of the inlet mass of each component is lost as fugitive emissions
                    fugitive_emission_kg_s = flow_rate_kg_s * fraction * 0.0001
                    annual_emission_kg = fugitive_emission_kg_s * 3600 * self.operating_hours
                    inventory[comp] = inventory.get(comp, 0) + annual_emission_kg

        return inventory

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
    lci_generator = LCI(flowsheet)
    inventory = lci_generator.generate_inventory()

    print("--- Life Cycle Inventory (LCI) Generation Example ---")
    print("Generated Annual Emissions (kg/year):")
    for substance, mass in inventory.items():
        print(f"  - {substance}: {mass:,.2f}")
