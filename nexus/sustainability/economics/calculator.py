from nexus.sustainability.economics.capex import Capex
from nexus.sustainability.economics.opex import Opex

class EconomicCalculator:
    """Performs a complete techno-economic analysis (TEA)."""

    def __init__(self, flowsheet, year=2023, operating_hours=8000, interest_rate=0.08, plant_life_years=20):
        self.flowsheet = flowsheet
        self.year = year
        self.operating_hours = operating_hours
        self.interest_rate = interest_rate
        self.plant_life = plant_life_years
        
        self.capex_estimator = Capex(flowsheet, year)
        self.opex_estimator = Opex(flowsheet, operating_hours)

    def run_analysis(self):
        """Runs all economic calculations and returns a summary report."""
        # 1. Calculate Capex
        total_capex = self.capex_estimator.calculate_total_capex()

        # 2. Calculate Opex
        opex_details = self.opex_estimator.calculate_total_opex()
        total_opex = opex_details['TotalOpex']

        # 3. Calculate Annualized Capital Cost (ACC)
        # Using capital recovery factor
        crf = (self.interest_rate * (1 + self.interest_rate) ** self.plant_life) / \
              ((1 + self.interest_rate) ** self.plant_life - 1)
        annualized_capex = total_capex * crf

        # 4. Calculate Total Annualized Cost
        total_annual_cost = annualized_capex + total_opex

        return {
            'TotalCapex': total_capex,
            'AnnualizedCapex': annualized_capex,
            'TotalOpex': total_opex,
            'OpexDetails': opex_details,
            'TotalAnnualCost': total_annual_cost,
            'AnalysisParams': {
                'InterestRate': self.interest_rate,
                'PlantLifeYears': self.plant_life
            }
        }

# Example Usage:
if __name__ == '__main__':
    # Mock objects from previous examples
    class MockUnitOp:
        def __init__(self, name, type_name, capacity):
            self.name = name
            self.__class__ = type(type_name, (self,), {})
            if type_name == 'CSTR':
                self.volume = capacity

    class MockFlowsheet:
        def __init__(self):
            self.unit_ops = [MockUnitOp('R-101', 'CSTR', 20)]
            self.streams = [
                {
                    'flow_rate': 0.1, # m^3/s
                    'composition': {'Ethanol': 0.8, 'Water': 0.2}
                }
            ]

    flowsheet = MockFlowsheet()
    tea_calculator = EconomicCalculator(flowsheet)
    economic_summary = tea_calculator.run_analysis()

    print("--- Full Techno-Economic Analysis Summary ---")
    print(f"Total Capital Cost (Capex): ${economic_summary['TotalCapex']:,.2f}")
    print(f"Annualized Capital Cost: ${economic_summary['AnnualizedCapex']:,.2f}/year")
    print(f"Total Operating Cost (Opex): ${economic_summary['TotalOpex']:,.2f}/year")
    print(f"  - Utility Cost: ${economic_summary['OpexDetails']['UtilityCost']:,.2f}/year")
    print(f"  - Raw Material Cost: ${economic_summary['OpexDetails']['RawMaterialCost']:,.2f}/year")
    print(f"--------------------------------------------------")
    print(f"TOTAL ANNUALIZED COST: ${economic_summary['TotalAnnualCost']:,.2f}/year")
    print(f"--------------------------------------------------")
