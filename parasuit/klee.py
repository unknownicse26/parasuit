from copy import deepcopy
from pathlib import Path

import os
import random

import subprocess as sp


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

        return testcases

    
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
                    tmp_list.append(random.choice(space))
                parameters[param] = tmp_list
        return parameters
