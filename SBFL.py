import json
import math
from enum import Enum


class Formula(Enum):
    GP13 = 0,
    OCHIAI = 1,
    JACCARD = 2,
    OP2 = 3,
    TARANTULA = 4,
    DSTAR = 5


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

    # 计算每条代码行的怀疑度
    for line in line_suspicion:
        ef, ep, nf, np = line_suspicion[line].values()
        if ef + nf > 0 and ef + ep > 0:
            line_suspicion[line]['suspicion'] = math.pow(
                ef, star_value) / ((ef + nf) * (ef + ep))
        else:
            line_suspicion[line]['suspicion'] = 0

    return line_suspicion


if __name__ == '__main__':
    cal_names = ['Dstar']
    dataset = ['Lang']

    for data_value in dataset:
        with open(f'pkl_data/{data_value}.json', 'r') as rf:
            datas = json.load(rf)

        for data in datas:
            lines = data["lines"]
            failed_test_count: int = len(data["ftest"])
            passed_test_count: int = len(data["rtest"])
            print(passed_test_count)
            # 存储每条代码行的 ef, ep, nf, np 值
            line_suspicion = {number_index: {'ef': 0, 'ep': 0, 'nf': 0, 'np': 0}
                              for number_index in data['lines'].values()}

            # 检查测试用例覆盖的代码行

            # 更新 ef, ep, nf, np 值
            for [line_index, ftest_index] in data['edge']:
                line_suspicion[line_index]['ef'] += 1
            for line_index in lines.values():
                line_suspicion[line_index]['nf'] = failed_test_count - \
                    line_suspicion[line_index]['ef']
            for [line_index, ftest_index] in data['edge10']:
                line_suspicion[line_index]['ep'] += 1
            for line_index in lines.values():
                line_suspicion[line_index]['np'] = passed_test_count - \
                    line_suspicion[line_index]['ep']
            ds_result = Dstar(line_suspicion)
            # 处理 ds_result，例如输出或保存怀疑度结果
            print(ds_result)
