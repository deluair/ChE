import numpy as np
from scipy.optimize import minimize

class ScipyOptimizer:
    """An optimizer that uses scipy.optimize.minimize to solve a problem."""

    def __init__(self, problem, method='SLSQP', options=None):
        self.problem = problem
        self.method = method
        self.options = options if options is not None else {'disp': True, 'maxiter': 100}

    def solve(self):
        """Runs the optimization and returns the result."""
        # Get bounds and initial guess (x0) from the problem definition
        bounds = [v['bounds'] for v in self.problem.variables.values()]
        # Use the midpoint of the bounds as the initial guess
        x0 = [np.mean(b) for b in bounds]

        print(f"--- Starting Optimization: {self.problem.name} ---")
        print(f"Algorithm: {self.method}")
        print(f"Initial Guess (x0): {x0}")
        print(f"Bounds: {bounds}")

        # The function to minimize is the problem's evaluate method
        objective_func = self.problem.evaluate

        # Format constraints for SciPy
        constraints = [c.to_scipy_dict(self.problem) for c in self.problem.constraints]
        if constraints:
            print(f"Applying {len(constraints)} constraints.")

        # Run the optimization
        result = minimize(
            objective_func,
            x0,
            method=self.method,
            bounds=bounds,
            constraints=constraints,
            options=self.options
        )

        print("--- Optimization Finished ---")
        if result.success:
            print(f"Successfully found optimal solution.")
            print(f"Optimal Variables (x*): {result.x}")
            print(f"Optimal Objective Value: {result.fun:.6f}")
        else:
            print(f"Optimization failed: {result.message}")
        
        return result

# Example Usage:
if __name__ == '__main__':
    # Import the example problem definition from base_problem
    # Note: This requires the nexus project to be installed in editable mode (`pip install -e .`)
    from nexus.optimization.problems.base_problem import OptimizationProblem

    # --- Mock objects for a self-contained example ---
    class MockUnitOp:
        def __init__(self, name):
            self.name = name
            self.operating_temp = 300
            self.conversion = 0.5
        def solve(self):
            # Conversion is a function of temperature
            self.conversion = 0.5 + (self.operating_temp - 300) / 100 - ((self.operating_temp - 370) / 50)**2
            # print(f"Solved {self.name} at {self.operating_temp}K, conversion: {self.conversion:.2%}")

    class MockFlowsheet:
        def __init__(self):
            self.unit_ops = {'R-101': MockUnitOp('R-101')}
        def solve(self):
            self.unit_ops['R-101'].solve()

    class ReactorProblem(OptimizationProblem):
        def evaluate(self, x):
            # 1. Update flowsheet
            temp_val = x[0]
            unit_op = self.flowsheet.unit_ops['R-101']
            setattr(unit_op, 'operating_temp', temp_val)
            # 2. Re-solve
            self.flowsheet.solve()
            # 3. Return objective (minimize -conversion)
            return -unit_op.conversion

    # --- Setup and run the optimization ---
    fs = MockFlowsheet()
    problem = ReactorProblem(name="MaximizeReactorConversionWithConstraint", flowsheet=fs)
    problem.add_variable('reactor_temp', 'R-101', 'operating_temp', bounds=(300, 400))

    # Add a constraint: temperature must be <= 380 K
    from nexus.optimization.constraints.base_constraint import Constraint
    class MaxTempConstraint(Constraint):
        def evaluate(self, x, flowsheet):
            # C(x) = 380 - T >= 0
            return 380 - x[0]
    
    problem.add_constraint(MaxTempConstraint('TempLimit', 'ineq'))

    # Create and run the optimizer
    optimizer = ScipyOptimizer(problem)
    result = optimizer.solve()

    # Print the final state
    if result.success:
        final_temp = result.x[0]
        final_conversion = -result.fun
        print(f"\nOptimal Temperature (with constraint): {final_temp:.2f} K")
        print(f"Maximum Conversion: {final_conversion:.2%}")
