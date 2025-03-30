# ParaSuit

Fully Automated and Program-Adaptive Parameter Tuning for Symbolic Execution

<img src="https://github.com/anonymousfse2024/parasuit/assets/150991397/d405595c-1eb7-4cd9-a100-f30450bf3bb4" width=30%, height=30%/>



### Build ParaSuit
First, you have to clone our source code. 
```bash
$ git clone https://github.com/unknownoopsla2025/parasuit.git
```

Second, build ParaSuit with Dockerfile. If you run the command below, ParaSuit and KLEE-2.1 will be built, and a benchmark (grep-3.4) will be installed.
```bash
$ cd parasuit
/parasuit $ docker build -t parasuit .
```

Third, connect to Docker using the command below. The command will take you to a directory named parasuit.
```bash
/parasuit $ docker run -it --ulimit='stack=-1:-1' parasuit
```

### Run ParaSuit
Finally, you can run ParaSuit with the following code. (e.g., grep-3.4) We provide the optimal parameter set provided by [KLEE](https://klee-se.org/docs/coreutils-experiments/) as initial parameter values.
```bash
/parasuit/benchmarks $ parasuit -t 3600 -d ParaSuit grep-3.4/obj-llvm/src/grep.bc grep-3.4/obj-gcov/src/grep
```
Format : parasuit -t <time_budget> -d <output_dir> <path_to_bc_file(llvm)> <path_to_exec_file(gcov)>
+ -t : Time Budget (seconds)
+ -d : Output Directory

If data for the target program exists, you will see logs as follows.
```bash
[INFO] ParaSuit : Coverage will be recorded at "ParaSuit/coverage.csv" at every iteration.
[INFO] ParaSuit : Loading parameter selection data.
[INFO] ParaSuit : All configuration loaded. Start testing.
[INFO] ParaSuit : Iteration: 1 Total budget: 3600 Time Elapsed: 153 Coverage: 1698 Iteration Coverage: 1698
```

Otherwise, the following log will be observed.
```bash
[INFO] ParaSuit : Coverage will be recorded at "ParaSuit/coverage.csv" at every iteration.
[INFO] ParaSuit : Extracting parameter selection data.
[INFO] ParaSuit : All configuration loaded. Start testing.
[INFO] ParaSuit : Iteration: 1 Total budget: 3600 Time Elapsed: 127 Coverage: 978 Iteration Coverage: 978
```

When the time budget expires without error, you can see the following output.
```bash
[INFO] ParaSuit : Iteration: 25 Total budget: 3600 Time Elapsed: 3385 Coverage: 2596 Iteration Coverage: 1272
[INFO] ParaSuit : Iteration: 26 Total budget: 3600 Time Elapsed: 3451 Coverage: 2604 Iteration Coverage: 1610
[INFO] ParaSuit : Iteration: 27 Total budget: 3600 Time Elapsed: 3601 Coverage: 2768 Iteration Coverage: 1842
[INFO] ParaSuit : ParaSuit done. Achieve 2768 coverage
```


## Reporting Results
### Branch Coverage
If you want to get results about how many branches ParaSuit has covered, run the following command.
```bash
/parasuit/benchmarks $ python3 report_coverage.py ParaSuit --benchmark grep-3.4
```

If the command was executed successfully, you will get a graph like the following in a file named "coverage_result.png".
![coverage_result](https://github.com/user-attachments/assets/b6ae9b8d-8122-44cf-b5fd-b8de30b5d4c4)


### Bug Finding
If you want to check information about the bugs ParaSuit has found, run the following command.
```bash
/parasuit/benchmarks $ python3 report_bugs.py ParaSuit
```

If the command was executed successfully, you will get a bug report in a file named "bug_result.txt".


## Usage
```
$ parasuit --help
usage: parasuit [-h] [--klee KLEE] [--klee-replay KLEE_REPLAY] [--gcov GCOV] [-p JSON]
                [--iteration-time-budget INT] [--threshold FLOAT] [--n-trial INT] 
                [-d OUTPUT_DIR] [--gcov-depth GCOV_DEPTH] [-t INT] [llvm_bc] [gcov_obj]
```


### Optional Arguments
| Option | Description |
|:------:|:------------|
| `-h, --help` | show help message and exit |
| `-d, --output-dir` | Directory where experiment results are saved |
| `--gcov-depth` | Depth from the obj-gcov directory to the directory where the gcov file was created |


### Executable Settings
| Option | Description |
|:------:|:------------|
| `--klee` | Path to "klee" executable |
| `--klee-replay` | Path to "klee-replay" executable |
| `--gcov` | Path to "gcov" executable |


### Hyperparameters
| Option | Description |
|:------:|:------------|
| `-p, --parameter-values` | Initial parameter set for tuning symbolic execution (default: [Coreutils Experiments](https://klee-se.org/docs/coreutils-experiments/)) |
| `--iteration-time-budget` | Time budget for each iteration |
| `--threshold` | Minimum silhouette score required to sample values using the exploit policy |
| `--n-tune` | Number of times each parameter is tried in the extraction step |


### Required Arguments
| Option | Description |
|:------:|:------------|
| `-t, --budget` | Total time budget of ParaSuit |
| `llvm_bc` | LLVM bitecode file for klee |
| `gcov_obj` | Executable with gcov support |


## Usage of Other Programs
### /benchmarks/report_bugs.py
```
/parasuit/benchmarks$ python3 report_bugs.py --help
usage: report_bugs.py [-h] [--benchmark STR] [--table PATH] [DIRS ...]
```
| Option | Description |
|:------:|:------------|
| `-h, --help`  | Show this help message and exit |
| `DIRS`        | Name of directory to detect bugs |
| `--benchmark` | Name of benchmark & verison |
| `--table`     | Path to save bug table graph |


### /benchmarks/report_coverage.py
```
/parasuit/benchmarks$ python3 report_coverage.py --help
usage: report_coverage.py [-h] [--benchmark STR] [--graph PATH] [--budget TIME] [DIRS ...]
```
| Option | Description |
|:------:|:------------|
| `-h, --help`  | Show help message and exit |
| `DIRS`        | Names of directories to draw figure |
| `--benchmark` | Name of benchmark & verison |
| `--graph`     | Path to save coverage graph |
| `--budget`    | Time budget of the coverage graph |



## Source Code Structure
Here are brief descriptions of the files. Some less important files may be omitted.
```
.
├── benchmarks                  Testing & reporting directory
    ├── report_bugs.py          Reporting bug finding results
    └── report_coverage.py      Reporting branch coverage results
├── data                        Directory for storing information about previously tested programs
    ├── candidates              Store the used values during trials in the Extraction stage
    ├── covered_branches        Store the branch log covered when each candidate value is used
    ├── init_values             Store the initial value of each selected parameter for value sampling
    ├── min_parameters          Store the minimal parameter set required for KLEE to run for each program
    └── param_scores            Store the score of each parameter from the most recent iteration
└── parasuit                    Main source code directory
    ├── bin.py                  Entry point of ParaSuit
    ├── evaluate.py             Evaluate and analyze the test-cases generated by the iteration
    ├── extract.py              Algorithm of Extraction stage
    ├── klee.py                 Running KLEE 
    ├── param_select.py         Algorithm of Parameter selection stage
    └── value_sample.py         Algorithm of Value sampling stage
```



## Accessing Experimental Results 
If you want to access data about the experiments of ParaSuit, you can download it at the following URL: 
https://github.com/unknownoopsla2025/parasuit/releases/tag/v1.0

Download the following file in the URL
+ expr_result.zip

By clicking file or running the following codes on the terminal, you can download the data files.

```bash
$ wget https://github.com/unknownoopsla2025/parasuit/releases/download/v1.0/parasuit_experiments.zip
$ unzip expr_result_merged.zip
```

You can access 3 kinds of data
+ The testcase directories for 5 programs: xorriso, gcal, grep, gawk, and combine.
+ Cumulative branch coverage over time for 12 programs.
+ The bug-finding logs found by ParaSuit at least once across 5 repetitions.
