
import logging
from util import *
import json
import numpy as np
import pickle

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
np.set_printoptions(suppress=True)

# TODO(Yue): Init the matrix by the SBFL result
def create_adjacency_matrix(length1, length2, edges, normalize_by_row=True):
    """
    Creates an adjacency matrix from edge list and normalizes it.

    Args:
    - length1 (int): The number of rows in the matrix.
    - length2 (int): The number of columns in the matrix.
    - edges (list of tuples): List of edges represented as tuples (start, end).
    - normalize_by_row (bool): Normalize by row if True, else by column.

    Returns:
    - np.array: A normalized adjacency matrix.
    """
    matrix = np.zeros((length1, length2))
    for start, end in edges:
        matrix[int(start)][int(end)] = 1

    if normalize_by_row:
        row_sums = matrix.sum(axis=1)
        matrix = np.divide(
            matrix, row_sums[:, np.newaxis], where=row_sums[:, np.newaxis] != 0)
    else:
        col_sums = matrix.sum(axis=0)
        matrix = np.divide(matrix, col_sums, where=col_sums != 0)
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


def process_method_to_method_matrix(data, length):
    """
    Processes method to method data.

    Args:
    - data (list): Method to method data.
    - length (int): The length of the methods.

    Returns:
    - np.array: A method to method matrix.
    """
    matrix = np.zeros((length, length))
    for index, targets in data:
        for target in targets:
            matrix[index][target] = 1.0 / len(targets)
    return matrix


if __name__ == '__main__':
    dataset = 'Lang'
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
    num_flag = 0
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
        logging.info(f"Get edge information of {project_name}")

        matrix = np.zeros((len_total, len_total))
        this_method2method_data = method2method_data[project_name]

        # method-method 矩阵 建立
        method2method_matrix = process_method_to_method_matrix(
            this_method2method_data, len_methods)

        # method-lines 矩阵 建立
        method2lines_matrix = create_adjacency_matrix(
            len_methods, len_lines, method2lines)

        # print(method2lines_matrix)

        # # mutation-lines 矩阵 建立
        # mutation2lines_matrix = create_adjacency_matrix(len_mutation, len_lines, mutation2lines, change= 1)

        # lines-rtest 矩阵 建立
        lines2rtest_matrix = create_adjacency_matrix(
            len_lines, len_rtest, lines2rtest)

        # line-ftest 矩阵 建立
        lines2ftest_matrix = create_adjacency_matrix(
            len_lines, len_ftest, lines2ftest)

        # # mutation-rtest 矩阵 建立
        # mutation2rtest_matrix = create_adjacency_matrix(len_mutation, len_rtest, mutation2rtest, -1)

        # # mutation-ftest 矩阵 建立
        # mutation2ftest_matrix = create_adjacency_matrix(len_mutation, len_ftest, mutation2ftest)

        logging.info("Integrating matrices")
        graph_with_passed_test_cases, graph_with_failed_test_cases = integrate_matrices(method2method_matrix, method2lines_matrix, lines2rtest_matrix,
                                                                                        lines2ftest_matrix, len_methods, len_lines, len_rtest, len_ftest)
        if project_name == "Lang1":
            print(adjacency_matrix_to_mermaid(
                graph_with_passed_test_cases, len_methods, len_lines, len_rtest))
        # f_matrix = integrate_matrices(method2method_matrix,method2lines_matrix,mutation2lines_matrix, lines2ftest_matrix, mutation2ftest_matrix, len_method, len_lines,len_mutation, len_ftest)

        graph_with_passed_test_cases_file_path = f'./data/graph/passed_test_cases/{dataset}/{project_name}_matrix.pkl'
        graph_with_failed_test_cases_file_path = f'./data/graph/failed_test_cases/{dataset}/{project_name}_matrix.pkl'

        # r_matrix.to_pickle(path=file_path)
        # print(f_matrix)
        # str_rmatrix = ''
        # for i in r_matrix.round(6):
        #     for j in i:
        #         str_rmatrix = str_rmatrix + str(j) + ' '
        #     str_rmatrix = str_rmatrix + '\n'
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
