from nexus.sustainability.lca.inventory import LCI
from nexus.sustainability.lca.impact_assessment import ImpactAssessment

class LCACalculator:
    """Performs a complete Life Cycle Assessment (LCA)."""

    def __init__(self, flowsheet, operating_hours=8000):
        self.flowsheet = flowsheet
        self.operating_hours = operating_hours
        self.lci_generator = LCI(flowsheet, operating_hours)

    def run_analysis(self):
        """Runs the full LCA and returns a summary report."""
        # 1. Generate the Life Cycle Inventory (LCI)
        inventory = self.lci_generator.generate_inventory()

        # 2. Perform the Impact Assessment
        impact_assessor = ImpactAssessment(inventory)
        impacts = impact_assessor.run_all_impacts()

        return {
            'LifeCycleInventory': inventory,
            'ImpactAssessment': impacts
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
    lca_calculator = LCACalculator(flowsheet)
    lca_summary = lca_calculator.run_analysis()

    print("--- Full Life Cycle Assessment (LCA) Summary ---")
    print("\nGenerated Annual Emissions (kg/year):")
    for substance, mass in lca_summary['LifeCycleInventory'].items():
        print(f"  - {substance}: {mass:,.2f}")

    print("\nCalculated Environmental Impacts:")
    for category, value in lca_summary['ImpactAssessment'].items():
        print(f"  - {category}: {value:,.2f} kg CO2-eq/year")
    print("--------------------------------------------------")
