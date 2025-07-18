import os
import re

import copy
import json

import numpy as np
import random as rd

from itertools import combinations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import manhattan_distances


class Selector:
    def __init__(self, option_data, pgm):
        self.option_data = option_data
        self.pgm = pgm
        self.cal_similarites()
        self.n_trial = 1
        

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
                candidates[key] = val_list
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
        
    
    def select(self, param_score, n_params, param_counter, errored, fixed_params):
        individual_score = {key[0] : value for key, value in param_score.items() if (len(key) == 1) and (key not in fixed_params)}
        keys = list(individual_score.keys())
        weights = list(individual_score.values())
        if sum(weights) == 0:
            best_p = rd.choice(keys)
        else:
            best_p = rd.choices(keys, weights=weights, k=1)[0]
        threshold = individual_score[best_p] / param_counter[best_p]
        
        combined_count = dict()
        combined_sum = dict()
        combined = {key : value for key, value in param_score.items() if len(key) > 1}
        for err in errored:
            if err in combined.keys():
                combined[err] = combined[err] - 1
        for key, value in combined.items():
            for p in key:
                if p in combined_sum.keys():
                    combined_sum[p] += value
                    combined_count[p] += 1
                else:
                    combined_sum[p] = value
                    combined_count[p] = 1
        combined_score = {key : combined_sum[key] / combined_count[key] for key in combined_sum.keys()}
        median_val = np.median(list(combined_score.values()))
        missing = [k for k in individual_score.keys() if k not in combined_score.keys()]
        for k in missing:
            combined_score[k] = median_val

        # Min-Max normalization
        values = list(combined_score.values())
        min_val = min(values)
        max_val = max(values)
        scale = max_val - min_val if max_val - min_val != 0 else 1e-8
        combined_score = {key: round((value - min_val) / scale, 4) for key, value in combined_score.items()}       
        if len(combined) > len(individual_score):
            score = {key : individual_score[key] + combined_score[key] for key in individual_score.keys() if key not in fixed_params}
            selected = rd.choices(list(score.keys()), weights=list(score.values()), k=n_params)
        else:
            selected = rd.choices(list(individual_score.keys()), weights=list(individual_score.values()), k=n_params)
        return list(set(selected))
        

