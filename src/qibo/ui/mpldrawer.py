# Some functions in MPLDrawer are from code provided by Rick Muller
# Simplified Plotting Routines for Quantum Circuits
# https://github.com/rpmuller/PlotQCircuit
#
import json
from os import path

import matplotlib
import numpy as np

from qibo import gates

from .FusedGateBarrier import FusedEndGateBarrier, FusedStartGateBarrier

STYLE = {}
SYMBOLS = {}

plot_params = {
    "scale": 1.0,
    "fontsize": 14.0,
    "linewidth": 1.0,
    "control_radius": 0.05,
    "not_radius": 0.15,
    "swap_delta": 0.08,
    "label_buffer": 0.0,
    "facecolor": "w",
    "edgecolor": "#000000",
    "fillcolor": "#000000",
    "linecolor": "k",
    "textcolor": "k",
    "gatecolor": "w",
    "controlcolor": "#000000",
}


def _plot_quantum_schedule(schedule, inits, labels=[], plot_labels=True, **kwargs):
    """Use Matplotlib to plot a quantum circuit.
    schedule  List of time steps, each containing a sequence of gates during that step.
              Each gate is a tuple containing (name,target,control1,control2...).
              Targets and controls initially defined in terms of labels.
    inits     Initialization list of gates
    labels    List of qubit labels, optional

    kwargs    Can override plot_parameters
    """
    plot_params.update(kwargs)
    scale = plot_params["scale"]

    # Create labels from gates. This will become slow if there are a lot
    #  of gates, in which case move to an ordered dictionary
    if not labels:
        labels = []
        for i, gate in _enumerate_gates(schedule, schedule=True):
            for label in gate[1:]:
                if label not in labels:
                    labels.append(label)

    nq = len(labels)
    nt = len(schedule)
    wire_grid = np.arange(0.0, nq * scale, scale, dtype=float)
    gate_grid = np.arange(0.0, nt * scale, scale, dtype=float)

    ax, _ = _setup_figure(nq, nt, gate_grid, wire_grid, plot_params)

    measured = _measured_wires(schedule, labels, schedule=True)
    _draw_wires(ax, nq, gate_grid, wire_grid, plot_params, measured)

    if plot_labels:
        _draw_labels(ax, labels, inits, gate_grid, wire_grid, plot_params)

    _draw_gates(
        ax, schedule, labels, gate_grid, wire_grid, plot_params, measured, schedule=True
    )
    return ax


def _plot_quantum_circuit(gates, inits, labels=[], plot_labels=True, **kwargs):
    """Use Matplotlib to plot a quantum circuit.
    gates     List of tuples for each gate in the quantum circuit.
              (name,target,control1,control2...). Targets and controls initially
              defined in terms of labels.
    inits     Initialization list of gates
    labels    List of qubit labels. optional

    kwargs    Can override plot_parameters
    """
    plot_params.update(kwargs)
    scale = plot_params["scale"]

    # Create labels from gates. This will become slow if there are a lot
    #  of gates, in which case move to an ordered dictionary
    if not labels:
        labels = []
        for i, gate in _enumerate_gates(gates):
            for label in gate[1:]:
                if label not in labels:
                    labels.append(label)

    nq = len(labels)
    ng = len(gates)
    wire_grid = np.arange(0.0, nq * scale, scale, dtype=float)
    gate_grid = np.arange(0.0, ng * scale, scale, dtype=float)

    ax, _ = _setup_figure(nq, ng, gate_grid, wire_grid, plot_params)

    measured = _measured_wires(gates, labels)
    _draw_wires(ax, nq, gate_grid, wire_grid, plot_params, measured)

    if plot_labels:
        _draw_labels(ax, labels, inits, gate_grid, wire_grid, plot_params)

    _draw_gates(ax, gates, labels, gate_grid, wire_grid, plot_params, measured)
    return ax


def _plot_lines_circuit(inits, labels, plot_labels=True, **kwargs):
    """Use Matplotlib to plot a quantum circuit.
    inits     Initialization list of gates
    labels    List of qubit labels

    kwargs    Can override plot_parameters
    """

    plot_params.update(kwargs)
    scale = plot_params["scale"]

    nq = len(labels)

    wire_grid = np.arange(0.0, nq * scale, scale, dtype=float)
    gate_grid = np.arange(0.0, nq * scale, scale, dtype=float)

    ax, _ = _setup_figure(nq, nq, gate_grid, wire_grid, plot_params)

    _draw_wires(ax, nq, gate_grid, wire_grid, plot_params)

    if plot_labels:
        _draw_labels(ax, labels, inits, gate_grid, wire_grid, plot_params)

    return ax


def _enumerate_gates(l, schedule=False):
    "Enumerate the gates in a way that can take l as either a list of gates or a schedule"
    if schedule:
        for i, gates in enumerate(l):
            for gate in gates:
                yield i, gate
    else:
        for i, gate in enumerate(l):
            yield i, gate


def _measured_wires(l, labels, schedule=False):
    "measured[i] = j means wire i is measured at step j"
    measured = {}
    for i, gate in _enumerate_gates(l, schedule=schedule):
        name, target = gate[:2]
        j = _get_flipped_index(target, labels)
        if name.startswith("M"):
            measured[j] = i
    return measured


def _draw_gates(
    ax, l, labels, gate_grid, wire_grid, plot_params, measured={}, schedule=False
):
    for i, gate in _enumerate_gates(l, schedule=schedule):
        _draw_target(ax, i, gate, labels, gate_grid, wire_grid, plot_params)
        if len(gate) > 2:  # Controlled
            _draw_controls(
                ax, i, gate, labels, gate_grid, wire_grid, plot_params, measured
            )


def _draw_controls(ax, i, gate, labels, gate_grid, wire_grid, plot_params, measured={}):

    name, target = gate[:2]

    if "FUSEDENDGATEBARRIER" in name:
        return

    linewidth = plot_params["linewidth"]
    scale = plot_params["scale"]
    control_radius = plot_params["control_radius"]

    target_index = _get_flipped_index(target, labels)
    controls = gate[2:]
    control_indices = _get_flipped_indices(controls, labels)
    gate_indices = control_indices + [target_index]
    min_wire = min(gate_indices)
    max_wire = max(gate_indices)

    if "FUSEDSTARTGATEBARRIER" in name:
        equal_qbits = False
        if "@EQUAL" in name:
            name = name.replace("@EQUAL", "")
            equal_qbits = True
        nfused = int(name.replace("FUSEDSTARTGATEBARRIER", ""))
        dx_right = 0.30
        dx_left = 0.30
        dy = 0.25
        _rectangle(
            ax,
            gate_grid[i + 1] - dx_left,
            gate_grid[i + nfused] + dx_right,
            wire_grid[min_wire] - dy - (0 if not equal_qbits else -0.9 * scale),
            wire_grid[max_wire] + dy,
            plot_params,
        )
    else:

        _line(
            ax,
            gate_grid[i],
            gate_grid[i],
            wire_grid[min_wire],
            wire_grid[max_wire],
            plot_params,
        )
        ismeasured = False
        for index in control_indices:
            if measured.get(index, 1000) < i:
                ismeasured = True
        if ismeasured:
            dy = 0.04  # TODO: put in plot_params
            _line(
                ax,
                gate_grid[i] + dy,
                gate_grid[i] + dy,
                wire_grid[min_wire],
                wire_grid[max_wire],
                plot_params,
            )

        for ci in control_indices:
            x = gate_grid[i]
            y = wire_grid[ci]

            is_dagger = False
            if name[-2:] == "DG":
                name = name.replace("DG", "")
                is_dagger = True

            if name == "SWAP":
                _swapx(ax, x, y, plot_params)
            elif name in [
                "ISWAP",
                "SISWAP",
                "FSWAP",
                "FSIM",
                "SYC",
                "GENERALIZEDFSIM",
                "RXX",
                "RYY",
                "RZZ",
                "RZX",
                "RXXYY",
                "G",
                "RBS",
                "ECR",
                "MS",
            ]:

                symbol = SYMBOLS.get(name, name)

                if is_dagger:
                    symbol += r"$\rm{^{\dagger}}$"

                _text(ax, x, y, symbol, plot_params, box=True)

            else:
                _cdot(ax, x, y, plot_params)


def _draw_target(ax, i, gate, labels, gate_grid, wire_grid, plot_params):
    name, target = gate[:2]

    if "FUSEDSTARTGATEBARRIER" in name or "FUSEDENDGATEBARRIER" in name:
        return

    is_dagger = False
    if name[-2:] == "DG":
        name = name.replace("DG", "")
        is_dagger = True

    symbol = SYMBOLS.get(name, name)  # override name with symbols

    if is_dagger:
        symbol += r"$\rm{^{\dagger}}$"

    x = gate_grid[i]
    target_index = _get_flipped_index(target, labels)
    y = wire_grid[target_index]
    if not symbol:
        return
    if name in ["CNOT", "TOFFOLI"]:
        _oplus(ax, x, y, plot_params)
    elif name == "CPHASE":
        _cdot(ax, x, y, plot_params)
    elif name == "SWAP":
        _swapx(ax, x, y, plot_params)
    else:
        if name == "ALIGN":
            symbol = "A({})".format(target[2:])
        _text(ax, x, y, symbol, plot_params, box=True)


def _line(ax, x1, x2, y1, y2, plot_params):
    Line2D = matplotlib.lines.Line2D
    line = Line2D(
        (x1, x2), (y1, y2), color=plot_params["linecolor"], lw=plot_params["linewidth"]
    )
    ax.add_line(line)


def _text(ax, x, y, textstr, plot_params, box=False):
    linewidth = plot_params["linewidth"]
    fontsize = (
        12.0
        if _check_list_str(["dagger", "sqrt"], textstr)
        else plot_params["fontsize"]
    )

    if box:
        bbox = dict(
            ec=plot_params["edgecolor"],
            fc=plot_params["gatecolor"],
            fill=True,
            lw=linewidth,
        )
    else:
        bbox = dict(fill=False, lw=0)
    ax.text(
        x,
        y,
        textstr,
        color=plot_params["textcolor"],
        ha="center",
        va="center",
        bbox=bbox,
        size=fontsize,
    )


def _oplus(ax, x, y, plot_params):
    Line2D = matplotlib.lines.Line2D
    Circle = matplotlib.patches.Circle
    not_radius = plot_params["not_radius"]
    linewidth = plot_params["linewidth"]
    c = Circle(
        (x, y),
        not_radius,
        ec=plot_params["edgecolor"],
        fc=plot_params["gatecolor"],
        fill=True,
        lw=linewidth,
    )
    ax.add_patch(c)
    _line(ax, x, x, y - not_radius, y + not_radius, plot_params)


def _cdot(ax, x, y, plot_params):
    Circle = matplotlib.patches.Circle
    control_radius = plot_params["control_radius"]
    scale = plot_params["scale"]
    linewidth = plot_params["linewidth"]
    c = Circle(
        (x, y),
        control_radius * scale,
        ec=plot_params["edgecolor"],
        fc=plot_params["controlcolor"],
        fill=True,
        lw=linewidth,
    )
    ax.add_patch(c)


def _swapx(ax, x, y, plot_params):
    d = plot_params["swap_delta"]
    linewidth = plot_params["linewidth"]
    _line(ax, x - d, x + d, y - d, y + d, plot_params)
    _line(ax, x - d, x + d, y + d, y - d, plot_params)


def _setup_figure(nq, ng, gate_grid, wire_grid, plot_params):
    scale = plot_params["scale"]
    fig = matplotlib.pyplot.figure(
        figsize=(ng * scale, nq * scale),
        facecolor=plot_params["facecolor"],
        edgecolor=plot_params["edgecolor"],
    )
    ax = fig.add_subplot(1, 1, 1, frameon=True)
    ax.set_axis_off()
    offset = 0.5 * scale
    ax.set_xlim(gate_grid[0] - offset, gate_grid[-1] + offset)
    ax.set_ylim(wire_grid[0] - offset, wire_grid[-1] + offset)
    ax.set_aspect("equal")
    return ax, fig


def _draw_wires(ax, nq, gate_grid, wire_grid, plot_params, measured={}):
    scale = plot_params["scale"]
    linewidth = plot_params["linewidth"]
    xdata = (gate_grid[0] - scale, gate_grid[-1] + scale)
    for i in range(nq):
        _line(
            ax,
            gate_grid[0] - scale,
            gate_grid[-1] + scale,
            wire_grid[i],
            wire_grid[i],
            plot_params,
        )


def _draw_labels(ax, labels, inits, gate_grid, wire_grid, plot_params):
    scale = plot_params["scale"]
    label_buffer = plot_params["label_buffer"]
    fontsize = plot_params["fontsize"]
    nq = len(labels)
    xdata = (gate_grid[0] - scale, gate_grid[-1] + scale)
    for i in range(nq):
        j = _get_flipped_index(labels[i], labels)
        _text(
            ax,
            xdata[0] - label_buffer,
            wire_grid[j],
            _render_label(labels[i], inits),
            plot_params,
        )


def _get_min_max_qbits(gates):
    def _get_all_tuple_items(iterable):
        t = []
        for each in iterable:
            t.extend(list(each) if isinstance(each, tuple) else [each])
        return tuple(t)

    all_qbits = []
    c_qbits = [t._control_qubits for t in gates.gates]
    t_qbits = [t._target_qubits for t in gates.gates]
    c_qbits = _get_all_tuple_items(c_qbits)
    t_qbits = _get_all_tuple_items(t_qbits)
    all_qbits.append(c_qbits + t_qbits)

    flatten_arr = _get_all_tuple_items(all_qbits)
    return min(flatten_arr), max(flatten_arr)


def _get_flipped_index(target, labels):
    """Get qubit labels from the rest of the line,and return indices

    >>> _get_flipped_index('q0', ['q0', 'q1'])
    1
    >>> _get_flipped_index('q1', ['q0', 'q1'])
    0
    """
    nq = len(labels)
    i = labels.index(target)
    return nq - i - 1


def _rectangle(ax, x1, x2, y1, y2, plot_style):
    Rectangle = matplotlib.patches.Rectangle
    x = min(x1, x2)
    y = min(y1, y2)
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    xm = x + w / 2.0
    ym = y + h / 2.0

    rect = Rectangle(
        (x, y),
        w,
        h,
        ec=plot_style["edgecolor"],
        fc=plot_style["fillcolor"],
        fill=False,
        lw=plot_style["linewidth"],
        label="",
    )
    ax.add_patch(rect)


def _get_flipped_indices(targets, labels):
    return [_get_flipped_index(t, labels) for t in targets]


def _render_label(label, inits={}):
    """Slightly more flexible way to render labels.

    >>> _render_label('q0')
    '$|q0\\\\rangle$'
    >>> _render_label('q0', {'q0':'0'})
    '$|0\\\\rangle$'
    """
    if label in inits:
        s = inits[label]
        if s is None:
            return ""
        else:
            return r"$|%s\rangle$" % inits[label]
    return r"$|%s\rangle$" % label


def _make_cluster_gates(gates_items):

    temp_gates = []
    temp_mgates = []
    cluster_gates = []

    for item in gates_items:
        if len(item) == 2:  # single qubit gates
            if item[0] == "MEASURE":
                temp_mgates.append(item)
            else:
                if len(temp_gates) > 0:
                    if item[1] in [tup[1] for tup in temp_gates]:
                        cluster_gates.append(temp_gates)
                        temp_gates = []
                        temp_gates.append(item)
                    else:
                        temp_gates.append(item)
                else:
                    temp_gates.append(item)
        else:
            if len(temp_gates) > 0:
                cluster_gates.append(temp_gates)
                temp_gates = []

            if len(temp_mgates) > 0:
                cluster_gates.append(temp_mgates)
                temp_mgates = []

            cluster_gates.append([item])

    if len(temp_gates) > 0:
        cluster_gates.append(temp_gates)

    if len(temp_mgates) > 0:
        cluster_gates.append(temp_mgates)

    return cluster_gates


def _build_path(filename):
    file_path = path.abspath(__file__)  # full path of current file
    dir_path = path.dirname(file_path)  # full path of the directory from file
    return path.join(dir_path, filename)  # absolute file path of given file


def _check_list_str(substrings, string):
    return any(item in str for item in list)


def _process_gates(array_gates):
    gates_plot = []

    for gate in array_gates:
        init_label = gate.name.upper()

        if init_label == "CCX":
            init_label = "TOFFOLI"

        if init_label == "CX":
            init_label = "CNOT"

        if _check_list_str(["SX", "CSX"], init_label):
            is_dagger = init_label[-2:] == "DG"
            init_label = (
                r"$\rm{\sqrt{X}}^{\dagger}$" if is_dagger else r"$\rm{\sqrt{X}}$"
            )

        if (
            len(gate._control_qubits) > 0
            and "C" in init_label[0]
            and "CNOT" != init_label
        ):
            init_label = gate.draw_label.upper()

        if init_label in [
            "ID",
            "MEASURE",
            "KRAUSCHANNEL",
            "UNITARYCHANNEL",
            "DEPOLARIZINGCHANNEL",
            "READOUTERRORCHANNEL",
        ]:
            for qbit in gate._target_qubits:
                item = (init_label,)
                item += ("q_" + str(qbit),)
                gates_plot.append(item)
        elif init_label == "ENTANGLEMENTENTROPY":
            for qbit in list(range(circuit.nqubits)):
                item = (init_label,)
                item += ("q_" + str(qbit),)
                gates_plot.append(item)
        else:
            item = ()
            item += (init_label,)

            for qbit in gate._target_qubits:
                if qbit is tuple:
                    item += ("q_" + str(qbit[0]),)
                else:
                    item += ("q_" + str(qbit),)

            for qbit in gate._control_qubits:
                if qbit is tuple:
                    item += ("q_" + str(qbit[0]),)
                else:
                    item += ("q_" + str(qbit),)

            gates_plot.append(item)

    return gates_plot


def plot(circuit, scale=0.6, cluster_gates=True, style=None):
    """Main matplotlib plot function for Qibo circuit
    circuit         A Qibo circuit to plot (type: qibo.models.circuit.Circuit)
    scale           Scale the ouput plot
    cluster_gates   Group single-qubit gates
    style           Style applied to the circuit (built-in styles: garnacha, fardelejo, quantumspain, color-blind and cachirulo)

    ax              An Axes object encapsulates all the elements of an individual plot in a figure (type: matplotlib.axes._axes.Axes)
    ax.figure       A Figure object (type: matplotlib.figure.Figure)
    """

    json_file = _build_path("symbols.json")

    with open(json_file) as file:
        SYMBOLS.update(json.load(file))

    json_file = _build_path("styles.json")

    with open(json_file) as file:
        STYLE.update(json.load(file))

    if style is not None:
        if type(style) is dict:
            plot_params.update(style)
        else:
            plot_params.update(
                STYLE[style] if style in list(STYLE.keys()) else STYLE["default"]
            )
    else:
        plot_params.update(STYLE["default"])

    inits = list(range(circuit.nqubits))

    labels = []
    for i in range(circuit.nqubits):
        labels.append("q_" + str(i))

    if len(circuit.queue) > 0:

        all_gates = []
        for gate in circuit.queue:
            if isinstance(gate, gates.FusedGate):
                min_q, max_q = _get_min_max_qbits(gate)

                fgates = None

                if cluster_gates:
                    fgates = _make_cluster_gates(_process_gates(gate.gates))
                else:
                    fgates = _process_gates(gate.gates)

                l_gates = len(gate.gates)
                equal_qbits = False
                if min_q != max_q:
                    l_gates = len(fgates)
                else:
                    max_q += 1
                    equal_qbits = True

                all_gates.append(
                    FusedStartGateBarrier(min_q, max_q, l_gates, equal_qbits)
                )
                all_gates += gate.gates
                all_gates.append(FusedEndGateBarrier(min_q, max_q))
            else:
                all_gates.append(gate)

        gates_plot = _process_gates(all_gates)

        if cluster_gates:
            gates_cluster = _make_cluster_gates(gates_plot)
            ax = _plot_quantum_schedule(gates_cluster, inits, labels, scale=scale)
            return ax, ax.figure

        ax = _plot_quantum_circuit(gates_plot, inits, labels, scale=scale)
        return ax, ax.figure
    else:
        ax = _plot_lines_circuit(inits, labels, scale=scale)
        return ax, ax.figure