# Undergraduate Thesis: Graph-based Suspiciousness Refinement for MBFL

## Getting Started

These instructions will guide you through the process of setting up the project on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them.

```bash
pip install -r requirement.txt
```


## Usage

This project consists of several steps to evaluate the suspiciousness of lines and methods based on SBFL, and contribution value of test cases. Follow these steps in order to get the results:

### Preprocess

Evaluate the suspiciousness of lines and methods based on SBFL, and the contribution value of test cases.

```bash
python preprocess.py
```

### Construct Graph

Construct a graph for further analysis.

```bash
python graph.py
```

### PageRank

Run the PageRank algorithm on the constructed graph.

```bash
python pagerank.py
```

### Reduction

Reduce the number of statements and test cases based on the specified ratios. Provide the `reduced_statements_ratio` and `reduced_test_cases_ratio` as command-line arguments.

```bash
python mbfl.py <reduced_statements_ratio> <reduced_test_cases_ratio>
```

For example, to reduce both statements and test cases by 70%, you would run:

```bash
python mbfl.py 0.7 0.7
```

### Evaluation

Finally, evaluate the results.

```bash
python evaluation.py
```