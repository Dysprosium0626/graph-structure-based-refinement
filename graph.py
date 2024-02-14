
from enum import Enum
import logging
from util import *
import json
import numpy as np
import pickle

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
np.set_printoptions(suppress=True)


class Type(Enum):
    STATEMENT = 0,
    PASSED_TEST = 1,
    FAILED_TEST = 2,


def create_adjacency_matrix(length1: int, length2: int, edges: list, suspicion_or_contribution: dict, type: Type) -> np.array:
    """
    Creates an adjacency matrix from edge list and normalizes it.

    Args:
    - length1 (int): The number of rows in the matrix.
    - length2 (int): The number of columns in the matrix.
    - edges (list of tuples): List of edges represented as tuples (start, end).
    - suspicion_or_contribution (dict): The suspicious data for line or contribution data for test cases
    - type (Type): The type of data (statement, passed test case or failed test case)

    Returns:
    - np.array: A normalized adjacency matrix.
    """
    matrix = np.zeros((length1, length2))
    for start, end in edges:
        if type == Type.STATEMENT:
            matrix[start][end] = suspicion_or_contribution[f"{end}"]["suspicion"]
        elif type == Type.PASSED_TEST:
            matrix[start][end] = suspicion_or_contribution["rtest"][f"{end}"]
        elif type == Type.FAILED_TEST:
            matrix[start][end] = suspicion_or_contribution["ftest"][f"{end}"]
    non_zero_elements = matrix[matrix > 0]
    if non_zero_elements.size == 0:  # Check if there are any non-zero elements
        return matrix  # Return the original matrix if all elements are zero

    min_val = non_zero_elements.min()
    max_val = non_zero_elements.max()
    # Apply min-max normalization only on non-zero elements
    for i in range(length1):
        for j in range(length2):
            if matrix[i][j] > 0:  # Normalize only non-zero elements
                matrix[i][j] = (matrix[i][j] - min_val) / (max_val - min_val) if max_val != min_val else 0.5
    return matrix


def integrate_matrices(method_to_method, method_to_lines, lines_to_passed_test_cases, lines_to_failed_test_cases,
                       num_methods, num_lines, num_r_tests, num_f_tests):
    """
    Integrates various matrices into two larger matrices for different test types.

    Args:
    - method_to_method (np.array): Adjacency matrix for method-method relationships.
    - method_to_lines (np.array): Adjacency matrix for method-lines relationships.
    - lines_to_tests (np.array): Adjacency matrix for lines-tests relationships.
    - method_to_tests (np.array): Adjacency matrix for method-tests relationships.
    - num_methods (int): Number of methods.
    - num_lines (int): Number of lines.
    - num_r_tests (int): Number of r tests.
    - num_f_tests (int): Number of f tests.

    Returns:
    - matrix_p: The graph of the relationship of method, lines and passed test cases
    - matrix_f: The graph of the relationship of method, lines and failed test cases
    """

    total_len = num_methods + num_lines
    matrix_p_len = total_len + num_r_tests
    matrix_f_len = total_len + num_f_tests

    matrix_p = np.zeros((matrix_p_len, matrix_p_len))
    matrix_f = np.zeros((matrix_f_len, matrix_f_len))

    # Method to Method
    matrix_p[:num_methods, :num_methods] = method_to_method
    matrix_f[:num_methods, :num_methods] = method_to_method

    # Method to Lines
    matrix_p[:num_methods, num_methods:num_methods +
             num_lines] = method_to_lines
    matrix_p[num_methods:num_methods + num_lines,
             :num_methods] = method_to_lines.T

    matrix_f[:num_methods, num_methods:num_methods +
             num_lines] = method_to_lines
    matrix_f[num_methods:num_methods + num_lines,
             :num_methods] = method_to_lines.T

    # Lines to R Tests
    matrix_p[num_methods:num_methods + num_lines,
             num_methods + num_lines:] = lines_to_passed_test_cases
    matrix_p[num_methods + num_lines:, num_methods: num_methods +
             num_lines] = lines_to_passed_test_cases.T
    # Lines to F Tests
    matrix_f[num_methods:num_methods + num_lines,
             num_methods + num_lines:] = lines_to_failed_test_cases
    matrix_f[num_methods + num_lines:, num_methods: num_methods +
             num_lines] = lines_to_failed_test_cases.T

    return matrix_p, matrix_f


def process_method_to_method_matrix(data: list, length: int, method_suspicion: dict) -> np.array:
    """
    Processes method to method data.
    The weight of edge in method to method matrix is the sum of 2 adjacent method nodes after normalization.
    For example:
        Suspiciousness:
            Method1 : 0.5
            Method2 : 0.3
            Method3 : 1.0
            Method4 : 0.2
        Call:
            Method1 -> Method2
            Method1 -> Method3
            Method3 -> Method4
        Weight before normalization:
            Method1 -> Method2 = 0.5 + 0.3 = 0.8
            Method1 -> Method3 = 0.5 + 1.0 = 1.5
            Method3 -> Method4 = 1.0 + 0.2 = 1.2
        Weight after normalization:
            Min = 0.8, Max = 1.5
            Method1 -> Method2 = (0.8 - Min) / (Max - Min) = 0.0
            Method1 -> Method3 = (1.5 - Min) / (Max - Min) = 1.0
            Method3 -> Method4 = (1.2 - Min) / (Max - Min) = 0.57

    Args:
    - data (list): Method to method data.
    - length (int): The length of the methods.
    - method_suspicion (dict): The suspiciousness for method and method

    Returns:
    - np.array: A method to method matrix.
    """
    matrix = np.zeros((length, length))
    # min_sus = min(method_suspicion.values(),
    #               key=lambda x: x["suspicion"])["suspicion"]
    # max_sus = max(method_suspicion.values(),
    #               key=lambda x: x["suspicion"])["suspicion"]
    for index, targets in data:
        for target in targets:
            matrix[index][target] = method_suspicion[f"{index}"]["suspicion"] + \
                method_suspicion[f"{target}"]["suspicion"]
    # Find non-zero minimum and maximum values for normalization
    non_zero_elements = matrix[matrix > 0]
    if non_zero_elements.size == 0:  # Check if there are any non-zero elements
        return matrix  # Return the original matrix if all elements are zero

    min_val = non_zero_elements.min()
    max_val = non_zero_elements.max()
    # Apply min-max normalization only on non-zero elements
    for i in range(length):
        for j in range(length):
            if matrix[i][j] > 0:  # Normalize only non-zero elements
                matrix[i][j] = (matrix[i][j] - min_val) / (max_val - min_val) if max_val != min_val else 0.5
    return matrix


if __name__ == '__main__':
    dataset = 'Lang'
    sbfl_formula = 'GP13'
    method2method_data = {}

    logging.info("Converting call graph to method to method in-memory matrix")
    with open(f'data/call_graph/{dataset}_M2M.txt', 'r') as call_graph:
        method2method_file = call_graph.readlines()
    for method2method in method2method_file:
        project_name = method2method.split(' * ')[0]
        method2method_list = eval(method2method.split(' * ')[1])
        method2method_data[project_name] = method2method_list
    logging.info("Converting finished")

    with open(f'pkl_data/{dataset}.json', 'r') as rf:
        datas = json.load(rf)
        logging.info("Load relationship from JSON file")

    for data in datas:
        project_name = data['proj']
        methods = data['methods']
        lines = data['lines']
        mutation = data['mutation']
        ftest = data['ftest']
        rtest = data['rtest']

        len_methods = len(data['methods'])
        len_lines = len(data['lines'])
        len_mutation = len(data['mutation'])
        len_ftest = len(data['ftest'])
        len_rtest = len(data['rtest'])
        logging.info(f"Begin processing {project_name}")
        logging.info(f"Number of methods: {len_methods}")
        logging.info(f"Number of lines: {len_lines}")
        logging.info(f"Number of mutation: {len_mutation}")
        logging.info(f"Number of rtest(passed test cases): {len_rtest}")
        logging.info(f"Number of ftest(failed test cases): {len_ftest}")
        len_total = len_methods + len_lines + len_mutation + len_rtest + len_ftest
        logging.info(f"Get vertex information of {project_name}")

        method2method = {}
        method2lines = data['edge2']
        mutation2lines = data['edge12']
        lines2rtest = data['edge10']
        lines2ftest = data['edge']
        mutation2rtest = data['edge13']
        mutation2ftest = data['edge14']
        this_method2method_data = method2method_data[project_name]
        logging.info(f"Get edge information of {project_name}")

        with open(f'data/sbfl/{dataset}/{sbfl_formula}/{project_name}.json', 'r') as rf:
            sbfl_data = json.load(rf)
            logging.info("Load SBFL suspiciousness from JSON file")
        with open(f'data/contribution/{dataset}/{project_name}.json', 'r') as rf:
            contribution_data = json.load(rf)
            logging.info("Load contribution data from JSON file")

        method_suspicion = sbfl_data["method suspicion"]
        line_suspicion = sbfl_data["line suspicion"]

        # method-method 矩阵 建立
        method2method_matrix = process_method_to_method_matrix(
            this_method2method_data, len_methods, method_suspicion)
        # method-lines 矩阵 建立
        method2lines_matrix = create_adjacency_matrix(
            len_methods, len_lines, method2lines, line_suspicion, Type.STATEMENT)

        # lines-rtest 矩阵 建立
        lines2rtest_matrix = create_adjacency_matrix(
            len_lines, len_rtest, lines2rtest, contribution_data, Type.PASSED_TEST)

        # line-ftest 矩阵 建立
        lines2ftest_matrix = create_adjacency_matrix(
            len_lines, len_ftest, lines2ftest, contribution_data, Type.FAILED_TEST)

        logging.info("Integrating matrices")
        graph_with_passed_test_cases, graph_with_failed_test_cases = integrate_matrices(method2method_matrix, method2lines_matrix, lines2rtest_matrix,
                                                                                        lines2ftest_matrix, len_methods, len_lines, len_rtest, len_ftest)

        graph_with_passed_test_cases_file_path = f'./data/graph/passed_test_cases/{dataset}/{project_name}_matrix.pkl'
        graph_with_failed_test_cases_file_path = f'./data/graph/failed_test_cases/{dataset}/{project_name}_matrix.pkl'

        directory = os.path.dirname(graph_with_passed_test_cases_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        with open(graph_with_passed_test_cases_file_path, 'wb') as wf:
            pickle.dump(graph_with_passed_test_cases, wf)
        directory = os.path.dirname(graph_with_failed_test_cases_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        with open(graph_with_failed_test_cases_file_path, 'wb') as wf:
            pickle.dump(graph_with_failed_test_cases, wf)
        logging.info(f"Process {project_name} finished")
