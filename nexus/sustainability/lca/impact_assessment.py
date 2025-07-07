import numpy as np

class ImpactAssessment:
    """Calculates environmental impacts based on life cycle inventory data."""

    # Simplified database of GWP100 (Global Warming Potential, 100-year) factors
    # Source: IPCC AR5. Units: kg CO2-eq / kg substance
    GWP_FACTORS = {
        'CO2': 1.0,
        'CH4': 28.0,  # Methane
        'N2O': 265.0, # Nitrous Oxide
        'Ethanol': 2.1, # From combustion, simplified
    }

    # Add other impact categories here, e.g., Acidification Potential (AP)
    # AP_FACTORS = { 'SO2': 1.0, 'NOx': 0.7, ... }

    def __init__(self, inventory):
        """Initializes with a Life Cycle Inventory (LCI)."""
        self.inventory = inventory # Expects a dictionary of emissions

    def calculate_gwp(self):
        """Calculates the total Global Warming Potential for the process."""
        total_gwp = 0.0
        for substance, mass in self.inventory.items():
            factor = self.GWP_FACTORS.get(substance, 0.0)
            if factor == 0.0:
                print(f"Warning: No GWP factor found for '{substance}'. Ignoring.")
            total_gwp += mass * factor
        return total_gwp

    def run_all_impacts(self):
        """Runs all defined impact assessments."""
        # This can be expanded to calculate and return multiple impact categories
        gwp = self.calculate_gwp()
        return {
            'GWP100': gwp
            # 'AP': self.calculate_ap(), ...
        }

# Example Usage:
if __name__ == '__main__':
    # A mock Life Cycle Inventory (LCI) representing annual emissions in kg
    life_cycle_inventory = {
        'CO2': 50000, # From energy consumption
        'CH4': 120,   # Fugitive emissions
        'Ethanol': 50 # Unreacted ethanol released
    }

    impact_assessor = ImpactAssessment(inventory=life_cycle_inventory)
    impacts = impact_assessor.run_all_impacts()

    print("--- Life Cycle Impact Assessment Example ---")
    print(f"Life Cycle Inventory (Emissions):\n{life_cycle_inventory}")
    print(f"\nCalculated Impacts:")
    for category, value in impacts.items():
        print(f"  - {category}: {value:,.2f} kg CO2-eq/year")
