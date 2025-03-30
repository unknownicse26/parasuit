import os
import re

import copy
import json

import random as rd

from itertools import combinations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import manhattan_distances


class Selector:
    def __init__(self, option_data, parameter_values, pgm, n_trial):
        self.option_data = option_data
        self.parameter_values = parameter_values
        self.pgm = pgm
        self.cal_similarites()
        self.selected_logs = dict()
        self.n_trial = n_trial


    def load_data(self, covered_branches):
        # Loading coverage dictionary from parameter selection data
        self.covered_branches = covered_branches


    def cal_similarites(self):
        options = list(self.option_data.keys())
        sentences = [opt.replace("-", " ").strip() for opt in options]
        descriptions = [self.option_data[opt][2] for opt in options]
        vectorizer = TfidfVectorizer()

        # Feature 1 : Similarities of option name
        tfidf_matrix_opt = vectorizer.fit_transform(sentences)
        similarities_opt = manhattan_distances(tfidf_matrix_opt)
        option_value = dict()
        for (idx1, idx2) in combinations(range(len(options)), 2):
            option_value[(options[idx1], options[idx2])] = similarities_opt[idx1][idx2]
        
        values = list(option_value.values())
        min_val = min(values)
        max_val = max(values)

        if min_val == max_val:
            option_value = {key: 0.0 for key in option_value.keys()}
        option_value = {key: round(1 - (value - min_val) / (max_val - min_val), 4) for key, value in option_value.items()}
        
        # Feature 2 : Similarities of descriptions
        tfidf_matrix_desc = vectorizer.fit_transform(descriptions)
        similarities_desc = manhattan_distances(tfidf_matrix_desc)
        description_value = dict()
        for (idx1, idx2) in combinations(range(len(options)), 2):
            description_value[(options[idx1], options[idx2])] = similarities_desc[idx1][idx2]
        
        values = list(description_value.values())
        min_val = min(values)
        max_val = max(values)

        if min_val == max_val:
            description_value = {key : 0.0 for key in data}
        description_value = {key : round(1 - (value - min_val) / (max_val - min_val), 4) for key, value in description_value.items()}

        # Calculate similarity score based on name and description
        self.similarity_scores = {key : round(option_value[key] + description_value[key], 4) for key in option_value.keys()}


    def make_candidates(self, seed_dir, seed_files, running_dir):
        def check_type(string):
            # Check the type of the value assigned to the parameter
            integer_pattern = r'^[+-]?\d+$'
            float_pattern = r'^[+-]?(\d+\.\d*|\.\d+|\d+\.)$'
            if re.match(integer_pattern, string):
                return "integer"
            elif re.match(float_pattern, string):
                return "float"
            else:
                return "string"
        candidates = {key: [] for key in self.option_data.keys()}
        opt_types = dict()
        etc_opts = list()
        for key, value in self.option_data.items():
            if len(value[-1]) > 0:
                # Sample candidates for string parameters
                opt_types[key] = "string"
                default_value = value[1]
                val_list = list(set(value[-1]) - {default_value})
                if len(val_list) >= self.n_trial:
                    candidates[key] = rd.sample(val_list, k=self.n_trial)
                else:
                    candidates[key] = rd.choices(val_list, k=self.n_trial)
            elif (value[0] == "boolean") and (value[1] in ["true", "false"]):
                # Sample candidates for boolean parameters
                if value[1] == "true":
                    candidates[key] = ["false"] * self.n_trial
                else:
                    candidates[key] = ["true"] * self.n_trial
            elif (key in ["seed-dir", "seed-file"]):
                if key == "seed-dir":
                    candidates[key] = [seed_dir] * self.n_trial
                else:
                    candidates[key] = rd.sample(seed_files, k=self.n_trial)
            else:
                d_type = check_type(str(value[1]))
                if (d_type == "integer"):
                    # Sample candidates for integer parameters
                    default_value = int(value[1])
                    if default_value <= 0:
                        etc_opts.append(key)
                    else:
                        opt_types[key] = "integer"
                        if self.n_trial == 1:
                            candidates[key] = [int(default_value * 0.5)]
                        else:
                            candidates[key] = [int(default_value * 0.5), int(default_value * 1.5)] + [rd.randint(int(default_value * 0.5), int(default_value * 1.5)) for _ in range(self.n_trial - 2)]
                elif (d_type == "float"):
                    # Sample candidates for float parameters
                    opt_types[key] = "float"
                    if (value[1][-1] =="."):
                        default_value = float(f"{value[1]}0")
                    else:
                        default_value = float(value[1])
                    if ("pct" in key) or ("ratio" in key):
                        candidates[key] = [round(default_value / self.n_trial * i, self.n_trial) for i in range(self.n_trial)]
                    else:
                        if self.n_trial == 1:
                            candidates[key] = [default_value * 0.5]
                        else:
                            candidates[key] = [default_value * 0.5, default_value * 1.5] + [rd.uniform(default_value * 0.5, default_value * 1.5) for _ in range(self.n_trial - 2)]
                elif check_type(str(value[1]).rstrip('s')) == "integer":
                    # Sample candidates for time(integer) parameters
                    default_value = int(f"{str(value[1]).rstrip('s')}")
                    if default_value <= 0:
                        etc_opts.append(key)
                    else:
                        opt_types[key] = "integer"
                        if self.n_trial == 1:
                            candidates[key] = [f"{int(default_value * 0.5)}s"]
                        else:
                            candidates[key] = [f"{int(default_value * 0.5)}s", f"{int(default_value * 1.5)}s"] + [f"{rd.randint(int(default_value * 0.5), int(default_value * 1.5))}s" for _ in range(self.n_trial - 2)]
                else:
                    etc_opts.append(key)
        
        # If no default value is specified, use the default value of the parameter with the highest similarity score.
        for key in etc_opts:
            sim_dict1 = {(key, opt): self.similarity_scores[(key, opt)] for opt in opt_types.keys() if ((key, opt) in self.similarity_scores.keys())}
            sim_dict2 = {(opt, key): self.similarity_scores[(opt, key)] for opt in opt_types.keys() if ((opt, key) in self.similarity_scores.keys())}
            sim_dict = {**sim_dict1, **sim_dict2}
            max_combination = (list(max(sim_dict, key=sim_dict.get)))
            max_combination.remove(key)
            max_similarity_opt = max_combination[0]
            candidates[key] = candidates[max_similarity_opt]

        # Save the defined candidates as data
        if not os.path.exists(f"{running_dir}/../data/candidates/{self.pgm}.json"):
            with open(f"{running_dir}/../data/candidates/{self.pgm}.json", 'w', encoding='utf-8') as candidates_w:
                json.dump(candidates, candidates_w, ensure_ascii=False, indent=4)
        self.covered_branches = {key : list() for key in list(candidates.keys()) + ["default"]}
        return candidates


    def try_param(self, parameters, candidates):
        # Try the configuration with all parameters set to their default values for n_trial times.
        if len(self.covered_branches['default']) < self.n_trial:
            self.trying = 'default'
            return parameters
        
        # Try the parameter set with only one parameter value modified for n_trial times
        if self.trying not in self.covered_branches.keys():
            next_opt_list = [key for key in self.covered_branches.keys() if len(self.covered_branches[key]) < self.n_trial]
            self.trying = rd.choice(next_opt_list)
            print(f'[INFO] ParaSuit : Trying "{self.trying}" parameter.')
        elif len(self.covered_branches[self.trying]) >= self.n_trial:
            next_opt_list = [key for key in self.covered_branches.keys() if len(self.covered_branches[key]) < self.n_trial]
            self.trying = rd.choice(next_opt_list)
            print(f'[INFO] ParaSuit : Trying "{self.trying}" parameter.')
        parameter_values = copy.deepcopy(self.parameter_values)
        parameter_values["space"][f"-{self.trying}"] = [[candidates[self.trying][len(self.covered_branches[self.trying])]], 1]
        return parameter_values
        

    def collect_data(self, running_dir, selected, coverage, branch_count, elapsed, iter_budget, candidates):
        # Save the results for the attempted parameter set
        if ((elapsed < iter_budget) or (len(coverage) <= 0)):
            if not self.trying == "default":
                self.covered_branches = {key : value for key, value in self.covered_branches.items() if key != self.trying}
        else:
            self.covered_branches[self.trying].append(coverage)
        return self.covered_branches

    
    def score_options(self, branch_count):
        # Scoring function to parameters
        union_branches = {key : set() for key in self.covered_branches.keys()}
        for key, value in self.covered_branches.items():
            for val in value:
                union_branches[key] = union_branches[key].union(val)
        br_reverse = {key : 1 / value for key, value in branch_count.items()}
        branch_score = {key : 0 for key in union_branches.keys()}
        for key, value in union_branches.items():
            for val in value:
                if val in br_reverse:
                    branch_score[key] += br_reverse[val]
        values = list(branch_score.values())
        min_val = min(values)
        max_val = max(values)

        if min_val == max_val:
            norm_branch_score = {key : 0.0 for key in branch_score.keys()}
        else:
            norm_branch_score = {key : round((value - min_val) / (max_val - min_val), 4) for key, value in branch_score.items()}
        self.option_score = {key : norm_branch_score[key] for key in self.covered_branches}


    def select_params(self, running_dir, init_selected, branch_count, n_trial, n_threshold):
        # Select a new setting composed of parameters more effective than the default, based on their scores
        with open(f"{running_dir}/../data/param_scores/{self.pgm}.json", "w", encoding="utf-8") as score_file:
            json.dump(self.option_score, score_file, ensure_ascii=False, indent=4)
        threshold = self.option_score["default"]
        selected = [key for key, value in self.option_score.items() if value > threshold and key != "default"]
        if tuple(selected) in self.selected_logs.keys():
            if tuple(init_selected) not in self.selected_logs.keys():
                selected = init_selected
            else:
                if len(self.selected_logs[tuple(selected)]) > n_trial:
                    key = tuple(selected)
                    score_selected = self.score_selected(branch_count)
                    if (score_selected[key] < score_selected[tuple(init_selected)]) or rd.random() < (1 - n_threshold):
                        selected = init_selected
        return selected


    def init_values(self, running_dir, selected, candidates, init_parameters):
        # For the selected parameters, define the initial value as the one with the highest score among n_trial attempts
        init_parameters = {key.strip("-") : value for key, value in init_parameters.items()}
        covered_for_selected = {key : [len(val) for val in value] for key, value in self.covered_branches.items() if key in selected}
        max_indices = {key : None for key in covered_for_selected.keys()}
        initial_values = {key : None for key in selected}
        for key, values in covered_for_selected.items():
            if values:
                max_value = max(values)
                maxs = [i for i, v in enumerate(values) if v == max_value]
                max_indices[key] = rd.choice(maxs) 
        
        for param in initial_values.keys():
            if param in init_parameters.keys():
                if type(init_parameters[param]) == str:
                    initial_values[param] = init_parameters[param].split()[0]
                else:
                    initial_values[param] = init_parameters[param]
            else:
                if (param in max_indices.keys()) and (param in candidates.keys()):
                    initial_values[param] = candidates[param][max_indices[param]]
                else:
                    initial_values[param] = self.option_data[param][1]
        # Save the initial values as data
        with open(f"{running_dir}/../data/init_values/{self.pgm}.json", "w", encoding="utf-8") as init_value_file:
            json.dump(initial_values, init_value_file, ensure_ascii=False, indent=4)
        return initial_values


    def save_selected_logs(self, selected, covered_iter):
        # Save the results for the newly selected parameter set
        data = tuple(selected)
        if data in self.selected_logs.keys():
            self.selected_logs[data].append(covered_iter)
        else:
            self.selected_logs[data] = [covered_iter]

    
    def score_selected(self, branch_count):
        # Scoring function to parameter set
        union_branches = {key : set() for key in self.selected_logs.keys()}
        for key, value in self.selected_logs.items():
            for val in value:
                union_branches[key] = union_branches[key].union(val)
        br_reverse = {key : 1 / value for key, value in branch_count.items()}
        branch_score = {key : 0 for key in union_branches.keys()}
        for key, value in union_branches.items():
            for val in value:
                if val in br_reverse:
                    branch_score[key] += br_reverse[val]
        values = list(branch_score.values())
        min_val = min(values)
        max_val = max(values)

        if min_val == max_val:
            norm_branch_score = {key : 0.0 for key in branch_score.keys()}
        else:
            norm_branch_score = {key : round((value - min_val) / (max_val - min_val), 4) for key, value in branch_score.items()}        
        selected_score = {key : norm_branch_score[key] for key in self.selected_logs.keys()}
        
        return selected_score