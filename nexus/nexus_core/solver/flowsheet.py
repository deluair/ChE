from collections import deque

class Flowsheet:
    """Manages unit operations, streams, and their connectivity."""
    def __init__(self, name):
        self.name = name
        self.unit_ops = {}
        self.streams = {}
        self._connections = []

    def add_unit(self, unit):
        """Adds a unit operation to the flowsheet."""
        if unit.name in self.unit_ops:
            raise ValueError(f"Unit '{unit.name}' already exists in the flowsheet.")
        self.unit_ops[unit.name] = unit

    def connect(self, stream_name, source_unit_name, dest_unit_name):
        """Connects two units with a stream."""
        if source_unit_name not in self.unit_ops or dest_unit_name not in self.unit_ops:
            raise ValueError("Source or destination unit not found in flowsheet.")
        
        source_unit = self.unit_ops[source_unit_name]
        dest_unit = self.unit_ops[dest_unit_name]
        
        # If stream already exists, use it. Otherwise, create a new blank one.
        if stream_name in self.streams:
            stream_data = self.streams[stream_name]
        else:
            stream_data = {'name': stream_name, 'composition': {}, 'temperature': None, 'pressure': None}
            self.streams[stream_name] = stream_data

        # Link the stream data object to the unit's inlets/outlets
        source_unit.add_outlet(stream_data)
        dest_unit.add_inlet(stream_data)
        self._connections.append((source_unit_name, dest_unit_name))

class SequentialModularSolver:
    """Solves the flowsheet using a sequential modular approach with topological sort."""
    def __init__(self, flowsheet):
        self.flowsheet = flowsheet

    def _topological_sort(self):
        """Determines the calculation order of units and detects cycles."""
        in_degree = {u: 0 for u in self.flowsheet.unit_ops}
        adj = {u: [] for u in self.flowsheet.unit_ops}
        for src, dest in self.flowsheet._connections:
            adj[src].append(dest)
            in_degree[dest] += 1

        queue = deque([u for u, d in in_degree.items() if d == 0])
        sorted_order = []
        
        while queue:
            u = queue.popleft()
            sorted_order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        if len(sorted_order) != len(self.flowsheet.unit_ops):
            raise RuntimeError("Cycle detected in the flowsheet! Recycle solver not yet implemented.")
        
        return sorted_order

    def solve(self):
        """Executes the solve method for each unit in a topologically sorted order."""
        print(f"--- Solving Flowsheet: {self.flowsheet.name} ---")
        try:
            calculation_order = self._topological_sort()
            print("Calculation order determined:", ' -> '.join(calculation_order))
        except RuntimeError as e:
            print(f"Error: {e}")
            return

        for unit_name in calculation_order:
            unit = self.flowsheet.unit_ops[unit_name]
            print(f"Solving unit: {unit.name}")
            try:
                unit.solve()
            except Exception as e:
                print(f"ERROR solving unit '{unit.name}': {e}")
                # Stop solving if a unit fails
                return
        print("--- Flowsheet solution complete. ---")

# Example Usage:
if __name__ == '__main__':
    # Import necessary classes
    from nexus.nexus_core.models.unit_operations import CSTR, UnitOperation
    from nexus.nexus_core.properties.property_models import PropertyPackage, Component
    from nexus.nexus_core.kinetics.kinetics import PowerLawReaction
    import numpy as np

    # 1. Define a dummy separator for demonstration
    class Separator(UnitOperation):
        def solve(self):
            inlet = self.inlets[0]
            # Split ethanol and water
            self.outlets[0]['composition'] = {'Ethanol': inlet['composition'].get('Ethanol', 0) * 0.99, 'Water': inlet['composition'].get('Water', 0) * 0.01}
            self.outlets[1]['composition'] = {'Ethanol': inlet['composition'].get('Ethanol', 0) * 0.01, 'Water': inlet['composition'].get('Water', 0) * 0.99}
            for out in self.outlets:
                out.update({k: v for k, v in inlet.items() if k != 'composition'})
            print(f"Separator '{self.name}' solved.")

    # 2. Setup flowsheet
    fs = Flowsheet(name='Process with Separator')

    # 3. Setup components, properties, and reaction
    prop_pkg = PropertyPackage(components=[Component('Ethanol', 'C2H6O'), Component('Water', 'H2O')])
    reaction = PowerLawReaction('r1', {'Ethanol': -1, 'Product': 1}, lambda T: 0.1, {'Ethanol': 1})

    # 4. Create and add unit operations
    feed_unit = UnitOperation(name='Feed') # Use base class for feed/product sinks
    reactor = CSTR(name='R-101', volume=10, prop_pkg=prop_pkg, reaction=reaction)
    separator = Separator(name='S-101')
    product_unit = UnitOperation(name='Product')
    waste_unit = UnitOperation(name='Waste')
    
    for unit in [feed_unit, reactor, separator, product_unit, waste_unit]:
        fs.add_unit(unit)

    # 5. Define feed stream and connect units
    fs.streams['feed'] = {'flow_rate': 0.1, 'temperature': 353, 'composition': {'Ethanol': 0.8, 'Water': 0.2}}
    feed_unit.add_outlet(fs.streams['feed'])
    
    fs.connect('s1', 'Feed', 'R-101')
    fs.connect('s2', 'R-101', 'S-101')
    fs.connect('s3', 'S-101', 'Product') # Product stream
    fs.connect('s4', 'S-101', 'Waste') # Waste stream

    # 6. Create a solver and solve the flowsheet
    solver = SequentialModularSolver(flowsheet=fs)
    solver.solve()

    # 7. Display results
    print("\n--- Results ---")
    print("Product Stream Composition:", fs.streams['s3']['composition'])
    print("Waste Stream Composition:", fs.streams['s4']['composition'])

    # 8. Example of a flowsheet with a cycle
    print("\n--- Testing Cycle Detection ---")
    fs_cycle = Flowsheet(name='Recycle Process')
    fs_cycle.add_unit(UnitOperation(name='A'))
    fs_cycle.add_unit(UnitOperation(name='B'))
    fs_cycle.connect('c1', 'A', 'B')
    fs_cycle.connect('c2', 'B', 'A') # This creates a recycle loop
    cycle_solver = SequentialModularSolver(flowsheet=fs_cycle)
    cycle_solver.solve()
