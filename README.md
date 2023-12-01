# ParaSuit

Enhancing Usability and Performance of Symbolic Execution via Fully Automated Parameter Tuning

<img src="https://github.com/anonymousfse2024/parasuit/assets/150991397/d405595c-1eb7-4cd9-a100-f30450bf3bb4" width=30%, height=30%/>


## Installation
We run ParaSuit with KLEE, one of the most commonly used symbolic execution tool.

### Install KLEE
We use KLEE-2.1 version on Ubuntu-18.04. So if you want to use the same version of the tool as ours, install KLEE by following the steps in the URL [KLEE-2.1 installation](https://klee.github.io/releases/docs/v2.1/build-llvm60/).
You have to clone KLEE with following command
```bash
git clone -b 2.1.x https://github.com/klee/klee.git
```

And if you want to use a version different from KLEE-2.1, select the "docs" of desired version from the URL [KLEE Releases](https://klee.github.io/releases/). After selecting the version, click “Getting Started with KLEE
Install KLEE by following the instructions in the "Build from source (with LLVM *)" category.


### Build ParaSuit
First, you have to clone our source code. 
```bash
$ git clone https://github.com/anonymousfse2024/parasuit.git
```

Second, in the "parasuit" directory, build ParaSuit with "setup.py" directory. And then, install the pip packages used to run ParaSuit.
```bash
$ cd parasuit
/parasuit $ (sudo) python3 setup.py install
/parasuit $ pip3 install numpy gensim scikit-learn
```

Third, with "building_benchmarks.sh" file in the "parasuit/benchmarks" directory, you have to install benchmarks you want to execute. In this instruction, we will use "trueprint-5.4" for example.
```bash
/parasuit $ cd benchmarks
/parasuit/benchmarks $ bash building_benchmarks.sh trueprint-5.4
```

### Run ParaSuit
Finally, you can run ParaSuit with following code. (e.g. trueprint-5.4)
```bash
/parasuit/benchmarks $ parasuit -t 43200 -p klee_default.json -d ParaSuit trueprint-5.4/obj-llvm/src/trueprint.bc trueprint-5.4/obj-gcov/src/trueprint
```
Format : parasuit -t <time_budget> -p <json_file> -d <output_dir> <path_to_bc_file(llvm)> <path_to_exec_file(gcov)>
+ -t : Time Budget (seconds)
+ -p : Initial Parameter Values (.json file)
+ -d : Output Directory


Then, you will see logs as follows.
```bash
[INFO] ParaSuit : ParaSuit Begin!
[INFO] ParaSuit : Coverage will be recoreded at "ParaSuit/coverage.csv" at every iteration.
[INFO] ParaSuit : Selected ParaSuit. Parameter values will be tuned.
[INFO] ParaSuit : All configuration loaded. Start testing.
[INFO] ParaSuit : Iteration: 1 Iteration budget: 30 Total budget: 3600 Time Elapsed: 36 Coverage: 348
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
/parasuit/benchmarks $ parasuit -t 43200 -p klee_default.json -d KLEEdefault --tool klee trueprint-5.4/obj-llvm/src/trueprint.bc trueprint-5.4/obj-gcov/src/trueprint
```


## Reporting Results
### Branch Coverage
If you want to get results about how many branches ParaSuit has covered, run the following command.
```bash
/parasuit/benchmarks $ python3 report_coverage.py ParaSuit KLEEdefault --benchmark trueprint-5.4
```

If the command was executed successfully, you will get a graph like the following in a file named "br_result.png".
<img src="https://github.com/anonymousfse2024/parasuit/assets/150991397/1da78ffb-254b-463f-9257-b0f70a38b6e8" width=30%, height=30%/>


### Bug Finding
If you want to check information about what bugs ParaSuit has found, run the following command.
```bash
/parasuit/benchmarks $ python3 report_bugs.py ParaSuit
```

If the command was executed successfully, you will get a bug table in a file named "bug_result.txt".


## Usage
```
$ parasuit --help
usage: parasuit [-h] [--klee KLEE] [--klee-replay KLEE_REPLAY] [--gcov GCOV] [-p JSON] [--iteration-time-budget INT] [--n-tune INT] [--clust-range INT] [-d OUTPUT_DIR]
                [--gcov-depth GCOV_DEPTH] [--tool TOOL] [-t INT]
                [llvm_bc] [gcov_obj]
...
```


### Optional Arguments
| Option | Description |
|:------:|:------------|
| `-h, --help` | show help message and exit |
| `-d, --output-dir` | Directory where experiment results are saved |
| `--gcov-depth` | Depth from the obj-gcov directory to the directory where the gcov file was created |
| `--tool TOOL` | Select a tool to run symbolic execution |


### Executable Settings
| Option | Description |
|:------:|:------------|
| `--klee` | Path to "klee" executable |
| `--klee-replay` | Path to "klee-replay" executable |
| `--gcov GCOV` | Path to "gcov" executable (default=gcov) |


### Hyperparameters
The hyperparameter `--parameter-values` is very important in our tool. You can check all the hyperparameters by passing `--help` option to SymTuner.
| Option | Description |
|:------:|:------------|
| `-p, --parameter-values` | Path to json file that defines parameter spaces |
| `--iteration-time-budget` | Time budget for each iteration |
| `--n-tune` | Number of times each parameter is compared in the parameter selection step |
| `--clust-range` | Clustering execution cycle at the parameter value sampling stage |

If you do not specify parameter values, ParaSuit will use the parameter values of [KLEE webpage](https://klee.github.io/docs/coreutils-experiments/)(OSDI'08).  
You can give your own parameter space with `--parameter-values` option such as "-p klee_default.json".

In the json file, there are two entries: `space` and `defaults`. For `space`, it includes symbolic parameters and a seed option that must be tuned. For `defaults`, the parameters to be used as initial parameter values and their values are defined. If you want to use new parameter values in experiment, edit the defaults section of the json file.


### Required Arguments
| Option | Description |
|:------:|:------------|
| `-t, --budget` | Total time budget of ParaSuit |
| `llvm_bc` | LLVM bitecode file for klee |
| `gcov_obj` | Executable with gcov support |



## Source Code Structure
Here are breif descriptions of files. Some less-important files may be omitted.
```
.
├── benchmarks                  Testing & reporting directory
    ├── report_bugs.py          Reporting bug finding results
    └── report_coverage.py      Reporting branch coverage results
└── parasuit                    Main source code directory
    ├── bin.py                  Entry point of ParaSuit
    ├── boolean.py              Tuning boolean parameters
    ├── errcheck.py             Handling parameter values that cause errors
    ├── exechandler.py          Converting parameter values to parameter command format of symbolic executor
    ├── keyword_filter.py       Removing default or useless parameters from parameter set
    ├── klee.py                 Running KLEE 
    ├── parameters.py           Including parameters and description of symbolic executor
    ├── paramselect.py          Algorithm of Parameter Selection
    ├── parasuit.py             Core algorithm of ParaSuit
    ├── psconstruct.py          Algorithm of Parameter Space Construction
    ├── pvsample.py             Algorithm of Parameter Value Sampling
    ├── setdefault.py           Extract the minimum default parameters from the parameter value given as input
    ├── string.py               Tuning string parameters
    ├── symbolic_executor.py    Interface for all symbolic executors (e.g., KLEE)
    └── symparams.py            Tuning symbolic parameters (e.g., --sym-arg)
```


