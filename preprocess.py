"""
Preprocess: preprocess stage is aimed to get pre-computed SBFL suspiciousness of methods and statements, as well as the contribution value of test cases

"""
import json
import math
from enum import Enum
from util import *


def CalculateSuspiciousnessBySBFL(formula_type, line_suspicion):
    if formula_type == Formula.GP13:
        return GP13(line_suspicion, FaultLocalization.SBFL)
    elif formula_type == Formula.OCHIAI:
        return Ochiai(line_suspicion, FaultLocalization.SBFL)
    elif formula_type == Formula.JACCARD:
        return Jaccard(line_suspicion, FaultLocalization.SBFL)
    elif formula_type == Formula.OP2:
        return OP2(line_suspicion, FaultLocalization.SBFL)
    elif formula_type == Formula.TARANTULA:
        return Tarantula(line_suspicion, FaultLocalization.SBFL)
    elif formula_type == Formula.DSTAR:
        return Dstar(line_suspicion, FaultLocalization.SBFL)
    else:
        raise ValueError("Unsupported formula type")


def SBFL_with_contribution(data, formula):
    failed_test_set: set = set(data["ftest"].values())
    passed_test_set: set = set(data["rtest"].values())
    # 存储每条代码行的 ef, ep, nf, np 值
    line_suspicion = {number_index: {"stats": {'ef': 0, 'ep': 0, 'nf': 0, 'np': 0, }, "test_cases": {'passed_test_cases': [], 'failed_test_cases': []}}
                      for number_index in data['lines'].values()}
    method_suspicion = {number_index: {"stats": {'ef': 0, 'ep': 0, 'nf': 0, 'np': 0}}
                        for number_index in data['methods'].values()}
    line_set = {number_index: {'ef': {'case_number': set()}, 'ep': {'case_number': set()}, 'nf': {'case_number': set()}, 'np': {'case_number': set()}}
                for number_index in data['lines'].values()}
    method_set = {number_index: {'ef': {'case_number': set()}, 'ep': {'case_number': set()}, 'nf': {'case_number': set()}, 'np': {'case_number': set()}}
                  for number_index in data['methods'].values()}
    # 更新 ef, ep, nf, np 值
    for [line_index, test_case] in data['edge']:
        line_set[line_index]['ef']['case_number'].add(test_case)
        line_set[line_index]['ef']['count'] = len(
            line_set[line_index]['ef']['case_number'])
    for line_index in lines.values():
        line_set[line_index]['nf']['case_number'] = failed_test_set.difference(
            line_set[line_index]['ef']['case_number'])
        line_set[line_index]['nf']['count'] = len(
            line_set[line_index]['nf']['case_number'])
    for [line_index, test_case] in data['edge10']:
        line_set[line_index]['ep']['case_number'].add(test_case)
        line_set[line_index]['ep']['count'] = len(
            line_set[line_index]['ef']['case_number'])
    for line_index in lines.values():
        line_set[line_index]['np']['case_number'] = passed_test_set.difference(
            line_set[line_index]['ep']['case_number'])
        line_set[line_index]['np']['count'] = len(
            line_set[line_index]['np']['case_number'])

    for [method, line] in data['edge2']:
        method_set[method]['ef']['case_number'] = method_set[method]['ef']['case_number'].union(
            line_set[line]['ef']['case_number'])
        method_set[method]['ep']['case_number'] = method_set[method]['ep']['case_number'].union(
            line_set[line]['ep']['case_number'])
        method_set[method]['nf']['case_number'] = failed_test_set.difference(
            method_set[method]['ef']['case_number'])
        method_set[method]['np']['case_number'] = passed_test_set.difference(
            method_set[method]['ep']['case_number'])

    for line in data['lines'].values():
        line_suspicion[line]['stats']['ef'] = len(
            line_set[line]['ef']['case_number'])
        line_suspicion[line]['stats']['nf'] = len(
            line_set[line]['nf']['case_number'])
        line_suspicion[line]['stats']['ep'] = len(
            line_set[line]['ep']['case_number'])
        line_suspicion[line]['stats']['np'] = len(
            line_set[line]['np']['case_number'])
        line_suspicion[line]['test_cases']['passed_test_cases'] = list(
            line_set[line]['ep']['case_number'])
        line_suspicion[line]['test_cases']['failed_test_cases'] = list(
            line_set[line]['ef']['case_number'])

    for method in data['methods'].values():
        method_suspicion[method]['stats']['ef'] = len(
            method_set[method]['ef']['case_number'])
        method_suspicion[method]['stats']['nf'] = len(
            method_set[method]['nf']['case_number'])
        method_suspicion[method]['stats']['ep'] = len(
            method_set[method]['ep']['case_number'])
        method_suspicion[method]['stats']['np'] = len(
            method_set[method]['np']['case_number'])

    line_SBFL_result = CalculateSuspiciousnessBySBFL(formula, line_suspicion)
    method_SBFL_result = CalculateSuspiciousnessBySBFL(
        formula, method_suspicion)
    test_case_contribution = contribution(data, line_suspicion, data['lines'].values(
    ), data['ftest'].values(), data['rtest'].values())
    return method_SBFL_result, line_SBFL_result, test_case_contribution


def contribution(data, line_suspicion, line_list, ftest_list, rtest_list):
    test_case_contribution = {
        "ftest": {test_case_index: 0 for test_case_index in data["ftest"].values()},
        "rtest": {test_case_index: 0 for test_case_index in data["rtest"].values()},
    }
    for [line_index, failed_test_case_index] in data['edge']:
        if line_index in line_list and failed_test_case_index in ftest_list:
            test_case_contribution["ftest"][failed_test_case_index] += line_suspicion[line_index]["suspicion"]
    for [line_index, passed_test_case_index] in data['edge10']:
        if line_index in line_list and passed_test_case_index in rtest_list:
            test_case_contribution["rtest"][passed_test_case_index] += line_suspicion[line_index]["suspicion"]
    return test_case_contribution


if __name__ == '__main__':
    # To support different dataset, just add the project name here
    # dataset = ['Chart', 'Cli', 'JxPath', 'Lang', 'Math']
    dataset = ['Lang']
    formulas = formula_list = [formula for _,
                               formula in Formula.__members__.items()]
    for dataset_name in dataset:
        with open(f'pkl_data/{dataset_name}.json', 'r') as rf:
            structural_data = json.load(rf)

        for data in structural_data:
            proj = data["proj"]
            lines = data["lines"]
            # 存储每条代码行的 ef, ep, nf, np 值
            for formula in formulas:
                method_suspicion, line_suspicion, test_case_contribution = SBFL_with_contribution(
                    data=data, formula=formula)

                # 处理 ds_result，保存怀疑度结果
                result = {
                    "proj": proj,
                    "formula": Formula.get_formula_name(formula),
                    "method suspicion": method_suspicion,
                    "line suspicion": line_suspicion
                }
                dictionary_to_json(
                    result, f"./data/sbfl/{dataset_name}/{Formula.get_formula_name(formula)}/{proj}.json")
                dictionary_to_json(test_case_contribution,
                                   f"./data/contribution/{dataset_name}/{proj}.json")
