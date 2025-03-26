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
Finally, you can run ParaSuit with following code. (e.g. grep-3.4) We provide the optimal parameter set provided by [KLEE](https://klee-se.org/docs/coreutils-experiments/) as initial parameter values.
```bash
/parasuit/benchmarks $ parasuit -t 43200 -p initial_values.json -d ParaSuit grep-3.4/obj-llvm/src/grep.bc grep-3.4/obj-gcov/src/grep
```
Format : parasuit -t <time_budget> -p <json_file> -d <output_dir> <path_to_bc_file(llvm)> <path_to_exec_file(gcov)>
+ -t : Time Budget (seconds)
+ -p : Initial Parameter Values (.json file)
+ -d : Output Directory

Then, you will see logs as follows.
```bash
[INFO] ParaSuit : Coverage will be recoreded at "ParaSuit/coverage.csv" at every iteration.
[INFO] ParaSuit : Selected ParaSuit. Parameters will be tuned.
[INFO] ParaSuit : All configuration loaded. Start testing.
[INFO] ParaSuit : Iteration: 1 Iteration budget: 30 Total budget: 43200 Time Elapsed: 42 Coverage: 1364
```

When time bugdet expired without error, you can see the following output.
```bash
[INFO] ParaSuit : Iteration: 365 Iteration budget: 120 Total budget: 43200 Time Elapsed: 42747 Coverage: 879
[INFO] ParaSuit : Iteration: 366 Iteration budget: 120 Total budget: 43200 Time Elapsed: 42912 Coverage: 879
[INFO] ParaSuit : Iteration: 367 Iteration budget: 120 Total budget: 43200 Time Elapsed: 43065 Coverage: 879
[INFO] ParaSuit : Iteration: 368 Iteration budget: 120 Total budget: 43200 Time Elapsed: 43069 Coverage: 879
[INFO] ParaSuit : Iteration: 369 Iteration budget: 120 Total budget: 43200 Time Elapsed: 43234 Coverage: 879
[INFO] ParaSuit : ParaSuit done. Achieve 879 coverage
```

### Run KLEE Default
You can also run KLEE without any tuning by following command below.
```bash
/parasuit/benchmarks $ parasuit -t 43200 -d KLEEdefault --tool klee trueprint-5.4/obj-llvm/src/trueprint.bc trueprint-5.4/obj-gcov/src/trueprint
```


## Reporting Results
### Branch Coverage
If you want to get results about how many branches ParaSuit has covered, run the following command.
```bash
/parasuit/benchmarks $ python3 report_coverage.py ParaSuit KLEEdefault --benchmark trueprint-5.4
```

If the command was executed successfully, you will get a graph like the following in a file named "coverage_result.png".
<img src="https://github.com/anonymousfse2024/parasuit/assets/150991397/1da78ffb-254b-463f-9257-b0f70a38b6e8" width=30%, height=30%/>


### Bug Finding
If you want to check information about what bugs ParaSuit has found, run the following command.
```bash
/parasuit/benchmarks $ python3 report_bugs.py ParaSuit
```

If the command was executed successfully, you will get a bug report in a file named "bug_result.txt".


## Usage
```
$ parasuit --help
usage: parasuit [-h] [--klee KLEE] [--klee-replay KLEE_REPLAY] [--gcov GCOV] [-p JSON] [--iteration-time-budget INT] [--threshold FLOAT] [--n-tune INT] [--clust-range INT] [-d OUTPUT_DIR] [--gcov-depth GCOV_DEPTH] [--tool TOOL] [-t INT] [llvm_bc] [gcov_obj]
```


### Optional Arguments
| Option | Description |
|:------:|:------------|
| `-h, --help` | show help message and exit |
| `-d, --output-dir` | Directory where experiment results are saved |
| `--gcov-depth` | Depth from the obj-gcov directory to the directory where the gcov file was created |
| `--tool TOOL` | Select a tool to run symbolic execution (e.g. parasuit, klee)|


### Executable Settings
| Option | Description |
|:------:|:------------|
| `--klee` | Path to "klee" executable |
| `--klee-replay` | Path to "klee-replay" executable |
| `--gcov GCOV` | Path to "gcov" executable |


### Hyperparameters
| Option | Description |
|:------:|:------------|
| `-p, --parameter-values` | Path to json file that defines parameter spaces |
| `--iteration-time-budget` | Time budget for each iteration |
| `--threshold` | Threshold to group parameters into a group in the parameter selection step |
| `--n-tune` | Number of times each parameter is compared in the parameter selection step |
| `--clust-range` | Clustering execution cycle at the parameter value sampling stage |

In the json file used as the value of --parameter-values, there are two entries: `space` and `defaults`. For `space`, it includes parameters that should be tuned. For `defaults`, it contains parameters whose value must be fixed to a specific value. If you want to use new parameter values in experiment, edit the defaults section of the json file.


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
└── parasuit                    Main source code directory
    ├── bin.py                  Entry point of ParaSuit
    ├── boolean.py              Tuning boolean parameters
    ├── collect.py              Value sampling method when collecting data
    ├── construct_sample.py     Value sampling using clustering
    ├── errcheck.py             Handling parameter values that cause errors
    ├── exechandler.py          Converting parameter values to parameter command format of symbolic executor
    ├── grouping.py             Group parameters and extract representative parameters from each group
    ├── keyword_filter.py       Removing default or useless parameters from parameter set
    ├── klee.py                 Running KLEE 
    ├── parameters.py           Including parameters and description of symbolic executor
    ├── paramselect.py          Algorithm of Parameter Selection
    ├── parasuit.py             Core algorithm of ParaSuit
    ├── setminimum.py           Extract the minimum default parameters from the parameter value given as input
    ├── string.py               Tuning string parameters
    ├── symbolic_executor.py    Interface for all symbolic executors (e.g., KLEE)
    └── symparams.py            Tuning symbolic parameters (--sym-arg, --sym-files)
```



## Accessing Representative Data 
If you want to access data about the experiments of ParaSuit, you can download it at the following URL: 
https://github.com/unknownoopsla2025/parasuit/releases/tag/v1.0

Download the following 3 files in the URL
+ expr_result.z01
+ expr_result.z02
+ expr_result.zip

By clicking each file or running the following codes on the terminal, you can download the data files.

```bash
$ wget https://github.com/unknownoopsla2025/parasuit/releases/download/v1.0/expr_result.zip \
https://github.com/unknownoopsla2025/parasuit/releases/download/v1.0/expr_result.z01 \
https://github.com/unknownoopsla2025/parasuit/releases/download/v1.0/expr_result.z02
```

Place all the split files (expr_result.z01, expr_result.z02, expr_result.zip) in the same directory. Then, merge the files and unzip them.
```bash
$ zip -FF expr_result.zip --out expr_result_merged.zip
$ unzip expr_result_merged.zip
```

You can access 3 kinds of data
+ The testcase directories for 5 programs: xorriso, gcal, grep, gawk, and combine.
+ Cumulative branch coverage over time for 12 programs.
+ The bug-finding logs found by ParaSuit at least once across 5 repetitions.
