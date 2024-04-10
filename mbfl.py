import argparse
import heapq
import json
import logging
import random

from util import *

random.seed(0)

# 创建命令行参数解析器
parser = argparse.ArgumentParser(
    description='Reduce statements and test cases.')
parser.add_argument('selected_statements_ratio', type=float,
                    help='Ratio for selecting statements to generate mutant (e.g. 0.7 for 70%, \
                            means that we should select 70% most suspected statement to generate mutant, \
                            while the 30% \less suspected ones should generate less mutant)')
parser.add_argument('reduced_test_cases_ratio', type=float,
                    help='Ratio for reducing passed test cases (e.g. 0.7 for 70%, \
                        means that we should reserve 70% passed tested cases with higher contribution, \
                            while just throw away the 30% \less contributed ones.)')
parser.add_argument('reduced_mutant_ratio', type=float,
                    help='Radio for selected statements to generate mutant (e.g. 0.7 for 70%, \
                        means that for selected less suspected statement, we should reserve 70% mutant for them \
                            while reduce 30% mutant)')
args = parser.parse_args()


def reduce_passed_test_cases(data, passed_test_cases_weights, percentage: float) -> list:
    """
    Get the list of passed test cases after reduction
    """
    num_of_methods = passed_test_cases_weights["passed_test_cases_lengths"]["methods"]
    num_of_statements = passed_test_cases_weights["passed_test_cases_lengths"]["statements"]
    num_of_rtest = passed_test_cases_weights["passed_test_cases_lengths"]["rtest"]
    N = int(
        passed_test_cases_weights["passed_test_cases_lengths"]["rtest"] * percentage)
    heap = [(passed_test_cases_weights["passed_test_cases_results"][i], i - (num_of_methods + num_of_statements)) for i in range(
        num_of_methods + num_of_statements, num_of_methods + num_of_statements + num_of_rtest)]

    # Find the top N largest values using the heap
    largest_values = heapq.nlargest(N, heap)
    top_n_indices_heap = [i for _, i in largest_values]
    passed_test_cases_reduced = []
    for passed_test_case in data:
        if passed_test_case in top_n_indices_heap:
            passed_test_cases_reduced.append(passed_test_case)
    # print("previous rtest case:", data)
    # print("reduced rtest case:", passed_test_cases_reduced)
    return passed_test_cases_reduced


def reduce_passed_test_cases_based_on_contribution(data, contribution_result, percentage: float) -> list:
    """
    Get the list of passed test cases after reduction based on contribution
    """
    num_of_rtest = len(data)
    N = int(num_of_rtest * percentage)
    heap = [(contribution_result[f"{i}"], i) for i in range(num_of_rtest)]

    # Find the top N largest values using the heap
    largest_values = heapq.nlargest(N, heap)
    top_n_indices_heap = [i for _, i in largest_values]
    passed_test_cases_reduced = []
    for passed_test_case in data:
        if passed_test_case in top_n_indices_heap:
            passed_test_cases_reduced.append(passed_test_case)
    # print("previous rtest case:", data)
    # print("reduced rtest case:", passed_test_cases_reduced)
    return passed_test_cases_reduced


def reduce_statements(lines, statement_weights, percentage: float) -> list:
    """
    Get the list of statement after reduction
    """
    num_of_methods = statement_weights["failed_passed_diff_lengths"]["methods"]
    num_of_statements = statement_weights["failed_passed_diff_lengths"]["statements"]
    N = int(statement_weights["failed_passed_diff_lengths"]
            ["statements"] * percentage)
    heap = [(statement_weights["failed_passed_diff_results"][i], i - num_of_methods) for i in range(
        num_of_methods, num_of_methods + num_of_statements)]

    # Find the top N largest values using the heap
    largest_values = heapq.nlargest(N, heap)
    top_n_indices_heap = [i for _, i in largest_values]
    statements_reduced = []
    for line in lines:
        if line in top_n_indices_heap:
            statements_reduced.append(line)
    # print("previous statements:", lines)
    # print("reduced statements", statements_reduced)
    return statements_reduced


def reduce_statements_based_on_random(lines, percentage: float) -> list:
    """
    Get the list of statement after reduction
    """
    N = int(len(lines) * percentage)
    lines = list(lines)
    # Create a list of indices for all statements
    # Randomly select N indices
    random_indices = random.sample(lines, N)

    # Get the statements corresponding to the randomly selected indices
    statements_reduced = [lines[i] for i in random_indices]

    return statements_reduced


def refactor_data(statements_reduced, passed_test_case_reduced, mutant2line, mutant2rtest, mutant2ftest, prob):
    mutant2line_reduced, mutant2rtest_reduced, mutant2ftest_reduced, mutant_list = {}, {}, {}, []
    for [mutant, line] in mutant2line:
        if line in statements_reduced:
            mutant2line_reduced[mutant] = line
            mutant_list.append(mutant)
        else:
            rand = random.randint(0, 99)
            if rand < prob * 100:
                mutant2line_reduced[mutant] = line
                mutant_list.append(mutant)

    for [mutant, rtest] in mutant2rtest:
        if mutant in mutant_list and rtest in passed_test_case_reduced:
            if mutant not in mutant2rtest_reduced:
                mutant2rtest_reduced[mutant] = [rtest]
            else:
                mutant2rtest_reduced[mutant].append(rtest)

    for [mutant, ftest] in mutant2ftest:
        if mutant in mutant_list:
            if mutant not in mutant2ftest_reduced:
                mutant2ftest_reduced[mutant] = [ftest]
            else:
                mutant2ftest_reduced[mutant].append(ftest)

    # print("previous mutant2line", mutant2line)
    # print("reduced mutant2line", mutant2line_reduced)
    # print("previous mutant2rtest", mutant2rtest)
    # print("reduced mutant2rtest", mutant2rtest_reduced)
    # print("reduced mutant2ftest", mutant2ftest_reduced)
    # print("reduced mutant_list", mutant_list)
    return mutant2line_reduced, mutant2rtest_reduced, mutant2ftest_reduced, mutant_list,


if __name__ == "__main__":
    dataset = ['Lang']
    formulas = formula_list = [formula for _,
                               formula in Formula.__members__.items()]

    for dataset_name in dataset:
        with open(f'pkl_data/{dataset_name}.json', 'r') as rf:
            structural_data = json.load(rf)
            logging.info("Load relationship from JSON file")

        for data in structural_data:
            project_name = data['proj']
            # if project_name != "Lang7":
            #     continue
            methods = data['methods']
            lines = data['lines']
            mutation = data['mutation']
            ftest = data['ftest']
            rtest = data['rtest']
            # print(project_name)
            len_methods = len(data['methods'])
            len_lines = len(data['lines'])
            len_mutation = len(data['mutation'])
            len_ftest = len(data['ftest'])
            len_rtest = len(data['rtest'])
            # Begin MBFL
            method2lines = data['edge2']
            lines2rtest = data['edge10']
            lines2ftest = data['edge']

            original_MTP = len_mutation * (len_ftest + len_rtest)

            for formula in formulas:

                with open(f'./data/page_rank/difference/{dataset_name}/{Formula.get_formula_name(formula)}/{project_name}.json', 'r') as diff_file:
                    difference = json.load(diff_file)
                    logging.info("Load difference from JSON file")

                with open(f'./data/page_rank/passed_test_cases/{dataset_name}/{Formula.get_formula_name(formula)}/{project_name}.json', 'r') as passed_test_cases_file:
                    passed_test_cases = json.load(passed_test_cases_file)
                    logging.info("Load passed test case from JSON file")

                with open(f'./data/sbfl/{dataset_name}/{Formula.get_formula_name(formula)}/{project_name}.json', 'r') as sbfl_file:
                    sbfl_result = json.load(sbfl_file)
                    logging.info("Load passed test case from JSON file")

                with open(f'./data/contribution/{dataset_name}/{project_name}.json', 'r') as sbfl_file:
                    contribution_result = json.load(sbfl_file)
                    logging.info("Load passed test case from JSON file")

                # GBSR reduction
                # Reduce statements with low suspiciousness and passed test case with low contribution
                # These two kinds of data should be reduced based on pre-computed result
                statements_reduced = reduce_statements(
                    lines.values(), difference, args.selected_statements_ratio)
                passed_test_cases_reduced = reduce_passed_test_cases(
                    rtest.values(), passed_test_cases, args.reduced_test_cases_ratio)

                mutant2line_reduced, mutant2rtest_reduced, mutant2ftest_reduced, mutant_list = refactor_data(
                    statements_reduced, passed_test_cases_reduced, data["edge12"], data["edge13"], data["edge14"], args.reduced_mutant_ratio)
                current_MTP = len(mutant_list) * \
                    (len_ftest + len(passed_test_cases_reduced))

                line_suspicion, mutant_suspicion = MBFL(mutants2lines=mutant2line_reduced, mutants_list=mutant_list,
                                                        line_list=lines.values(), original_line_test_case_data=sbfl_result["line suspicion"],
                                                        mutants2passed_test_cases=mutant2rtest_reduced,
                                                        mutants2failed_test_cases=mutant2ftest_reduced,
                                                        formula=formula)
                result = {
                    "proj": project_name,
                    "formula": Formula.get_formula_name(formula),
                    "num_of_mutants": len(mutant_list),
                    "num_of_test_cases": len_ftest + len(passed_test_cases_reduced),
                    "original_MTP": original_MTP,
                    "current_MTP": current_MTP,
                    "line suspicion": line_suspicion,
                    "mutant suspicion": mutant_suspicion
                }
                # print(result)
                dictionary_to_json(
                    result, f"./data/mbfl/{dataset_name}/{args.selected_statements_ratio:.1f}/{args.reduced_test_cases_ratio:.1f}/{args.reduced_mutant_ratio:.1f}/{Formula.get_formula_name(formula)}/{project_name}.json")

                # Contribution based reduction
                passed_test_cases_reduced_based_on_contribution = reduce_passed_test_cases_based_on_contribution(
                    rtest.values(), contribution_result["rtest"], args.reduced_test_cases_ratio)

                mutant2line_reduced_based_on_contribution, mutant2rtest_reduced_based_on_contribution, mutant2ftest_reduced_based_on_contribution, mutant_list_based_on_contribution = refactor_data(
                    lines.values(), passed_test_cases_reduced_based_on_contribution, data["edge12"], data["edge13"], data["edge14"], args.reduced_mutant_ratio)
                current_MTP = len(mutant_list_based_on_contribution) * \
                    (len_ftest + len(passed_test_cases_reduced_based_on_contribution))

                line_suspicion_based_on_contribution, mutant_suspicion_based_on_contribution = MBFL(mutants2lines=mutant2line_reduced_based_on_contribution, mutants_list=mutant_list_based_on_contribution,
                                                                                                    line_list=lines.values(), original_line_test_case_data=sbfl_result["line suspicion"],
                                                                                                    mutants2passed_test_cases=mutant2rtest_reduced_based_on_contribution,
                                                                                                    mutants2failed_test_cases=mutant2ftest_reduced_based_on_contribution,
                                                                                                    formula=formula)
                result = {
                    "proj": project_name,
                    "formula": Formula.get_formula_name(formula),
                    "num_of_mutants": len(mutant_list_based_on_contribution),
                    "num_of_test_cases": len_ftest + len(passed_test_cases_reduced_based_on_contribution),
                    "original_MTP": original_MTP,
                    "current_MTP": current_MTP,
                    "line suspicion": line_suspicion_based_on_contribution,
                    "mutant suspicion": mutant_suspicion_based_on_contribution
                }
                # print(result)
                dictionary_to_json(
                    result, f"./data/baseline/cbtcr/{dataset_name}/{args.selected_statements_ratio:.1f}/{args.reduced_test_cases_ratio:.1f}/{args.reduced_mutant_ratio:.1f}/{Formula.get_formula_name(formula)}/{project_name}.json")

                # Random statement reduction
                statements_reduced_random = reduce_statements_based_on_random(
                    lines.values(), args.selected_statements_ratio)

                mutant2line_reduced_random, mutant2rtest_reduced_random, mutant2ftest_reduced_random, mutant_list_random = refactor_data(
                    statements_reduced_random, rtest.values(), data["edge12"], data["edge13"], data["edge14"], args.reduced_mutant_ratio)
                current_MTP = len(mutant_list) * \
                    (len_ftest + len(rtest.values()))

                line_suspicion_random, mutant_suspicion_random = MBFL(mutants2lines=mutant2line_reduced_random, mutants_list=mutant_list_random,
                                                                      line_list=lines.values(), original_line_test_case_data=sbfl_result["line suspicion"],
                                                                      mutants2passed_test_cases=mutant2rtest_reduced_random,
                                                                      mutants2failed_test_cases=mutant2ftest_reduced_random,
                                                                      formula=formula)
                result = {
                    "proj": project_name,
                    "formula": Formula.get_formula_name(formula),
                    "num_of_mutants": len(mutant_list_random),
                    "num_of_test_cases": len_ftest + len(rtest.values()),
                    "original_MTP": original_MTP,
                    "current_MTP": current_MTP,
                    "line suspicion": line_suspicion_random,
                    "mutant suspicion": mutant_suspicion_random
                }
                # print(result)
                dictionary_to_json(
                    result, f"./data/baseline/random/{dataset_name}/{args.selected_statements_ratio:.1f}/{args.reduced_test_cases_ratio:.1f}/{args.reduced_mutant_ratio:.1f}/{Formula.get_formula_name(formula)}/{project_name}.json")
