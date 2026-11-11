# pushquantum

A minimal template for compiling circuits for a zoned neutral-atom architecture. It includes:

- a custom Qiskit `move` instruction for AOD row/column moves;
- an `Architecture` that loads its zones from a stored file, together with the initial positions of the qubits;
- a template entry point, `compile_circuit(circuit, architecture_spec) -> (circuit, architecture)`.

Your compiled circuit is checked by a separate validator package (`pushquantum-validator`). It checks that every move and gate follows the rules below, and that the circuit is equivalent to the input.

## Setup

```bash
uv sync
```

## Architecture

The default architecture is stored in [src/pushquantum/architectures/default.json](src/pushquantum/architectures/default.json):

| Zone       | x     | y       | Allowed gates |
|------------|-------|---------|---------------|
| storage    | 0 – 9 | 0 – 9   | `rx`, `rz`    |
| entangling | 0 – 9 | 10 – 19 | `cz`          |

`measure`, `barrier` and `move` are allowed anywhere.

**Geometry.** Row and column indices are shared by all zones, so `cols=(0, 1)` covers columns 0 and 1 in storage and in the entangling zone alike. Physical positions come from each zone's geometry:

- **Storage:** sites are evenly spaced, `spacing` 1.0 apart.
- **Entangling:** columns form interaction pairs (0, 1), (2, 3), …. The two sites of a pair are 0.3 apart and pairs repeat every 2.0, so columns sit at x = 0, 0.3, 2, 2.3, 4, 4.3, …. In the file this is `"pairs": {"axis": "x", "distance": 0.3}`.

Two consequences follow from the pairs:

- **`cz` only act within a pair:** both atoms must be on the same row, in columns 2k and 2k+1.

The initial loading maps each qubit to its starting `(x, y)` site. Every site must be in storage; the validator checks this.

```python
from pushquantum import Architecture

arch = Architecture({0: (0, 0), 1: (1, 0)})  # or Architecture(loading, spec="my_arch.json")
arch.zones  # zone definitions (bounds, allowed gates, geometry)
arch.initial_loading  # qubit -> starting site
```

## Moves

A move uses one AOD pair. It selects `rows` (y) and `cols` (x), and every atom on a rows × cols intersection moves to the matching `new_rows` × `new_cols` intersection. You also list the qubits being moved.

```python
from qiskit import QuantumCircuit
import pushquantum  # registers QuantumCircuit.move

qc = QuantumCircuit(2)
qc.rx(0.5, 0)
qc.move([0, 1], rows=0, cols=(0, 1), new_rows=10, new_cols=(0, 1))  # into the entangling zone
qc.cz(0, 1)
qc.move([0, 1], rows=10, cols=(0, 1), new_rows=0, new_cols=(0, 1))  # back to storage
```

Rows and columns follow these rules, each axis on its own:

- **Pickup** (`rows`, `cols`): must be **contiguous** and ascending, e.g. `cols=(0, 1, 2, 3)`.
- **Drop-off** (`new_rows`, `new_cols`): the exact final coordinates of the moved atoms, ascending 
- **Proportional spacing** (a warning): every gap between drop-off lines should equal the matching gap between the source lines, times one common factor. With all picked-up lines kept, the source is contiguous, so the drop-off should be evenly spaced, e.g. `(0, 1, 2, 3) -> (0, 2, 4, 6)`. Moves that break this are still allowed; the validator logs a warning, counts it and doubles that move's time.
- **Dropping empty lines**: the drop-off may list *fewer* lines than the pickup. Selected rows/columns with no atom on them are then removed, and the remaining occupied lines must map one-to-one and proportionally onto the drop-off lines. With atoms on columns `0, 1, 4` of `range(5)` (gaps 1, 3):
  - `(0, 2, 8)` works (gaps ×2);
  - `(0, 1, 2)` and `(0, 2, 4)` are allowed but logged, because the gaps don't scale evenly.

```python
# pick up 4 adjacent atoms on row 0 and spread them out on row 10
qc.move([0, 1, 2, 3], rows=0, cols=(0, 1, 2, 3), new_rows=10, new_cols=(0, 2, 4, 6))
# reverse it: atoms on columns 0, 2, 4, 6 of row 10 -> columns 0..3 of row 0 (gaps x1/2)
qc.move([0, 1, 2, 3], rows=10, cols=range(7), new_rows=0, new_cols=(0, 1, 2, 3))
```

A move is rejected when:

- **the pickup isn't contiguous**, e.g. `cols=(0, 2)`;
- **the drop-off has more lines than the pickup**, or, after dropping empty lines, the number of occupied lines differs from the number of drop-off lines;
- **the drop-off reorders lines**, e.g. the permutation `(0, 1) -> (2, 0)`;
- **the atoms at the intersections are not exactly the listed qubits**: an unlisted atom would be picked up (a ghost), or a listed qubit isn't at an intersection;
- **it drops an atom onto an occupied site**, i.e. one held by an atom that isn't part of this move;
- **a target lies outside every zone**.

A `move` leaves the quantum state unchanged, so its definition is the identity.

## Template

Write your compilation in `compile_circuit(circuit, architecture_spec)` in [src/pushquantum/template.py](src/pushquantum/template.py). It returns the compiled circuit and an `Architecture(initial_loading, spec=architecture_spec)` holding your initial loading. 