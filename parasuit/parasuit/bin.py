from pathlib import Path
import argparse
import json
import shutil
import sys
import time
import csv

# Running KLEE
from parasuit.klee import KLEE
from parasuit.klee import KLEEConvert

# Running ParaSuit
from parasuit.parasuit import ParaSuit


def main(argv=None):

    if argv == None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()

    # Execution settings
    executable = parser.add_argument_group('executable settings')
    executable.add_argument('--klee', default='klee', type=str,
                            help='Path to "klee" executable (default=klee)')
    executable.add_argument('--klee-replay', default='klee-replay', type=str,
                            help='Path to "klee-replay" executable (default=klee-replay)')
    executable.add_argument('--gcov', default='gcov', type=str,
                            help='Path to "gcov" executable (default=gcov)')

    # Hyperparameters
    hyperparameters = parser.add_argument_group('hyperparameters')
    hyperparameters.add_argument('-p', '--parameter-values', default="klee_default.json", type=str, metavar='JSON',
                                 help='Json file defining parameter values')
    hyperparameters.add_argument('--iteration-time-budget', default=120, type=int, metavar='INT',
                                 help='Time budget for each iteration (default=120)')
    hyperparameters.add_argument('--n-tune', default=3, type=int, metavar='INT',
                                 help='Number of times each parameter is compared in the parameter selection step (default=3)')
    hyperparameters.add_argument('--clust-range', default=10, type=int, metavar='INT',
                                 help='Clustering execution cycle at the parameter value sampling stage (default=10)')

    # Others
    parser.add_argument('-d', '--output-dir', default='parasuit-result', type=str,
                        help='Directory where experiment results are saved (default=parasuit-result)')
    parser.add_argument('--gcov-depth', default=1, type=int,
                        help='Depth from the obj-gcov directory to the directory where the gcov file was created (default=1)')
    parser.add_argument('--tool', default='parasuit', type=str,
                        help='Select a tool to run symbolic execution (default=parasuit)')

    # Required arguments
    required = parser.add_argument_group('required arguments')
    required.add_argument('-t', '--budget', default=None, type=int, metavar='INT',
                          help='Total time budget of ParaSuit')
    required.add_argument('llvm_bc', nargs='?', default=None,
                          help='LLVM bitecode file for klee')
    required.add_argument('gcov_obj', nargs='?', default=None,
                          help='Executable with gcov support')
    args = parser.parse_args(argv)


    if args.llvm_bc is None or args.gcov_obj is None or args.budget is None:
        parser.print_usage()
        print('[INFO] ParaSuit : following parameters are required: -t, llvm_bc, gcov_obj')
        sys.exit(1)

    output_dir = Path(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(str(output_dir))
        print('[WARNING] ParaSuit : Existing output directory is deleted: '
                             f'{output_dir}')
    output_dir.mkdir(parents=True)
    coverage_csv = output_dir / 'coverage.csv'
    coverage_csv.touch()
    print(
        f'[INFO] ParaSuit : Coverage will be recoreded at "{coverage_csv}" at every iteration.')

    # Initialize Symbolic Executor
    symbolic_executor = KLEE(args.klee)

    # Load Search_Spaces
    with open(args.parameter_values, 'r') as f:
        parameter_values = json.load(f)

    # Initialize ParaSuit
    parasuit = ParaSuit(args.budget, parameter_values, args.n_tune, args.clust_range)

    # Start Execution
    start = time.time()
    converter = KLEEConvert(args.klee_replay, args.gcov, 10, parameter_values)
    evaluation_argument = {'folder_depth': args.gcov_depth}

    # Initialize Variables
    coverage_one = set()
    elapsed = 0
    score = 0
    i = 0
    

    
    # Do until timeout
    if args.tool == "parasuit":
        print('[INFO] ParaSuit : Selected ParaSuit. Parameter values will be tuned.')
    elif args.tool == "klee":
        print('[INFO] ParaSuit : Selected default KLEE. Parameter values will not be tuned.')
        if "-seed-file" in parameter_values['space'].keys():
            del parameter_values['space']['-seed-file']

    print('[INFO] ParaSuit : All configuration loaded. Start testing.')

    while elapsed <= args.budget:
        budget = time.time() - start
        iteration_dir = output_dir / f'iteration-{i + 1}'

        if (args.tool == "parasuit") and (len(parasuit.setD.select_list) > 0):
            time_budget = 30
        else:
            time_budget = converter.budget_handler(elapsed, args.budget, args.iteration_time_budget)

        # Sample parameters
        parameters = converter.convert(parameter_values, budget)

        # Run symbolic executor
        parameters[symbolic_executor.get_time_parameter()] = time_budget
        parameters['-output-dir'] = str(iteration_dir)
        testcases, klee_time = symbolic_executor.run(args.llvm_bc, parameters)

        # Collect result
        converter.add(args.gcov_obj, parameters, testcases, evaluation_argument)
        coverage, coverage_one = converter.get_coverage_and_bugs()
        elapsed = int(time.time() - start)
        print(f'[INFO] ParaSuit : Iteration: {i + 1} '
                          f'Iteration budget: {time_budget} '
                          f'Total budget: {args.budget} '
                          f'Time Elapsed: {elapsed} '
                          f'Coverage: {len(coverage)} ')

        with coverage_csv.open('a') as stream:
            stream.write(f'{elapsed}, {len(coverage)}\n')

        if args.tool == "parasuit":
            # Update search space
            parameter_values = parasuit.sample(elapsed, len(coverage), coverage_one, parameter_values, output_dir, i)
        
        i += 1

    coverage, coverage_one = converter.get_coverage_and_bugs()
    print(f'[INFO] ParaSuit : ParaSuit done. Achieve {len(coverage)} coverage')

