# Devin/modules/quantum_tools.py
# Purpose: A high-level facade that orchestrates Devin's quantum-computing,
#          post-quantum-cryptography, and quantum-pentesting toolkits into a
#          single, agent-friendly interface.

import base64
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Import the low-level quantum tools this facade will manage ---
# Every one of these underlying modules already guards its own optional
# third-party dependency (qiskit, oqs, pykyber, ...) with try/except
# ImportError internally and only raises when the *class* is instantiated,
# never on import -- but we guard the imports here too in case a whole
# submodule is missing/renamed, so a bad path can never take the facade
# (and, via main.py, the whole assistant) down with it.

_QUANTUM_ROOT = Path(__file__).resolve().parent.parent / "quantum"


def _load_module_from_path(module_name: str, file_path: Path):
    """
    Loads a module directly from a file path via importlib, bypassing
    normal dotted-path package resolution.

    This is needed because `quantum/post_quantum_crypto.py` (a module) and
    `quantum/post_quantum_crypto/` (a directory containing
    crystal_kyber_integration.py and quantum_vault.py) share the same name.
    Python's import system resolves `quantum.post_quantum_crypto` to the
    *file*, which shadows the directory -- so `quantum.post_quantum_crypto
    .crystal_kyber_integration` is unreachable via a normal dotted import
    ("'quantum.post_quantum_crypto' is not a package"). This pre-existing
    naming collision lives in the directory layout, not in any one file, so
    it's worked around here rather than by renaming/moving repo files.
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


try:
    from quantum.optimization.quantum_computing import QuantumComputer
    _HAS_QUANTUM_COMPUTING_MOD = True
except ImportError:
    _HAS_QUANTUM_COMPUTING_MOD = False

try:
    from quantum.optimization.annealing_scheduler import AnnealingScheduler, Task
    _HAS_ANNEALING_MOD = True
except ImportError:
    _HAS_ANNEALING_MOD = False

try:
    from quantum.optimization.qml_models import QML_Modeler
    _HAS_QML_MOD = True
except ImportError:
    _HAS_QML_MOD = False

try:
    from quantum.post_quantum_crypto import PostQuantumCrypto
    _HAS_PQC_MOD = True
except ImportError:
    _HAS_PQC_MOD = False

try:
    _kyber_integration_mod = _load_module_from_path(
        "devin_quantum_crystal_kyber_integration",
        _QUANTUM_ROOT / "post_quantum_crypto" / "crystal_kyber_integration.py",
    )
    KyberKEM = _kyber_integration_mod.KyberKEM
    _HAS_KYBER_MOD = True
except (ImportError, FileNotFoundError, AttributeError):
    _HAS_KYBER_MOD = False

try:
    _quantum_vault_mod = _load_module_from_path(
        "devin_quantum_vault", _QUANTUM_ROOT / "post_quantum_crypto" / "quantum_vault.py"
    )
    QuantumVault = _quantum_vault_mod.QuantumVault
    _HAS_VAULT_MOD = True
except (ImportError, FileNotFoundError, AttributeError):
    _HAS_VAULT_MOD = False
except BaseException:
    # A broken/mismatched native build of the 'cryptography' wheel can raise
    # a pyo3 PanicException here -- a BaseException, not an Exception -- on
    # import rather than a clean ImportError. That's a third-party binary
    # install problem, not a code bug, but a single bad optional dependency
    # must never be allowed to crash facade construction (and, via main.py,
    # the whole assistant), so it's caught this broadly only around this one
    # optional, isolated load.
    _HAS_VAULT_MOD = False

try:
    from quantum.quantum_pentesting.shors_algorithm_sim import ShorSimulator
    _HAS_SHOR_MOD = True
except ImportError:
    _HAS_SHOR_MOD = False

try:
    from quantum.quantum_pentesting.quantum_sidechannel_detector import (
        ClassicalCryptoProcess,
        QuantumSensorSimulator,
    )
    _HAS_SIDECHANNEL_MOD = True
except ImportError:
    _HAS_SIDECHANNEL_MOD = False

# Configure basic logging
logger = logging.getLogger("QuantumFacade")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


def _b64e(data: bytes) -> str:
    """Encodes raw bytes as a base64 string (JSON/tool-call friendly)."""
    return base64.b64encode(data).decode("ascii")


def _b64d(data: str) -> bytes:
    """Decodes a base64 string back into raw bytes."""
    return base64.b64decode(data.encode("ascii"))


class QuantumFacade:
    """
    A single, simplified interface to Devin's quantum toolchain: circuit
    simulation, quantum-inspired optimization, quantum machine learning,
    post-quantum cryptography, and quantum-pentesting simulations.

    Every capability degrades gracefully: if its underlying optional
    dependency (qiskit, qiskit-aer, qiskit-machine-learning, liboqs-python,
    pykyber, ...) is not installed, the corresponding component is simply
    disabled (logged as a warning) and its methods return None / an error
    dict instead of raising and taking down the whole facade.
    """

    def __init__(self):
        # --- Qiskit-based circuit simulator ---
        self.quantum_computer: Optional["QuantumComputer"] = None
        if _HAS_QUANTUM_COMPUTING_MOD:
            try:
                self.quantum_computer = QuantumComputer()
            except ImportError as e:
                logger.warning(f"Quantum circuit simulation unavailable: {e}")
        else:
            logger.warning("quantum.optimization.quantum_computing module not found; circuit simulation disabled.")

        # --- Classical simulated-annealing scheduler (pure Python, no optional deps) ---
        self._annealing_available = _HAS_ANNEALING_MOD
        if not self._annealing_available:
            logger.warning("quantum.optimization.annealing_scheduler module not found; task scheduling disabled.")

        # --- Quantum machine learning (VQC) ---
        self.qml_modeler: Optional["QML_Modeler"] = None
        if _HAS_QML_MOD:
            try:
                self.qml_modeler = QML_Modeler()
            except ImportError as e:
                logger.warning(f"Quantum machine learning unavailable: {e}")
        else:
            logger.warning("quantum.optimization.qml_models module not found; QML disabled.")

        # --- Post-quantum cryptography (liboqs-python / 'oqs') -- the real,
        # working PQC backend. It supports Kyber (KEM) and Dilithium/Falcon
        # (signatures) natively, so this is the recommended path for any
        # real Kyber usage -- see KyberFacade note below.
        self.pqc: Optional["PostQuantumCrypto"] = None
        if _HAS_PQC_MOD:
            try:
                self.pqc = PostQuantumCrypto()
            except ImportError as e:
                logger.warning(f"Post-quantum crypto (liboqs) unavailable: {e}")
        else:
            logger.warning("quantum.post_quantum_crypto module not found; PQC disabled.")

        # --- Standalone CRYSTALS-Kyber wrapper ---
        # NOTE: as shipped, this module imports `from kyber import ...`. The
        # only PyPI package literally named "kyber" is an unrelated, decade-old
        # Confluence space-exporter -- not a cryptography library -- so this
        # import will fail even after `pip install kyber`. The real Rust-based
        # Kyber implementation on PyPI is published as `pykyber` (module name
        # `pykyber`), but even that package's API (`Kyber768()` constructor +
        # `.encapsulate`/`.decapsulate` staticmethods) does not match the
        # `.keygen()/.enc()/.dec()` calls this file makes. In practice this
        # component will stay disabled with any published package; use
        # `pqc_*` methods with algorithm="Kyber768" instead for real,
        # working Kyber via liboqs.
        self.kyber: Optional["KyberKEM"] = None
        if _HAS_KYBER_MOD:
            try:
                self.kyber = KyberKEM()
            except ImportError as e:
                logger.warning(f"Standalone Kyber wrapper unavailable (see module docstring): {e}")
        else:
            logger.warning("quantum.post_quantum_crypto.crystal_kyber_integration module not found; disabled.")

        # --- Hybrid Kyber+AES vault (depends on the standalone Kyber wrapper above) ---
        self._vault_available = _HAS_VAULT_MOD
        if not self._vault_available:
            logger.warning("quantum.post_quantum_crypto.quantum_vault module not found; vault disabled.")
        # Vault instances are opened per-path on demand (see vault_* methods),
        # so we don't eagerly construct one here.
        self._vault_cache: Dict[str, "QuantumVault"] = {}

        # --- Shor's algorithm simulator ---
        # NOTE: this depends on `qiskit.algorithms.Shor`, which was removed
        # from modern Qiskit (it was deprecated then dropped when Qiskit
        # Terra's `algorithms` module was slimmed down). Even with
        # qiskit/qiskit-aer installed, this will typically still be
        # unavailable unless an old, pinned Qiskit version is used
        # specifically for this feature -- it degrades gracefully either way.
        self.shor_simulator: Optional["ShorSimulator"] = None
        if _HAS_SHOR_MOD:
            try:
                self.shor_simulator = ShorSimulator()
            except ImportError as e:
                logger.warning(f"Shor's algorithm simulator unavailable: {e}")
        else:
            logger.warning("quantum.quantum_pentesting.shors_algorithm_sim module not found; disabled.")

        # --- Quantum-inspired side-channel analysis (pure numpy, always available) ---
        self._sidechannel_available = _HAS_SIDECHANNEL_MOD
        if not self._sidechannel_available:
            logger.warning("quantum.quantum_pentesting.quantum_sidechannel_detector module not found; disabled.")

        logger.info("QuantumFacade initialized.")

    # ------------------------------------------------------------------
    # Circuit simulation (Qiskit)
    # ------------------------------------------------------------------

    def run_bell_state_demo(self, shots: int = 1024) -> Optional[Dict[str, int]]:
        """
        Builds and simulates a 2-qubit Bell (entangled) state circuit.

        Args:
            shots: Number of times to run the simulated circuit.

        Returns:
            A dict of measured bitstring -> count (roughly 50/50 '00'/'11'),
            or None if qiskit/qiskit-aer are not installed.
        """
        if not self.quantum_computer:
            logger.error("Circuit simulation unavailable (qiskit not installed).")
            return None
        circuit = self.quantum_computer.create_bell_state_circuit()
        return self.quantum_computer.simulate(circuit, shots=shots)

    def run_ghz_state_demo(self, num_qubits: int = 3, shots: int = 1024) -> Optional[Dict[str, int]]:
        """
        Builds and simulates a multi-qubit GHZ entangled state circuit.

        Args:
            num_qubits: Number of qubits in the GHZ state (>= 2).
            shots: Number of times to run the simulated circuit.

        Returns:
            A dict of measured bitstring -> count, or None if unavailable.
        """
        if not self.quantum_computer:
            logger.error("Circuit simulation unavailable (qiskit not installed).")
            return None
        circuit = self.quantum_computer.create_ghz_state_circuit(num_qubits)
        return self.quantum_computer.simulate(circuit, shots=shots)

    def run_qft_demo(self, num_qubits: int = 4, shots: int = 1024) -> Optional[Dict[str, int]]:
        """
        Builds and simulates a Quantum Fourier Transform circuit.

        Args:
            num_qubits: Number of qubits to transform.
            shots: Number of times to run the simulated circuit.

        Returns:
            A dict of measured bitstring -> count, or None if unavailable.
        """
        if not self.quantum_computer:
            logger.error("Circuit simulation unavailable (qiskit not installed).")
            return None
        circuit = self.quantum_computer.create_qft_circuit(num_qubits)
        return self.quantum_computer.simulate(circuit, shots=shots)

    def draw_bell_circuit(self) -> Optional[str]:
        """Returns a text diagram of a Bell-state circuit, or None if unavailable."""
        if not self.quantum_computer:
            return None
        return self.quantum_computer.draw_circuit(self.quantum_computer.create_bell_state_circuit())

    # ------------------------------------------------------------------
    # Quantum-inspired classical optimization (simulated annealing)
    # ------------------------------------------------------------------

    def solve_task_schedule(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: Dict[str, List[str]],
        initial_temp: float = 1000.0,
        cooling_rate: float = 0.995,
        max_iterations: int = 5000,
    ) -> Optional[Dict[str, Any]]:
        """
        Finds a near-optimal task execution order using simulated annealing.

        This is pure classical Python -- no optional third-party dependency
        is required, so it is always available.

        Args:
            tasks: List of {"id": str, "duration": int} dicts.
            dependencies: Map of task_id -> list of prerequisite task_ids.
            initial_temp: Starting annealing temperature.
            cooling_rate: Per-iteration temperature decay factor (0 < rate < 1).
            max_iterations: Number of annealing iterations to run.

        Returns:
            {"schedule": [...], "makespan": int}, or None on error
            (e.g. a cyclic dependency or unknown task id).
        """
        if not self._annealing_available:
            logger.error("Task scheduling unavailable (annealing_scheduler module missing).")
            return None
        try:
            task_objs = [Task(id=t["id"], duration=int(t["duration"])) for t in tasks]
            scheduler = AnnealingScheduler(task_objs, dependencies)
            schedule, makespan = scheduler.solve(initial_temp, cooling_rate, max_iterations)
            return {"schedule": schedule, "makespan": makespan}
        except Exception as e:
            logger.error(f"Task scheduling failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Quantum machine learning
    # ------------------------------------------------------------------

    def train_quantum_classifier(
        self,
        features: List[List[float]],
        labels: List[int],
        num_qubits: int,
        num_layers: int = 2,
    ) -> Optional[Dict[str, float]]:
        """
        Trains and evaluates a Variational Quantum Classifier (VQC) on the
        given dataset.

        Args:
            features: A list of feature vectors (each of length num_qubits).
            labels: A list of integer class labels, one per feature vector.
            num_qubits: Number of qubits to use (should match feature length).
            num_layers: Number of layers in the variational ansatz.

        Returns:
            {"train_accuracy": float, "test_accuracy": float}, or None if
            qiskit-machine-learning/scikit-learn are not installed.
        """
        if not self.qml_modeler:
            logger.error("QML unavailable (qiskit-machine-learning not installed).")
            return None
        try:
            import numpy as np
            vqc = self.qml_modeler.create_vqc(num_qubits=num_qubits, num_layers=num_layers)
            train_acc, test_acc = self.qml_modeler.train_and_evaluate(
                vqc, np.array(features), np.array(labels)
            )
            return {"train_accuracy": float(train_acc), "test_accuracy": float(test_acc)}
        except Exception as e:
            logger.error(f"QML training failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Post-quantum cryptography (liboqs / 'oqs') -- the real, working PQC backend
    # ------------------------------------------------------------------

    def list_supported_pqc_algorithms(self) -> Optional[Dict[str, List[str]]]:
        """Lists the KEM and signature algorithms enabled in this liboqs build."""
        if not self.pqc:
            logger.error("Post-quantum crypto unavailable (liboqs-python not installed).")
            return None
        return {"kems": list(self.pqc.supported_kems), "signatures": list(self.pqc.supported_sigs)}

    def pqc_generate_kem_keypair(self, algorithm: str = "Kyber768") -> Optional[Dict[str, str]]:
        """
        Generates a post-quantum KEM keypair (e.g. Kyber768).

        Returns:
            {"public_key": base64 str, "secret_key": base64 str}, or None on failure.
        """
        if not self.pqc:
            logger.error("Post-quantum crypto unavailable (liboqs-python not installed).")
            return None
        result = self.pqc.kem_generate_keypair(algorithm)
        if not result:
            return None
        public_key, secret_key = result
        return {"public_key": _b64e(public_key), "secret_key": _b64e(secret_key)}

    def pqc_kem_encapsulate(self, algorithm: str, public_key_b64: str) -> Optional[Dict[str, str]]:
        """
        Encapsulates a fresh shared secret for the given public key (client side).

        Returns:
            {"ciphertext": base64 str, "shared_secret": base64 str}, or None on failure.
        """
        if not self.pqc:
            logger.error("Post-quantum crypto unavailable (liboqs-python not installed).")
            return None
        result = self.pqc.kem_encapsulate_secret(algorithm, _b64d(public_key_b64))
        if not result:
            return None
        ciphertext, shared_secret = result
        return {"ciphertext": _b64e(ciphertext), "shared_secret": _b64e(shared_secret)}

    def pqc_kem_decapsulate(self, algorithm: str, secret_key_b64: str, ciphertext_b64: str) -> Optional[str]:
        """
        Decapsulates a ciphertext to recover the shared secret (server side).

        Returns:
            The shared secret as a base64 string, or None on failure.
        """
        if not self.pqc:
            logger.error("Post-quantum crypto unavailable (liboqs-python not installed).")
            return None
        shared_secret = self.pqc.kem_decapsulate_secret(algorithm, _b64d(secret_key_b64), _b64d(ciphertext_b64))
        return _b64e(shared_secret) if shared_secret else None

    def pqc_generate_signature_keypair(self, algorithm: str = "Dilithium3") -> Optional[Dict[str, str]]:
        """Generates a post-quantum digital-signature keypair (e.g. Dilithium3)."""
        if not self.pqc:
            logger.error("Post-quantum crypto unavailable (liboqs-python not installed).")
            return None
        result = self.pqc.signature_generate_keypair(algorithm)
        if not result:
            return None
        public_key, secret_key = result
        return {"public_key": _b64e(public_key), "secret_key": _b64e(secret_key)}

    def pqc_sign_message(self, algorithm: str, secret_key_b64: str, message: str) -> Optional[str]:
        """Signs a UTF-8 message with a post-quantum secret key. Returns a base64 signature."""
        if not self.pqc:
            logger.error("Post-quantum crypto unavailable (liboqs-python not installed).")
            return None
        signature = self.pqc.signature_sign_message(algorithm, _b64d(secret_key_b64), message.encode("utf-8"))
        return _b64e(signature) if signature else None

    def pqc_verify_signature(self, algorithm: str, public_key_b64: str, message: str, signature_b64: str) -> bool:
        """Verifies a base64-encoded post-quantum signature against a UTF-8 message."""
        if not self.pqc:
            logger.error("Post-quantum crypto unavailable (liboqs-python not installed).")
            return False
        return self.pqc.signature_verify(
            algorithm, _b64d(public_key_b64), message.encode("utf-8"), _b64d(signature_b64)
        )

    # ------------------------------------------------------------------
    # Standalone CRYSTALS-Kyber wrapper + hybrid vault
    # (see the __init__ note above -- effectively always unavailable with
    #  published packages; prefer pqc_* with algorithm="Kyber768" above)
    # ------------------------------------------------------------------

    def kyber_generate_keypair(self) -> Optional[Dict[str, str]]:
        """Generates a Kyber keypair via the standalone wrapper, if available."""
        if not self.kyber:
            logger.error("Standalone Kyber wrapper unavailable; use pqc_generate_kem_keypair('Kyber768') instead.")
            return None
        public_key, private_key = self.kyber.generate_keypair()
        return {"public_key": _b64e(public_key), "private_key": _b64e(private_key)}

    def vault_store_secret(self, vault_path: str, public_key_b64: str, item_name: str, item_value: str) -> bool:
        """
        Encrypts and stores a secret in a hybrid Kyber+AES-GCM vault file.

        NOTE: requires the standalone Kyber wrapper (see __init__ note);
        practically always unavailable with published packages today.
        """
        if not self._vault_available:
            logger.error("Quantum vault unavailable (quantum_vault module missing).")
            return False
        try:
            vault = self._get_vault(vault_path)
            if not vault:
                return False
            vault.add_item(_b64d(public_key_b64), item_name, item_value)
            return True
        except Exception as e:
            logger.error(f"Vault store failed: {e}")
            return False

    def vault_retrieve_secret(self, vault_path: str, private_key_b64: str, item_name: str) -> Optional[str]:
        """Retrieves and decrypts a secret from a hybrid Kyber+AES-GCM vault file."""
        if not self._vault_available:
            logger.error("Quantum vault unavailable (quantum_vault module missing).")
            return None
        try:
            vault = self._get_vault(vault_path)
            if not vault:
                return None
            return vault.get_item(_b64d(private_key_b64), item_name)
        except Exception as e:
            logger.error(f"Vault retrieve failed: {e}")
            return None

    def _get_vault(self, vault_path: str) -> Optional["QuantumVault"]:
        """Internal: lazily opens (and caches) a QuantumVault for a given path."""
        if vault_path in self._vault_cache:
            return self._vault_cache[vault_path]
        try:
            vault = QuantumVault(vault_path=Path(vault_path))
            self._vault_cache[vault_path] = vault
            return vault
        except ImportError as e:
            logger.error(f"Cannot open vault: {e}")
            return None

    # ------------------------------------------------------------------
    # Quantum-pentesting simulations (educational/analysis only -- these
    # operate on toy/simulated inputs the caller supplies, never on
    # real-world cryptographic material or third-party systems)
    # ------------------------------------------------------------------

    def factor_number_shor(self, n: int) -> Optional[List[int]]:
        """
        Attempts to factor a small integer using a simulation of Shor's
        algorithm, to demonstrate the concept behind the quantum threat to
        RSA-style cryptography. Limited to small N (<= 21) because
        simulating a real quantum computer classically is exponentially
        expensive.

        Returns:
            The prime factors of n, or None if factoring failed/was
            infeasible, or if qiskit's Shor implementation isn't available
            (it was removed from modern Qiskit -- see __init__ note).
        """
        if not self.shor_simulator:
            logger.error("Shor's algorithm simulator unavailable.")
            return None
        return self.shor_simulator.factor(n)

    def simulate_sidechannel_attack(
        self,
        secret_exponent: int,
        base: int = 7,
        modulus: int = 57,
        noise_level: float = 2.5,
        num_traces: int = 5000,
    ) -> Optional[Dict[str, Any]]:
        """
        Simulates recovering the bit pattern of a secret exponent from a
        noisy "square-and-multiply" side-channel trace, demonstrating how
        timing/power side channels can leak cryptographic secrets. All
        inputs are toy values supplied by the caller -- no real system or
        cryptographic key is touched.

        Args:
            secret_exponent: The (simulated) secret exponent to leak.
            base: Base used in the modular exponentiation.
            modulus: Modulus used in the modular exponentiation.
            noise_level: Standard deviation of simulated sensor noise.
            num_traces: Number of noisy traces to average over.

        Returns:
            {"true_operations": [...], "deduced_operations": [...],
             "recovered_match": bool}, or None if unavailable.
        """
        if not self._sidechannel_available:
            logger.error("Side-channel simulator unavailable.")
            return None
        try:
            process = ClassicalCryptoProcess(secret_key=secret_exponent)
            sensor = QuantumSensorSimulator(noise_level=noise_level)
            _, true_operations = process.square_and_multiply(base=base, modulus=modulus)
            true_signal = sensor._generate_true_signal(true_operations)
            recovered_signal = sensor.recover_signal_by_averaging(true_signal, num_traces=num_traces)
            deduced_operations = sensor.deduce_operations(recovered_signal)
            return {
                "true_operations": true_operations,
                "deduced_operations": deduced_operations,
                "recovered_match": true_operations == deduced_operations,
            }
        except Exception as e:
            logger.error(f"Side-channel simulation failed: {e}")
            return None


# --- Example Usage ---
if __name__ == "__main__":
    import json

    print("=========================================================")
    print("=== Quantum Facade Demo ===")
    print("=========================================================")

    facade = QuantumFacade()

    print("\n--- Classical task scheduling (always available) ---")
    result = facade.solve_task_schedule(
        tasks=[{"id": "A", "duration": 5}, {"id": "B", "duration": 3}],
        dependencies={"B": ["A"]},
        max_iterations=200,
    )
    print(json.dumps(result, indent=2))

    print("\n--- Side-channel simulation (always available) ---")
    sc_result = facade.simulate_sidechannel_attack(secret_exponent=13, num_traces=200)
    print(json.dumps(sc_result, indent=2))

    print("\n--- PQC algorithm listing (requires liboqs-python) ---")
    print(facade.list_supported_pqc_algorithms())

    print("\n=========================================================")
    print("=== Quantum Facade Demo Complete ===")
    print("=========================================================")
