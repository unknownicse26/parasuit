import numpy as np


class Analyzer:
    def __init__(self):
        pass

    def load_init_data(self, option_data, extracted_data, selected, coverage_iter):
        covered_branches = dict()
        new_candidates = dict()
        self.branch_count = dict()
        self.param_counter = dict()
        for data in extracted_data:
            if data["param_set"][0] in new_candidates.keys():
                new_candidates[data["param_set"][0]].append(data["param_set"][1])
                self.param_counter[data["param_set"][0]] += 1
            else:
                new_candidates[data["param_set"][0]] = [data["param_set"][1]]
                self.param_counter[data["param_set"][0]] = 1

            if tuple([data["param_set"][0]]) in covered_branches.keys():
                covered_branches[tuple([data["param_set"][0]])] = covered_branches[tuple([data["param_set"][0]])].union(set(data["covered"]))
            else:
                covered_branches[tuple([data["param_set"][0]])] = set(data["covered"])
            
            for br in data["covered"]:
                if br in self.branch_count.keys():
                    self.branch_count[br] += 1
                else:
                    self.branch_count[br] = 1
        for key, value in option_data.items():
            if (len(value[-1]) > 0) and key in new_candidates.keys():
                option_data[key] = tuple(list(value[:-1]) + [new_candidates[key]])
        score = self.scoring(covered_branches, selected, coverage_iter)
        return option_data, covered_branches, score
        

    def scoring(self, covered_branches, selected, iter_covered=set()):
        param_score = dict()
        if tuple(selected) in covered_branches.keys():
            covered_branches[tuple(selected)] = covered_branches[tuple(selected)].union(iter_covered)
        else:
            covered_branches[tuple(selected)] = iter_covered
        for br in iter_covered:
            if br in self.branch_count.keys():
                self.branch_count[br] += 1
            else:
                self.branch_count[br] = 1

        freq_score = {key : 1 / value for key, value in self.branch_count.items()}
        iter_score = 0
        for br in iter_covered:
            iter_score = iter_score + self.branch_count[br]
        for key, value in covered_branches.items():
            score = 0
            for br in value:
                score = score + self.branch_count[br]
            param_score[key] = score
        values = np.array(list(param_score.values()))
        keys = list(param_score.keys())

        sorted_idx = np.argsort(values)
        ranks = np.empty_like(sorted_idx)
        ranks[sorted_idx] = np.arange(len(values))

        threshold_rank = int(len(values) * 0.05)
        lower_rank_indices = np.where(ranks < threshold_rank)[0]
        upper_rank_indices = np.where(ranks >= threshold_rank)[0]
        upper_values = values[upper_rank_indices]

        min_val = np.min(upper_values)
        max_val = np.max(upper_values)
        scale = max_val - min_val if max_val - min_val != 0 else 1e-8

        norm_param_score = dict()
        for idx, key in enumerate(keys):
            if idx in lower_rank_indices:
                norm_param_score[key] = 0.0
            else:
                normed = round((values[idx] - min_val) / scale, 4)
                norm_param_score[key] = normed
        return norm_param_score

