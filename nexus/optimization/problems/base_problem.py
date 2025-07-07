from abc import ABC, abstractmethod

class OptimizationProblem(ABC):
    """Abstract base class for defining an optimization problem."""

    def __init__(self, name, flowsheet):
        self.name = name
        self.flowsheet = flowsheet
        self.variables = {} # { 'var_name': {'bounds': (min, max), 'unit_op': 'name', 'param': 'attr'} }
        self.constraints = []
        self.objective_function = None

    def add_variable(self, name, unit_op_name, parameter_name, bounds):
        """Defines a decision variable for the optimization.

        Args:
            name (str): A unique name for the variable.
            unit_op_name (str): The name of the unit operation to modify.
            parameter_name (str): The attribute of the unit op to change (e.g., 'volume').
            bounds (tuple): A (min, max) tuple defining the variable's range.
        """
        if unit_op_name not in self.flowsheet.unit_ops:
            raise ValueError(f"Unit operation '{unit_op_name}' not found in the flowsheet.")
        
        self.variables[name] = {
            'unit_op': unit_op_name,
            'param': parameter_name,
            'bounds': bounds
        }

    def set_objective(self, objective_callable):
        """Sets the function to be minimized or maximized.

        The callable should accept the flowsheet as an argument and return a single
        numeric value to be optimized.
        """
        self.objective_function = objective_callable

    def add_constraint(self, constraint_obj):
        """Adds a constraint to the optimization problem."""
        self.constraints.append(constraint_obj)

    @abstractmethod
    def evaluate(self, x):
        """Evaluates the objective function for a given set of variable values.

        Args:
            x (list or np.array): A list of values for the decision variables,
                                  in the order they were added.
        
        Returns:
            float: The calculated value of the objective function.
        """
        pass

# Example of a concrete implementation
if __name__ == '__main__':
    # This demonstrates how a user would define a specific problem.
    
    # Mock classes for demonstration
    class MockUnitOp:
        def __init__(self, name):
            self.name = name
            self.operating_temp = 300
            self.conversion = 0.5
        def solve(self):
            # Simulate that higher temp gives better conversion
            self.conversion = 0.5 + (self.operating_temp - 300) / 100
            print(f"Solved {self.name} at {self.operating_temp}K, conversion: {self.conversion:.2%}")

    class MockFlowsheet:
        def __init__(self):
            self.unit_ops = {'R-101': MockUnitOp('R-101')}
            self.solver = self # Dummy solver
        def solve(self):
            self.unit_ops['R-101'].solve()

    class ReactorProblem(OptimizationProblem):
        def evaluate(self, x):
            """The specific evaluation logic for this problem."""
            # 1. Update the flowsheet with the new variable values
            var_names = list(self.variables.keys())
            temp_val = x[0]
            var_info = self.variables[var_names[0]]
            unit_op = self.flowsheet.unit_ops[var_info['unit_op']]
            setattr(unit_op, var_info['param'], temp_val)

            # 2. Re-solve the flowsheet with the new parameters
            self.flowsheet.solve()

            # 3. Calculate and return the objective function value
            # Objective: Maximize conversion (or minimize -conversion)
            return -unit_op.conversion

    # --- Setup and run ---
    fs = MockFlowsheet()
    problem = ReactorProblem(name="MaximizeReactorConversion", flowsheet=fs)

    # Define the variable: Reactor temperature
    problem.add_variable('reactor_temp', 'R-101', 'operating_temp', bounds=(300, 400))

    # The objective is defined within the evaluate method for this simple case.

    # Test the evaluation
    print("--- Testing Optimization Problem Definition ---")
    print("Evaluating with temp = 350K...")
    objective_value = problem.evaluate([350])
    print(f"Objective function value: {objective_value:.4f}")

    print("\nEvaluating with temp = 375K...")
    objective_value = problem.evaluate([375])
    print(f"Objective function value: {objective_value:.4f}")

    # Example of adding a constraint (though it's not used until the optimizer step)
    from nexus.optimization.constraints.base_constraint import Constraint
    class DummyConstraint(Constraint):
        def evaluate(self, x, flowsheet):
            # Constraint: temp must be <= 390
            return 390 - x[0]
    
    problem.add_constraint(DummyConstraint('TempLimit', 'ineq'))
    print(f"\nNumber of constraints added: {len(problem.constraints)}")
