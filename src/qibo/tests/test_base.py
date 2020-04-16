"""
Test imports and basic functionality that is indepedent of calculation backend.
"""
import numpy as np
from qibo.models import *
from qibo.gates import *


def test_circuit_sanity():
    """Check if the number of qbits is preserved."""
    c = Circuit(2)
    assert c.nqubits == 2
    assert c.size == 2


def test_importing_qibo():
    """Checks accessing `models` and `gates` from `qibo`."""
    import qibo
    c = qibo.models.Circuit(2)
    c.add(qibo.gates.H(0))
    assert c.nqubits == 2
    assert c.depth == 1


def test_importing_qibo():
    """Checks importing `models` and `gates`."""
    from qibo import models, gates
    c = models.Circuit(2)
    c.add(gates.H(0))
    assert c.nqubits == 2
    assert c.depth == 1


def test_circuit_add():
    """Check if circuit depth increases with the add method."""
    c = Circuit(2)
    c.add(H(0))
    c.add(H(1))
    c.add(CNOT(0, 1))
    assert c.depth == 3


def test_circuit_add_iterable():
    """Check if `circuit.add` works with iterables."""
    c = Circuit(2)
    # Try adding list
    c.add([H(0), H(1), CNOT(0, 1)])
    assert c.depth == 3
    assert isinstance(c.queue[-1], CNOT)
    # Try adding tuple
    c.add((H(0), H(1), CNOT(0, 1)))
    assert c.depth == 6
    assert isinstance(c.queue[-1], CNOT)


def test_circuit_add_generator():
    """Check if `circuit.add` works with generators."""
    def gen():
        yield H(0)
        yield H(1)
        yield CNOT(0, 1)
    c = Circuit(2)
    c.add(gen())
    assert c.depth == 3
    assert isinstance(c.queue[-1], CNOT)


def test_circuit_addition():
    """Check if circuit addition increases depth."""
    c1 = Circuit(2)
    c1.add(H(0))
    c1.add(H(1))
    assert c1.depth == 2

    c2 = Circuit(2)
    c2.add(CNOT(0, 1))
    assert c2.depth == 1

    c3 = c1 + c2
    assert c3.depth == 3