import json
import os
import pickle
import numpy as np
import logging

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
np.set_printoptions(suppress=True)


def page_rank_internal(transition_matrix, initial_rank_vector, convergence_threshold):
    """
    Computes the PageRank vector for a given transition matrix.

    Parameters:
    - transition_matrix (np.ndarray): The transition probability matrix representing the web graph.
    - initial_rank_vector (np.ndarray): The initial PageRank vector, typically a uniform distribution.
    - convergence_threshold (float): The threshold for convergence. The computation stops when the change between iterations falls below this value.

    Returns:
    - np.ndarray: The converged PageRank vector.

    The function iteratively applies the PageRank algorithm until the rank vector stabilizes within the specified convergence threshold or reaches the iteration limit.
    """
    iteration_limit = 10000  # Limit to prevent infinite loop in case of non-convergence
    for _ in range(iteration_limit):
        # Set numpy print options for debugging
        np.set_printoptions(precision=6)
        # Compute next rank vector
        next_rank_vector = np.dot(transition_matrix, initial_rank_vector)
        # Normalize to prevent overflow or underflow
        normalized_rank_vector = next_rank_vector / max(next_rank_vector)
        error = max(np.abs(normalized_rank_vector -
                    initial_rank_vector))  # Compute error

        if error < convergence_threshold:  # Check for convergence
            return initial_rank_vector  # Return the stabilized rank vector

        initial_rank_vector = normalized_rank_vector  # Prepare for next iteration

    # Return the last computed vector if convergence threshold not met
    return initial_rank_vector


def page_rank(file_path):
    """
    Calculates the PageRank vector for a graph defined in a file.

    Parameters:
    - file_path (str): The path to the file containing the graph's adjacency list, stored in binary format with pickle.

    Returns:
    - np.ndarray: The PageRank vector of the graph.

    The function reads the graph's adjacency list from the file, constructs the transition matrix, and computes the PageRank vector using the PageRank algorithm.
    """
    with open(file_path, 'rb') as file:
        adjacency_list = pickle.load(file)

    number_of_pages = len(adjacency_list[0])
    adjacency_matrix = np.array(adjacency_list, dtype=float)
    # print(adjacency_matrix)
    initial_rank_vector = np.ones(number_of_pages)
    damping_factor = 0.8
    uniform_matrix = np.ones((number_of_pages, number_of_pages))
    transition_matrix = damping_factor * adjacency_matrix + \
        ((1 - damping_factor) / number_of_pages) * uniform_matrix

    convergence_threshold = 1e-7
    page_rank_vector = page_rank_internal(
        transition_matrix, initial_rank_vector, convergence_threshold)

    return page_rank_vector


def page_rank_results_to_string(test_case_results, lengths, prefix=""):
    """
    Formats the PageRank results along with the lengths into a string suitable for output.

    Parameters:
    - test_case_results (np.ndarray): The PageRank results for test cases.
    - lengths (tuple): Tuple containing lengths of methods, lines, rtest, and ftest.
    - prefix (str): A prefix to differentiate between passed and failed test cases.

    Returns:
    - str: Formatted string ready for writing to a file.
    """
    len_methods, len_lines, len_rtest, len_ftest = lengths
    results_dict = {
        f"{prefix}_lengths": {
            "methods": len_methods,
            "statements": len_lines,
            "rtest": len_rtest,
            "ftest": len_ftest
        },
        f"{prefix}_results": list(test_case_results)
    }
    return results_dict


if __name__ == '__main__':
    dataset = "Lang"
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
        print(project_name)
        len_methods = len(data['methods'])
        len_lines = len(data['lines'])
        len_mutation = len(data['mutation'])
        len_ftest = len(data['ftest'])
        len_rtest = len(data['rtest'])

        passed_test_cases_filepath = f'./data/graph/passed_test_cases/{dataset}/{project_name}_matrix.pkl'
        failed_test_cases_filepath = f'./data/graph/failed_test_cases/{dataset}/{project_name}_matrix.pkl'
        passed_test_cases_matrix_after_page_rank = page_rank(
            passed_test_cases_filepath)
        failed_test_cases_matrix_after_page_rank = page_rank(
            failed_test_cases_filepath)
        # print(passed_test_cases_matrix_after_page_rank.round(6))
        # print(failed_test_cases_matrix_after_page_rank.round(6))
        # Format lengths for output
        lengths = (len(data['methods']), len(data['lines']),
                   len(data['rtest']), len(data['ftest']))

        # Prepare result strings
        passed_results_str = page_rank_results_to_string(
            passed_test_cases_matrix_after_page_rank, lengths, prefix="passed_test_cases")
        failed_results_str = page_rank_results_to_string(
            failed_test_cases_matrix_after_page_rank, lengths, prefix="failed_test_cases")
        difference_results_str = page_rank_results_to_string(failed_test_cases_matrix_after_page_rank[0:len(data['methods']) + len(
            data['lines'])] - passed_test_cases_matrix_after_page_rank[0:len(data['methods']) + len(data['lines'])], lengths, prefix="failed_passed_diff")

        passed_test_cases_dir = os.path.join(
            "data", 'page_rank', "passed_test_cases", dataset)
        failed_test_cases_dir = os.path.join(
            "data", 'page_rank', "failed_test_cases", dataset)
        difference_dir = os.path.join(
            "data", 'page_rank', "difference", dataset)

        os.makedirs(passed_test_cases_dir, exist_ok=True)
        os.makedirs(failed_test_cases_dir, exist_ok=True)
        os.makedirs(difference_dir, exist_ok=True)

        passed_test_cases_page_rank_result = os.path.join(
            passed_test_cases_dir, f'{project_name}.json')
        failed_test_cases_page_rank_result = os.path.join(
            failed_test_cases_dir, f'{project_name}.json')
        difference_page_rank_result = os.path.join(
            difference_dir, f'{project_name}.json')

        if not os.path.isfile(passed_test_cases_page_rank_result):
            with open(passed_test_cases_page_rank_result, 'w') as json_file:
                json.dump(passed_results_str, json_file, indent=4)
        else:
            logging.info(
                f"File {passed_test_cases_page_rank_result} already exists. Skipping...")

        if not os.path.isfile(failed_test_cases_page_rank_result):
            with open(failed_test_cases_page_rank_result, 'w') as json_file:
                json.dump(failed_results_str, json_file, indent=4)
        else:
            logging.info(
                f"File {failed_test_cases_page_rank_result} already exists. Skipping...")

        if not os.path.isfile(difference_page_rank_result):
            with open(difference_page_rank_result, 'w') as json_file:
                json.dump(difference_results_str, json_file, indent=4)
        else:
            logging.info(
                f"File {difference_page_rank_result} already exists. Skipping...")
