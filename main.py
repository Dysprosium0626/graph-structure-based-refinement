import subprocess
import numpy as np
from tqdm import tqdm


def run_script(script_name, args=[]):
    """Helper function to run a python script with optional arguments."""
    command = ['python', script_name] + args
    subprocess.run(command, check=True)


if __name__ == "__main__":
    # Run the first three scripts
    run_script('preprocess.py')
    run_script('graph.py')
    run_script('pagerank.py')

    # Parameters for mbfl.py
    ratios = np.arange(0, 1.2, 0.2)

    # Run mbfl.py with different combinations of parameters
    total_iterations = len(ratios) ** 3
    with tqdm(total=total_iterations, desc='Running mbfl.py', unit='iter') as pbar:
        for a in ratios:
            for b in ratios:
                for c in ratios:
                    a = round(a, 1)
                    b = round(b, 1)
                    c = round(c, 1)
                    run_script('mbfl.py', [str(a), str(b), str(c)])
                    pbar.update(1)

    # Finally, run the evaluation script
    run_script('evaluation.py')

    print("All processes completed successfully.")
