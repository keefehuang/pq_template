"""Write your compiler here. The validator checks the result against the input (moves are identity)."""

from __future__ import annotations

from qiskit import QuantumCircuit, transpile

import pushquantum.move  # noqa: F401 -- registers QuantumCircuit.move
from pushquantum.architecture import Architecture, ArchitectureSpec


def compile_circuit(
    circuit: QuantumCircuit, architecture_spec: ArchitectureSpec
) -> tuple[QuantumCircuit, Architecture]:
    """Returns the compiled circuit and the `Architecture` (zones of `architecture_spec`, your initial loading)."""
    # TODO: implement your compilation here.
    num_qubits = circuit.num_qubits
    # Transpile to native gates (rx, rz, cz) with no optimization. This is a placeholder for your
    # transpilation logic.
    native = transpile(circuit, basis_gates=["rx", "rz", "cz"], optimization_level=0)

    compiled = native.copy_empty_like()
    # for _instruction in native.data:
    # add movements here
    # pass

    # Determine your initial loading;
    # naive_loading = {i: pushquantum.move.Site(0, i) for i in range(num_qubits)}
    # architecture = Architecture(naive_loading, spec=architecture_spec)
    return compiled, architecture
