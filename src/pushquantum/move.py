"""The `move` instruction: one AOD pair moves every atom at `rows` x `cols` to `new_rows` x `new_cols`.

Importing this module adds `QuantumCircuit.move`. See the README for the rules.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from numbers import Integral
from typing import TYPE_CHECKING

from qiskit.circuit import Instruction, QuantumCircuit, Qubit

if TYPE_CHECKING:
    from qiskit.circuit import InstructionSet

Site = tuple[int, int]


def _as_lines(values: int | Sequence[int], name: str) -> tuple[int, ...]:
    items = [values] if isinstance(values, Integral) else list(values)
    if not items:
        msg = f"`{name}` must not be empty."
        raise ValueError(msg)
    if not all(isinstance(v, Integral) for v in items):
        msg = f"`{name}` must contain integers, got {items!r}."
        raise ValueError(msg)
    result = tuple(int(v) for v in items)
    if len(set(result)) != len(result):
        msg = f"`{name}` must not contain duplicates, got {result!r}."
        raise ValueError(msg)
    return result


def _check_lines(start: tuple[int, ...], end: tuple[int, ...], name: str) -> None:
    if len(end) > len(start):
        msg = f"`new_{name}` cannot have more lines than `{name}`, got {len(end)} and {len(start)}."
        raise ValueError(msg)
    contiguous = tuple(range(start[0], start[0] + len(start)))
    if start != contiguous:
        msg = f"Picked-up {name} {start} must be contiguous and ascending, e.g. {contiguous}."
        raise ValueError(msg)
    if any(b <= a for a, b in itertools.pairwise(end)):
        msg = f"Target {name} {end} must be ascending: the order of {name} is preserved."
        raise ValueError(msg)


class Move(Instruction):
    """Params are `(rows, cols, new_rows, new_cols)`, tuples of ints; rows are y, columns are x."""

    def __init__(
        self,
        rows: int | Sequence[int],
        cols: int | Sequence[int],
        new_rows: int | Sequence[int],
        new_cols: int | Sequence[int],
        num_qubits: int,
    ) -> None:
        names = ("rows", "cols", "new_rows", "new_cols")
        lines = [_as_lines(v, n) for v, n in zip((rows, cols, new_rows, new_cols), names, strict=True)]
        _check_lines(lines[0], lines[2], "rows")
        _check_lines(lines[1], lines[3], "cols")
        if num_qubits < 1:
            msg = "A move must act on at least one qubit."
            raise ValueError(msg)
        super().__init__("move", num_qubits, 0, lines)

    rows = property(lambda self: self.params[0])
    cols = property(lambda self: self.params[1])
    new_rows = property(lambda self: self.params[2])
    new_cols = property(lambda self: self.params[3])

    def validate_parameter(self, parameter: object) -> tuple[int, ...]:
        if isinstance(parameter, tuple) and all(isinstance(v, Integral) for v in parameter):
            return parameter
        msg = f"Move params must be tuples of ints, got {parameter!r}."
        raise TypeError(msg)

    def _define(self) -> None:
        self.definition = QuantumCircuit(self.num_qubits, name=self.name)  # identity


def move(
    self: QuantumCircuit,
    qubits: int | Qubit | Sequence[int | Qubit],
    rows: int | Sequence[int],
    cols: int | Sequence[int],
    new_rows: int | Sequence[int],
    new_cols: int | Sequence[int],
) -> InstructionSet:
    """Appends a `Move` of the atoms at `rows` x `cols`, which must be exactly `qubits`."""
    qubit_list = [qubits] if isinstance(qubits, (int, Qubit)) else list(qubits)
    return self.append(Move(rows, cols, new_rows, new_cols, len(qubit_list)), qubit_list)


QuantumCircuit.move = move  # type: ignore[attr-defined]
