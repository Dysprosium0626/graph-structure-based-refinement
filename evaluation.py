import csv
import json
import os
from collections import Counter
import re
import sys

import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill

from util import Formula, dictionary_to_json


import sys
import os
import json


def get_top_suspicious_lines(json_data):
    # 首先按照怀疑度进行排序
    sorted_lines = sorted(
        [(line, details.get('suspicion', 0))
         for line, details in json_data.items()],
        key=lambda item: item[1],
        reverse=True
    )

    # 然后，为具有相同怀疑度的行分配相同的排名
    current_rank = len(sorted_lines)
    next_suspicion = None
    for index, (line, suspicion) in enumerate(reversed(sorted_lines)):
        actual_index = len(sorted_lines) - 1 - index
        # The last one, give it the rank
        if index == current_rank - 1:
            next_suspicion = suspicion
        if suspicion != next_suspicion:
            current_rank = actual_index + 1
            next_suspicion = suspicion
        sorted_lines[actual_index] = (line, suspicion, current_rank)

    # 提取行号和排名
    top_line_numbers = [(int(line[0]), line[2]) for line in sorted_lines]
    return top_line_numbers


def get_top_suspicious_lines_from_all_files(directory_path, file_name, fault, method2line):
    file_path = os.path.join(directory_path, f"{file_name}.json")
    method_stat = {method: {"top1": 0, "top3": 0,
                            "top5": 0, "top10": 0, "sum_rank": 0, "line_count": 0, "first": sys.maxsize} for method in fault}

    with open(file_path, 'r') as f:
        json_data = json.load(f)
    top_lines = get_top_suspicious_lines(json_data["line suspicion"])
    # 处理每一行和方法
    for [method, line] in method2line:
        if method in fault:
            line_rank = next(
                (rank for (l, rank) in top_lines if l == line), None)
            if line_rank is not None:
                if line_rank == 1:
                    method_stat[method]["top1"] += 1
                if line_rank <= 3:
                    method_stat[method]["top3"] += 1
                if line_rank <= 5:
                    method_stat[method]["top5"] += 1
                if line_rank <= 10:
                    method_stat[method]["top10"] += 1
                if method_stat[method]["first"] > line_rank:
                    method_stat[method]["first"] = line_rank
                method_stat[method]["sum_rank"] += line_rank
                method_stat[method]["line_count"] += 1

    # 计算最终结果
    result = {"project_name": project_name, "top1": 0, "top3": 0, "top5": 0,
              "top10": 0, "FR": 0.0, "AR": 0.0, "fault_count": 0}
    for method, stat in method_stat.items():
        if stat["top1"] != 0:
            result["top1"] += 1
        if stat["top3"] != 0:
            result["top3"] += 1
        if stat["top5"] != 0:
            result["top5"] += 1
        if stat["top10"] != 0:
            result["top10"] += 1
        result["FR"] += stat["first"] if stat["first"] != sys.maxsize else 0
        result["AR"] += stat["sum_rank"] / \
            stat["line_count"] if stat["line_count"] != 0 else 0

    result["fault_count"] = len(fault)
    result["MTP"] = json_data["current_MTP"]
    return result


def save_selected_results(selected_statements_ratio, reduced_test_cases_ratio, reduced_mutant_ratio, method):
    '''
    Save the selected results with given ratios for plotting
    '''
    if method == 'gbsr':
        return selected_statements_ratio == 0.2 and reduced_test_cases_ratio == 0.8 and reduced_mutant_ratio == 0.8
    elif method == 'cbtcr':
        return reduced_test_cases_ratio == 0.8
    elif method == 'random':
        return selected_statements_ratio == 0.2 and reduced_mutant_ratio == 0.8


if __name__ == "__main__":

    # dataset = ['Chart', 'Cli', 'JxPath', 'Lang', 'Math']
    dataset = ['Lang']
    formulas = [formula for _,
                formula in Formula.__members__.items()]
    selected_statements_ratios = np.arange(0.2, 1.2, 0.2)
    reduced_test_cases_ratios = np.arange(0.2, 1.2, 0.2)
    reduced_mutant_ratios = np.arange(0.2, 1.2, 0.2)

    # gbsr
    for dataset_name in dataset:
        gbsr_all_results = pd.DataFrame()
        with open(f'pkl_data/{dataset_name}.json', 'r') as rf:
            structural_data = json.load(rf)
        for selected_statements_ratio in selected_statements_ratios:
            for reduced_test_cases_ratio in reduced_test_cases_ratios:
                for reduced_mutant_ratio in reduced_mutant_ratios:
                    selected_statements_ratio = round(
                        selected_statements_ratio, 1)
                    reduced_test_cases_ratio = round(
                        reduced_test_cases_ratio, 1)
                    reduced_mutant_ratio = round(reduced_mutant_ratio, 1)
                    for formula in formulas:
                        sum_up_evaluation = {"formula": Formula.get_formula_name(formula), "top1": 0, "top3": 0, "top5": 0,
                                             "top10": 0, "MFR": 0.0, "MAR": 0.0, "MTP": 0.0, "fault_count": 0, "results": {}}
                        result = {"project_name": "", "top1": 0, "top3": 0, "top5": 0,
                                  "top10": 0, "FR": 0.0, "AR": 0.0, "fault_count": 0, "MTP": 0}
                        for data in structural_data:
                            project_name = data['proj']
                            fault = data['ans']
                            methods = data['methods']
                            lines = data['lines']
                            method2lines = data['edge2']
                            directory_path = f"./data/mbfl/{dataset_name}/{selected_statements_ratio:.1f}/{reduced_test_cases_ratio:.1f}/{reduced_mutant_ratio:.1f}/{Formula.get_formula_name(formula)}"
                            result = get_top_suspicious_lines_from_all_files(
                                directory_path, project_name, fault, method2lines)
                            sum_up_evaluation["top1"] += result["top1"]
                            sum_up_evaluation["top3"] += result["top3"]
                            sum_up_evaluation["top5"] += result["top5"]
                            sum_up_evaluation["top10"] += result["top10"]
                            sum_up_evaluation["MFR"] += result["FR"]
                            sum_up_evaluation["MAR"] += result["AR"]
                            sum_up_evaluation["MTP"] += result["MTP"]
                            sum_up_evaluation["fault_count"] += 1
                            sum_up_evaluation["results"][project_name] = result
                        sum_up_evaluation["MFR"] = sum_up_evaluation["MFR"] / \
                            sum_up_evaluation["fault_count"]
                        sum_up_evaluation["MAR"] = sum_up_evaluation["MAR"] / \
                            sum_up_evaluation["fault_count"]
                        if save_selected_results(selected_statements_ratio, reduced_test_cases_ratio, reduced_mutant_ratio, method='gbsr'):
                            dictionary_to_json(
                                sum_up_evaluation, f"./data/baseline/gbsr/{dataset_name}/result/{Formula.get_formula_name(formula)}.json")
                        csv_row = {
                            'function': sum_up_evaluation["formula"],
                            'type': 'worst',
                            'selected_statements_ratio': selected_statements_ratio,
                            'reduced_test_cases_ratio': reduced_test_cases_ratio,
                            "reduced_mutant_ratio": reduced_mutant_ratio,
                            'ftop1': sum_up_evaluation["top1"],
                            'ftop3': sum_up_evaluation["top3"],
                            'ftop5': sum_up_evaluation["top5"],
                            'ftop10': sum_up_evaluation["top10"],
                            'MAP': sum_up_evaluation["MAR"],
                            'MFR': sum_up_evaluation["MFR"],
                            'MTP': sum_up_evaluation["MTP"],
                        }
                        temp_df = pd.DataFrame([csv_row])
                        gbsr_all_results = pd.concat(
                            [gbsr_all_results, temp_df], ignore_index=True)

        # Convert pd to excel and calculate score for each row
        excel_file_name = f'{dataset_name}_evaluation_results.xlsx'
        with pd.ExcelWriter(excel_file_name, engine='openpyxl') as writer:
            for formula in formulas:
                formula_df = gbsr_all_results[gbsr_all_results['function']
                                              == Formula.get_formula_name(formula)]
                ftop1_normalized = (formula_df['ftop1'] - formula_df['ftop1'].min()) / (
                    formula_df['ftop1'].max() - formula_df['ftop1'].min())
                map_normalized = 1 - (formula_df['MAP'] - formula_df['MAP'].min()) / (
                    formula_df['MAP'].max() - formula_df['MAP'].min())
                mfr_normalized = 1 - (formula_df['MFR'] - formula_df['MFR'].min()) / (
                    formula_df['MFR'].max() - formula_df['MFR'].min())
                weights = {'ftop1': 1, 'MAP': 1, 'MFR': 1}
                formula_df.loc[:, 'score'] = weights['ftop1'] * ftop1_normalized + \
                    weights['MAP'] * map_normalized + \
                    weights['MFR'] * mfr_normalized
                top_five_indices = formula_df.nsmallest(5, 'score').index
                formula_df.to_excel(
                    writer, sheet_name=Formula.get_formula_name(formula), index=False)
            writer.save()

    # contribution
    for dataset_name in dataset:
        cbtcr_all_results = pd.DataFrame()
        with open(f'pkl_data/{dataset_name}.json', 'r') as rf:
            structural_data = json.load(rf)
        for reduced_test_cases_ratio in reduced_test_cases_ratios:
            reduced_test_cases_ratio = round(
                reduced_test_cases_ratio, 1)
            for formula in formulas:
                sum_up_evaluation = {"formula": Formula.get_formula_name(formula), "top1": 0, "top3": 0, "top5": 0,
                                     "top10": 0, "MFR": 0.0, "MAR": 0.0, "MTP": 0.0, "fault_count": 0, "results": {}}
                result = {"project_name": "", "top1": 0, "top3": 0, "top5": 0,
                          "top10": 0, "FR": 0.0, "AR": 0.0, "fault_count": 0, "MTP": 0}
                for data in structural_data:
                    project_name = data['proj']
                    fault = data['ans']
                    methods = data['methods']
                    lines = data['lines']
                    method2lines = data['edge2']
                    directory_path = f"./data/baseline/cbtcr/{dataset_name}/1.0/{reduced_test_cases_ratio:.1f}/1.0/{Formula.get_formula_name(formula)}"
                    result = get_top_suspicious_lines_from_all_files(
                        directory_path, project_name, fault, method2lines)
                    sum_up_evaluation["top1"] += result["top1"]
                    sum_up_evaluation["top3"] += result["top3"]
                    sum_up_evaluation["top5"] += result["top5"]
                    sum_up_evaluation["top10"] += result["top10"]
                    sum_up_evaluation["MFR"] += result["FR"]
                    sum_up_evaluation["MAR"] += result["AR"]
                    sum_up_evaluation["MTP"] += result["MTP"]
                    sum_up_evaluation["fault_count"] += 1
                    sum_up_evaluation["results"][project_name] = result
                sum_up_evaluation["MFR"] = sum_up_evaluation["MFR"] / \
                    sum_up_evaluation["fault_count"]
                sum_up_evaluation["MAR"] = sum_up_evaluation["MAR"] / \
                    sum_up_evaluation["fault_count"]
                if save_selected_results(0, reduced_test_cases_ratio, 0, method='cbtcr'):
                    dictionary_to_json(
                        sum_up_evaluation, f"./data/baseline/cbtcr/{dataset_name}/result/{Formula.get_formula_name(formula)}.json")
                csv_row = {
                    'function': sum_up_evaluation["formula"],
                    'type': 'worst',
                    'selected_statements_ratio': selected_statements_ratio,
                    'reduced_test_cases_ratio': reduced_test_cases_ratio,
                    "reduced_mutant_ratio": reduced_mutant_ratio,
                    'ftop1': sum_up_evaluation["top1"],
                    'ftop3': sum_up_evaluation["top3"],
                    'ftop5': sum_up_evaluation["top5"],
                    'ftop10': sum_up_evaluation["top10"],
                    'MAP': sum_up_evaluation["MAR"],
                    'MFR': sum_up_evaluation["MFR"],
                    'MTP': sum_up_evaluation["MTP"],
                }
                temp_df = pd.DataFrame([csv_row])
                cbtcr_all_results = pd.concat(
                    [cbtcr_all_results, temp_df], ignore_index=True)

        # Convert pd to excel and calculate score for each row
        excel_file_name = f'{dataset_name}_evaluation_results_cbtcr.xlsx'
        with pd.ExcelWriter(excel_file_name, engine='openpyxl') as writer:
            for formula in formulas:
                formula_df = cbtcr_all_results[cbtcr_all_results['function']
                                               == Formula.get_formula_name(formula)]
                ftop1_normalized = (formula_df['ftop1'] - formula_df['ftop1'].min()) / (
                    formula_df['ftop1'].max() - formula_df['ftop1'].min())
                map_normalized = 1 - (formula_df['MAP'] - formula_df['MAP'].min()) / (
                    formula_df['MAP'].max() - formula_df['MAP'].min())
                mfr_normalized = 1 - (formula_df['MFR'] - formula_df['MFR'].min()) / (
                    formula_df['MFR'].max() - formula_df['MFR'].min())
                weights = {'ftop1': 1, 'MAP': 1, 'MFR': 1}
                formula_df.loc[:, 'score'] = weights['ftop1'] * ftop1_normalized + \
                    weights['MAP'] * map_normalized + \
                    weights['MFR'] * mfr_normalized
                top_five_indices = formula_df.nsmallest(5, 'score').index
                formula_df.to_excel(
                    writer, sheet_name=Formula.get_formula_name(formula), index=False)
            writer.save()

    # random
    for dataset_name in dataset:
        random_all_results = pd.DataFrame()
        with open(f'pkl_data/{dataset_name}.json', 'r') as rf:
            structural_data = json.load(rf)
        for selected_statements_ratio in selected_statements_ratios:
            for reduced_mutant_ratio in reduced_mutant_ratios:
                selected_statements_ratio = round(
                    selected_statements_ratio, 1)
                reduced_mutant_ratio = round(
                    reduced_mutant_ratio, 1)
                for formula in formulas:
                    sum_up_evaluation = {"formula": Formula.get_formula_name(formula), "top1": 0, "top3": 0, "top5": 0,
                                        "top10": 0, "MFR": 0.0, "MAR": 0.0, "MTP": 0.0, "fault_count": 0, "results": {}}
                    result = {"project_name": "", "top1": 0, "top3": 0, "top5": 0,
                            "top10": 0, "FR": 0.0, "AR": 0.0, "fault_count": 0, "MTP": 0}
                    for data in structural_data:
                        project_name = data['proj']
                        fault = data['ans']
                        methods = data['methods']
                        lines = data['lines']
                        method2lines = data['edge2']
                        directory_path = f"./data/baseline/random/{dataset_name}/{selected_statements_ratio:.1f}/1.0/{reduced_mutant_ratio}/{Formula.get_formula_name(formula)}"
                        result = get_top_suspicious_lines_from_all_files(
                            directory_path, project_name, fault, method2lines)
                        sum_up_evaluation["top1"] += result["top1"]
                        sum_up_evaluation["top3"] += result["top3"]
                        sum_up_evaluation["top5"] += result["top5"]
                        sum_up_evaluation["top10"] += result["top10"]
                        sum_up_evaluation["MFR"] += result["FR"]
                        sum_up_evaluation["MAR"] += result["AR"]
                        sum_up_evaluation["MTP"] += result["MTP"]
                        sum_up_evaluation["fault_count"] += 1
                        sum_up_evaluation["results"][project_name] = result
                    sum_up_evaluation["MFR"] = sum_up_evaluation["MFR"] / \
                        sum_up_evaluation["fault_count"]
                    sum_up_evaluation["MAR"] = sum_up_evaluation["MAR"] / \
                        sum_up_evaluation["fault_count"]
                    if save_selected_results(selected_statements_ratio, 1.0, reduced_mutant_ratio, method='random'):
                        dictionary_to_json(
                            sum_up_evaluation, f"./data/baseline/random/{dataset_name}/result/{Formula.get_formula_name(formula)}.json")
                    csv_row = {
                        'function': sum_up_evaluation["formula"],
                        'type': 'worst',
                        'selected_statements_ratio': selected_statements_ratio,
                        'reduced_test_cases_ratio': reduced_test_cases_ratio,
                        "reduced_mutant_ratio": reduced_mutant_ratio,
                        'ftop1': sum_up_evaluation["top1"],
                        'ftop3': sum_up_evaluation["top3"],
                        'ftop5': sum_up_evaluation["top5"],
                        'ftop10': sum_up_evaluation["top10"],
                        'MAP': sum_up_evaluation["MAR"],
                        'MFR': sum_up_evaluation["MFR"],
                        'MTP': sum_up_evaluation["MTP"],
                    }
                    temp_df = pd.DataFrame([csv_row])
                    random_all_results = pd.concat(
                        [random_all_results, temp_df], ignore_index=True)

        # Convert pd to excel and calculate score for each row
        excel_file_name = f'{dataset_name}_evaluation_results_random.xlsx'
        with pd.ExcelWriter(excel_file_name, engine='openpyxl') as writer:
            for formula in formulas:
                formula_df = random_all_results[random_all_results['function']
                                                == Formula.get_formula_name(formula)]
                ftop1_normalized = (formula_df['ftop1'] - formula_df['ftop1'].min()) / (
                    formula_df['ftop1'].max() - formula_df['ftop1'].min())
                map_normalized = 1 - (formula_df['MAP'] - formula_df['MAP'].min()) / (
                    formula_df['MAP'].max() - formula_df['MAP'].min())
                mfr_normalized = 1 - (formula_df['MFR'] - formula_df['MFR'].min()) / (
                    formula_df['MFR'].max() - formula_df['MFR'].min())
                weights = {'ftop1': 1, 'MAP': 1, 'MFR': 1}
                formula_df.loc[:, 'score'] = weights['ftop1'] * ftop1_normalized + \
                    weights['MAP'] * map_normalized + \
                    weights['MFR'] * mfr_normalized
                top_five_indices = formula_df.nsmallest(5, 'score').index
                formula_df.to_excel(
                    writer, sheet_name=Formula.get_formula_name(formula), index=False)
            writer.save()
