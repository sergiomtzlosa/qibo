"""Test that Qibo matplotlib drawer"""

import pytest
from qibo import Circuit, gates
from qibo.ui import plot_circuit

# defining a dummy circuit
def circuit(nqubits=2):
    c = Circuit(nqubits)
    c.add(gates.H(0))
    c.add(gates.CNOT(0, 1))
    c.add(gates.M(0))
    c.add(gates.M(1))
    return c

def test_plot_circuit():
    circ = circuit()
    assert plot_circuit(circ) == plot_circuit(circ)