# Devin/recovery/quantum_self_repair/error_correction.py
# Purpose: A simulation of a basic Quantum Error Correction (QEC) code
#          (the 3-qubit bit-flip code) to demonstrate quantum self-repair.

import logging
from typing import Optional, List

try:
    import numpy as np
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_aer import AerSimulator
    from qiskit import transpile
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("QuantumErrorCorrection")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class QuantumErrorCorrector:
    """
    Simulates the 3-qubit bit-flip Quantum Error Correction code.
    """
    def __init__(self):
        if not QISKIT_AVAILABLE:
            raise ImportError("Qiskit is required. Please run 'pip install qiskit qiskit-aer'")
        self.simulator = AerSimulator()
        logger.info("Quantum Error Corrector initialized with local AerSimulator.")

    def _create_bit_flip_circuit(self, initial_state: List[float], error_qubit: Optional[int]) -> QuantumCircuit:
        """Constructs the full circuit for the bit-flip code demonstration."""
        
        # We need 3 qubits for the code, and 2 ancillary qubits for syndrome measurement
        data_qubits = QuantumRegister(3, name='data')
        ancilla_qubits = QuantumRegister(2, name='ancilla')
        # A classical register to store the syndrome measurement
        classical_bits = ClassicalRegister(2, name='syndrome')
        
        qc = QuantumCircuit(data_qubits, ancilla_qubits, classical_bits)

        # 1. Initialize the logical qubit (data[0]) to the desired state
        qc.initialize(initial_state, [data_qubits[0]])
        qc.barrier()

        # 2. ENCODING: Entangle the 3 data qubits
        # Encodes α|0⟩ + β|1⟩  into  α|000⟩ + β|111⟩
        qc.cx(data_qubits[0], data_qubits[1])
        qc.cx(data_qubits[0], data_qubits[2])
        qc.barrier()

        # 3. ERROR SIMULATION: Introduce a bit-flip (X gate) on a chosen qubit
        if error_qubit is not None:
            logger.warning(f"Simulating a bit-flip error on data qubit {error_qubit}...")
            qc.x(data_qubits[error_qubit])
            qc.barrier()

        # 4. ERROR DETECTION (Syndrome Measurement)
        # Compare qubits and store parity information in the ancillas
        qc.cx(data_qubits[0], ancilla_qubits[0])
        qc.cx(data_qubits[1], ancilla_qubits[0])
        qc.cx(data_qubits[1], ancilla_qubits[1])
        qc.cx(data_qubits[2], ancilla_qubits[1])
        qc.barrier()
        # Measure the ancillas to get the error syndrome
        qc.measure(ancilla_qubits, classical_bits)
        qc.barrier()
        
        # 5. CORRECTION: Apply a correction based on the syndrome measurement
        # If syndrome is '01', qubit 2 flipped.
        # If syndrome is '10', qubit 0 flipped.
        # If syndrome is '11', qubit 1 flipped.
        # If syndrome is '00', no error occurred.
        qc.x(data_qubits[2]).c_if(classical_bits, 1) # c_if(register, value)
        qc.x(data_qubits[0]).c_if(classical_bits, 2)
        qc.x(data_qubits[1]).c_if(classical_bits, 3)
        qc.barrier()
        
        return qc

    def run_correction_demo(self, error_qubit: Optional[int] = None):
        """
        Runs the full simulation: encode, corrupt, detect, correct, and verify.
        """
        # We'll test the recovery of the |1> state.
        # Initial state vector for |1> is [0, 1]
        initial_state_vector = [0, 1]
        
        circuit = self._create_bit_flip_circuit(initial_state_vector, error_qubit)
        
        # Add a final measurement of the logical qubit to verify the result
        final_measurement = ClassicalRegister(1, name='final_result')
        circuit.add_register(final_measurement)
        
        # DECODING: Reverse the encoding process to recover the state
        circuit.cx(data_qubits[0], data_qubits[2])
        circuit.cx(data_qubits[0], data_qubits[1])
        circuit.measure(data_qubits[0], final_measurement[0])
        
        print("\n--- Full Quantum Circuit Diagram ---")
        print(circuit.draw(output='text'))
        
        # Simulate the circuit
        logger.info("Simulating the full QEC circuit...")
        compiled_circuit = transpile(circuit, self.simulator)
        job = self.simulator.run(compiled_circuit, shots=1024)
        result = job.result()
        counts = result.get_counts()
        
        print("\n--- Simulation Results ---")
        print(counts)
        return counts

# --- Example Usage ---
if __name__ == "__main__":
    if not QISKIT_AVAILABLE:
        print("\nERROR: Qiskit is not installed. Please run: pip install qiskit qiskit-aer")
    else:
        print("=========================================================")
        print("=== Quantum Error Correction Simulator ⚛️⚕️ ===")
        print("=========================================================")
        
        corrector = QuantumErrorCorrector()
        
        # --- Demo 1: No error ---
        print("\n\n--- DEMO 1: No Error ---")
        print("Simulating the circuit with no errors. The final state should be '1'.")
        no_error_counts = corrector.run_correction_demo(error_qubit=None)
        # Results are formatted as 'final_result syndrome_bits'. We expect '1 00'.
        assert '1 00' in no_error_counts and len(no_error_counts) == 1
        
        # --- Demo 2: Error on qubit 1 ---
        print("\n\n--- DEMO 2: Error on Data Qubit 1 ---")
        print("Simulating a bit-flip on qubit 1. The code should detect and correct it.")
        error_1_counts = corrector.run_correction_demo(error_qubit=1)
        # We expect the syndrome to be '11' (binary for 3) and the final result to be '1'.
        assert '1 11' in error_1_counts and len(error_1_counts) == 1

        # --- Demo 3: Error on qubit 2 ---
        print("\n\n--- DEMO 3: Error on Data Qubit 2 ---")
        print("Simulating a bit-flip on qubit 2. The code should detect and correct it.")
        error_2_counts = corrector.run_correction_demo(error_qubit=2)
        # We expect the syndrome to be '01' (binary for 1) and the final result to be '1'.
        assert '1 01' in error_2_counts and len(error_2_counts) == 1

        print("\n\n[SUCCESS] All demonstrations showed successful error correction.")
        print("The final logical state was perfectly recovered in all cases.")

        print("\n=========================================================")
        print("=== Quantum Error Correction Demo Complete ===")
        print("=========================================================")
