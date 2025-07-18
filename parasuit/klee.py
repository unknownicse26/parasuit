from copy import deepcopy
from pathlib import Path

import json
import os
import re
import sys
import time

import random as rd
import subprocess as sp


class GCov:
    def __init__(self, bin='gcov'):
        self.bin = bin


    def run(self, target, gcdas, folder_depth=1):
        if len(gcdas) == 0:
            return set()

        original_path = Path().absolute()
        target_dir = Path(target).parent
        gcdas = [gcda.absolute() for gcda in gcdas]
        os.chdir(str(target_dir))

        cmd = [str(self.bin), '-b', *list(map(str, gcdas))]
        cmd = ' '.join(cmd)
        _ = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, check=True)

        base = Path()
        for _ in range(folder_depth):
            if "gawk" in str(target) or "make" in str(target) or "sqlite" in str(target):
                pass
            else:
                base = base / '..'

        gcov_pattern = base / '**/*.gcov'
        gcovs = list(Path().glob(str(gcov_pattern)))

        covered = set()
        for gcov in gcovs:
            try:
                with gcov.open(encoding='UTF-8', errors='replace') as f:
                    file_name = f.readline().strip().split(':')[-1]
                    for i, line in enumerate(f):
                        if ('branch' in line) and ('never' not in line) and ('taken 0%' not in line) and (
                                ":" not in line) and ("returned 0% blocks executed 0%" not in line):
                            bid = f'{file_name} {i}'
                            covered.add(bid)
            except:
                pass

        os.chdir(str(original_path))
        return covered


class KLEE:
    def __init__(self, bin='klee'):
        self.bin = bin

    def run(self, target, parameters, budget, **kwargs):
        target = Path(target).absolute()
        # Setting output directory
        possible_output_dir = ['-output-dir', '--output-dir']
        for output_dir_param in possible_output_dir:
            if output_dir_param in parameters.keys():
                output_dir = Path(parameters[output_dir_param]).absolute()
                parameters[output_dir_param] = str(output_dir)
                break

        original_path = Path().absolute()
        os.chdir(str(target.parent))

        klee_options = []
        seed_options = []
        sym_arg_options = []
        sym_files_options = []
        sym_stdin_options = []
        sym_stdout_options = []
        
        # Seperate symbolic parameters
        space_seperate_keys = ['sym-arg', 'sym-args',
                               'sym-files', 'sym-stdin']
        sym_arg_keys = ['sym-arg', 'sym-args']

        # Convert the parameter set into KLEE command format
        for key, values in parameters.items():
            stripped_key = key.strip('-').split()[0]
            if not isinstance(values, list):
                values = [values]
            
            if key in ["-seed-file", "--seed-file"]:
                for value in values:
                    param = f'{key}={value}'
                    seed_options.append(param)
            else:
                for value in values:
                    if value is None:
                        param = key
                    elif stripped_key in space_seperate_keys:
                        param = f'{key} {value}'
                    elif stripped_key == 'sym-stdout':
                        if value == 'off':
                            continue
                        param = key
                    else:
                        param = f'{key}={value}'
                    if stripped_key in sym_arg_keys:
                        sym_arg_options.append(param)
                    elif stripped_key == 'sym-files':
                        sym_files_options.append(param)
                    elif stripped_key == 'sym-stdin':
                        sym_stdin_options.append(param)
                    elif stripped_key == 'sym-stdout':
                        sym_stdout_options.append(param)
                    else:
                        klee_options.append(param)
                    

        # Make KLEE running command
        cmd = [str(self.bin), *klee_options, *seed_options, str(target),
               *sym_arg_options, *sym_files_options, *sym_stdin_options, *sym_stdout_options]
        cmd = ' '.join(cmd)
        errored = 0

        # Run KLEE
        try:
            _ = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE,
                       shell=True, check=True, timeout=budget*1.25)

        except sp.TimeoutExpired:
            print('[WARNING] ParaSuit : KLEE exceeded the time budget. Iteration terminated.')

        except sp.CalledProcessError as e:
            if not os.path.exists(str(output_dir)):
                os.mkdir(str(output_dir))
            stderr = e.stderr.decode(errors='replace')
            lastline = stderr.strip().splitlines()[-1]
            if 'KLEE' in lastline and 'kill(9)' in lastline:
                print(f'[WARNING] ParaSuit : KLEE process kill(9)ed. Failed to terminate nicely.')
            else:
                possible_output_dir = ['-output-dir', '--output-dir']
                for output_dir_param in possible_output_dir:
                    if output_dir_param in parameters.keys():
                        output_dir = Path(parameters[output_dir_param])
                        break
                else:
                    output_dir = target.parent / 'klee-last'
                    if output_dir.exists():
                        output_dir = output_dir.resolve()
                    else:
                        output_dir = original_path
                log_file = output_dir / 'parasuit.log'
                print(f'[WARNING] ParaSuit : Fail({e.returncode})ed to execute KLEE. '
                                     f'See for more details: {log_file}')
                errored = 1
                with log_file.open('w', encoding='UTF-8') as f:
                    f.write(f'command: {cmd}\n')
                    f.write(f'return code: {e.returncode}\n')
                    f.write('\n')
                    f.write('-- stdout --\n')
                    stdout = e.stdout.decode(errors='replace')
                    f.write(f'{stdout}\n')
                    f.write('-- stderr --\n')
                    stderr = e.stderr.decode(errors='replace')
                    f.write(f'{stderr}\n')

        # Collect generated test-cases
        testcases = list(output_dir.glob('*.ktest'))
        testcases = [tc.absolute() for tc in testcases]

        os.chdir(str(original_path))

        return testcases, errored

    
    def budget_handler(self, elapsed, total_budget, iteration_budget):
        if ((total_budget - elapsed) >= iteration_budget):
            # If there is enough time to use full budget
            return iteration_budget
        else:
            # If there is no enough time to use full budget
            return total_budget - elapsed


    def convert(self, parameter_values, output_dir, budget):
        # Select values for symbolic parameters
        parameter_values["defaults"]["-output-dir"] = output_dir
        parameter_values["defaults"]["-max-time"] = budget
        self.space = parameter_values['space']
        self.default = parameter_values['defaults']
        parameters = dict()
        for param, value in self.default.items():
            parameters[param] = value

        for param, (space, n_sample) in self.space.items():
            if n_sample == 1:
                parameters[param] = space
            else:
                tmp_list = []
                for _ in range(n_sample):
                    tmp_list.append(rd.choice(space))
                parameters[param] = tmp_list
        return parameters


class KLEEReplay:
    def __init__(self, bin='klee-replay'):
        self.bin = bin

    def run(self, target, testcases, error_type=None, folder_depth=1):
        errors = set()
        target = Path(target).absolute()
        original_path = Path().absolute()
        for testcase in testcases:
            testcase = Path(testcase).absolute()
            os.chdir(str(target.parent))

            cmd = [str(self.bin), str(target), str(testcase)]
            cmd = ' '.join(cmd)
            process = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
            try:
                _, stderr = process.communicate(timeout=0.1)
            except sp.TimeoutExpired:
                print(f'[WARNING] SEvolve : KLEE replay timeout: {testcase}')
            finally:
                process.kill()

        base = Path()
        for _ in range(folder_depth):
            base = base / '..'
        gcda_pattern = base / '**/*.gcda'
        gcdas = list(target.parent.glob(str(gcda_pattern)))
        gcdas = [gcda.absolute() for gcda in gcdas]

        os.chdir(str(original_path))
        return gcdas


class Evaluator:
    def __init__(self, gcov_path, budget, klee_replay=None, gcov=None):
        if klee_replay is None:
            klee_replay = KLEEReplay()
        elif isinstance(klee_replay, str):
            klee_replay = KLEEReplay(klee_replay)
        self.klee_replay = klee_replay
        if gcov is None:
            gcov = GCov()
        elif isinstance(gcov, str):
            gcov = GCov(gcov)
        self.gcov = gcov
        self.gcov_path = gcov_path[:gcov_path.rfind('/')]
        self.budget = budget
        self.const_count = dict()

    def evaluate(self, target, testcases, folder_depth=1):
        base = Path(target).parent
        # Run symbolic executor
        for _ in range(folder_depth):
            base = base / '..'
        cmd = ['rm', '-f', str(base / '**/*.gcda'), str(base / '**/*.gcov')]
        cmd = ' '.join(cmd)
        _ = sp.run(cmd, shell=True, check=True)
        # Replay test-cases generated by the symbolic executor
        gcdas = self.klee_replay.run(target, testcases, folder_depth=folder_depth)
        # Extract the set of branches covered by the generated test-cases
        covered = self.gcov.run(target, gcdas, folder_depth=folder_depth)
        return covered

    def budget_handler(self, elapsed, iteration_budget):
        ## Take the best one to the Methodology           
        if ((self.budget - elapsed) >= iteration_budget):
            return iteration_budget
        else:
            return self.budget - elapsed

    def const_data(self, output_dir, seed_data):
        ktests = [f"{output_dir}/{tc}" for tc in os.listdir(output_dir) if tc.endswith(".ktest")]
        constraints = [tc.replace(".ktest", ".const") for tc in ktests]
        for const in constraints:
            if os.path.exists(const):
                with open(const, "r") as f:
                    const_list = [f"{i} {val}" for i, val in enumerate(json.load(f))]
                    seed_data[const] = const_list
                    for const in const_list:
                        if const in self.const_count.keys():
                            self.const_count[const] += 1
                        else:
                            self.const_count[const] = 1
            else:
                seed_data[const] = 0
        return seed_data

    def select_seed(self, parameter_values, seed_data, num_seeds=10):
        # If the seed-file parameter is selected, choose the number of seeds based on its value
        if "-seed-file" in parameter_values['space'].keys():
            const_score = {key : 1 / value for key, value in self.const_count.items()}
            tc_score = dict()
            for tc, consts in seed_data.items():
                try:
                    score = 0
                    for const in consts:
                        print(const)
                        print(const_score[const])
                        score += const_score[const]
                    tc_score[tc.replace(".const", ".ktest")] = score
                except:
                    pass
            best_seeds = rd.choices(list(tc_score.keys()), weights=list(tc_score.values()), k=num_seeds)
            parameter_values['space']['-seed-file'] = [best_seeds, 1]
        return parameter_values