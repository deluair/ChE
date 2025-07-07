import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class MonteCarlo:
    """Performs Monte Carlo simulation for uncertainty quantification."""

    def __init__(self, flowsheet, solver, num_samples=1000):
        self.flowsheet = flowsheet
        self.solver = solver
        self.num_samples = num_samples
        self.uncertain_setters = []
        self.output_responses = {}

    def add_uncertain_parameter(self, setter_callable, distribution, dist_params):
        """Adds a parameter with uncertainty using a generic setter function.

        Args:
            setter_callable (function): A function that takes a single value and sets
                                        the appropriate parameter in the simulation.
            distribution (str): The name of the numpy.random distribution (e.g., 'normal', 'uniform').
            dist_params (dict): Parameters for the distribution (e.g., {'loc': 10, 'scale': 1}).
        """
        self.uncertain_setters.append({
            'setter': setter_callable,
            'dist': getattr(np.random, distribution),
            'params': dist_params
        })

    def add_output_response(self, name, response_callable):
        """Defines an output response to track during the simulation.

        Args:
            name (str): A name for the output response (e.g., 'ProductPurity').
            response_callable (function): A function that takes the flowsheet as input
                                        and returns the desired output value.
        """
        self.output_responses[name] = response_callable

    def run_simulation(self):
        """Runs the Monte Carlo simulation."""
        results = {name: [] for name in self.output_responses.keys()}

        print(f"--- Running Monte Carlo Simulation ({self.num_samples} samples) ---")
        for i in range(self.num_samples):
            # 1. Sample new values and set them using the setter functions
            for param_info in self.uncertain_setters:
                sample_val = param_info['dist'](**param_info['params'])
                param_info['setter'](sample_val)

            # 2. Solve the flowsheet with the new parameters
            try:
                self.solver.solve()
            except Exception as e:
                print(f"Warning: Sample {i+1} failed to solve. Skipping. Error: {e}")
                continue

            # 3. Record the output responses
            for name, func in self.output_responses.items():
                results[name].append(func(self.flowsheet))
            
            if (i + 1) % (self.num_samples // 10) == 0:
                print(f"Completed {i + 1}/{self.num_samples} samples...")

        print("--- Monte Carlo Simulation Complete ---")
        return pd.DataFrame(results)

    @staticmethod
    def analyze_results(results_df):
        """Prints a statistical summary and saves histograms of the results."""
        print("\n--- Uncertainty Analysis Results ---")
        print(results_df.describe())

        for col in results_df.columns:
            plt.figure(figsize=(8, 5))
            sns.histplot(results_df[col], kde=True)
            plt.title(f'Distribution of {col}')
            plt.xlabel('Value')
            plt.ylabel('Frequency')
            plt.grid(True)
            output_filename = f'{col}_distribution.png'
            plt.savefig(output_filename)
            plt.close()  # Close the figure to free memory
            print(f"Saved plot to {output_filename}")

# Example Usage:
if __name__ == '__main__':
    # --- Mock objects for a self-contained example ---
    class MockCSTR:
        def __init__(self, name):
            self.name = name
            self.volume = 10 # m^3
            self.inlet_conc = 0.8
            self.outlet_conc = 0.2
        def solve(self):
            # A simple model where conversion depends on volume and inlet concentration
            # conversion = k * tau = k * V / v_dot
            # Let's say outlet_conc = inlet_conc * (1 - 0.05 * V)
            self.outlet_conc = self.inlet_conc * (1 - 0.05 * self.volume)
            self.outlet_conc = max(0, self.outlet_conc)

    class MockSolver:
        def solve(self):
            for unit in self.flowsheet.unit_ops.values():
                unit.solve()

    class MockFlowsheet:
        def __init__(self):
            self.unit_ops = {'R-101': MockCSTR('R-101')}
            self.solver = MockSolver()
            self.solver.flowsheet = self # Link solver back to flowsheet

    # --- Setup and run the UQ analysis ---
    fs = MockFlowsheet()
    mc_sim = MonteCarlo(fs, num_samples=500)

    # 1. Define uncertain parameters
    # Reactor volume is uncertain, normally distributed around 10 m^3
    mc_sim.add_uncertain_parameter('R-101', 'volume', 'normal', {'loc': 10, 'scale': 0.5})
    # Inlet concentration is also uncertain, uniformly distributed
    mc_sim.add_uncertain_parameter('R-101', 'inlet_conc', 'uniform', {'low': 0.75, 'high': 0.85})

    # 2. Define output responses to track
    def get_outlet_conc(flowsheet):
        return flowsheet.unit_ops['R-101'].outlet_conc
    
    mc_sim.add_output_response('FinalConcentration', get_outlet_conc)

    # 3. Run the simulation and analyze results
    results = mc_sim.run_simulation()
    if not results.empty:
        MonteCarlo.analyze_results(results)
