import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from util import Formula

if __name__ == "__main__":
    dataset = ['Lang']
    formulas = [formula for _, formula in Formula.__members__.items()]

    for dataset_name in dataset:
        # 设置绘图的大小
        plt.figure(figsize=(12, 8))

        # 遍历每个formula，为每个formula创建一个子图
        for i, formula in enumerate(formulas, 1):
            plt.subplot(3, 2, i)  # 假设你有6个formula，所以创建3行2列的子图
            with open(f'./data/baseline/gbsr/{dataset_name}/result/{Formula.get_formula_name(formula)}.json', 'r') as rf:
                results = json.load(rf)
                GBSR_AR_values = []
                for project_name, stat in results["results"].items():
                    GBSR_AR_values.append(stat["AR"])
            with open(f'./data/baseline/mbfl/{dataset_name}/result/{Formula.get_formula_name(formula)}.json', 'r') as rf:
                results = json.load(rf)
                MBFL_AR_values = []
                for project_name, stat in results["results"].items():
                    MBFL_AR_values.append(stat["AR"])
            with open(f'./data/baseline/sbfl/{dataset_name}/result/{Formula.get_formula_name(formula)}.json', 'r') as rf:
                results = json.load(rf)
                SBFL_AR_values = []
                for project_name, stat in results["results"].items():
                    SBFL_AR_values.append(stat["AR"])
            methods = ['SBFL', 'MBFL', 'GBSR']
            # 创建小提琴图
            sns.violinplot(
                data=[SBFL_AR_values, MBFL_AR_values, GBSR_AR_values])

            # 设置每个子图的标题
            plt.xticks(ticks=np.arange(len(methods)), labels=methods)

            plt.title(Formula.get_formula_name(formula))
            plt.xlabel('Method')
            plt.ylabel('AR')

        # 调整子图之间的间距
        plt.tight_layout()

        # 显示图形
        plt.show()


