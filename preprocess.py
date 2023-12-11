import json
import math
from enum import Enum
from util import *


class Formula(Enum):
    GP13 = 0,
    OCHIAI = 1,
    JACCARD = 2,
    OP2 = 3,
    TARANTULA = 4,
    DSTAR = 5

    @staticmethod
    def get_formula_name(formula) -> str:
        if formula == Formula.GP13:
            return "GP13"
        elif formula == Formula.OCHIAI:
            return "Ochiai"
        elif formula == Formula.JACCARD:
            return "Jaccard"
        elif formula == Formula.OP2:
            return "OP2"
        elif formula == Formula.TARANTULA:
            return "Tarantula"
        elif formula == Formula.DSTAR:
            return "DSTAR"


def GP13(line_suspicion):
    for line in line_suspicion:
        ef, ep, nf, np = line_suspicion[line].values()
        total_tests = ef + ep + nf + np
        line_suspicion[line]['suspicion'] = ef / \
            total_tests if total_tests > 0 else 0
    return line_suspicion


def Ochiai(line_suspicion):
    for line in line_suspicion:
        ef, ep, nf, np = line_suspicion[line].values()
        denominator = math.sqrt((ef + nf) * (ef + ep))
        line_suspicion[line]['suspicion'] = ef / \
            denominator if denominator > 0 else 0
    return line_suspicion


def Jaccard(line_suspicion):
    for line in line_suspicion:
        ef, ep, nf, np = line_suspicion[line].values()
        denominator = ef + nf + ep
        line_suspicion[line]['suspicion'] = ef / \
            denominator if denominator > 0 else 0
    return line_suspicion


def OP2(line_suspicion):
    for line in line_suspicion:
        ef, ep, nf, np = line_suspicion[line].values()
        line_suspicion[line]['suspicion'] = ef - np / (np + ep + 1)
    return line_suspicion


def Tarantula(line_suspicion):
    total_ef = sum([line_suspicion[line]['ef'] for line in line_suspicion])
    total_ep = sum([line_suspicion[line]['ep'] for line in line_suspicion])

    for line in line_suspicion:
        ef, ep, nf, np = line_suspicion[line].values()
        ef_ratio = ef / total_ef if total_ef > 0 else 0
        ep_ratio = ep / total_ep if total_ep > 0 else 0
        line_suspicion[line]['suspicion'] = ef_ratio / \
            (ef_ratio + ep_ratio) if (ef_ratio + ep_ratio) > 0 else 0
    return line_suspicion


def Dstar(line_suspicion, star_value=2):
    for line in line_suspicion:
        ef, ep, nf, np = line_suspicion[line].values()
        if ef + nf > 0 and ef + ep > 0:
            line_suspicion[line]['suspicion'] = math.pow(
                ef, star_value) / ((ef + nf) * (ef + ep))
        else:
            line_suspicion[line]['suspicion'] = 0

    return line_suspicion


def formula_factory(formula_type, line_suspicion):
    if formula_type == Formula.GP13:
        return GP13(line_suspicion)
    elif formula_type == Formula.OCHIAI:
        return Ochiai(line_suspicion)
    elif formula_type == Formula.JACCARD:
        return Jaccard(line_suspicion)
    elif formula_type == Formula.OP2:
        return OP2(line_suspicion)
    elif formula_type == Formula.TARANTULA:
        return Tarantula(line_suspicion)
    elif formula_type == Formula.DSTAR:
        return Dstar(line_suspicion)
    else:
        raise ValueError("Unsupported formula type")


def SBFL_with_contribution(data, formula):
    # 存储每条代码行的 ef, ep, nf, np 值
    line_suspicion = {number_index: {'ef': 0, 'ep': 0, 'nf': 0, 'np': 0}
                      for number_index in data['lines'].values()}
    # 更新 ef, ep, nf, np 值
    for [line_index, _] in data['edge']:
        line_suspicion[line_index]['ef'] += 1
    for line_index in lines.values():
        line_suspicion[line_index]['nf'] = failed_test_count - \
            line_suspicion[line_index]['ef']
    for [line_index, _] in data['edge10']:
        line_suspicion[line_index]['ep'] += 1
    for line_index in lines.values():
        line_suspicion[line_index]['np'] = passed_test_count - \
            line_suspicion[line_index]['ep']
    SBFL_result = formula_factory(formula, line_suspicion)

    test_case_contribution = contribution(data, line_suspicion)
    return SBFL_result, test_case_contribution


def contribution(data, line_suspicion):
    test_case_contribution = {
        "ftest": {test_case_index: 0 for test_case_index in data["ftest"].values()},
        "rtest": {test_case_index: 0 for test_case_index in data["rtest"].values()},
    }
    for [line_index, failed_test_case_index] in data['edge']:
        test_case_contribution["ftest"][failed_test_case_index] += line_suspicion[line_index]["suspicion"]
    for [line_index, passed_test_case_index] in data['edge10']:
        test_case_contribution["rtest"][passed_test_case_index] += line_suspicion[line_index]["suspicion"]
    print(test_case_contribution)
    return test_case_contribution


if __name__ == '__main__':
    dataset = ['Lang']
    formulas = formula_list = [formula for _,
                               formula in Formula.__members__.items()]
    for data_value in dataset:
        with open(f'pkl_data/{data_value}.json', 'r') as rf:
            datas = json.load(rf)

        for data in datas:
            proj = data["proj"]
            lines = data["lines"]
            failed_test_count: int = len(data["ftest"])
            passed_test_count: int = len(data["rtest"])
            print(passed_test_count)
            # 存储每条代码行的 ef, ep, nf, np 值
            # TODO(Yue): 扩展到所有formula
            SBFL_result, test_case_contribution = SBFL_with_contribution(
                data=data, formula=formulas[0])

            # 处理 ds_result，保存怀疑度结果
            result = {
                "proj": proj,
                "formula": Formula.get_formula_name(formulas[0]),
                "line suspicion": SBFL_result
            }
            dictionary_to_json(result, f"/data/sbfl/{data_value}/{proj}.json")
            dictionary_to_json(test_case_contribution,
                               f"/data/contribution/{data_value}/{proj}.json")
