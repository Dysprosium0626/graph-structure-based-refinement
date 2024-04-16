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
    return result


def evaluate_contribution():
    pass


if __name__ == "__main__":
    all_results = pd.DataFrame()

    dataset = ['Lang']
    formulas = [formula for _,
                formula in Formula.__members__.items()]
    for dataset_name in dataset:
        with open(f'pkl_data/{dataset_name}.json', 'r') as rf:
            structural_data = json.load(rf)
            for formula in formulas:
                MBFL_sum_up_evaluation = {
                    "formula": Formula.get_formula_name(formula), "results": {}}
                SBFL_sum_up_evaluation = {
                    "formula": Formula.get_formula_name(formula), "results": {}}
                FTMES_sum_up_evaluation = {
                    "formula": Formula.get_formula_name(formula), "results": {}}
                for data in structural_data:
                    project_name = data['proj']
                    fault = data['ans']
                    methods = data['methods']
                    lines = data['lines']
                    method2lines = data['edge2']

                    # MBFL
                    MBFL_directory_path = f'./data/baseline/mbfl/{dataset_name}/{Formula.get_formula_name(formula)}'
                    result = get_top_suspicious_lines_from_all_files(
                        MBFL_directory_path, project_name, fault, method2lines)
                    MBFL_sum_up_evaluation["results"][project_name] = result


                    # SBFL
                    SBFL_directory_path = f'./data/sbfl/{dataset_name}/{Formula.get_formula_name(formula)}'
                    result = get_top_suspicious_lines_from_all_files(
                        SBFL_directory_path, project_name, fault, method2lines)
                    SBFL_sum_up_evaluation["results"][project_name] = result

                    # FTMES
                    FTMES_directory_path = f'./data/baseline/ftmes/{dataset_name}/{Formula.get_formula_name(formula)}'
                    result = get_top_suspicious_lines_from_all_files(
                        FTMES_directory_path, project_name, fault, method2lines)
                    FTMES_sum_up_evaluation["results"][project_name] = result

                dictionary_to_json(
                    MBFL_sum_up_evaluation, f"./data/baseline/mbfl/{dataset_name}/result/{Formula.get_formula_name(formula)}.json")

                dictionary_to_json(
                    SBFL_sum_up_evaluation, f"./data/baseline/sbfl/{dataset_name}/result/{Formula.get_formula_name(formula)}.json")

                dictionary_to_json(
                    FTMES_sum_up_evaluation, f"./data/baseline/ftmes/{dataset_name}/result/{Formula.get_formula_name(formula)}.json")

    # Initialize a DataFrame to store the accumulated results
    columns = ['Formula', 'Technique', 'Top1', 'Top3',
               'Top5', 'Top10', 'FR', 'AR']
    accumulated_results = pd.DataFrame(columns=columns)

    # Iterate over the datasets and formulas
    for dataset_name in dataset:
        for formula in formulas:
            formula_name = Formula.get_formula_name(formula)

            # Initialize the sums for each technique
            sums = {
                'MBFL': {key: 0 for key in ['top1', 'top3', 'top5', 'top10', 'FR', 'AR', 'MTP']},
                'SBFL': {key: 0 for key in ['top1', 'top3', 'top5', 'top10', 'FR', 'AR', 'MTP']},
                'FTMES': {key: 0 for key in ['top1', 'top3', 'top5', 'top10', 'FR', 'AR', 'MTP']}
            }

            # Load the sum up evaluation results for each technique
            MBFL_path = f"./data/baseline/mbfl/{dataset_name}/result/{formula_name}.json"
            SBFL_path = f"./data/baseline/sbfl/{dataset_name}/result/{formula_name}.json"
            FTMES_path = f"./data/baseline/ftmes/{dataset_name}/result/{formula_name}.json"

            MBFL_results = json.load(open(MBFL_path))['results']
            SBFL_results = json.load(open(SBFL_path))['results']
            FTMES_results = json.load(open(FTMES_path))['results']

            # Accumulate results for each project and technique
            for technique, results in [('MBFL', MBFL_results), ('SBFL', SBFL_results), ('FTMES', FTMES_results)]:
                for project_name, result in results.items():
                    for key in ['top1', 'top3', 'top5', 'top10', 'FR', 'AR']:
                        sums[technique][key] += result[key]
                sums[technique]['FR'] = sums[technique]['FR'] / len(results)
                sums[technique]['AR'] = sums[technique]['AR'] / len(results)
                # Add the accumulated sums to the DataFrame
                row = [formula_name, technique] + [sums[technique][key]
                                                   for key in ['top1', 'top3', 'top5', 'top10', 'FR', 'AR']]
                accumulated_results.loc[len(accumulated_results)] = row

    # Write the accumulated results to an Excel file
    excel_path = 'accumulated_results.xlsx'
    accumulated_results.to_excel(excel_path, index=False)

    print(f"Accumulated results saved to {excel_path}")
