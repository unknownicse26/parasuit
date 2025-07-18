from pathlib import Path
import argparse
import json
import shutil
import sys
import os 
import time
import csv
import copy

import random as rd
import subprocess as sp

# Running ParaSuit
from parasuit.klee import KLEE, Evaluator
from parasuit.extract import Extractor
from parasuit.select_param import Selector
from parasuit.value_sample import Sampler
from parasuit.result_analyze import Analyzer


def main(argv=None):
    if argv == None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    home_directory = os.path.abspath(os.path.join(os.getcwd(), '../'))
    
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
                                 help='Initial parameter set for tuning symbolic execution (default=OSDI_08 Coreutils Experiments)')
    hyperparameters.add_argument('--iteration-time-budget', default=120, type=int, metavar='INT',
                                 help='Time budget for each iteration (default=120)')
    hyperparameters.add_argument('--threshold', default=0.7, type=float, metavar='FLOAT',
                                 help='Threshold to group parameters into a group in the parameter selection step (default=0.6 -> 60 Groups)')

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
    errored_combine = set()
    selected = list()
    parameter_values = dict()
    branch_count = dict()
    covered_branches = dict()
    coverage_log = dict()
    sampled_values = dict()
    seed_data = dict()
    fixed_params = dict()
    elapsed = 0
    data = list()
    i = 1

    extractor = Extractor(args.gcov_depth, args.gcov_obj, args.klee, args.klee_replay, home_directory)
    with open(args.parameter_values, 'r') as f:
        init_params = json.load(f)

    options, opt_types = extractor.get_help_output()
    option_data = dict()
    for opt in options:
        option_data[opt] = (extractor.find_block(f'"{opt}"', opt_types[opt], init_params))
    option_data, filtered = extractor.filtering(option_data)
    init_params = {key : value for key, value in init_params.items() if key.strip('-') not in filtered}
    init_tcs = extractor.make_cmd(args.llvm_bc, f"{running_dir}/{args.output_dir}", args.iteration_time_budget, init_params)

    # Initialize KLEE
    symbolic_executor = KLEE(args.klee)
    evaluator = Evaluator(args.gcov_obj, args.budget, args.klee_replay, args.gcov)
    coverage_iter = evaluator.evaluate(args.gcov_obj, init_tcs, args.gcov_depth)
    coverage = coverage.union(coverage_iter)
    seed_data = evaluator.const_data(f"{running_dir}/{args.output_dir}/iteration-0", seed_data)
    seed_default = [k for k, v in sorted(seed_data.items(), key=lambda item: item[1], reverse=True)[:1]]

    symb_params = ["sym-arg", "sym-args", "sym-files", "sym-stdin", "sym-stdout", "seed-file"]
    other_opts = [opt for opt in init_params.keys() if opt.strip('-') not in symb_params]
    if os.path.exists(f"{running_dir}/../data/fixed_params/{pgm}.json"):
        with open(f"{running_dir}/../data/fixed_params/{pgm}.json", 'r') as f:
            fixed_params = json.load(f)
    else:
        while (len(other_opts) > 0):
            cand_params = copy.deepcopy(init_params)
            other_opts, cand_params, fixed_params, testcases = extractor.minimize(other_opts, cand_params, fixed_params, args.llvm_bc, f"{running_dir}/{args.output_dir}", args.iteration_time_budget, i, args.gcov)
            shutil.rmtree(f"{running_dir}/{args.output_dir}/iteration-{i}", ignore_errors=True)
        with open(f"{running_dir}/../data/fixed_params/{pgm}.json", 'w', encoding='utf-8') as f:
            json.dump(fixed_params, f, ensure_ascii=False, indent=4)
    option_data = {key : value for key, value in option_data.items() if (key not in [p.strip('-') for p in fixed_params.keys()]) or (key in symb_params)}
    symb_values = {key : value for key, value in fixed_params.items() if key.lstrip("-") in symb_params}

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
    parameter_values["defaults"] = {key : value for key, value in fixed_params.items() if key.lstrip("-") not in symb_params}
    fixed_parameter_values = copy.deepcopy(parameter_values)

    # Initialize ParaSuit
    selector = Selector(option_data, pgm)
    analyzer = Analyzer()
    if os.path.exists(f"{running_dir}/../data/candidates/{pgm}.json"):
        with open(f"{running_dir}/../data/candidates/{pgm}.json", 'r') as f:
            candidates = json.load(f)
    else:
        candidates = selector.make_candidates(f"{running_dir}/{args.output_dir}/iteration-0", seed_default, running_dir)

    # Start Execution
    extractor.clear_gcov(args.gcov_depth)
    start = time.time()
    i = 1
    if os.path.exists(f"{running_dir}/../data/init_values/{pgm}.json"):
        print('[INFO] ParaSuit : Loading parameter selection data.')
        with open(f"{running_dir}/../data/init_values/{pgm}.json", 'r') as f:
            enable_selects = json.load(f)
        with open(f"{running_dir}/../data/baseline_data/{pgm}.json", 'r') as f:
            data = json.load(f)
    else:
        for key, values in candidates.items():
            errored = []
            # Try only a parameter per iteration
            for value in values:
                iter_data = {"param_set" : list(), "covered" : list()}
                parameter_values = copy.deepcopy(fixed_parameter_values)
                parameter_values["space"][f"-{key}"] = [[value], 1]
                iter_data["param_set"] = [key, value]

                # Run symbolic executor
                parameters = symbolic_executor.convert(parameter_values, f"{running_dir}/{args.output_dir}/iteration-{i}", args.iteration_time_budget)
                iter_start = time.time()
                testcases, errored_flag = symbolic_executor.run(args.llvm_bc, parameters, args.iteration_time_budget)
                exec_period = int(time.time() - iter_start)

                # Collect result
                coverage_iter = evaluator.evaluate(args.gcov_obj, testcases, args.gcov_depth)
                coverage = coverage.union(coverage_iter)
                print(f"Parameter : {key}, Value : {value}, Running Time : {exec_period}, Branch Coverage : {len(coverage_iter)}, Accumulative Coverage : {len(coverage)}")
                if (exec_period < args.iteration_time_budget) or (len(coverage_iter) <= 0) or (errored_flag):
                    errored.append(value)
                else:
                    iter_data["covered"] = list(coverage_iter)
                    data.append(iter_data)
                i += 1
            candidates[key] = [value for value in values if value not in errored]
        enable_selects = {key : rd.choice(value) for key, value in candidates.items() if len(value) > 0}
        with open(f"{running_dir}/../data/init_values/{pgm}.json", "w", encoding="utf-8") as f:
            json.dump(enable_selects, f, ensure_ascii=False, indent=4)
        with open(f"{running_dir}/../data/baseline_data/{pgm}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4) 
    option_data, covered_branches, param_score = analyzer.load_init_data(option_data, data, [key.lstrip("-") for key in init_params.keys() if key.lstrip("-") not in symb_params], coverage_iter)
    sampler = Sampler(pgm, f"{running_dir}/{args.output_dir}", args.iteration_time_budget, enable_selects, fixed_parameter_values, symb_params, option_data)      # value_sample / value_sample_random
    # sampler = Sampler(f"{running_dir}/{args.output_dir}", args.iteration_time_budget, enable_selects, fixed_parameter_values, symb_params, option_data)             # value_sample_ml / value_sample_symtuner
    print('[INFO] ParaSuit : All configuration loaded. Start testing.')

    # Iterative Stages
    while elapsed <= args.budget:
        os.chdir(running_dir)
        tool_params = sampler.tune_other_params(tool_params)

        # Select parameters
        selected = selector.select(param_score, tool_params["num_params"], analyzer.param_counter, errored_combine, [key.lstrip("-") for key in fixed_params.keys()])

        # Sample values
        parameter_values, sampled_values = sampler.sample_value(selected, coverage_log, enable_selects, args.threshold, tool_params)
        if "seed-file" in sampled_values:
            parameter_values = evaluator.select_seed(parameter_values, seed_data, sampled_values["seed-file"])

        if len(sampled_values) <= 0:
            time_budget = symbolic_executor.budget_handler(elapsed, args.budget, args.iteration_time_budget)
        else:
            time_budget = symbolic_executor.budget_handler(elapsed, args.budget, sampled_values['max-time'])

        # Run symbolic executor
        parameters = symbolic_executor.convert(parameter_values, f"{running_dir}/{args.output_dir}/iteration-{i}", time_budget)
        iter_start = time.time()
        testcases, errored_flag = symbolic_executor.run(args.llvm_bc, parameters, time_budget)
        if errored_flag:
            errored_combine.add(tuple(selected))
        exec_period = int(time.time() - iter_start)

        # Collect result
        check_time = time.time()
        coverage_iter = evaluator.evaluate(args.gcov_obj, testcases, args.gcov_depth)
        seed_time = int(time.time() - check_time)
        coverage = coverage.union(coverage_iter)
        elapsed = int(time.time() - start)
        if len(coverage_iter) > 0:
            coverage_log[f"iteration-{i}"] = len(coverage_iter)
        
        print(f'[INFO] ParaSuit : Iteration: {i} '
                          f'Total budget: {args.budget} '
                          f'Time Elapsed: {elapsed} '
                          f'Coverage: {len(coverage)} '
                          f'Iteration Coverage: {len(coverage_iter)} ')

        with coverage_csv.open('a') as stream:
            stream.write(f'{elapsed}, {len(coverage)}, {len(coverage_iter)}\n')
        
        # Update results of iteration
        param_score = analyzer.scoring(covered_branches, selected, coverage_iter)
        seed_data = evaluator.const_data(f"{running_dir}/{args.output_dir}/iteration-{i}", seed_data)

        sampler.save(sampled_values, coverage_iter, analyzer.branch_count)
        sampler.update(enable_selects)

        i += 1

    print(f'[INFO] ParaSuit : ParaSuit done. Achieve {len(coverage)} coverage.')




