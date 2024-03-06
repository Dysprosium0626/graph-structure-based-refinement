import json
import os
from collections import Counter
import re
import sys

from util import Formula


def get_top_suspicious_lines(json_data):
    sorted_lines = sorted(
        [(line, details.get('suspicion', 0))
         for line, details in json_data.items()],
        key=lambda item: item[1],
        reverse=True
    )
    top_line_numbers = [int(line[0]) for line in sorted_lines]
    return top_line_numbers


def get_top_suspicious_lines_from_all_files(directory_path, file_name, fault, method2line):
    file_path = os.path.join(directory_path, f"{file_name}.json")
    method_stat = {method: {"top1": 0, "top3": 0,
                            "top5": 0, "top10": 0, "sum_rank": 0, "line_count": 0, "first": sys.maxsize}for method in fault}

    with open(file_path, 'r') as f:
        json_data = json.load(f)
    top_lines = get_top_suspicious_lines(json_data["line suspicion"])
    for [method, line] in method2line:
        if method in fault:
            if line in top_lines[:1]:
                method_stat[method]["top1"] += 1
            if line in top_lines[:3]:
                method_stat[method]["top3"] += 1
            if line in top_lines[:5]:
                method_stat[method]["top5"] += 1
            if line in top_lines[:10]:
                method_stat[method]["top10"] += 1
            rank = top_lines.index(line) + 1
            if method_stat[method]["first"] > rank:
                method_stat[method]["first"] = rank
            method_stat[method]["sum_rank"] += rank
            method_stat[method]["line_count"] += 1
    result = {"top1": 0, "top3": 0, "top5": 0,
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


if __name__ == "__main__":
    dataset = ['Lang']
    formulas = [formula for _,
                formula in Formula.__members__.items()]
    for dataset_name in dataset:
        with open(f'pkl_data/{dataset_name}.json', 'r') as rf:
            structural_data = json.load(rf)
        for formula in formulas:
            sum_up_evaluation = {"formula": Formula.get_formula_name(formula), "top1": 0, "top3": 0, "top5": 0,
                                "top10": 0, "MFR": 0.0, "MAR": 0.0, "fault_count": 0}
            evaluation = dict()
            for data in structural_data:
                project_name = data['proj']
                fault = data['ans']
                methods = data['methods']
                lines = data['lines']
                method2lines = data['edge2']
                directory_path = f'./data/mbfl/{dataset_name}/{Formula.get_formula_name(formula)}'
                result = get_top_suspicious_lines_from_all_files(
                    directory_path, project_name, fault, method2lines)
                evaluation[project_name] = result
                sum_up_evaluation["top1"] += result["top1"]
                sum_up_evaluation["top3"] += result["top3"]
                sum_up_evaluation["top5"] += result["top5"]
                sum_up_evaluation["top10"] += result["top10"]
                sum_up_evaluation["MFR"] += result["FR"]
                sum_up_evaluation["MAR"] += result["AR"]
                sum_up_evaluation["fault_count"] += 1
            sum_up_evaluation["MFR"] = sum_up_evaluation["MFR"] / \
                sum_up_evaluation["fault_count"]
            sum_up_evaluation["MAR"] = sum_up_evaluation["MAR"] / \
                sum_up_evaluation["fault_count"]
            print(sum_up_evaluation)
