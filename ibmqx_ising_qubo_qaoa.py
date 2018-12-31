from collections import OrderedDict
import numpy as np
from qiskit.quantum_info import Pauli
from qiskit_aqua import Operator
from qiskit_aqua.algorithms.adaptive import QAOA
from qiskit_aqua.components.optimizers import *
from qiskit_aqua import QuantumInstance
import networkx as nx
from qiskit_aqua import get_aer_backend

def sample_most_likely(state_vector):
    if isinstance(state_vector, dict) or isinstance(state_vector, OrderedDict):
        binary_string = sorted(state_vector.items(), key=lambda kv: kv[1])[-1][0]
        x = np.asarray([int(y) for y in reversed(list(binary_string))])
        return x
    else:
        n = int(np.log2(state_vector.shape[0]))
        k = np.argmax(np.abs(state_vector))
        x = np.zeros(n)
        for i in range(n):
            x[i] = k % 2
            k >>= 1
        return x
def get_qubitops(input):
    w = np.array(input.tolist())
    num_nodes = len(w)
    pauli_list = []
    shift = 0
    for i in range(num_nodes):
        for j in range(i+1, num_nodes):
            if w[i, j] != 0:
                xp = np.zeros(num_nodes, dtype=np.bool)
                zp = np.zeros(num_nodes, dtype=np.bool)
                zp[i] = True
                zp[j] = True
                pauli_list.append([w[i, j], Pauli(zp, xp)])
                shift += 1
    for i in range(num_nodes):
        degree = np.sum(w[i, :])
        xp = np.zeros(num_nodes, dtype=np.bool)
        zp = np.zeros(num_nodes, dtype=np.bool)
        zp[i] = True
        pauli_list.append([w[i, i], Pauli(zp, xp)])
    return Operator(paulis=pauli_list)
def get_vertexcover_qubitops(G):
    weight_matrix = nx.to_numpy_matrix(G)
    n = len(weight_matrix)
    pauli_list = []
    shift = 0
    A = 5

    for i in range(n):
        for j in range(i):
            if (weight_matrix[i, j] != 0):
                wp = np.zeros(n)
                vp = np.zeros(n)
                vp[i] = 1
                vp[j] = 1
                pauli_list.append([A*0.25, Pauli(vp, wp)])

                vp2 = np.zeros(n)
                vp2[i] = 1
                pauli_list.append([-A*0.25, Pauli(vp2, wp)])

                vp3 = np.zeros(n)
                vp3[j] = 1
                pauli_list.append([-A*0.25, Pauli(vp3, wp)])

                shift += A*0.25

    for i in range(n):
        wp = np.zeros(n)
        vp = np.zeros(n)
        vp[i] = 1
        pauli_list.append([0.5, Pauli(vp, wp)])
        shift += 0.5
    return Operator(paulis=pauli_list)

#'ibmqx4'
#'ibmq_16_melbourne'
from qiskit import IBMQ
IBMQ.load_accounts()

def solve_ising_qubo(G, matrix_func, optimizer, p):
        #backend = IBMQ.get_backend("ibmq_qasm_simulator")
        backend = get_aer_backend('qasm_simulator')
        w = matrix_func(G)
        ops = get_qubitops(w)
        qaoa = QAOA(ops, optimizer, p, operator_mode='paulis')
        quantum_instance = QuantumInstance(backend)
        result = qaoa.run(quantum_instance)
        x = sample_most_likely(result['eigvecs'][0])
        return x
