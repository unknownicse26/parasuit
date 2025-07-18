import re
import copy
import time

import numpy as np
import random as rd

from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.metrics import silhouette_score


class Sampler:
    def __init__(self, pgm, running_dir, iteration_budget, initial_values, min_parameters, symb_params, option_data, tool_params):
        self.pgm = pgm
        self.running_dir = running_dir
        self.iteration_budget = iteration_budget
        self.option_data = option_data
        self.initial_values = initial_values
        # If seed-dir is selected, use the iteration with the highest coverage as the seed
        if "seed-dir" in self.initial_values.keys():
            self.initial_values["seed-dir"] = f"{self.running_dir}/iteration-0"
        self.sym_init_values = dict()
        self.sym_type = dict()
        # Further divide symbolic parameters for more fine-grained tuning
        for key, value in min_parameters['space'].items():
            self.initial_values[key.strip("-")] = value
            if key.strip("-") in ["sym-files"]:
                num_file, len_file = value[0][0].split()
                self.sym_init_values[f"{key.strip('-')}-num"] = int(num_file)
                self.sym_init_values[f"{key.strip('-')}-len"] = int(len_file)
            elif key.strip("-") in ["sym-arg"]:
                self.sym_init_values[f"{key.strip('-')}-num"] = int(value[1])
                self.sym_init_values[f"{key.strip('-')}-len"] = int(value[0][0])
            else:
                self.sym_init_values[key.strip('-')] = value[0][0]
        self.sym_init_values["seed-file"] = 4
        self.sym_init_values["search-num"] = 1  # For intersective heuristics
        self.sym_init_values["max-time"] = iteration_budget
        for key, value in self.sym_init_values.items():
            if key in ["sym-stdout"]:
                self.sym_type[key] = "string"
            else:
                self.sym_type[key] = "integer"
            
        self.min_parameters = min_parameters
        self.min_parameters["space"]["-seed-file"] = [[1], 1]
        self.min_parameters["space"]["-max-time"] = [[iteration_budget], 1]
        self.symb_params = symb_params + ["seed-dir", "seed-file", "max-time", "search-num"]

        self.opt_types = {key : "" for key in self.initial_values.keys()}
        for key, value in self.initial_values.items():        
            self.divide_types(key, value)
        self.opt_types["seed-file"] = "symbolic"
        self.opt_types["search-num"] = "symbolic"
        self.opt_types["max-time"] = "symbolic"
        self.clust_data = {key : [] for key in list(self.opt_types.keys()) + list(self.sym_init_values.keys())}
        self.covered_data = {key : [] for key in list(self.opt_types.keys()) + list(self.sym_init_values.keys())}

        self.other_param_data = {key : [] for key in ["threshold", "num_params"]}
        self.other_defaults = tool_params


    def divide_types(self, key, value):
        # Check the type of the value assigned to the parameter
        minimum_params = [key.lstrip('-') for key in self.min_parameters["defaults"].keys()]
        def check_type(string):
            integer_pattern = r'^[+-]?\d+$'
            float_pattern = r'^[+-]?(\d+\.\d*|\.\d+|\d+\.)$'
            if re.match(integer_pattern, string):
                return "integer"
            elif re.match(float_pattern, string):
                return "float"
            else:
                return "string"

        if key in self.symb_params:
            # Perform independent tuning for symbolic parameters
            self.opt_types[key] = "symbolic"
        elif key in minimum_params:
            pass            
        elif len(self.option_data[key][-1]) > 0:
            self.opt_types[key] = "string"
        elif value in ['true', 'false']:
            self.opt_types[key] = "boolean"
        else:
            if (isinstance(value, float) or check_type(str(value)) == "float"):
                if ("pct" in key) or ("ratio" in key):
                    self.opt_types[key] = "float_ratio"
                else:
                    self.opt_types[key] = "float"
            elif (isinstance(value, int) or check_type(str(value)) == "integer"):
                self.opt_types[key] = "integer"
            elif str(value).rstrip('s').isdigit():
                self.opt_types[key] = "integer_time"
                self.initial_values[key] = int(str(value).rstrip('s'))
            else:
                self.opt_types[key] = "others"


    def explore(self, param, coverage_log):
        # Randomly sample a value for each parameter
        if self.opt_types[param] in ["boolean", "string"]:
            if self.opt_types[param] == "boolean":
                candidates = ["true", "false"]
            else:
                candidates = self.option_data[param][-1]
            return rd.choice(candidates)
        elif param in ["seed-dir"]:
            if len(coverage_log) > 0:
                return f"{self.running_dir}/{max(coverage_log, key=lambda k: coverage_log[k])}"
            else:
                return f"{self.running_dir}/iteration-0"
        elif self.opt_types[param] in ["float_ratio"]:
            return round(rd.random(), 4)
        else:
            if self.opt_types[param] in ["integer", "integer_time"]:
                if len(self.clust_data[param]) <= 0:
                    return self.initial_values[param]
                else:
                    values = [x for x, _ in self.clust_data[param]]
                    scores = [y for _, y in self.clust_data[param]]
                    if rd.random() < 0.5:
                        best_v = rd.choice(values)
                    else:
                        best_v = int(max(self.clust_data[param], key=lambda pair: pair[1])[0])
                    if best_v == 1:
                        return rd.randint(max(1, int(best_v * 0.5)), int(best_v * 2))
                    else:
                        return rd.randint(max(1, int(best_v * 0.5)), int(best_v * 1.5))
            elif self.opt_types[param] == "float":
                if len(self.clust_data[param]) <= 0:
                    return self.initial_values[param]
                else:
                    best_v = int(max(self.clust_data[param], key=lambda pair: pair[1])[0])
                    return round(rd.uniform(max(0, best_v * 0.5), best_v * 1.5), 4)
    

    def exploit(self, param, coverage_log):       
        # Sample effective values based on the data
        if (self.opt_types[param] in ["boolean", "string"]):
            value_scores = dict()
            for key, score in self.clust_data[param]:
                if key not in value_scores:
                    value_scores[key] = []
                value_scores[key].append(score)
            avg_score = {key: sum(scores) / len(scores) for key, scores in value_scores.items()}
            keys = list(avg_score.keys())
            values = np.array(list(avg_score.values()))
            probabilities = values / values.sum()
            return np.random.choice(keys, p=probabilities)
        elif param in ["seed-dir"]:
            if (len(coverage_log) > 0) and (max(coverage_log.values()) > 0):
                return f"{self.running_dir}/{max(coverage_log, key=lambda k: coverage_log[k])}"
            else:
                return f"{self.running_dir}/iteration-0"
        else:
            if self.opt_types[param] in ["integer_time"]:
                data = np.array([(int(value.rstrip("s")), score) for value, score in self.clust_data[param]], dtype=np.float64)
            else:
                data = np.array(self.clust_data[param], dtype=np.float64)
            bandwidth = estimate_bandwidth(data)
            mean_shift = MeanShift(bandwidth=bandwidth)
            mean_shift.fit(data)
            labels = mean_shift.labels_
            num_clusters = len(set(labels))
            clustered_data = [[] for _ in range(num_clusters)]

            for point, label in zip(data, labels):
                clustered_data[label].append(tuple(point))

            cluster_scores = {}
            for cluster in clustered_data:
                values = [x[0] for x in cluster]
                scores = [x[1] for x in cluster]
                min_val, max_val = min(values), max(values)
                avg_score = sum(scores) / len(scores)
                cluster_scores[(min_val, max_val)] = avg_score

            keys = list(cluster_scores.keys())
            values = np.array(list(cluster_scores.values()))
            probabilities = values / values.sum()
            selected_key = keys[np.random.choice(len(keys), p=probabilities)]

            for cluster in clustered_data:
                values = [x[0] for x in cluster]
                scores = [x[1] for x in cluster]

                min_val, max_val = min(values), max(values)
                if (min_val, max_val) == selected_key:
                    if sum(scores):
                        new_value = sum(values) / len(values)
                    else:
                        new_value = round(sum(v * s for v, s in zip(values,scores)) / sum(scores), 4)
                    break

            if self.opt_types[param] in ["integer_time"]:
                return f"{int(new_value)}s"
            elif self.opt_types[param] in ["integer"]:
                return int(new_value)
            else:
                return new_value


    def sym_explore(self, param):
        # Randomly sample a value for each parameter
        if param in ["sym-stdout"]:
            candidates = ["on", "off"]
            return rd.choice(candidates)
        elif param in ['sym-files-num', "search-num"]:
            return rd.choice([1, 2])
        else:
            if len(self.clust_data[param]) <= 0:
                return self.initial_values[param]
            else:
                values = [x for x, _ in self.clust_data[param]]
                scores = [y for _, y in self.clust_data[param]]
                if rd.random() < 0.5:
                    best_v = rd.choice(values)
                else:
                    best_v = int(max(self.clust_data[param], key=lambda pair: pair[1])[0])
                if best_v == 1:
                    return rd.randint(max(1, int(best_v * 0.5)), int(best_v * 2))
                else:
                    return rd.randint(max(1, int(best_v * 0.5)), int(best_v * 1.5))

    def sym_exploit(self, param):
        # Sample effective values based on the data
        if param in ["sym-stdout", 'sym-files-num', 'search-num']:
            value_scores = dict()
            for key, score in self.clust_data[param]:
                if key not in value_scores:
                    value_scores[key] = []
                value_scores[key].append(score)
            avg_score = {key: sum(scores) / len(scores) for key, scores in value_scores.items()}
            keys = list(avg_score.keys())
            values = np.array(list(avg_score.values()))
            probabilities = values / values.sum()
            return np.random.choice(keys, p=probabilities)
        else:
            data = np.array(self.clust_data[param], dtype=np.float64)
            bandwidth = estimate_bandwidth(data)
            mean_shift = MeanShift(bandwidth=bandwidth)
            mean_shift.fit(data)
            labels = mean_shift.labels_
            num_clusters = len(set(labels))
            clustered_data = [[] for _ in range(num_clusters)]

            for point, label in zip(data, labels):
                clustered_data[label].append(tuple(point))

            cluster_scores = {}
            for cluster in clustered_data:
                values = [x[0] for x in cluster]
                scores = [x[1] for x in cluster]
                min_val, max_val = min(values), max(values)
                avg_score = sum(scores) / len(scores)
                cluster_scores[(min_val, max_val)] = avg_score

            keys = list(cluster_scores.keys())
            values = np.array(list(cluster_scores.values()))
            probabilities = values / values.sum()
            selected_key = keys[np.random.choice(len(keys), p=probabilities)]

            for cluster in clustered_data:
                values = [x[0] for x in cluster]
                scores = [x[1] for x in cluster]

                min_val, max_val = min(values), max(values)
                if (min_val, max_val) == selected_key:
                    if sum(scores):
                        new_value = sum(values) / len(values)
                    else:
                        new_value = round(sum(v * s for v, s in zip(values,scores)) / sum(scores), 4)
                    return int(new_value)


    def tune_other_params(self, tool_params):
        sampled_other = dict()
        other_params = ["threshold", "num_params"]
        for param in other_params:
            values = [x for x, _ in self.other_param_data[param]]
            scores = [y for _, y in self.other_param_data[param]]
            if (len(values) <= 0) or (len(scores) <= 0):
                if param == "num_params":
                    new_value = rd.randint(2, len(self.option_data) // 2)
                else:
                    new_value = rd.random()
            else:
                best_value = int(max(self.other_param_data[param], key=lambda pair: pair[1])[0])
                if rd.random() <= tool_params["threshold"]:
                    if len(self.other_param_data[param]) <= 0:
                        new_value = self.other_defaults[param]
                    else:
                        new_value = best_value
                else:
                    if param == "num_params":
                        new_value = rd.randint(2, len(self.option_data))
                    else:
                        new_value = rd.random()
            sampled_other[param] = new_value
        return sampled_other


    def sample_value(self, selected, coverage_log, initial_values, threshold, tool_params):
        # Sample a new value for each parameter based on its defined policy
        sampled_values = dict()
        for param in self.sym_init_values.keys():
            if len(self.covered_data[param]) <= 0:
                sampled_values[param] = self.sym_init_values[param]
            else:
                try:
                    policy = self.try_cluster(param, self.sym_type[param], tool_params)
                except:
                    policy = "explore" 
                if policy == "explore":
                    sampled_values[param] = self.sym_explore(param)
                else:
                    try:
                        sampled_values[param] = self.sym_exploit(param)
                    except:
                        sampled_values[param] = self.sym_explore(param)
        for param in selected:
            if (param not in self.covered_data.keys()):
                self.update(initial_values)
            if len(self.covered_data[param]) <= 0:
                sampled_values[param] = self.initial_values[param]
            else:
                try:
                    policy = self.try_cluster(param, self.opt_types[param], tool_params)
                except:
                    policy = "explore"
                if policy == "explore":
                    sampled_values[param] = self.explore(param, coverage_log)
                else:
                    try:
                        sampled_values[param] = self.exploit(param, coverage_log)
                    except:
                        sampled_values[param] = self.explore(param, coverage_log)
        sampled_values["max-time"] = max(self.iteration_budget, sampled_values["max-time"])
        parameter_values = self.make_parameter_values(sampled_values)
        return parameter_values, sampled_values


    def try_cluster(self, param, types, threshold, tool_params):
        # When there isn't enough data for clustering, apply the exploration policy
        if len(self.covered_data[param]) <= 1:
            return "explore"

        # Transform the data into a format suitable for clustering
        if param in ["sym-arg-num", "sym-arg-len", "sym-files-num", "sym-files-len", "sym-stdin", "sym-stdout"]:
            if param in ["sym-stdout"]:
                data = np.array([(1 if b == "on" else 0, s) for b, s in self.clust_data[param]], dtype=np.float64)
            else:
                data = np.array(self.clust_data[param], dtype=np.float64)
        else:
            if types == "boolean":
                data = np.array([(1 if b == "true" else 0, s) for b, s in self.clust_data[param]], dtype=np.float64)
            elif types == "string":
                data = np.array([(self.option_data[param][-1].index(b), s) for b, s in self.clust_data[param]], dtype=np.float64)
            elif types == "integer_time":
                if (self.clust_data[param][0][-1] == 's') and (type(self.clust_data[param][0]) == str):
                    data = np.array([(int(value.rstrip("s")), score) for value, score in self.clust_data[param]], dtype=np.float64)
                else:
                    data = np.array([(int(value), score) for value, score in self.clust_data[param]], dtype=np.float64)
            else:
                data = np.array(self.clust_data[param], dtype=np.float64)

        # Perform mean shift clustering
        start = time.time()
        bandwidth = estimate_bandwidth(data, quantile=0.2, n_samples=len(data))
        if bandwidth == 0.0:
            return "explore"
        else:
            mean_shift = MeanShift(bandwidth=bandwidth, n_jobs=1, bin_seeding=True)
        labels = mean_shift.fit_predict(data)
        n_clusters = len(set(labels))
        if 2 <= n_clusters < len(data):
            silhouette_avg = silhouette_score(data, labels)
            # Select the exploit policy if the silhouette score exceeds the threshold
            if silhouette_avg >= tool_params["threshold"]:
                return "exploit"
            else:
                return "explore"
        else:
            return "explore"

    def make_parameter_values(self, sampled_values):
        # Convert the sampled parameter values into a parameter set format
        parameter_values = copy.deepcopy(self.min_parameters)
        not_symbolic = [key for key in sampled_values.keys() if f"-{key}" not in list(self.min_parameters["space"].keys()) + ['-sym-arg-num', '-sym-arg-len', '-sym-files-num', '-sym-files-len', "-search-num"]]
        for key, value in sampled_values.items():
            if key == "search-num":
                continue
            if key in not_symbolic:
                if key == "use-merge":
                    if "search" in sampled_values.keys():
                        if sampled_values["search"] == "random-path":
                            parameter_values['space'][f"-{key}"] = [["false"], 1]    
                        else:
                            parameter_values['space'][f"-{key}"] = [[value], 1]
                    else:
                        parameter_values['space'][f"-{key}"] = [[value], 1]    
                elif key == "search":
                    if (sampled_values["search-num"] > 1):
                        candidates = copy.deepcopy(self.option_data[key][-1])
                        candidates.remove(value)
                        if len(candidates) >= 1:
                            intersect_h = [rd.choice(candidates)]
                            for heuristic in intersect_h:
                                value = f"{value} -search={heuristic}"
                            if ("use-merge" in sampled_values.keys()) and ("random-path" in intersect_h):
                                parameter_values['space'][f"-use-merge"] = [["false"], 1]
                                sampled_values["use-merge"] = "false"
                    parameter_values['space'][f"-{key}"] = [[value], 1]    
                elif self.opt_types[key] in ["integer_time"]:
                    parameter_values['space'][f"-{key}"] = [[f"{value}s"], 1]
                else:
                    parameter_values['space'][f"-{key}"] = [[value], 1]
            else:
                if key == "sym-arg-len":
                    spaces = []
                    for _ in range(sampled_values["sym-arg-num"]):
                        spaces.append(max(1, rd.randint(int(value * 0.5), int(value * 1.5))))
                    parameter_values['space'][f"-sym-arg"] = [spaces, sampled_values["sym-arg-num"]]
                elif key == "sym-files-len":
                    parameter_values['space'][f"-sym-files"] = [[f"{sampled_values['sym-files-num']} {value}"], 1]
                elif key not in ["sym-arg-num", "sym-files-num"]:
                    parameter_values['space'][f"-{key}"] = [[value], 1]
        return parameter_values


    def update(self, initial_values):
        # If a newly selected parameter has not been tried before, add storage space for it in the data variable
        for key, value in initial_values.items():
            if key not in self.initial_values.keys():
                self.initial_values[key] = initial_values[key]
                self.divide_types(key, value)
            if key not in self.clust_data.keys():
                self.clust_data[key] = []
            if key not in self.covered_data.keys():
                self.covered_data[key] = []


    def save(self, sampled_values, covered_branches, branch_count):
        # Accumulate data for each value based on the iterations in which it was used
        self.clust_data = {key : [] for key in self.covered_data.keys()}
        for key, value in sampled_values.items():
            self.covered_data[key].append((value, list(covered_branches)))
            self.re_score(key, branch_count)


    def re_score(self, param, branch_count):
        # Re-calculate scores based on the total coverage up to the current iteration
        value_list = [value for value, _ in self.covered_data[param]]
        covered_list = [covered_branches for _, covered_branches in self.covered_data[param]]
        br_reverse = {key : 1 / value for key, value in branch_count.items()}
        unique_score = []
        for covered in covered_list:
            score = 0
            for br in covered:
                if br in br_reverse:
                    score += br_reverse[br]
            unique_score.append(score)
        min_val = min(unique_score)
        max_val = max(unique_score)
        if min_val == max_val:
            norm_unique_score = [0.0 for _ in unique_score]
        else:
            norm_unique_score = [round((value - min_val) / (max_val - min_val), 4) for value in unique_score]
        
        for i in range(len(value_list)):
            self.clust_data[param].append((value_list[i], round(norm_unique_score[i], 4)))
