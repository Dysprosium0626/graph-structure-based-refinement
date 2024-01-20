import json
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


if __name__ == "__main__":
    import numpy as np
    adj_matrix = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]])

    # Convert to Mermaid graph
    mermaid_graph = adjacency_matrix_to_mermaid(adj_matrix)
    print(mermaid_graph)
