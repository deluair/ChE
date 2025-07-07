import numpy as np

class Capex:
    """Estimates the capital cost of process equipment."""

    # Cost data for different equipment types (source: simplified from engineering handbooks)
    # Format: { 'equipment_type': [base_cost, reference_capacity, cost_exponent] }
    COST_DATA = {
        'CSTR': [50000, 10, 0.6],  # Base cost for a 10 m^3 reactor
        'DistillationColumn': [200000, 1, 0.65], # Base cost for 1 m diameter column
        'HeatExchanger': [25000, 50, 0.7], # Base cost for 50 m^2 area
        'Pump': [10000, 100, 0.8], # Base cost for 100 kW pump
        'Separator': [15000, 0.1, 0.6], # Base cost for 0.1 m^3/s flow rate
    }

    def __init__(self, flowsheet, year=2023):
        self.flowsheet = flowsheet
        self.year = year
        # Placeholder for CEPCI data for cost indexing
        self.CEPCI = {2020: 607.5, 2023: 708.0} # Chemical Engineering Plant Cost Index

    def estimate_unit_cost(self, unit_op):
        """Estimates the cost of a single unit operation using cost-scaling laws."""
        unit_type = unit_op.__class__.__name__
        # Ignore base class used for conceptual units like 'Feed'
        if unit_type == 'UnitOperation':
            return 0.0
        if unit_type not in self.COST_DATA:
            print(f"Warning: No cost data found for unit type '{unit_type}'. Skipping.")
            return 0.0

        base_cost, ref_capacity, exponent = self.COST_DATA[unit_type]

        # Determine the capacity attribute based on unit type
        if unit_type == 'CSTR':
            capacity = unit_op.volume
        elif unit_type == 'Separator':
            # Use inlet flow rate as capacity basis (m^3/s)
            if unit_op.inlets:
                capacity = unit_op.inlets[0].get('flow_rate', ref_capacity)
            else:
                capacity = ref_capacity # Fallback if no inlet connected
        # Add other unit type capacity logic here (e.g., area for heat exchanger)
        else:
            print(f"Warning: Capacity attribute for '{unit_type}' not defined. Using ref_capacity.")
            capacity = ref_capacity

        # Cost scaling formula: Cost = BaseCost * (Capacity / RefCapacity)^Exponent
        cost_2020 = base_cost * (capacity / ref_capacity) ** exponent

        # Adjust for inflation using CEPCI
        cost_current = cost_2020 * (self.CEPCI[self.year] / self.CEPCI[2020])
        return cost_current

    def calculate_total_capex(self):
        """Calculates the total installed capital cost for the entire flowsheet."""
        total_equipment_cost = sum(self.estimate_unit_cost(unit) for unit in self.flowsheet.unit_ops.values())

        # Lang Factor method for total installed cost (includes piping, instruments, etc.)
        # Typical factors: 3.1 (solid), 4.74 (fluid), 3.63 (mixed)
        lang_factor = 4.74 # Assuming a fluid processing plant
        total_installed_cost = total_equipment_cost * lang_factor

        return total_installed_cost

# Example Usage:
if __name__ == '__main__':
    # Mock objects for demonstration since we don't have a full flowsheet yet
    class MockUnitOp:
        def __init__(self, name, type_name, capacity):
            self.name = name
            self.__class__ = type(type_name, (self,), {})
            if type_name == 'CSTR':
                self.volume = capacity

    class MockFlowsheet:
        def __init__(self):
            self.unit_ops = [
                MockUnitOp('R-101', 'CSTR', 20), # 20 m^3 reactor
                MockUnitOp('R-102', 'CSTR', 50), # 50 m^3 reactor
                MockUnitOp('P-101', 'Pump', 150) # Non-defined capacity logic
            ]

    flowsheet = MockFlowsheet()
    capex_estimator = Capex(flowsheet, year=2023)
    total_capex = capex_estimator.calculate_total_capex()

    print(f"--- Capex Estimation Example ---")
    for unit in flowsheet.unit_ops:
        cost = capex_estimator.estimate_unit_cost(unit)
        print(f"Estimated cost for {unit.name} ({unit.__class__.__name__}): ${cost:,.2f}")
    
    print(f"\nTotal Equipment Cost: ${sum(capex_estimator.estimate_unit_cost(u) for u in flowsheet.unit_ops):,.2f}")
    print(f"Total Installed Capital Cost (Capex): ${total_capex:,.2f}")
