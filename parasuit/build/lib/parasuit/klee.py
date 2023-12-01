from copy import deepcopy
from pathlib import Path
import os
import random
import subprocess as sp
import time

from parasuit.symbolic_executor import SymbolicExecutor
from parasuit.exechandler import ExecHandler


class GCov:
    def __init__(self, bin='gcov'):
        self.bin = bin
        self.smoke_test()
        if self.bin != 'gcov':
            print(f'[INFO] ParaSuit : Use gcov executable at: {self.bin}')

    def smoke_test(self):
        try:
            _ = sp.run(f'{self.bin} -version', stdout=sp.PIPE, stderr=sp.PIPE,
                       shell=True, check=True)
        except sp.CalledProcessError as e:
            print(f'[ERROR] ParaSuit : Failed to find gcov: {self.bin}')
            raise e

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
            if "gawk" in str(target):
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


class KLEE(SymbolicExecutor):
    def __init__(self, bin='klee'):
        self.bin = bin
        self.smoke_test()
        if self.bin != 'klee':
            print(f'[INFO] ParaSuit : Use klee executable at: {self.bin}')
        self.ratio = 0
        self.errored = 0
        self.end_default = 0
        self.time_budget = 150
        self.init_budget = 150

    def smoke_test(self):
        try:
            _ = sp.run(f'{self.bin} -version', stdout=sp.PIPE, stderr=sp.PIPE,
                       shell=True, check=True)
        except sp.CalledProcessError as e:
            print(f'[ERROR] ParaSuit : Failed to find klee: {self.bin}')
            raise e

    def run(self, target, parameters, **kwargs):
        target = Path(target).absolute()

        possible_output_dir = ['-output-dir', '--output-dir']
        for output_dir_param in possible_output_dir:
            if output_dir_param in parameters.keys():
                output_dir = Path(parameters[output_dir_param]).absolute()
                parameters[output_dir_param] = str(output_dir)
                break

        original_path = Path().absolute()
        os.chdir(str(target.parent))

        klee_options = []
        sym_arg_options = []
        sym_files_options = []
        sym_stdin_options = []
        sym_stdout_options = []

        space_seperate_keys = ['sym-arg', 'sym-args',
                               'sym-files', 'sym-stdin']
        sym_arg_keys = ['sym-arg', 'sym-args']
        for key, values in parameters.items():
            stripped_key = key.strip('-').split()[0]
            if not isinstance(values, list):
                values = [values]
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
        cmd = [str(self.bin), *klee_options, str(target),
               *sym_arg_options, *sym_files_options, *sym_stdin_options, *sym_stdout_options]

        cmd = ' '.join(cmd)
        ok = time.time()
        try:
            _ = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE,
                       shell=True, check=True)
            self.errored = 0

        except sp.CalledProcessError as e:
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
            self.errored = 1

        elapsed = time.time() - ok

        if self.errored:
            elapsed = 0

        testcases = list(output_dir.glob('*.ktest'))
        testcases = [tc.absolute() for tc in testcases]

        os.chdir(str(original_path))

        return testcases, elapsed

    def get_time_parameter(self):
        return '-max-time'


class KLEEReplay:
    def __init__(self, bin='klee-replay'):
        self.bin = bin
        self.smoke_test()
        if self.bin != 'klee-replay':
            print(f'[INFO] ParaSuit : Use klee-replay executable at: {self.bin}')

    def smoke_test(self):
        try:
            _ = sp.run(f'which {self.bin}', stdout=sp.PIPE, stderr=sp.PIPE,
                       shell=True, check=True)
        except sp.CalledProcessError as e:
            print(f'[ERROR] ParaSuit : Failed to find klee-replay: {self.bin}')
            raise e

    def run(self, target, testcase, error_type=None, folder_depth=1):
        target = Path(target).absolute()
        testcase = Path(testcase).absolute()

        original_path = Path().absolute()
        os.chdir(str(target.parent))

        if error_type is None:
            error_type = ['CRASHED signal 11', 'CRASHED signal 6']
        if isinstance(error_type, str):
            error_type = [error_type]

        cmd = [str(self.bin), str(target), str(testcase)]
        cmd = ' '.join(cmd)
        process = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
        errors = set()
        try:
            _, stderr = process.communicate(timeout=0.1)
            lastline = str(stderr.splitlines()[-1])

            for error in error_type:
                if error in lastline:
                    errs = list(testcase.parent.glob(testcase.stem + '.*.err'))

                    for err in errs:
                        with err.open(encoding='UTF-8', errors='replace') as f:
                            lines = f.readlines()
                            file_name = lines[1].split()[1]
                            line_num = lines[2].split()[1]
                            err_type = f'{file_name} {line_num}'
                            errors.add(err_type)
        except sp.TimeoutExpired:
            print(f'[WARNING] ParaSuit : KLEE replay timeout: {testcase}')
        finally:
            process.kill()

        base = Path()
        for _ in range(folder_depth):
            if "gawk" in str(target):
                pass

            else:
                base = base / '..'
        gcda_pattern = base / '**/*.gcda'
        gcdas = list(target.parent.glob(str(gcda_pattern)))
        gcdas = [gcda.absolute() for gcda in gcdas]

        os.chdir(str(original_path))

        return errors, gcdas


class KLEEConvert(ExecHandler):
    def __init__(self, klee_replay=None, gcov=None, k_seeds=10, *args, **kwargs):
        super(KLEEConvert, self).__init__(*args, **kwargs)

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

        self.k_seeds = k_seeds

    def convert(self, parameter_space, budget):
        parameters = super(KLEEConvert, self).convert(parameter_space, budget)

        if '-seed-file' in parameters.keys() or '--seed-file' in parameters.keys():
            key = '-seed-file' if '-seed-file' in parameters.keys() else '--seed-file'
            value = parameters[key]

            if value == 'random_from_all':
                testcases = [tc for _, _, tc, _ in self.data]
                if len(testcases) > 0:
                    testcase = random.choice(testcases)
                    parameters[key] = str(testcase)
                else:
                    del parameters[key]

        return parameters

    def add(self, target, parameters, testcases, evaluation_kwargs=None):
        super(KLEEConvert, self).add(target, parameters, testcases, evaluation_kwargs)

        if '-seed-file' not in self.space.keys() and '--seed-file' not in self.space.keys():
            return self

        buggy_seeds = []
        found_bugs = []
        for _, bugs, tc, _ in self.data[::-1]:
            for bug in bugs:
                if bug not in found_bugs:
                    found_bugs.append(bug)
                    buggy_seeds.append(tc)

        accumulated_coverage = set()
        copied_data = deepcopy(self.data)
        top_k_seeds = []

        for _ in range(self.k_seeds):
            if len(copied_data) == 0:
                break
            copied_data = sorted(copied_data,
                                 key=lambda elem: len(elem[0]),
                                 reverse=True)
            top_cov, _, tc, _ = copied_data.pop(0)
            if len(top_cov) > 0:
                accumulated_coverage = accumulated_coverage | top_cov
                copied_data = [(cov - accumulated_coverage, bug, tc, param)
                               for cov, bug, tc, param in copied_data]
                top_k_seeds.append(tc)
            else:
                break

        key = '-seed-file' if '-seed-file' in self.space.keys() else '--seed-file'
        seed_files = buggy_seeds + top_k_seeds
        self.space[key] = (seed_files, self.space[key][1])
        for seed in seed_files:
            if seed not in self.cnts[key].keys():
                self.cnts[key][seed] = 0
        return self

    def evaluate(self, target, testcase, folder_depth=1):
        base = Path(target).parent
        for _ in range(folder_depth):
            if "gawk" in str(target):
                pass
            else:
                base = base / '..'
        cmd = ['rm', '-f', str(base / '**/*.gcda'), str(base / '**/*.gcov')]
        cmd = ' '.join(cmd)
        _ = sp.run(cmd, shell=True, check=True)
        errors, gcdas = self.klee_replay.run(target, testcase,
                                             folder_depth=folder_depth)
        branches = self.gcov.run(target, gcdas, folder_depth=folder_depth)
        return branches, errors

    @classmethod
    def get_space(cls):
        space = {
            "-sym-stdout": [["on"], 1],
            "-sym-arg": [[1, 2, 3, 4, 5], 5],
            "-sym-files": [["1 9"], 1],
            "-sym-stdin": [[8], 1],

            "-seed-file": [[], 1]
        }
        return space

    @classmethod
    def get_default_params(cls):
        defaults = {
            "-simplify-sym-indices": null,
            "-write-cvcs": null,
            "-write-cov": null,
            "-output-module": null,
            "-max-memory": 1000,
            "-disable-inlining": null,
            "-optimize": null,
            "-use-forked-solver": null,
            "-use-cex-cache": null,
            "-libc": "uclibc",
            "-posix-runtime": null,
            "-external-calls": "all",
            "-only-output-states-covering-new": null,
            "-max-sym-array-size": 4096,
            "-max-solver-time": "30s",
            "-watchdog": null,
            "-max-memory-inhibit": "false",
            "-max-static-fork-pct": 1,
            "-max-static-solve-pct": 1,
            "-max-static-cpfork-pct": 1,
            "-switch-type": "internal",
            "-use-batching-search": null,
            "-batch-instructions": 10000,
            "-allow-seed-extension": null,
            "-allow-seed-truncation": null
        }
        return defaults