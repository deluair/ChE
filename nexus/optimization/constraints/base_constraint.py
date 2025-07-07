from abc import ABC, abstractmethod

class Constraint(ABC):
    """Abstract base class for an optimization constraint."""

    def __init__(self, name, constraint_type):
        self.name = name
        if constraint_type not in ['eq', 'ineq']:
            raise ValueError("Constraint type must be 'eq' (equality) or 'ineq' (inequality).")
        self.constraint_type = constraint_type

    @abstractmethod
    def evaluate(self, x, flowsheet):
        """Evaluates the constraint function at a given point x.

        For 'ineq', the function should be >= 0 for a feasible point.
        For 'eq', the function should be == 0 for a feasible point.

        Args:
            x (list or np.array): The vector of decision variables.
            flowsheet: The current state of the flowsheet after being updated with x.

        Returns:
            float: The value of the constraint function.
        """
        pass

    def to_scipy_dict(self, problem):
        """Formats the constraint for use with scipy.optimize.minimize."""
        return {
            'type': self.constraint_type,
            'fun': lambda x: self.evaluate(x, problem.flowsheet)
        }

# Example of a concrete implementation
if __name__ == '__main__':
    # This demonstrates how a user would define a specific constraint.

    # Mock classes for demonstration
    class MockUnitOp:
        def __init__(self, name):
            self.name = name
            self.outlet_purity = 0.9

    class MockFlowsheet:
        def __init__(self):
            self.unit_ops = {'S-101': MockUnitOp('S-101')}

    class PurityConstraint(Constraint):
        def __init__(self, name, unit_name, min_purity):
            super().__init__(name, 'ineq') # C(x) >= 0
            self.unit_name = unit_name
            self.min_purity = min_purity

        def evaluate(self, x, flowsheet):
            """Constraint: Purity - MinPurity >= 0"""
            # In a real problem, 'x' would influence the purity.
            # Here, we just retrieve the current purity for demonstration.
            unit = flowsheet.unit_ops[self.unit_name]
            current_purity = unit.outlet_purity
            return current_purity - self.min_purity

    # --- Setup and test ---
    fs = MockFlowsheet()
    # Let's say the current purity is 0.9
    fs.unit_ops['S-101'].outlet_purity = 0.90
    
    # Constraint: Purity must be >= 0.95
    constraint = PurityConstraint(name='MinProductPurity', unit_name='S-101', min_purity=0.95)
    
    print("--- Testing Constraint Definition ---")
    # We pass a dummy 'x' because it's not used in this simple evaluation
    value = constraint.evaluate([], fs)
    print(f"Constraint '{constraint.name}' evaluated to: {value:.3f}")
    if value >= 0:
        print("Constraint is satisfied.")
    else:
        print("Constraint is VIOLATED.")

    # Now, let's say the purity is 0.98
    fs.unit_ops['S-101'].outlet_purity = 0.98
    value = constraint.evaluate([], fs)
    print(f"\nConstraint '{constraint.name}' re-evaluated to: {value:.3f}")
    if value >= 0:
        print("Constraint is satisfied.")
    else:
        print("Constraint is VIOLATED.")
