from pathlib import Path
import os
import re
import time
import subprocess as sp
import random as rd


class Extractor:
    def __init__(self, depth, gcov_path, bin, klee_replay, home_directory):
        self.bin = bin
        self.klee_replay = klee_replay
        self.depth = depth
        self.gcov_path = gcov_path[:gcov_path.rfind("/")]
        self.pgm = gcov_path[gcov_path.rfind("/") + 1:]
        self.src_files = self.find_all(f"{home_directory}/klee/lib", "cpp")
        self.src_files = self.src_files + self.find_all(f"{home_directory}/klee/tools/klee", "cpp")
        # Add parameters that should not be tuned
        self.default_options = ["-only-output-states-covering-new", "-allow-seed-extension", "-allow-seed-truncation", "-optimize"]


    def get_help_output(self):
        opt_type = dict()
        
        # Command to get help output
        command = [self.bin, '--help']
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
        if result.stdout == "":
            output = result.stderr
        else:
            output = result.stdout
        lines = [l.split() for l in output.split("\n")]
        
        # Extract parameters from the help output
        options = set()
        for line in lines:
            if len(line) > 0:
                if line[0][0] == '-':
                    if "=" in line[0]:
                        opt = line[0][:line[0].find('=')]
                        types = line[0][line[0].find('=') + 1:]
                        options.add(opt)
                        opt_type[opt.strip("-")] = types.strip("<").strip(">")
                    else:
                        options.add(line[0])
                        opt_type[line[0].strip("-")] = "unknown"

        return [opt.strip("-") for opt in list(options)], opt_type


    def find_block(self, option, val_type, init_parameters):
        block_lines = []
        values = []
        default_value = None
        description = None
        description_default = None
        category = None

        # Explore the source code of the symbolic executor
        for file_path in self.src_files:
            with open(file_path, 'r') as src_file:
                code = src_file.read()
                lines = code.splitlines()
                inside_block = False
                for line in lines:
                    if option in line:
                        inside_block = True
                    if inside_block:
                        block_lines.append(line)
                        if line.strip().endswith(");"):
                            break

        # When a block defining a parameter is found
        if block_lines:
            block = " ".join([b.strip() for b in block_lines])
            init_match = re.search(r"cl::init\((.*?)\)", block)
            # Extract the default value of the parameter
            if init_match:
                default_value = init_match.group(1).strip('"')
            desc_match = re.search(r"cl::desc\((.*?)\)", block)
            if desc_match:
                description = desc_match.group(1)
                if desc_match:
                    description = desc_match.group(1)
                    default_in_desc_match = re.search(r"default=[^ ]+", description)
                    if default_in_desc_match:
                        description_default = default_in_desc_match.group(0).replace("default=", "").strip().strip('"')

            # Extract the category of the parameter
            cat_match = re.search(r"cl::cat\((.*?)\)", block)
            if cat_match:
                category = cat_match.group(1)

            # Extract the candidate value of the parameter
            values_matches = re.findall(r"clEnumValN\(.*?,\s*\"(.*?)\"", block)
            if values_matches:
                values.extend(values_matches)

            # Extract the type of the values for the parameter
            if (default_value != description_default) and (description_default in values):
                default_value = description_default
            if (default_value in ['true', 'false']) and (val_type == "unknown"):
                val_type = "boolean"
            if (len(values) > 0):
                val_type = "categorical"

        init_parameters = {param.strip("-") : value for param, value in init_parameters.items()}
        if option.strip('"') in init_parameters.keys():
            return (val_type, str(init_parameters[option.strip('"')]), description, category, values)
        else:
            return (val_type, default_value, description, category, values)


    def filtering(self, option_data):
        '''
        Exclude parameters from tuning if their names contain certain keywords
        '''

        removed = list()
        filtered_list = list()
        keywords = ["write", "debug", "log", "pc", "print", "replay", "stop", "close", "output-dir", "max-time", "seed-file"]
        escapes = ["pct"]
        
        for opt, data in option_data.items():
            filtered = 0
            for word in keywords:
                if (word in opt) or (data[2] is not None and word in data[2]) or (data[0] == "unknown" and data[1] is None):
                    filtered = 1
            for e_word in escapes:
                if e_word in opt:
                    filtered = 0
            if filtered:
                filtered_list.append(opt)
        for key in filtered_list:
            del option_data[key]
        return option_data, filtered_list


    def run_klee(self, cmd, iter_budget, running_dir):
        '''
        Run KLEE with defined command
        '''

        try:
            result = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, check=True, timeout=int(1.25*iter_budget))
        except sp.TimeoutExpired:
            print('[WARNING] Symplate : KLEE exceeded the time budget. Iteration terminated.')
        except sp.CalledProcessError as e:
            stderr = e.stderr.decode(errors='replace')
            lastline = stderr.strip().splitlines()[-1]
            if 'KLEE' in lastline and 'kill(9)' in lastline:
                print(f'[WARNING] Symplate : KLEE process kill(9)ed. Failed to terminate nicely.')
            else:                
                print(f'[WARNING] Symplate : Fail({e.returncode})ed to execute KLEE.')
        testcases = [f"{running_dir}/iteration-0/{tc}" for tc in os.listdir(f"{running_dir}/iteration-0") if tc.endswith(".ktest")]
        
        return testcases


    def make_cmd(self, target, running_dir, iter_budget, parameters, iter=0):
        '''
        Convert the parameter set into KLEE command format
        '''
                
        opt_cmd, sym_cmd = "", ""
        original_path = Path().absolute()
        for key, value in parameters.items():
            if key in ["-sym-arg", "-sym-args", "-sym-files", "-sym-stdin", "-sym-stdout"]:
                continue
            elif key in ["-seed-file"]:
                for val in parameters[key]:
                    opt_cmd = f"{opt_cmd} {key}={val}"
            else:
                opt_cmd = f"{opt_cmd} {key}={value}"

        opt_cmd = f"{opt_cmd} -write-depth-info -max-time={iter_budget} -output-dir={running_dir}/iteration-{iter}"

        if "-sym-arg" in parameters.keys():
            sym_cmd = f"{sym_cmd} -sym-arg {parameters['-sym-arg']}"
        if "-sym-args" in parameters.keys():
            sym_cmd = f"{sym_cmd} -sym-args {parameters['-sym-args']}"
        if "-sym-files" in parameters.keys():
            sym_cmd = f"{sym_cmd} -sym-files {parameters['-sym-files']}"
        if "-sym-stdin" in parameters.keys():
            sym_cmd = f"{sym_cmd} -sym-stdin {parameters['-sym-stdin']}"
        if "-sym-stdout" in parameters.keys():
            if parameters["-sym-stdout"] == "on":
                sym_cmd = f"{sym_cmd} -sym-stdout"

        cmd = " ".join([f"{self.bin}", opt_cmd.strip(), str(target), sym_cmd.strip()])

        testcases = self.run_klee(cmd, iter_budget, running_dir)
        os.chdir(str(original_path))

        return sorted(testcases)
    

    def minimize(self, options, param_dict, target, running_dir, iter_budget, iteration, gcov_bin):
        '''
        Search for the minimal parameter set required to run KLEE
        '''
        if iter_budget >= 120:
            iter_budget = iter_budget // 4
        opt = options.pop()
        param_value = param_dict[opt]
        del param_dict[opt]
        start = time.time()
        testcases = self.make_cmd(target, running_dir, iter_budget, param_dict, iteration)
        elapsed = int(time.time() - start)
        covered = self.cal_coverage(running_dir, iteration, testcases, gcov_bin)
        iter_covered = set()
        for value in covered.values():
            iter_covered = iter_covered.union(value)
        
        if (elapsed < iter_budget) or (len(iter_covered) <= 0) or (opt in self.default_options):
            param_dict[opt] = param_value

        return options, param_dict, testcases


    def cal_coverage(self, running_dir, iteration, testcases, gcov_bin):
        '''
        Measure the branch coverage of the test-cases generated by KLEE
        '''

        coverages = dict()
        ktests = [f"{running_dir}/iteration-{iteration}/{f}" for f in os.listdir(f"{running_dir}/iteration-{iteration}") if f.endswith(".ktest")]
        for i in range(len(ktests)):
            tc = ktests[i]
            self.clear_gcov(self.depth)
            os.chdir(self.gcov_path)
            
            cmd = f"{self.klee_replay} {self.gcov_path}/{self.pgm} {tc}"
            process = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)

            try:
                _, stderr = process.communicate(timeout=0.1)
            except sp.TimeoutExpired:
                pass
            finally:
                process.kill()
            
            os.chdir(self.gcov_path)
            for _ in range(self.depth):
                os.chdir("../")
            gcdas = self.find_all(os.getcwd(), "gcda")

            os.chdir(self.gcov_path)
            for gcda in gcdas:
                _ = sp.run([gcov_bin, "-b", gcda], capture_output=True, text=True).stdout
            for _ in range(self.depth):
                os.chdir("../")
            gcovs = self.find_all(os.getcwd(), "gcov")
            
            covered = set()
            for gcov in gcovs:
                if os.path.exists(gcov):
                    try:
                        with open(gcov, "r") as gcov_file:
                            gcov_lines = [l.strip() for l in gcov_file.readlines()]
                    except:
                        with open(gcov, "r", encoding='latin-1') as gcov_file:
                            gcov_lines = [l.strip() for l in gcov_file.readlines()]
                    for line_num in range(len(gcov_lines)):
                        try:
                            if ('branch' in gcov_lines[line_num]) and ('never' not in gcov_lines[line_num]) and ('taken 0%' not in gcov_lines[line_num]):
                                covered.add(f"{gcov} {line_num}")
                        except:
                            pass
            coverages[tc] = covered
        return coverages


    def find_all(self, path, ends):
        found = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(f'.{ends}'):
                    found.append(os.path.join(root, file))
        return found


    def clear_gcov(self, depth):
        '''
        Initialize the gcov directory
        '''

        g_path = self.gcov_path
        for _ in range(depth):
            g_path = g_path[:g_path.rfind('/')]
        gcdas = self.find_all(g_path, "gcda")
        gcovs = self.find_all(g_path, "gcov")
        for gcda in gcdas:
            os.system(f"rm -f {gcda}")
        for gcov in gcovs:
            os.system(f"rm -f {gcov}")