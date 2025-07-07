# Nexus: A Chemical Engineering Simulation and Analysis Framework

Nexus is a Python-based framework for chemical process simulation, optimization, and analysis. It provides a flexible and extensible platform for modeling complex chemical processes, performing economic and life cycle assessments, and optimizing process designs under uncertainty.

## Key Features

- **Modular Flowsheeting:** Build process flowsheets by connecting unit operations in a modular and intuitive way.
- **Extensible Unit Operations:** A library of common unit operations (e.g., CSTR) and the ability to create custom models.
- **Property & Reaction Packages:** Define components, thermodynamic properties, and reaction kinetics.
- **Process Optimization:** Optimize process variables to minimize costs or environmental impact using gradient-based and other optimization algorithms.
- **Sustainability Analysis:** Integrated tools for Techno-Economic Analysis (TEA) and Life Cycle Assessment (LCA).
- **Uncertainty Quantification:** Analyze the effect of parameter uncertainty on process performance using Monte Carlo simulation.
- **Digital Twin Capabilities:** Includes modules for real-time data interfacing, model adaptation, and visualization.

## Project Structure

The repository is organized into the following main directories:

- `nexus/`: The main source code for the framework.
  - `nexus_core/`: Core components for simulation (solvers, unit operations, properties, kinetics).
  - `optimization/`: Tools for process optimization.
  - `sustainability/`: Modules for TEA and LCA.
  - `digital_twin/`: Components for creating digital twins of chemical processes.
  - `ml_suite/`: Tools for integrating machine learning models.
- `data/`: Example data and data generation scripts.
- `tests/`: Unit and integration tests.

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/deluair/ChE.git
    cd ChE
    ```

2.  Install the required dependencies:
    ```bash
    pip install -r nexus/requirements.txt
    ```

## Usage Example

Here is a simple example of how to build a flowsheet, run a simulation, and perform an economic analysis.

```python
from nexus.nexus_core.solver.flowsheet import Flowsheet, SequentialModularSolver
from nexus.nexus_core.models.unit_operations import CSTR
from nexus.nexus_core.properties.property_models import PropertyPackage, Component
from nexus.nexus_core.kinetics.kinetics import PowerLawReaction
from nexus.sustainability.economics.calculator import EconomicCalculator

# 1. Define components, properties, and reaction
prop_pkg = PropertyPackage(components=[
    Component('Ethanol', 'C2H6O'),
    Component('Water', 'H2O'),
    Component('Product', 'Prod', mw=100)
])
reaction = PowerLawReaction('r1', {'Ethanol': -1, 'Product': 1}, lambda T: 0.1, {'Ethanol': 1})

# 2. Build the flowsheet
fs = Flowsheet(name='SimpleReactionProcess')
reactor = CSTR(name='R-101', volume=20, prop_pkg=prop_pkg, reaction=reaction)
fs.add_unit(reactor)

# 3. Define the feed stream
fs.streams['feed_stream'] = {
    'flow_rate': 0.1,
    'temperature': 353,
    'composition': {'Ethanol': 0.8, 'Water': 0.2, 'Product': 0.0}
}

# 4. Connect the units
fs.connect('feed_stream', None, 'R-101') # Feed stream connects to the reactor

# 5. Solve the flowsheet
solver = SequentialModularSolver(flowsheet=fs)
solver.solve()

# 6. Run economic analysis
tea_calculator = EconomicCalculator(fs)
economic_summary = tea_calculator.run_analysis()

print(f"Reactor Outlet Composition: {fs.streams['R-101_outlet']['composition']}")
print(f"Total Annualized Cost: ${economic_summary['TotalAnnualCost']:,.2f}/year")
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
