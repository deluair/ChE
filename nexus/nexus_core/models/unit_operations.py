import numpy as np
from nexus.nexus_core.properties.property_models import PropertyPackage, Component
from nexus.nexus_core.kinetics.kinetics import PowerLawReaction

class UnitOperation:
    """Base class for all unit operations in the flowsheet."""
    def __init__(self, name):
        self.name = name
        self.inlets = []
        self.outlets = []

    def add_inlet(self, stream):
        self.inlets.append(stream)

    def add_outlet(self, stream):
        self.outlets.append(stream)

    def solve(self):
        """Default solve method for simple passthrough units.
        Copies inlet properties to all outlets.
        """
        if not self.inlets:
            # Source unit (like a feed) - outlets are already defined
            return

        if len(self.inlets) > 1:
            print(f"Warning: Default solve for unit '{self.name}' uses only the first inlet.")

        inlet_stream = self.inlets[0]
        for outlet_stream in self.outlets:
            outlet_stream.update(inlet_stream)

class CSTR(UnitOperation):
    """Represents a Continuous Stirred-Tank Reactor using a kinetic model."""
    def __init__(self, name, volume, prop_pkg, reaction):
        super().__init__(name)
        self.volume = volume  # in m^3
        self.prop_pkg = prop_pkg
        self.reaction = reaction

    def solve(self):
        """Solves the CSTR mass balance using the provided reaction kinetics."""
        inlet_stream = self.inlets[0]
        outlet_stream = self.outlets[0]

        # For simplicity, we assume concentrations are equivalent to mole fractions.
        # A rigorous model would use activities and handle density changes.
        # --- Normalise inlet composition to ensure it sums to 1.0 and is non-negative ---
        inlet_comp = inlet_stream['composition'].copy()
        total_inlet = sum(max(v, 0.0) for v in inlet_comp.values())
        if total_inlet == 0:
            raise ValueError("Inlet composition cannot be all zeros.")
        if not np.isclose(total_inlet, 1.0):
            inlet_comp = {k: max(v, 0.0) / total_inlet for k, v in inlet_comp.items()}
            inlet_stream['composition'] = inlet_comp
        temp = inlet_stream['temperature']
        inlet_flow = inlet_stream['flow_rate']
        tau = self.volume / inlet_flow # Residence time

        # This is a simplified iterative solver for a single reaction.
        # A real solver would handle multiple reactions and be more robust.
        # We are solving C_A_in - C_A_out - tau * rate = 0
        # Let's assume the reactant is the first one in the stoichiometry dict
        main_reactant = next(iter(self.reaction.reactants))
        
        # Initial guess for outlet composition is the inlet composition
        outlet_comp = inlet_comp.copy()

        # Simple fixed-point iteration to find outlet concentration
        for _ in range(10): # Iterate a few times to converge
            rate = self.reaction.get_rate(outlet_comp, temp)
            C_A_in = inlet_comp[main_reactant]
            C_A_out = C_A_in / (1 + tau * rate / max(C_A_in, 1e-12))  # avoid div-by-zero
            # Clamp to physical bounds [0, C_A_in]
            C_A_out = max(0.0, min(C_A_out, C_A_in))
            outlet_comp[main_reactant] = C_A_out

            # Update other components based on stoichiometry
            for comp, stoich_coeff in self.reaction.stoichiometry.items():
                if comp != main_reactant:
                    # This is a simplification. A real model tracks moles.
                    delta = (C_A_in - C_A_out) * (-stoich_coeff)
                    outlet_comp[comp] = max(0.0, inlet_comp.get(comp, 0) + delta)

        # Renormalise outlet composition to sum to 1.0
        total_out = sum(outlet_comp.values())
        if total_out == 0:
            raise ValueError("Outlet composition collapsed to zero.")
        outlet_comp = {k: v / total_out for k, v in outlet_comp.items()}

        # Update outlet stream
        outlet_stream.update(inlet_stream)
        outlet_stream['composition'] = outlet_comp

        # Clamp conversion to [0, 1]
        conversion = (inlet_comp[main_reactant] - outlet_comp[main_reactant]) / inlet_comp[main_reactant]
        conversion = max(0.0, min(conversion, 1.0))
        print(f"CSTR '{self.name}' solved with conversion: {conversion:.2%}")

# Example Usage:
if __name__ == '__main__':
    # 1. Define components and property package
    water = Component('Water', 'H2O')
    ethanol = Component('Ethanol', 'C2H6O')
    prop_pkg = PropertyPackage(components=[water, ethanol])

    # 2. Define the reaction (Ethanol -> Product)
    stoich = {'Ethanol': -1, 'Product': 1}
    def arrhenius_k(T):
        return 0.1 * np.exp(5000 * (1/350 - 1/T)) # Simple Arrhenius
    reactants = {'Ethanol': 1}
    reaction = PowerLawReaction('Ethanol_Oxidation', stoich, arrhenius_k, reactants)

    # 3. Create a CSTR instance with the reaction
    reactor = CSTR(name='R-101', volume=10, prop_pkg=prop_pkg, reaction=reaction)

    # 4. Define inlet and outlet streams
    inlet_stream = {
        'flow_rate': 0.1,  # m^3/s
        'temperature': 353.15, # 80 C
        'pressure': 101325,
        'composition': {'Ethanol': 0.8, 'Water': 0.2, 'Product': 0.0}
    }
    outlet_stream = inlet_stream.copy()

    # 5. Connect streams to the unit operation
    reactor.add_inlet(inlet_stream)
    reactor.add_outlet(outlet_stream)

    # 6. Solve the unit operation
    reactor.solve()

    # 7. Display results
    print("\nInlet Composition:", inlet_stream['composition'])
    print("Outlet Composition:", outlet_stream['composition'])
