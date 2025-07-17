# ParaSuit - Benchmarks

Using ParaSuit, you can install 12 benchmarks

| Benchmark | version | Benchmark | version | Benchmark | version |
|:------:|:------------|:------:|:------------|:------:|:------------|
| combine   | 0.4.0 | gawk      | 5.1.0  | nano         | 4.9   |
| diff      | 3.7   | gcal      | 4.1    | sed          | 4.8   |
| du        | 8.32  | grep      | 3.4    | trueprint    | 5.4   |
| enscript  | 1.6.6 | ls        | 8.32   | xorriso     | 1.5.2 |

## Install Benchmarks
To install a benchmark to test, use the following command.
```
# Example for grep-3.4
/parasuit/benchmarks$ bash building_benchmark.sh grep-3.4
```

If you want to install multiple benchmarks, you can simply list benchmarks.
```
/parasuit/benchmarks$ bash building_benchmark.sh grep-3.4 gcal-4.1 gawk-5.1.0 ...
```

If you want to install all 12 benchmarks, just run the following command.
```
/parasuit/benchmarks$ bash building_benchmark.sh all
```

Finally, if you want to install multiple cores for a benchmark, use '--n-objs' option.
```
/parasuit/benchmarks$ bash building_benchmark.sh --n-objs 10 grep-3.4
```

## Run ParaSuit
### Testing Benchmarks
After the installation is complete, you can run ParaSuit with that benchmark. For more information about running ParaSuit, you can access the README.md file in the parent directory (/parasuit).

```bash
/parasuit/benchmarks $ parasuit -t 3600 -d ParaSuit grep-3.4/obj-llvm/src/grep.bc grep-3.4/obj-gcov/src/grep
```
Format : parasuit -t <time_budget> -d <output_dir> <path_to_bc_file(llvm)> <path_to_exec_file(gcov)>


## Analyzing Results
### Branch Coverage
When the experiment is completed, ParaSuit provides a line graph showing how many branches were covered in each time budget section through the 'report_coverage.py' program. If you run the command below, ParaSuit returns the graph by creating a 'coverage_result.png' file in the same directory.
```
/parasuit/benchmarks$ python3 report_coverage.py --benchmark grep-3.4 ParaSuit
usage: report_coverage.py [-h] [--benchmark STR] [--graph PATH] [--budget TIME] [DIRS ...]
```

If you want to return multiple results in a single graph, just list the names of the directories, such as:
```
/parasuit/benchmarks$ python3 report_coverage.py --benchmark grep-3.4 ParaSuit ParaSuit1 ...
```

### Bug-Finding
ParaSuit also provides the "report_bugs.py" program to extract test-cases that cause system errors among those generated through the experiment. When you execute the command below, ParaSuit automatically detects bug-triggering test cases. As a result of execution, ParaSuit returns the test case causing the bug, its arguments, system crash signal, and the location (file name and line) of the code where the bug occurs.
```
/parasuit/benchmarks$ python3 report_bugs.py --benchmark grep-3.4 ParaSuit
```

Similar to branch coverage, bug-finding also allows you to search multiple directories at once by simply listing the directories.

```
/parasuit/benchmarks$ python3 report_bugs.py --benchmark grep-3.4 ParaSuit ParaSuit2 ...
```

★ Caution: Multiple directories must all target the same benchmark.


### Options for Reporting Programs
+ /benchmarks/report_coverage.py

| Option | Description |
|:------:|:------------|
| `-h, --help`  | Show help message and exit |
| `DIRS`        | Names of directories to draw figure |
| `--benchmark` | Name of benchmark & verison |
| `--graph`     | Path to save coverage graph |
| `--budget`    | Time budget of the coverage graph |

+ /benchmarks/report_bugs.py
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
