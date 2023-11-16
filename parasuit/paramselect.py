# Requires sklearn and gensim pip packages
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec

import random as rd


class ParamTuning:
    def __init__(self, options, param_datas, typeSizes, intParams, strTimeParams):
        self.options = options
        self.param_datas = param_datas

        self.boolSize = typeSizes[0]
        self.intSize = typeSizes[0] + typeSizes[1]
        self.floatSize = typeSizes[0] + typeSizes[1] + typeSizes[2]
        self.stringTimeSize = typeSizes[0] + typeSizes[1] + typeSizes[2] + typeSizes[3]
        self.stringSize = typeSizes[0] + typeSizes[1] + typeSizes[2] + typeSizes[3] + typeSizes[4]

        self.select_list = list(range(len(self.options)))
        self.i = rd.choice(self.select_list)
        self.select_list.remove(self.i)

        self.tuned_scores = []
        self.tuned_values = []
        self.tuned_branches = []

        self.selected_scores = []
        self.selected_branches = []
        self.selected_opts = []

        self.default_scores = []
        self.default_branches = []

        self.branch_count = dict()
        self.branch_scores = dict()
        self.type = ''

        self.offed_params = []

  
    def branch_datas(self, coverages):
        for cov in coverages:
            if cov not in self.branch_count.keys():
                self.branch_count[cov] = 1
            else:
                self.branch_count[cov] += 1

  
    def compare(self, search_space, intParams, strTimeParams, total_cov):
        if len(self.tuned_scores) == len(self.default_scores):
            self.update_score(total_cov)
            if sum(self.tuned_scores) <= sum(self.default_scores) or (0 in self.tuned_scores):
                del search_space['space'][self.options[self.i]]

            else:
                self.selected_scores.append(self.tuned_scores)
                self.selected_opts.append(self.options[self.i])
                self.selected_branches.append(self.tuned_branches)
                if self.type == "bool":
                    search_space['space'][self.options[self.i]] = [[self.param_datas[self.i][1]], 1]
                elif self.type == "str":
                    if self.param_datas[self.i][1] == None:
                        search_space['space'][self.options[self.i]] = [[], 1]
                    else:
                        search_space['space'][self.options[self.i]] = [[self.param_datas[self.i][1]], 1]
                elif self.type == "float":
                    search_space['space'][self.options[self.i]] = [[1], 1]
                else:
                    if self.param_datas[self.i][1] == self.param_datas[self.i][2]:
                        self.offed_params.append([self.param_datas[self.i][0], self.default, self.type])
                    search_space['space'][self.options[self.i]] = [[self.param_datas[self.i][1]], 1]
                print("%s Parameter Saved." % self.options[self.i])
                print("Parameter Spaces : ", search_space['space'][self.options[self.i]])
                print()
            self.tuned_scores = []
            self.tuned_values = []
            self.tuned_branches = []
            self.i = rd.choice(self.select_list)
            self.select_list.remove(self.i)
            self.tune(intParams, strTimeParams)

        search_space['space'][self.options[self.i]] = [[self.tuned_values[len(self.tuned_scores) - 1]], 1]

        return search_space


    def sample_bool(self):
        print("BOOL Param Tuning")
        print("Now Tuning Parameter '%s'" % (self.param_datas[self.i][0]))
        self.type = "bool"

        if self.options[self.i] == "-make-concrete-symbolic":
            self.tuned_values = [1] * len(self.default_scores)

        else:
            if self.param_datas[self.i][1] == "false":
                self.tuned_values = ["true"] * len(self.default_scores)
            else:
                self.tuned_values = ["false"] * len(self.default_scores)
        print("Using Parameter Values ", self.tuned_values)

  
    def sample_int(self, intParams):
        print("INT Param Tuning")
        print("Now Tuning Parameter '%s'" % (self.param_datas[self.i][0]))
        self.type = "int"

        haveValue = []
        for data in intParams:
            if data[1] != data[2]:
                haveValue.append(data)

        else:
            if self.param_datas[self.i][2] is not None:  # Parameters that can be turned on and off
                if self.param_datas[self.i][1] == self.param_datas[self.i][2]:  # Parameter whose default setting is to turn off
                    self.default = self.similarity(haveValue)

                else:  # Parameter whose default setting is not to turn off
                    self.default = self.param_datas[self.i][1]

            else:  # Parameters that cannot be turned on and off
                self.default = self.param_datas[self.i][1]

            if self.default == 1:  # If default is 1, set values based on other ways (can only increase)
                self.tuned_values = [self.default * 2, self.default * 4, self.default * 8]
            else:
                self.tuned_values = [self.default // 2, self.default + (self.default // 2),
                                     rd.randint(self.default // 2, self.default + (self.default // 2))]

            while len(self.tuned_values) < len(self.default_scores):  # If comparing 4 or more results, create more samples
                self.tuned_values.append(rd.randint(self.tuned_values[0], self.tuned_values[1]))
        print("Using Parameter Values ", self.tuned_values)

  
    def sample_float(self):
        print("FLOAT Param Tuning")
        print("Now Tuning Parameter '%s'" % (self.param_datas[self.i][0]))
        self.type = "float"

        times = len(self.default_scores)
        for i in range(times):
            self.tuned_values.append(self.param_datas[self.i][1] / (times + 1) * (i + 1))
        print("Using Parameter Values ", self.tuned_values)

  
    def sample_stringTime(self, strTimeParams):
        print("TIME Param Tuning")
        print("Now Tuning Parameter '%s'" % (self.param_datas[self.i][0]))
        self.type = "time"

        haveValue = []
        for data in strTimeParams:
            if data[1] != data[2]:
                haveValue.append(data)

        if self.param_datas[self.i][2] is not None:  # Parameters that can be turned on and off
            if self.param_datas[self.i][1] == self.param_datas[self.i][2]:  # Parameter whose default setting is to turn off
                self.default = self.similarity(haveValue)

            else:  # Parameter whose default setting is not to turn off
                self.default = self.param_datas[self.i][1]

        else:  # Parameters that cannot be turned on and off
            self.default = self.param_datas[self.i][1]

        self.default = int(self.default[:self.default.find('s')])

        if self.default == 1:  # If default is 1, set values based on other ways (can only increase)
            self.tuned_values = ["%ds" % (self.default * 2), "%ds" % (self.default * 4), "%ds" % (self.default * 8)]
        else:
            self.tuned_values = ["%ds" % (self.default // 2), "%ds" % (self.default + (self.default // 2)),
                                 "%ds" % (rd.randint(self.default // 2, self.default + (self.default // 2)))]

        while len(self.tuned_values) < len(self.default_scores):  # If comparing 4 or more results, create more samples
            if self.default == 1:
                self.tuned_values.append("%ds" % (rd.randint(self.default * 2, self.default * 8)))
            else:
                self.tuned_values.append("%ds" % (rd.randint(self.default // 2, self.default + (self.default // 2))))
        print("Using Parameter Values ", self.tuned_values)

  
    def sample_string(self):
        print("STR Param Tuning")
        print("Now Tuning Parameter '%s'" % (self.param_datas[self.i][0]))
        self.type = "str"
        self.removed = 0

        choiceList = self.param_datas[self.i][2]
        if self.param_datas[self.i][1] in choiceList:
            choiceList.remove(self.param_datas[self.i][1])
            self.removed = 1
        for _ in range(len(self.default_scores)):
            self.tuned_values.append(rd.choice(choiceList))
        print("Using Parameter Values ", self.tuned_values)

  
    def similarity(self, haveValue):
        similar_score = []
        for data in haveValue:
            # Split a sentence into words
            tokens1 = self.param_datas[self.i][0].split('-')
            tokens2 = data[0].split('-')

            # Train Word2Vec model
            param = [tokens1, tokens2]
            model = Word2Vec(param, window=5, min_count=1, workers=4)

            # Generate sentence embeddings
            param1_vector = sum([model.wv[word] for word in tokens1]) / len(tokens1)
            param2_vector = sum([model.wv[word] for word in tokens2]) / len(tokens2)

            # Calculate cosine similarity of two sentences
            similarity = cosine_similarity([param1_vector], [param2_vector])[0][0]
            similar_score.append(similarity)

        default_idx = similar_score.index(max(similar_score))

        return haveValue[default_idx][1]

  
    def score(self, coverages, total_cov):
        total_covered = sum(self.branch_count.values())
        for br in self.branch_count.keys():
            self.branch_scores[br] = total_covered / self.branch_count[br]

        br_score = 0
        for cov in coverages:
            br_score += self.branch_scores[cov]

        iter_score = len(coverages) / total_cov

        return br_score * iter_score

  
    def tune(self, intParams, strTimeParams):
        if self.i < self.boolSize:
            print("Boolean Parameter")
            self.sample_bool()
        elif self.i < self.intSize:
            print("Integer Parameter")
            self.sample_int(intParams)
        elif self.i < self.floatSize:
            print("Float Parameter")
            self.sample_float()
        elif self.i < self.stringTimeSize:
            print("StringTime Parameter")
            self.sample_stringTime(strTimeParams)
        else:
            print("String Parameter")
            self.sample_string()

  
    def update_score(self, total_cov):
        for i in range(len(self.default_branches)):
            self.default_scores[i] = self.score(self.default_branches[i], total_cov)

        for j in range(len(self.tuned_branches)):
            self.tuned_scores[j] = self.score(self.tuned_branches[j], total_cov)

  
    def final_select(self, search_space):
        for data in self.offed_params:
            if data[2] == "int":
                search_space['space'][data[0]] = [[data[1]], 1]
            else:
                search_space['space'][data[0]] = [["%ds" % (data[1])], 1]

        return search_space
