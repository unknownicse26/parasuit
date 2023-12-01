import os
import random as rd


class SetDefault:
    def __init__(self, parameter_values):
        self.tuning_params = list(parameter_values['defaults'].keys())
        self.tuning_params.remove("-only-output-states-covering-new")
        self.select_list = list(range(len(self.tuning_params)))

        self.errored = 0
        self.found_early = 0
        self.scores = []

    def removing(self, coverage, parameter_values, iter, fd_name):
        if iter == 1:
            pass
        else:
            errored = ""
            print("[INFO] ParaSuit : Now %d-th iteration" % iter)
            file_list = os.listdir("/home/minjong/parasuit/benchmarks/%s/iteration-%d" % (fd_name, iter))
            for f in file_list:
                if (".external.err" in f) or (".user.err" in f):
                    self.errored = 1
                    errored = f
                if (".early" in f):
                    self.found_early = 1
            if (errored != "") and f[:10] > errored[:10]:
                self.errored = 0

            if (coverage == 0) or (self.errored) or (len(file_list) >= 1000) or (
                    self.tuning_params[self.removed] == "-only-output-states-covering-new") or (
            not self.found_early) or ("seed" in self.tuning_params[self.removed]) or (self.tuning_params[self.removed] == "-optimize"):
                parameter_values["defaults"][self.tuning_params[self.removed]] = self.removed_value
                print("[INFO] ParaSuit : This Parameter is Necessary! Re-added in Default Space")
                self.errored = 0

            else:
                self.scores.append(coverage)

            self.found_early = 0

        if len(self.select_list) > 0:
            self.removed = rd.choice(self.select_list)
            self.removed_value = parameter_values["defaults"][self.tuning_params[self.removed]]
            print()
            print("[INFO] ParaSuit : Now Removing %s" % (self.tuning_params[self.removed]))
            self.select_list.remove(self.removed)

            del parameter_values["defaults"][self.tuning_params[self.removed]]

        return parameter_values


    def optimizing(self, parameter_values):
        self.defaults = list(parameter_values["defaults"].keys())
        if "-optimize" not in list(parameter_values["defaults"].keys()):
            parameter_values["defaults"]["-optimize"] = None
        
        if "-seed-file" in list(parameter_values["defaults"].keys()):
            if "-allow-seed-extension" not in list(parameter_values["defaults"].keys()):
                parameter_values["defaults"]["-allow-seed-extension"] = None
            if "-allow-seed-truncation" not in list(parameter_values["defaults"].keys()):
                parameter_values["defaults"]["-allow-seed-truncation"] = None

        return parameter_values