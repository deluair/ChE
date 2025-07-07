import numpy as np

class Reaction:
    """Base class for a chemical reaction."""
    def __init__(self, name, stoichiometry):
        self.name = name
        self.stoichiometry = stoichiometry

    def get_rate(self, composition, temperature):
        """Calculates the rate of reaction."""
        raise NotImplementedError("get_rate() must be implemented by subclasses.")

class PowerLawReaction(Reaction):
    """Represents a reaction following a power-law rate expression."""
    def __init__(self, name, stoichiometry, rate_constant_func, reactants):
        """
        Args:
            name (str): Name of the reaction.
            stoichiometry (dict): Stoichiometric coefficients (negative for reactants).
            rate_constant_func (callable): A function that takes temperature (K) and returns the rate constant (k).
            reactants (dict): A dictionary mapping reactant names to their reaction order.
        """
        super().__init__(name, stoichiometry)
        self.rate_constant_func = rate_constant_func
        self.reactants = reactants

    def get_rate(self, composition, temperature):
        """
        Calculates the reaction rate based on the power-law model.
        Rate = k(T) * Product(C_i^order_i)
        """
        k = self.rate_constant_func(temperature)
        rate = k
        for reactant, order in self.reactants.items():
            if reactant not in composition:
                raise ValueError(f"Reactant '{reactant}' not found in composition.")
            rate *= composition[reactant] ** order
        return rate

# Example Usage:
if __name__ == '__main__':
    # Define a simple first-order reaction A -> B
    # Stoichiometry: -1 for A, +1 for B
    stoich = {'A': -1, 'B': 1}

    # Use Arrhenius equation for the rate constant: k = A * exp(-Ea / (R * T))
    def arrhenius_k(T):
        A = 1e10  # Pre-exponential factor
        Ea = 7e4   # Activation energy (J/mol)
        R = 8.314  # Gas constant
        return A * np.exp(-Ea / (R * T))

    # Define the reactants and their orders
    reactants_orders = {'A': 1}

    # Create the reaction object
    reaction = PowerLawReaction(
        name='A_to_B',
        stoichiometry=stoich,
        rate_constant_func=arrhenius_k,
        reactants=reactants_orders
    )

    # Define process conditions
    temp = 350  # K
    composition = {'A': 0.5, 'B': 0.1, 'Solvent': 0.4} # Molar concentrations

    # Calculate the rate
    rate = reaction.get_rate(composition, temp)

    print(f"Reaction: {reaction.name}")
    print(f"Rate at {temp} K: {rate:.6f} mol/L*s")
