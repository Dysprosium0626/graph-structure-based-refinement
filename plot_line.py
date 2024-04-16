
import matplotlib.pyplot as plt
import pandas as pd


from util import Formula

if __name__ == "__main__":
    # 设置绘图的大小
    fig, axs = plt.subplots(3, 2, figsize=(12, 8))  # 假设你有6个公式，所以创建3行2列的子图

    # 打开Excel文件
    excel_file = 'Lang_evaluation_results.xlsx'

    # 获取Excel文件中所有工作表的名称，每个工作表对应一个公式
    xls = pd.ExcelFile(excel_file)
    sheet_names = xls.sheet_names

    # 遍历每个工作表（公式）
    for i, sheet_name in enumerate(sheet_names):
        # 读取当前工作表的数据
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # 定位当前的子图位置
        ax1 = axs[i // 2, i % 2]
        ax2 = ax1.twinx()

        # 假设'reduced_test_cases_ratio'和'reduced_mutant_ratio'是横轴的两组数据
        x = df['reduced_test_cases_ratio'].unique()
        x.sort()

        # 绘制MAP的折线图
        ax1.plot(x, df.groupby('reduced_test_cases_ratio')[
                'MAP'].mean(), label='MAP (reduced test cases)', color='blue')
        ax1.plot(x, df.groupby('reduced_mutant_ratio')['MAP'].mean(
        ), label='MAP (reduced mutants)', color='blue', linestyle='dashed')

        # 绘制MFR的折线图
        ax2.plot(x, df.groupby('reduced_test_cases_ratio')[
                'MFR'].mean(), label='MFR (reduced test cases)', color='orange')
        ax2.plot(x, df.groupby('reduced_mutant_ratio')['MFR'].mean(
        ), label='MFR (reduced mutants)', color='orange', linestyle='dashed')

        # 设置子图标题和轴标签
        ax1.set_title(sheet_name)
        ax1.set_xlabel('Reduction ratio')
        ax1.set_ylabel('MAP')
        ax2.set_ylabel('MFR')

        # 显示图例
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

    # 调整子图之间的间距
    plt.tight_layout()

    # 显示图形
    plt.show()
