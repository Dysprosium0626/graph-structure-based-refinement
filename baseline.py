import json
import logging
from util import *


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


def get_mutant_to_lines(mutation_to_line_list):
    mutant_to_lines, mutations = {}, []
    for [mutant, line] in mutation_to_line_list:
        mutant_to_lines[mutant] = line
        mutations.append(mutant)

    return mutant_to_lines, mutations


def get_mutant_to_test_cases(mutant2rtest, mutant2ftest):
    mutant_to_passed_test_case, mutant_to_failed_test_case = {}, {}
    for [mutant, rtest] in mutant2rtest:
        if mutant not in mutant_to_passed_test_case:
            mutant_to_passed_test_case[mutant] = [rtest]
        else:
            mutant_to_passed_test_case[mutant].append(rtest)

    for [mutant, ftest] in mutant2ftest:
        if mutant in mutant_to_passed_test_case:
            if mutant not in mutant_to_failed_test_case:
                mutant_to_failed_test_case[mutant] = [ftest]
            else:
                mutant_to_failed_test_case[mutant].append(ftest)
    return mutant_to_passed_test_case, mutant_to_failed_test_case

# MBFL


def baseline_MBFL(mutants2lines, mutants_list, line_list, original_line_test_case_data, mutants2passed_test_cases, mutants2failed_test_cases, formula):
    line_suspicion = {number_index: {"mutants": [], "suspicion": 0}
                      for number_index in line_list}
    mutant_suspicion = {number_index: {"stats": {'akp': 0, 'anp': 0, 'akf': 0, 'anf': 0}, "suspicion": 0}
                        for number_index in mutants_list}
    mutant_set = {number_index: {"killed": set(), "non-killed": set(), "passed": set(), "failed": set()}
                  for number_index in mutants_list}

    for mutant, passed_test_cases in mutants2passed_test_cases.items():
        line = mutants2lines[mutant]
        for passed_test_case in passed_test_cases:
            mutant_set[mutant]["killed"].add(passed_test_case)
        mutant_set[mutant]["passed"] = set(
            original_line_test_case_data[f"{line}"]["test_cases"]["passed_test_cases"])
        mutant_set[mutant]["non-killed"] = set(
            original_line_test_case_data[f"{line}"]["test_cases"]["passed_test_cases"]).difference(mutant_set[mutant]["killed"])

    for mutant, failed_test_cases in mutants2failed_test_cases.items():
        line = mutants2lines[mutant]
        for failed_test_case in failed_test_cases:
            mutant_set[mutant]["failed"].add(failed_test_case)
            mutant_set[mutant]["killed"].add(failed_test_case)
        mutant_set[mutant]["failed"] = set(
            original_line_test_case_data[f"{line}"]["test_cases"]["failed_test_cases"])
        mutant_set[mutant]["non-killed"].union(set(
            original_line_test_case_data[f"{line}"]["test_cases"]["failed_test_cases"]).difference(mutant_set[mutant]["killed"]))

    for index, test_cases_sets in mutant_set.items():
        mutant_suspicion[index]["stats"]["akp"] = len(
            test_cases_sets["killed"].intersection(test_cases_sets["passed"]))
        mutant_suspicion[index]["stats"]["anp"] = len(
            test_cases_sets["non-killed"].intersection(test_cases_sets["passed"]))
        mutant_suspicion[index]["stats"]["akf"] = len(
            test_cases_sets["killed"].intersection(test_cases_sets["failed"]))
        mutant_suspicion[index]["stats"]["anf"] = len(
            test_cases_sets["non-killed"].intersection(test_cases_sets["failed"]))
    mutant_suspicion = CalculateSuspiciousnessByMBFL(
        formula, mutant_suspicion)
    # print("mutant set", mutant_set)
    # print("mutant suspicion", mutant_suspicion)
    for mutant in mutant_suspicion.keys():
        line = mutants2lines[mutant]
        line_suspicion[line]["mutants"].append(mutant)
        if line_suspicion[line]["suspicion"] < mutant_suspicion[mutant]["suspicion"]:
            line_suspicion[line]["suspicion"] = mutant_suspicion[mutant]["suspicion"]
    return line_suspicion, mutant_suspicion

# Contribution-based


def baseline_contribution_based():
    pass


def baseline_failed_test_oriented(mutants2lines, mutants_list, line_list, passed_test_case_length, original_line_test_case_data, mutants2passed_test_cases, mutants2failed_test_cases, formula):
    line_suspicion = {number_index: {"mutants": [], "suspicion": 0}
                      for number_index in line_list}
    mutant_suspicion = {number_index: {"stats": {'akp': 0, 'anp': 0, 'akf': 0, 'anf': 0}, "suspicion": 0}
                        for number_index in mutants_list}
    mutant_set = {number_index: {"killed": set(), "non-killed": set(), "passed": set(), "failed": set()}
                  for number_index in mutants_list}

    for mutant, passed_test_cases in mutants2passed_test_cases.items():
        line = mutants2lines[mutant]
        for passed_test_case in passed_test_cases:
            mutant_set[mutant]["killed"].add(passed_test_case)
        mutant_set[mutant]["passed"] = set(
            original_line_test_case_data[f"{line}"]["test_cases"]["passed_test_cases"])
        mutant_set[mutant]["non-killed"] = set(
            original_line_test_case_data[f"{line}"]["test_cases"]["passed_test_cases"]).difference(mutant_set[mutant]["killed"])

    for mutant, failed_test_cases in mutants2failed_test_cases.items():
        line = mutants2lines[mutant]
        for failed_test_case in failed_test_cases:
            mutant_set[mutant]["failed"].add(failed_test_case)
            mutant_set[mutant]["killed"].add(failed_test_case)
        mutant_set[mutant]["failed"] = set(
            original_line_test_case_data[f"{line}"]["test_cases"]["failed_test_cases"])
        mutant_set[mutant]["non-killed"].union(set(
            original_line_test_case_data[f"{line}"]["test_cases"]["failed_test_cases"]).difference(mutant_set[mutant]["killed"]))

    # In this step, the coverage information replaces killing information in order to avoid run the mutants
    # which means akp = the length of kill + non-kill passed test cases
    # anp = total number of passed test cases - akp
    for index, test_cases_sets in mutant_set.items():
        mutant_suspicion[index]["stats"]["akp"] = len(
            test_cases_sets["killed"]) + len(test_cases_sets["non-killed"])
        mutant_suspicion[index]["stats"]["anp"] = passed_test_case_length - \
            mutant_suspicion[index]["stats"]["akp"]
        mutant_suspicion[index]["stats"]["akf"] = len(
            test_cases_sets["killed"].intersection(test_cases_sets["failed"]))
        mutant_suspicion[index]["stats"]["anf"] = len(
            test_cases_sets["non-killed"].intersection(test_cases_sets["failed"]))
    mutant_suspicion = CalculateSuspiciousnessByMBFL(
        formula, mutant_suspicion)

    for mutant in mutant_suspicion.keys():
        line = mutants2lines[mutant]
        line_suspicion[line]["mutants"].append(mutant)
        if line_suspicion[line]["suspicion"] < mutant_suspicion[mutant]["suspicion"]:
            line_suspicion[line]["suspicion"] = mutant_suspicion[mutant]["suspicion"]
    return line_suspicion, mutant_suspicion


def baseline_random_mutant():
    pass


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
            # Begin MBFL
            method2lines = data['edge2']
            lines2rtest = data['edge10']
            lines2ftest = data['edge']

            original_MTP = len_mutation * (len_ftest + len_rtest)

            mutation2lines = data['edge12']
            mutation2rtest = data['edge13']
            mutation2ftest = data['edge14']

            mutation_to_lines, mutations = get_mutant_to_lines(mutation2lines)
            mutant_to_passed_test_case, mutant_to_failed_test_case = get_mutant_to_test_cases(
                mutation2rtest, mutation2ftest)

            for formula in formulas:
                with open(f'./data/sbfl/{dataset_name}/{Formula.get_formula_name(formula)}/{project_name}.json', 'r') as sbfl_file:
                    sbfl_result = json.load(sbfl_file)
                    logging.info("Load passed test case from JSON file")

                # MBFL
                mbfl_line_suspicion, mbfl_mutant_suspicion = baseline_MBFL(mutation_to_lines, mutations, lines.values(
                ), sbfl_result["line suspicion"], mutant_to_passed_test_case, mutant_to_failed_test_case, formula)

                result = {
                    "proj": project_name,
                    "formula": Formula.get_formula_name(formula),
                    "num_of_mutants": len(mutation),
                    "num_of_test_cases": len_ftest + len_rtest,
                    "original_MTP": original_MTP,
                    "line suspicion": mbfl_line_suspicion,
                    "mutant suspicion": mbfl_mutant_suspicion
                }
                dictionary_to_json(
                    result, f"./data/baseline/mbfl/{dataset_name}/{Formula.get_formula_name(formula)}/{project_name}.json")

                # ftmes
                ftmes_line_suspicion, ftmes_mutant_suspicion = baseline_failed_test_oriented(mutation_to_lines, mutations, lines.values(
                ), len_rtest, sbfl_result["line suspicion"],  mutant_to_passed_test_case, mutant_to_failed_test_case, formula)

                result = {
                    "proj": project_name,
                    "formula": Formula.get_formula_name(formula),
                    "num_of_mutants": len(mutation),
                    "num_of_test_cases": len_ftest + len_rtest,
                    "original_MTP": original_MTP,
                    "line suspicion": ftmes_line_suspicion,
                    "mutant suspicion": ftmes_mutant_suspicion
                }
                dictionary_to_json(
                    result, f"./data/baseline/ftmes/{dataset_name}/{Formula.get_formula_name(formula)}/{project_name}.json")
