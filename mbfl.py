import heapq
import json
import logging
import fastrand

from util import *

fastrand.pcg32_seed(0)

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
    print("previous rtest case:", data)
    print("reduced rtest case:", passed_test_cases_reduced)
    return passed_test_cases_reduced


def reduce_statements(lines, statement_weights, percentage: float):
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
    print("previous statements:", lines)
    print("reduced statements", statements_reduced)
    return statements_reduced


def refactor_data(statements_reduced, passed_test_case_reduced, mutant2line, mutant2rtest, mutant2ftest, prob=0.7):
    mutant2line_reduced, mutant2rtest_reduced, mutant2ftest_reduced, mutant_list = {}, {}, {}, []
    for [mutant, line] in mutant2line:
        if line in statements_reduced:
            mutant2line_reduced[mutant] = line
            mutant_list.append(mutant)
        else:
            rand = fastrand.pcg32bounded(101)
            if rand > prob * 100:
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

    print("previous mutant2line", mutant2line)
    print("reduced mutant2line", mutant2line_reduced)
    print("previous mutant2rtest", mutant2rtest)
    print("reduced mutant2rtest", mutant2rtest_reduced)
    print("reduced mutant2ftest", mutant2ftest_reduced)
    print("reduced mutant_list", mutant_list)
    return mutant2line_reduced, mutant2rtest_reduced, mutant2ftest_reduced, mutant_list


def CalculateSuspiciousnessByMBFL(formula_type, line_suspicion):
    if formula_type == Formula.GP13:
        return GP13(line_suspicion, FaultLocalization.MBFL)
    elif formula_type == Formula.OCHIAI:
        return Ochiai(line_suspicion, FaultLocalization.MBFL)
    elif formula_type == Formula.JACCARD:
        return Jaccard(line_suspicion, FaultLocalization.MBFL)
    elif formula_type == Formula.OP2:
        return OP2(line_suspicion, FaultLocalization.MBFL)
    elif formula_type == Formula.TARANTULA:
        return Tarantula(line_suspicion, FaultLocalization.MBFL)
    elif formula_type == Formula.DSTAR:
        return Dstar(line_suspicion, FaultLocalization.MBFL)
    else:
        raise ValueError("Unsupported formula type")


def MBFL(mutants2lines, mutants_list, line_list, original_line_test_case_data, mutants2passed_test_cases, mutants2failed_test_cases, formula):
    
    line_suspicion = {number_index: {"mutants": [], "suspicion": 0}
                      for number_index in line_list}
    mutant_suspicion = {number_index: {"stats": {'akp': 0, 'anp': 0, 'akf': 0, 'anf': 0}, "suspicion": 0}
                        for number_index in mutants_list}
    mutant_set = {number_index: {"killed": set(), "non-killed": set(), "passed": set(), "failed": set()}
                  for number_index in mutants_list}

    for mutant, passed_test_cases in mutants2passed_test_cases.items():
        line = mutants2lines[mutant]
        for passed_test_case in passed_test_cases:
            mutant_set[mutant]["passed"].add(passed_test_case)
            if passed_test_case in original_line_test_case_data[f"{line}"]["test_cases"]["passed_test_cases"]:
                mutant_set[mutant]["non-killed"].add(passed_test_case)
            else:
                mutant_set[mutant]["killed"].add(passed_test_case)

    for mutant, failed_test_cases in mutants2failed_test_cases.items():
        line = mutants2lines[mutant]
        for failed_test_case in failed_test_cases:
            mutant_set[mutant]["failed"].add(failed_test_case)
            if failed_test_case in original_line_test_case_data[f"{line}"]["test_cases"]["failed_test_cases"]:
                mutant_set[mutant]["non-killed"].add(failed_test_case)
            else:
                mutant_set[mutant]["killed"].add(failed_test_case)

    for index, test_cases_sets in mutant_set.items():
        mutant_suspicion[index]["stats"]["akp"] = len(
            test_cases_sets["killed"].intersection(test_cases_sets["passed"]))
        mutant_suspicion[index]["stats"]["anp"] = len(
            test_cases_sets["non-killed"].intersection(test_cases_sets["passed"]))
        mutant_suspicion[index]["stats"]["akf"] = len(
            test_cases_sets["killed"].intersection(test_cases_sets["failed"]))
        mutant_suspicion[index]["stats"]["anf"] = len(
            test_cases_sets["non-killed"].intersection(test_cases_sets["failed"]))
    mutant_suspicion = CalculateSuspiciousnessByMBFL(formula, mutant_suspicion)

    for mutant in mutant_suspicion.keys():
        line = mutants2lines[mutant]
        line_suspicion[line]["mutants"].append(mutant)
        if line_suspicion[line]["suspicion"] < mutant_suspicion[mutant]["suspicion"]:
            line_suspicion[line]["suspicion"] = mutant_suspicion[mutant]["suspicion"]
    return line_suspicion


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
            print(project_name)
            len_methods = len(data['methods'])
            len_lines = len(data['lines'])
            len_mutation = len(data['mutation'])
            len_ftest = len(data['ftest'])
            len_rtest = len(data['rtest'])
            # Begin MBFL
            method2lines = data['edge2']
            lines2rtest = data['edge10']
            lines2ftest = data['edge']

            with open(f'./data/page_rank/difference/{dataset_name}/{project_name}.json', 'r') as diff_file:
                difference = json.load(diff_file)
                logging.info("Load difference from JSON file")

            with open(f'./data/page_rank/passed_test_cases/{dataset_name}/{project_name}.json', 'r') as passed_test_cases_file:
                passed_test_cases = json.load(passed_test_cases_file)
                logging.info("Load passed test case from JSON file")

            for formula in formulas:
                if formula != Formula.GP13:
                    continue
                with open(f'./data/sbfl/{dataset_name}/{Formula.get_formula_name(formula)}/{project_name}.json', 'r') as sbfl_file:
                    sbfl_result = json.load(sbfl_file)
                    logging.info("Load passed test case from JSON file")

                # Reduce statements with low suspiciousness and passed test case with low contribution
                # These two kinds of data should be reduced based on pre-computed result
                statements_reduced = reduce_statements(
                    lines.values(), difference, 0.7)
                passed_test_cases_reduced = reduce_passed_test_cases(
                    rtest.values(), passed_test_cases, 0.7)

                mutant2line_reduced, mutant2rtest_reduced, mutant2ftest_reduced, mutant_list = refactor_data(
                    statements_reduced, passed_test_cases_reduced, data["edge12"], data["edge13"], data["edge14"])
                for formula in formulas:
                    line_suspicion = MBFL(mutants2lines=mutant2line_reduced, mutants_list=mutant_list,
                                          line_list=lines.values(), original_line_test_case_data=sbfl_result["line suspicion"],
                                          mutants2passed_test_cases=mutant2rtest_reduced,
                                          mutants2failed_test_cases=mutant2ftest_reduced,
                                          formula=formula)
                    result = {
                        "proj": project_name,
                        "formula": Formula.get_formula_name(formula),
                        # "method suspicion": method_suspicion,
                        "line suspicion": line_suspicion
                    }

                    dictionary_to_json(
                        result, f"./data/mbfl/{dataset_name}/{Formula.get_formula_name(formula)}/{project_name}.json")
                    exit(0)