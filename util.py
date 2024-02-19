from enum import Enum
import json
import math
import os
import logging


def dictionary_to_json(dictionary: dict, file_path: str):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(file_path, 'w') as fp:
        json.dump(dictionary, fp)


def adjacency_matrix_to_mermaid(matrix, number_of_methods, number_of_lines, number_of_test_cases, passed_or_failed=True):
    """
    Converts an adjacency matrix to a Mermaid graph representation.

    Args:
    - matrix (np.array): An adjacency matrix representing a directed graph.
    - number_of_methods (int): The number of methods
    - number_of_lines (int): The number of lines
    - number_of_test_cases (int): The number of test cases
    - passed_or_failed (bool): True for passed test case and False for failed test cases 
    Returns:
    - str: A string formatted in Mermaid syntax representing the directed graph.
    """
    mermaid_str = "```mermaid\ngraph LR\n"
    rows, cols = matrix.shape
    assert (rows == cols)
    assert (rows == number_of_methods + number_of_lines + number_of_test_cases)

    for i in range(number_of_methods):
        for j in range(cols):
            if matrix[i][j] != 0:
                if j < number_of_methods:
                    mermaid_str += f"    method_{i} --> method_{j}\n"
                elif j < number_of_methods + number_of_lines:
                    mermaid_str += f"    method_{i} --- line_{j - number_of_methods}\n"

    for i in range(number_of_methods, number_of_methods + number_of_lines):
        for j in range(number_of_methods + number_of_lines, cols):
            if matrix[i][j] != 0:
                if j < number_of_methods + number_of_lines + number_of_test_cases:
                    if passed_or_failed:
                        mermaid_str += f"    line_{i- number_of_methods} --- passed_case_{j - number_of_methods - number_of_lines}\n"
                    else:
                        mermaid_str += f"    line_{i -number_of_methods} --- failed_case_{j - number_of_methods - number_of_lines}\n"

    mermaid_str += "```"
    return mermaid_str


class FaultLocalization(Enum):
    SBFL = 0,
    MBFL = 1


class Formula(Enum):
    GP13 = 0,
    OCHIAI = 1,
    JACCARD = 2,
    OP2 = 3,
    TARANTULA = 4,
    DSTAR = 5

    @staticmethod
    def get_formula_name(formula) -> str:
        if formula == Formula.GP13:
            return "GP13"
        elif formula == Formula.OCHIAI:
            return "Ochiai"
        elif formula == Formula.JACCARD:
            return "Jaccard"
        elif formula == Formula.OP2:
            return "OP2"
        elif formula == Formula.TARANTULA:
            return "Tarantula"
        elif formula == Formula.DSTAR:
            return "DSTAR"


def GP13(line_suspicion, type: FaultLocalization):
    if type == FaultLocalization.SBFL:
        for line in line_suspicion:
            ef, ep, nf, np = line_suspicion[line]['stats'].values()
            line_suspicion[line]['suspicion'] = ef * \
                (1 + 1 / (2 * ep + ef)) if ef != 0 else 0
        return line_suspicion
    elif type == FaultLocalization.MBFL:
        for line in line_suspicion:
            kf, kp, nf, np = line_suspicion[line]['stats'].values()
            line_suspicion[line]['suspicion'] = kf * \
                (1 + 1 / (2 * kp + kf)) if kf != 0 else 0
        return line_suspicion
        return


def Ochiai(line_suspicion, type: FaultLocalization):
    if type == FaultLocalization.SBFL:
        for line in line_suspicion:
            ef, ep, nf, np = line_suspicion[line]['stats'].values()
            denominator = math.sqrt((ef + nf) * (ef + np))
            line_suspicion[line]['suspicion'] = ef / \
                denominator if denominator > 0 else 0
        return line_suspicion
    elif type == FaultLocalization.MBFL:
        for line in line_suspicion:
            kf, kp, nf, np = line_suspicion[line]['stats'].values()
            denominator = math.sqrt((kf + nf) * (kf + np))
            line_suspicion[line]['suspicion'] = kf / \
                denominator if denominator > 0 else 0
        return line_suspicion


def Jaccard(line_suspicion, type: FaultLocalization):
    if type == FaultLocalization.SBFL:
        for line in line_suspicion:
            ef, ep, nf, np = line_suspicion[line]['stats'].values()
            denominator = ef + nf + ep
            line_suspicion[line]['suspicion'] = ef / \
                denominator if denominator > 0 else 0
        return line_suspicion
    elif type == FaultLocalization.MBFL:
        for line in line_suspicion:
            kf, kp, nf, np = line_suspicion[line]['stats'].values()
            denominator = kf + nf + kp
            line_suspicion[line]['suspicion'] = kf / \
                denominator if denominator > 0 else 0
        return line_suspicion


def OP2(line_suspicion, type: FaultLocalization):
    if type == FaultLocalization.SBFL:
        for line in line_suspicion:
            ef, ep, nf, np = line_suspicion[line]['stats'].values()
            line_suspicion[line]['suspicion'] = ef - ep / (np + ep + 1)
        return line_suspicion
    elif type == FaultLocalization.MBFL:
        for line in line_suspicion:
            kf, kp, nf, np = line_suspicion[line]['stats'].values()
            line_suspicion[line]['suspicion'] = kf - kp / (np + kp + 1)
        return line_suspicion


def Tarantula(line_suspicion, type: FaultLocalization):
    if type == FaultLocalization.SBFL:
        for line in line_suspicion:
            ef, ep, nf, np = line_suspicion[line]['stats'].values()
            if ef == 0:
                line_suspicion[line]['suspicion'] = 0
                continue
            ef_ratio_in_failed_cases = ef / (ef + nf) if ef + nf != 0 else 0
            ep_ratio_in_passed_cases = ep / (ep + np) if ep + np != 0 else 1
            line_suspicion[line]['suspicion'] = ef_ratio_in_failed_cases / \
                (ef_ratio_in_failed_cases + ep_ratio_in_passed_cases)
        return line_suspicion
    elif type == FaultLocalization.MBFL:
        for line in line_suspicion:
            kf, kp, nf, np = line_suspicion[line]['stats'].values()
            if kf == 0:
                line_suspicion[line]['suspicion'] = 0
                continue
            kf_ratio_in_failed_cases = kf / (kf + nf) if kf + nf != 0 else 0
            kp_ratio_in_passed_cases = kp / (kp + np) if kp + np != 0 else 1
            line_suspicion[line]['suspicion'] = kf_ratio_in_failed_cases / \
                (kf_ratio_in_failed_cases + kp_ratio_in_passed_cases)
        return line_suspicion


def Dstar(line_suspicion, type: FaultLocalization, star_value=2):
    if type == FaultLocalization.SBFL:
        for line in line_suspicion:
            ef, ep, nf, np = line_suspicion[line]['stats'].values()
            line_suspicion[line]['suspicion'] = math.pow(
                ef, star_value) / ((ep + nf)) if ep + nf > 0 else 0
        return line_suspicion
    elif type == FaultLocalization.MBFL:
        for line in line_suspicion:
            kf, kp, nf, np = line_suspicion[line]['stats'].values()
            line_suspicion[line]['suspicion'] = math.pow(
                kf, star_value) / ((kp + nf)) if kp + nf > 0 else 0
        return line_suspicion


if __name__ == "__main__":
    import numpy as np
    adj_matrix = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]])

    # Convert to Mermaid graph
    mermaid_graph = adjacency_matrix_to_mermaid(adj_matrix)
    print(mermaid_graph)
