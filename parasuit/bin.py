from pathlib import Path
import argparse
import json
import shutil
import sys
import os 
import time
import csv
import copy

# Running ParaSuit
from parasuit.klee import KLEE
from parasuit.extract import Extractor
from parasuit.param_select import Selector
from parasuit.evaluate import Evaluator
from parasuit.value_sample import Sampler


def main(argv=None):
    if argv == None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    home_directory = os.path.abspath(os.path.join(os.getcwd(), '../../'))
    
    # Execution settings
    executable = parser.add_argument_group('executable settings')
    executable.add_argument('--klee', default=f'{home_directory}/klee/build/bin/klee', type=str,
                            help='Path to "klee" executable (default=klee)')
    executable.add_argument('--klee-replay', default=f'{home_directory}/klee/build/bin/klee-replay', type=str,
                            help='Path to "klee-replay" executable (default=klee-replay)')
    executable.add_argument('--gcov', default='gcov', type=str,
                            help='Path to "gcov" executable (default=gcov)')

    # Hyperparameters
    hyperparameters = parser.add_argument_group('hyperparameters')
    hyperparameters.add_argument('-p', '--parameter-values', default="parameters.json", type=str, metavar='JSON',
                                 help='Initial parameter set for tuning symbolic execution (default=OSDI'08 Coreutils Experiments)')
    hyperparameters.add_argument('--iteration-time-budget', default=120, type=int, metavar='INT',
                                 help='Time budget for each iteration (default=120)')
    hyperparameters.add_argument('--threshold', default=0.7, type=float, metavar='FLOAT',
                                 help='Minimum silhouette score required to sample values using the exploit policy (default=0.7)')
    hyperparameters.add_argument('--n-trial', default=3, type=int, metavar='INT',
                                 help='Number of times each parameter is tried in the extraction step (default=3)')

    # Others
    parser.add_argument('-d', '--output-dir', default='ParaSuit', type=str,
                        help='Directory where experiment results are saved (default=ParaSuit)')
    parser.add_argument('--gcov-depth', default=1, type=int,
                        help='Depth from the obj-gcov directory to the directory where the gcov file was created (default=1)')

    # Required arguments
    required = parser.add_argument_group('required arguments')
    required.add_argument('-t', '--budget', default=None, type=int, metavar='INT',
                          help='Total time budget of ParaSuit')
    required.add_argument('llvm_bc', nargs='?', default=None,
                          help='LLVM bitecode file for klee')
    required.add_argument('gcov_obj', nargs='?', default=None,
                          help='Executable with gcov support')
    
    args = parser.parse_args(argv)
    args.gcov_obj = f"{str(os.getcwd())}/{args.gcov_obj}"
    args.llvm_bc = f"{str(os.getcwd())}/{args.llvm_bc}"
    running_dir = os.getcwd()
    pgm = args.gcov_obj[args.gcov_obj.rfind("/") + 1:]

    if args.llvm_bc is None or args.gcov_obj is None or args.budget is None:
        parser.print_usage()
        print('[INFO] ParaSuit : following parameters are required: -t, llvm_bc, gcov_obj')
        sys.exit(1)

    if args.gcov_obj[0] != "/":
        args.gcov_obj = f"{str(os.getcwd())}/{args.gcov_obj}"
    if args.llvm_bc[0] != "/":
        args.llvm_bc = f"{str(os.getcwd())}/{args.llvm_bc}"
    output_dir = Path(args.output_dir)

    if output_dir.exists():
        shutil.rmtree(str(output_dir))
        print(f'[WARNING] ParaSuit : Existing output directory is deleted: {output_dir}')
    output_dir.mkdir(parents=True)
    coverage_csv = output_dir / 'coverage.csv'
    coverage_csv.touch()
    print(f'[INFO] ParaSuit : Coverage will be recorded at "{coverage_csv}" at every iteration.')

    # Initialize Variables
    coverage = set()
    selected = list()
    parameter_values = dict()
    branch_count = dict()
    covered_branches = dict()
    coverage_log = dict()
    sampled_values = dict()
    elapsed = 0
    i = 1

    extractor = Extractor(args.gcov_depth, args.gcov_obj, args.klee, args.klee_replay, home_directory)
    with open(args.parameter_values, 'r') as init_params:
        min_parameters = json.load(init_params)
    init_parameters = copy.deepcopy(min_parameters)

    options, opt_types = extractor.get_help_output()
    option_data = dict()
    for opt in options:
        option_data[opt] = (extractor.find_block(f'"{opt}"', opt_types[opt], init_parameters))
    option_data, filtered = extractor.filtering(option_data)
    min_parameters = {key : value for key, value in min_parameters.items() if key.strip('-') not in filtered}
    init_tcs = extractor.make_cmd(args.llvm_bc, f"{running_dir}/{args.output_dir}", args.iteration_time_budget, min_parameters)
    init_covs = extractor.cal_coverage(f"{running_dir}/{args.output_dir}", 0, init_tcs, args.gcov)
    init_coverage = {key : len(value) for key, value in init_covs.items()}
    seed_default = [k for k, v in sorted(init_coverage.items(), key=lambda item: item[1], reverse=True)[:args.n_trial]]

    symb_params = ["sym-arg", "sym-args", "sym-files", "sym-stdin", "sym-stdout", "seed-file"]
    minimize_opts = [opt for opt in min_parameters.keys() if opt.strip('-') not in symb_params]
    if os.path.exists(f"{running_dir}/../data/min_parameters/{pgm}.json"):
        with open(f"{running_dir}/../data/min_parameters/{pgm}.json", 'r') as min_params:
            min_parameters = json.load(min_params)
    else:
        while (len(minimize_opts) > 0):
            minimize_opts, min_parameters, testcases = extractor.minimize(minimize_opts, min_parameters, args.llvm_bc, f"{running_dir}/{args.output_dir}", args.iteration_time_budget, i, args.gcov)
            os.system(f"rm -rf {running_dir}/{args.output_dir}/iteration-{i}")
        with open(f"{running_dir}/../data/min_parameters/{pgm}.json", 'w', encoding='utf-8') as min_params_w:
            json.dump(min_parameters, min_params_w, ensure_ascii=False, indent=4)
    option_data = {key : value for key, value in option_data.items() if (key not in [p.strip('-') for p in min_parameters.keys()]) or (key in symb_params)}
    symb_values = {key : value for key, value in min_parameters.items() if key.lstrip("-") in symb_params}

    parameter_values["space"] = dict()
    for key, value in symb_values.items():
        if key in ["-sym-args", "-sym-arg"]:
            sym_cmd = f"{key} {value}".replace(key, "")
            cmd_data = sym_cmd.split()
            if key.strip("-") in ["sym-args"]:
                num_args, len_args = 0, 0
                for i in range(len(cmd_data) // 3):
                    num_args += int(cmd_data[i * 3 + 1])
                    len_args += int(cmd_data[i * 3 + 1]) * int(cmd_data[i * 3 + 2])
                parameter_values["space"]['-sym-arg'] = [[len_args], num_args]
            else:
                arg_data = [int(num) for num in cmd_data]
                parameter_values["space"]['-sym-arg'] = [[max(arg_data)], len(arg_data)]
        else:
            parameter_values["space"][key] = [[value], 1]
    parameter_values["defaults"] = {key : value for key, value in min_parameters.items() if key.lstrip("-") not in symb_params}
    minimum_parameters = copy.deepcopy(parameter_values)

    # Initialize ParaSuit
    symbolic_executor = KLEE(args.klee)
    selector = Selector(option_data, parameter_values, pgm, args.n_trial)
    evaluator = Evaluator(pgm, args.gcov_obj, args.output_dir, args.gcov_depth, running_dir, args.klee_replay)
    coverage_iter = evaluator.save_result(0, args.gcov)
    coverage = coverage.union(coverage_iter)
    if os.path.exists(f"{running_dir}/../data/candidates/{pgm}.json"):
        with open(f"{running_dir}/../data/candidates/{pgm}.json", 'r') as init_params:
            candidates = json.load(init_params)
    else:
        candidates = selector.make_candidates(f"{running_dir}/{args.output_dir}/iteration-0", seed_default, running_dir)

    # Start Execution
    extractor.clear_gcov(args.gcov_depth)
    start = time.time()
    if os.path.exists(f"{running_dir}/../data/covered_branches/{pgm}.json"):
        print('[INFO] ParaSuit : Loading parameter selection data.')
        with open(f"{running_dir}/../data/covered_branches/{pgm}.json", 'r') as cov_file:
            covered_branches = json.load(cov_file)
            selector.load_data(covered_branches)
        for value in covered_branches.values():
            for val in value:
                for cov in val:
                    if cov in branch_count.keys():
                        branch_count[cov] += 1
                    else:
                        branch_count[cov] = 1
        selector.score_options(branch_count)
        init_selected = [p.strip('-') for p in init_parameters.keys() if (p.strip('-') in covered_branches.keys())]
        selector.save_selected_logs(init_selected, coverage_iter)
        selected = selector.select_params(running_dir, init_selected, branch_count, args.n_trial, args.threshold)
        initial_values = selector.init_values(running_dir, selected, candidates, init_parameters)
        sampler = Sampler(pgm, f"{running_dir}/{args.output_dir}", args.iteration_time_budget, initial_values, minimum_parameters, symb_params, option_data)
    else:
        print("[INFO] ParaSuit : Extracting parameter selection data.")
    print('[INFO] ParaSuit : All configuration loaded. Start testing.')

    # Iterative Stages
    while elapsed <= args.budget:
        # Select parameters and Sample values
        os.chdir(running_dir)
        if (not all(len(value) == args.n_trial for value in selector.covered_branches.values())) and (not os.path.exists(f"{running_dir}/../data/covered_branches/{pgm}.json")):
            parameter_values = selector.try_param(minimum_parameters, candidates)
        else:
            parameter_values, sampled_values = sampler.sample_value(selected, coverage_log, initial_values, args.n_trial, args.threshold)
        parameter_values = evaluator.select_seed(parameter_values)

        if len(sampled_values) <= 0:
            time_budget = symbolic_executor.budget_handler(elapsed, args.budget, args.iteration_time_budget)
        else:
            time_budget = symbolic_executor.budget_handler(elapsed, args.budget, sampled_values['max-time'])

        # Run symbolic executor
        parameters = symbolic_executor.convert(parameter_values, f"{running_dir}/{args.output_dir}/iteration-{i}", time_budget)
        iter_start = time.time()
        testcases = symbolic_executor.run(args.llvm_bc, parameters, time_budget)
        exec_period = int(time.time() - iter_start)

        # Collect result
        check_time = time.time()
        coverage_iter = evaluator.save_result(i, args.gcov)
        seed_time = int(time.time() - check_time)
        coverage = coverage.union(coverage_iter)
        elapsed = int(time.time() - start)
        for br in coverage_iter:
            if br in branch_count.keys():
                branch_count[br] += 1
            else:
                branch_count[br] = 1
        if len(coverage_iter) > 0:
            coverage_log[f"iteration-{i}"] = len(coverage_iter)
        
        print(f'[INFO] ParaSuit : Iteration: {i} '
                          f'Total budget: {args.budget} '
                          f'Time Elapsed: {elapsed} '
                          f'Coverage: {len(coverage)} '
                          f'Iteration Coverage: {len(coverage_iter)} ')

        with coverage_csv.open('a') as stream:
            stream.write(f'{elapsed}, {len(coverage)}, {len(coverage_iter)}\n')

        if (not all(len(value) == args.n_trial for value in selector.covered_branches.values())) and (not os.path.exists(f"{running_dir}/../data/covered_branches/{pgm}.json")):
            covered_branches = selector.collect_data(running_dir, selected, coverage_iter, branch_count, exec_period, time_budget, candidates)
            if all(len(value) == args.n_trial for value in selector.covered_branches.values()):
                param_covered = copy.deepcopy(selector.covered_branches)
                for key, value in param_covered.items():
                    param_covered[key] = [list(val) for val in value]
                with open(f"{running_dir}/../data/covered_branches/{pgm}.json", 'w', encoding='utf-8') as covered_branches_w:
                    json.dump({key: value for key, value in param_covered.items()}, covered_branches_w, ensure_ascii=False, indent=4)
                selector.score_options(branch_count)
                init_selected = [p.strip('-') for p in init_parameters.keys() if (p.strip('-') in covered_branches.keys())]
                selected = selector.select_params(running_dir, init_selected, branch_count, args.n_trial, args.threshold)
                initial_values = selector.init_values(running_dir, selected, candidates, init_parameters)
                sampler = Sampler(pgm, f"{running_dir}/{args.output_dir}", args.iteration_time_budget, initial_values, minimum_parameters, symb_params, option_data)
        else:
            # Update results of iteration
            sampler.save(sampled_values, coverage_iter, branch_count)
            selector.save_selected_logs(selected, coverage_iter)
            selector.score_options(branch_count)
            selected = selector.select_params(running_dir, init_selected, branch_count, args.n_trial, args.threshold)
            initial_values = selector.init_values(running_dir, selected, candidates, init_parameters)
            sampler.update(initial_values)

        i += 1
        os.chdir(running_dir)

    print(f'[INFO] ParaSuit : ParaSuit done. Achieve {len(coverage)} coverage.')

