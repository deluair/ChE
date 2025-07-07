import CoolProp.CoolProp as CP

class Component:
    """Represents a single chemical component with its properties."""
    def __init__(self, name, formula, mw=None):
        self.name = name
        self.formula = formula
        if mw is not None:
            self.mw = mw
        else:
            try:
                self.mw = CP.PropsSI('M', name) * 1000  # Molar mass in g/mol
            except ValueError:
                raise ValueError(f"Could not find molecular weight for '{name}'. "
                                 f"Please provide it manually using the 'mw' argument "
                                 f"for pseudo-components.")

class PropertyPackage:
    """Handles thermodynamic and transport property calculations for a mixture."""
    def __init__(self, components):
        self.components = {comp.name: comp for comp in components}
        self.component_names = list(self.components.keys())

    def get_properties(self, temp, press, composition):
        """
        Calculate thermodynamic properties for a given state.

        Args:
            temp (float): Temperature in Kelvin.
            press (float): Pressure in Pascals.
            composition (dict): Mole fractions of components.

        Returns:
            dict: A dictionary of calculated properties.
        """
        # Ensure composition keys match component names
        if set(composition.keys()) != set(self.component_names):
            raise ValueError("Composition keys must match component names.")

        # For simplicity, this example calculates properties for the first component.
        # A real implementation would handle mixtures.
        main_component = self.component_names[0]
        
        properties = {
            'temperature': temp,
            'pressure': press,
            'density': CP.PropsSI('D', 'T', temp, 'P', press, main_component),
            'enthalpy': CP.PropsSI('H', 'T', temp, 'P', press, main_component),
            'entropy': CP.PropsSI('S', 'T', temp, 'P', press, main_component),
            'viscosity': CP.PropsSI('V', 'T', temp, 'P', press, main_component),
        }
        return properties

# Example Usage:
if __name__ == '__main__':
    # Define components
    water = Component('Water', 'H2O')
    ethanol = Component('Ethanol', 'C2H6O')

    # Create a property package
    prop_pkg = PropertyPackage(components=[water, ethanol])

    # Define process conditions
    temp = 353.15  # 80 C
    press = 101325  # 1 atm
    composition = {'Water': 0.5, 'Ethanol': 0.5}

    # Get properties
    state_properties = prop_pkg.get_properties(temp, press, composition)

    print(f"Properties at {temp} K and {press} Pa:")
    for key, value in state_properties.items():
        print(f"  {key}: {value:.4f}")
