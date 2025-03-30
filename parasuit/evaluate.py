import os
import re
import random as rd
import subprocess as sp


class Evaluator:
    def __init__(self, pgm, gcov_path, test_dir, depth, running_dir, replay_bin):
        self.replay_bin = replay_bin
        self.running_dir = running_dir
        self.pgm = pgm
        self.depth = depth
        self.test_dir = f"{running_dir}/{test_dir}"
        self.tc_data = []
        self.gcov_path = gcov_path[:gcov_path.rfind('/')]
        match = re.search(r"obj-gcov\d+", gcov_path)
        if match:
            self.obj_index = match.group(0) 
        else:
            self.obj_index = "obj-gcov"


    def save_result(self, iteration, gcov_bin):
        # Analyze the results of the iteration
        covered_set = set()
        if os.path.exists(f"{self.test_dir}/iteration-{iteration}"):
            ktests = [f"{self.test_dir}/iteration-{iteration}/{f}" for f in os.listdir(f"{self.test_dir}/iteration-{iteration}") if f.endswith(".ktest")]
            self.tc_data = self.tc_data + ktests
            covered_set = self.evaluate(iteration, ktests, gcov_bin)
        return covered_set


    def select_seed(self, parameter_values):
        # If the seed-file parameter is selected, choose the number of seeds based on its value
        if "-seed-file" in parameter_values['space'].keys():
            best_seeds = rd.sample(self.tc_data, parameter_values['space']['-seed-file'][0][0])
            parameter_values['space']['-seed-file'] = [best_seeds, 1]
        return parameter_values

    
    def evaluate(self, iteration, ktests, gcov_bin):
        # Measure the branch coverage of the test cases generated in the iteration
        self.clear_gcov(self.depth)
        tc_covered = set()
        os.chdir(self.gcov_path)
        for tc in ktests:
            cmd = f"{self.replay_bin} {self.gcov_path}/{self.pgm} {tc}"
            process = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
            try:
                _, stderr = process.communicate(timeout=0.1)
            except sp.TimeoutExpired:
                pass
            finally:
                process.kill()
                
        for _ in range(self.depth):
            os.chdir("../")
        gcdas = [gcda for gcda in self.find_all(os.getcwd(), "gcda") if self.obj_index in gcda]
        cov = 0
        cmd = [gcov_bin, "-b"] + gcdas
        result = sp.run(cmd, capture_output=True, text=True)
        gcovs = [gcov for gcov in self.find_all(os.getcwd(), "gcov") if self.obj_index in gcov]
        for gcov in gcovs:
            try:
                with open(gcov, 'r') as f:
                    lines = f.readlines()
                    for l in range(len(lines)):
                        line = lines[l]
                        if ('branch' in line) and ('never' not in line) and ('taken 0%' not in line) and (
                            ":" not in line) and ("returned 0% blocks executed 0%" not in line):
                            tc_covered.add(f"{gcov} {l}")
            except:
                with open(gcov, 'r', encoding="latin-1") as f:
                    lines = f.readlines()
                    for l in range(len(lines)):
                        line = lines[l]
                        if ('branch' in line) and ('never' not in line) and ('taken 0%' not in line) and (
                            ":" not in line) and ("returned 0% blocks executed 0%" not in line):
                            tc_covered.add(f"{gcov} {l}")
        os.chdir(self.running_dir)
        return tc_covered


    def find_all(self, path, ends):
        found = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(f'.{ends}'):
                    found.append(os.path.join(root, file))
        return found


    def clear_gcov(self, depth):
        # Initialize the gcov directory
        g_path = self.gcov_path
        for _ in range(depth):
            g_path = g_path[:g_path.rfind('/')]
        gcdas = self.find_all(g_path, "gcda")
        gcovs = self.find_all(g_path, "gcov")
        for gcda in gcdas:
            os.system(f"rm -f {gcda}")
        for gcov in gcovs:
            os.system(f"rm -f {gcov}")
