import numpy as np

# --- Import all the necessary modules from the Nexus framework ---
# Core simulation components
from nexus.nexus_core.solver.flowsheet import Flowsheet, SequentialModularSolver
from nexus.nexus_core.models.unit_operations import CSTR, UnitOperation
from nexus.nexus_core.properties.property_models import PropertyPackage, Component
from nexus.nexus_core.kinetics.kinetics import PowerLawReaction

# Sustainability and economic analysis
from nexus.sustainability.economics.calculator import EconomicCalculator
from nexus.sustainability.lca.calculator import LCACalculator

# Optimization
from nexus.optimization.problems.base_problem import OptimizationProblem
from nexus.optimization.algorithms.scipy_optimizer import ScipyOptimizer

# Uncertainty Quantification
from nexus.nexus_core.uq.monte_carlo import MonteCarlo

# --- 1. Define a Custom Unit Operation (Separator) ---
class Separator(UnitOperation):
    """A simple component separator."""
    def solve(self):
        inlet = self.inlets[0]
        # Split ethanol and water with 99% efficiency
        self.outlets[0]['composition'] = {'Ethanol': inlet['composition'].get('Ethanol', 0) * 0.99, 'Water': inlet['composition'].get('Water', 0) * 0.01}
        self.outlets[1]['composition'] = {'Ethanol': inlet['composition'].get('Ethanol', 0) * 0.01, 'Water': inlet['composition'].get('Water', 0) * 0.99}
        for out in self.outlets:
            out.update({k: v for k, v in inlet.items() if k != 'composition'})
        print(f"Separator '{self.name}' solved.")

# --- 2. Build the Flowsheet ---
def build_flowsheet():
    fs = Flowsheet(name='Bioethanol Process')

    # Setup components, properties, and reaction
    # For pseudo-components like 'Product', provide a manual molecular weight (e.g., 100 g/mol)
    prop_pkg = PropertyPackage(components=[Component('Ethanol', 'C2H6O'), 
                                           Component('Water', 'H2O'), 
                                           Component('Product', 'Prod', mw=100)])
    reaction = PowerLawReaction('r1', {'Ethanol': -1, 'Product': 1}, lambda T: 0.1, {'Ethanol': 1})

    # Create and add unit operations
    feed_unit = UnitOperation(name='Feed')
    reactor = CSTR(name='R-101', volume=20, prop_pkg=prop_pkg, reaction=reaction)
    separator = Separator(name='S-101')
    product_unit = UnitOperation(name='Product')
    waste_unit = UnitOperation(name='Waste')
    
    for unit in [feed_unit, reactor, separator, product_unit, waste_unit]:
        fs.add_unit(unit)

    # Define the feed stream's properties
    fs.streams['feed_stream'] = {'flow_rate': 0.1, 'temperature': 353, 'composition': {'Ethanol': 0.8, 'Water': 0.2, 'Product': 0.0}}

    # Connect the units, using the predefined 'feed_stream' for the first connection
    fs.connect('feed_stream', 'Feed', 'R-101')
    fs.connect('reactor_outlet', 'R-101', 'S-101')
    fs.connect('product_stream', 'S-101', 'Product')
    fs.connect('waste_stream', 'S-101', 'Waste')
    
    return fs

# --- Main Execution Block ---
if __name__ == '__main__':

    # --- Part A: Baseline Simulation and Analysis ---
    print("\n" + "="*50)
    print("PART A: BASELINE SIMULATION & ANALYSIS")
    print("="*50)
    flowsheet = build_flowsheet()
    solver = SequentialModularSolver(flowsheet=flowsheet)
    solver.solve()

    print("\n--- Baseline Economic Analysis ---")
    tea_calculator = EconomicCalculator(flowsheet)
    economic_summary = tea_calculator.run_analysis()
    print(f"Total Annualized Cost: ${economic_summary['TotalAnnualCost']:,.2f}/year")

    print("\n--- Baseline Life Cycle Assessment ---")
    lca_calculator = LCACalculator(flowsheet)
    lca_summary = lca_calculator.run_analysis()
    print(f"Total GWP: {lca_summary['ImpactAssessment']['GWP100']:,.2f} kg CO2-eq/year")

    # --- Part B: Process Optimization ---
    print("\n" + "="*50)
    print("PART B: PROCESS OPTIMIZATION")
    print("="*50)
    
    class CostOptimizationProblem(OptimizationProblem):
        def evaluate(self, x):
            # Update reactor volume
            reactor_volume = x[0]
            self.flowsheet.unit_ops['R-101'].volume = reactor_volume
            # Re-solve the flowsheet
            SequentialModularSolver(self.flowsheet).solve()
            # Calculate and return the objective: total annualized cost
            cost = EconomicCalculator(self.flowsheet).run_analysis()['TotalAnnualCost']
            print(f"  (Evaluating volume={reactor_volume:.2f} m^3, cost=${cost:,.2f})")
            return cost

    opt_problem = CostOptimizationProblem("MinimizeCost", flowsheet)
    opt_problem.add_variable('reactor_volume', 'R-101', 'volume', bounds=(5, 50))
    
    optimizer = ScipyOptimizer(opt_problem, options={'disp': False})
    opt_result = optimizer.solve()

    if opt_result.success:
        print(f"\nOptimal Reactor Volume: {opt_result.x[0]:.2f} m^3")
        print(f"Minimum Annualized Cost: ${opt_result.fun:,.2f}/year")

    # --- Part C: Uncertainty Quantification ---
    print("\n" + "="*50)
    print("PART C: UNCERTAINTY QUANTIFICATION")
    print("="*50)
    
    # Reset to the optimal volume
    flowsheet.unit_ops['R-101'].volume = opt_result.x[0]
    
    # The solver is needed for the UQ simulation runs
    solver_uq = SequentialModularSolver(flowsheet)
    mc_sim = MonteCarlo(flowsheet, solver_uq, num_samples=200)
    
    # Create a single economic calculator instance for the UQ study
    tea_calculator_uq = EconomicCalculator(flowsheet)

    # Define a setter function for the uncertain parameter (ethanol cost)
    def set_ethanol_cost(cost):
        tea_calculator_uq.opex_estimator.RAW_MATERIAL_COSTS['Ethanol'] = cost

    # Add the uncertain parameter using the new setter method
    mc_sim.add_uncertain_parameter(
        setter_callable=set_ethanol_cost,
        distribution='normal',
        dist_params={'loc': 0.7, 'scale': 0.07} # Base cost $0.7/kg, 10% std dev
    )

    # Define the output response, using the same calculator instance
    def get_total_cost(fs):
        # The flowsheet is solved inside the MC loop. We just run analysis.
        return tea_calculator_uq.run_analysis()['TotalAnnualCost']

    mc_sim.add_output_response('TotalAnnualCost', get_total_cost)

    # Run UQ simulation
    uq_results = mc_sim.run_simulation()
    if not uq_results.empty:
        MonteCarlo.analyze_results(uq_results)

    print("\n" + "="*50)
    print("NEXUS FRAMEWORK DEMO COMPLETE")
    print("="*50)
