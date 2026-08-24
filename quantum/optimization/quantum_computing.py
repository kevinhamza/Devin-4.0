# Devin/quantum/optimization/quantum_computing.py
# Purpose: A general-purpose toolkit for building, simulating, and
#          visualizing fundamental quantum circuits using Qiskit.

# Defers evaluation of type annotations (e.g. the `QuantumCircuit` return
# hints below) so the class can still be *defined* when qiskit isn't
# installed -- only instantiating QuantumComputer() requires it. Without
# this, merely importing this module without qiskit raises NameError on the
# annotations, breaking the try/except ImportError degradation pattern below.
from __future__ import annotations

import logging
from typing import Dict, Optional

try:
    import numpy as np
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from qiskit.circuit.library import QFT
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("QuantumComputer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class QuantumComputer:
    """
    A simulated quantum computer for building and running quantum circuits.
    """
    def __init__(self):
        if not QISKIT_AVAILABLE:
            raise ImportError("Qiskit is not installed. Please run 'pip install qiskit[visualization] qiskit-aer'")
        
        # Initialize a high-performance local simulator
        self.simulator = AerSimulator()
        logger.info("QuantumComputer simulator initialized.")

    def create_bell_state_circuit(self) -> QuantumCircuit:
        """
        Creates a quantum circuit to generate a Bell state (a simple entangled state).
        This state is 1/sqrt(2) * (|00> + |11>).
        """
        logger.info("Creating Bell State circuit...")
        # Create a circuit with 2 qubits and 2 classical bits for measurement
        qc = QuantumCircuit(2, 2)
        # Apply a Hadamard gate to the first qubit to create superposition
        qc.h(0)
        # Apply a Controlled-NOT (CNOT) gate to entangle the two qubits
        qc.cx(0, 1)
        # Map the quantum measurement to the classical bits
        qc.measure([0, 1], [0, 1])
        return qc

    def create_ghz_state_circuit(self, num_qubits: int) -> QuantumCircuit:
        """
        Creates a circuit to generate a Greenberger-Horne-Zeilinger (GHZ) state.
        This is a multi-qubit entangled state: 1/sqrt(2) * (|00...0> + |11...1>).
        """
        if num_qubits < 2:
            raise ValueError("GHZ state requires at least 2 qubits.")
        logger.info(f"Creating {num_qubits}-qubit GHZ State circuit...")
        qc = QuantumCircuit(num_qubits, num_qubits)
        # Put the first qubit into superposition
        qc.h(0)
        # Cascade CNOT gates to entangle all other qubits with the first one
        for i in range(1, num_qubits):
            qc.cx(0, i)
        qc.measure(range(num_qubits), range(num_qubits))
        return qc
        
    def create_qft_circuit(self, num_qubits: int) -> QuantumCircuit:
        """
        Creates a Quantum Fourier Transform (QFT) circuit.
        """
        logger.info(f"Creating {num_qubits}-qubit Quantum Fourier Transform (QFT) circuit...")
        # Use Qiskit's built-in QFT circuit library for convenience
        qft_circuit = QFT(num_qubits=num_qubits, do_swaps=True).decompose()
        qft_circuit.measure_all()
        return qft_circuit

    def simulate(self, circuit: QuantumCircuit, shots: int = 1024) -> Dict[str, int]:
        """
        Simulates a quantum circuit and returns the measurement counts.
        """
        logger.info(f"Simulating circuit with {shots} shots...")
        # Transpile the circuit for the simulator for better performance
        compiled_circuit = transpile(circuit, self.simulator)
        # Execute the job
        job = self.simulator.run(compiled_circuit, shots=shots)
        result = job.result()
        counts = result.get_counts(compiled_circuit)
        logger.info(f"Simulation complete. Results: {counts}")
        return counts

    def draw_circuit(self, circuit: QuantumCircuit) -> str:
        """
        Generates a text-based drawing of the quantum circuit.
        """
        return circuit.draw(output='text').text

# --- Example Usage ---
if __name__ == "__main__":
    if not QISKIT_AVAILABLE:
        print("\nERROR: Qiskit is not installed. Please run: pip install qiskit[visualization] qiskit-aer")
    else:
        print("=========================================================")
        print("=== Fundamental Quantum Computing Prototype ⚛️⚙️ ===")
        print("=========================================================")
        
        qc = QuantumComputer()
        
        # --- 1. Bell State (Entanglement) Demo ---
        print("\n--- 1. Bell State Demo ---")
        bell_circuit = qc.create_bell_state_circuit()
        
        print("Circuit Diagram:")
        print(qc.draw_circuit(bell_circuit))
        
        print("Simulation Results (should be approx. 50% '00' and 50% '11'):")
        bell_counts = qc.simulate(bell_circuit)
        print(bell_counts)
        
        # --- 2. GHZ State (Multi-Qubit Entanglement) Demo ---
        print("\n\n--- 2. 3-Qubit GHZ State Demo ---")
        ghz_circuit = qc.create_ghz_state_circuit(3)
        
        print("Circuit Diagram:")
        print(qc.draw_circuit(ghz_circuit))

        print("Simulation Results (should be approx. 50% '000' and 50% '111'):")
        ghz_counts = qc.simulate(ghz_circuit)
        print(ghz_counts)
        
        # --- 3. Quantum Fourier Transform (QFT) Demo ---
        print("\n\n--- 3. 4-Qubit QFT Circuit Demo ---")
        qft_circuit = qc.create_qft_circuit(4)
        print("Circuit Diagram for a more complex algorithm (QFT):")
        print(qc.draw_circuit(qft_circuit))


        print("\n=========================================================")
        print("=== Quantum Computing Prototype Complete ===")
        print("=========================================================")
