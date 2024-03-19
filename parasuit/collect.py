import random as rd


class Collect:
    def __init__(self, prev_branch_count, prev_branch_scores):
        self.integer_option = []
        self.string_option = []
        self.float_option = []
        self.scores = []
        self.branches = []
        self.cnt_cov = dict()
        self.tmp = dict()
        self.branch_count = prev_branch_count
        self.branch_scores = prev_branch_scores
        self.not_string = ["dfs", "bfs"]


    def branch_datas(self, coverages):
        for cov in coverages:
            if cov not in self.branch_count.keys():
                self.branch_count[cov] = 1
            else:
                self.branch_count[cov] += 1


    def solver(self, options, parameter_values, coverage, branches, iter, total_cov):
        if iter % 2 == 1:
            self.update_score(total_cov)

        parameter_values = self.integer(options[0], parameter_values, coverage)
        parameter_values = self.string(options[1], parameter_values, coverage)
        parameter_values = self.floats(options[2], parameter_values)

        return parameter_values


    def integer(self, options, parameter_values, value):
        for i in range(len(options)):
            option = options[i]

            if (self.i_i[i] % 2) == 1:
                self.i_r2[i] = value

                if self.i_i[i] == 1:
                    self.i_n[i] = parameter_values['space'][option][0][-1]
                    self.i_min[i] = self.i_n[i] - (self.i_n[i] // 2)
                    self.i_max[i] = self.i_n[i] + (self.i_n[i] // 2)

                else:
                    self.i_n[i] = self.select_next_n(i, self.i_r1[i], self.i_r2[i], self.i_num1[i], self.i_num2[i],
                                                     self.branches[-2], self.branches[-1], self.i_n[i])
                    self.i_min[i] = self.i_n[i] - (self.i_n[i] // 2)
                    self.i_max[i] = self.i_n[i] + (self.i_n[i] // 2)

                if (self.i_num1[i] == self.i_num2[i] == self.i_n[i]):
                    if self.i_n[i] == max(self.datas[i]):
                        self.i_num1[i] = rd.randint(self.i_n[i], int(max(self.datas[i]) * 1.5))
                    else:
                        self.i_num1[i] = rd.randint(self.i_n[i], max(self.datas[i]))

                else:
                    self.i_num1[i] = rd.randint(self.i_min[i], self.i_n[i])
                self.datas[i].append(self.i_num1[i])
                parameter_values['space'][option][0] = [self.i_num1[i]]

            else:
                if (self.i_num1[i] == self.i_num2[i] == self.i_n[i]):
                    if self.i_n[i] == max(self.datas[i]):
                        self.i_num2[i] = rd.randint(self.i_n[i], int(max(self.datas[i]) * 1.5))
                    else:
                        self.i_num2[i] = rd.randint(self.i_n[i], max(self.datas[i]))

                else:
                    if self.i_n[i] == 1:
                        self.i_num2[i] = rd.randint(self.i_n[i], self.i_n[i] * 5)
                    else:
                        self.i_num2[i] = rd.randint(self.i_n[i], self.i_max[i])
                self.datas[i].append(self.i_num2[i])
                parameter_values['space'][option][0] = [self.i_num2[i]]
                self.i_r1[i] = value

            self.i_i[i] += 1

        return parameter_values


    def string(self, options, parameter_values, value):
        for i in range(len(options)):
            option = options[i]

            if (self.s_i[i] % 2) == 1:
                self.s_r2[i] = value

                if self.s_i[i] == 1:
                    n = parameter_values['space'][option][0][-1]
                    idx = n.find('s')
                    self.s_n[i] = int(n[:idx])
                    self.s_min[i] = self.s_n[i] - (self.s_n[i] // 2)
                    self.s_max[i] = self.s_n[i] + (self.s_n[i] // 2)

                else:
                    self.s_n[i] = self.select_next_n(len(self.integer_option) + i, self.s_r1[i], self.s_r2[i],
                                                     self.s_num1[i], self.s_num2[i], self.branches[-2],
                                                     self.branches[-1], self.s_n[i])
                    self.s_min[i] = self.s_n[i] - (self.s_n[i] // 2)
                    self.s_max[i] = self.s_n[i] + (self.s_n[i] // 2)

                if (self.s_num1[i] == self.s_num2[i] == self.s_n[i]):
                    if self.s_n[i] == max(self.datas[len(self.integer_option) + i]):
                        self.s_num1[i] = rd.randint(self.s_n[i],
                                                    int(max(self.datas[len(self.integer_option) + i]) * 1.5))
                    else:
                        self.s_num1[i] = rd.randint(self.s_n[i], max(self.datas[len(self.integer_option) + i]))

                else:
                    self.s_num1[i] = rd.randint(self.s_min[i], self.s_n[i])
                self.datas[len(self.integer_option) + i].append(self.s_num1[i])
                parameter_values['space'][option][0] = ["%ds" % (self.s_num1[i])]

            else:
                if (self.s_num1[i] == self.s_num2[i] == self.s_n[i]):
                    if self.s_n[i] == max(self.datas[len(self.integer_option) + i]):
                        self.s_num2[i] = rd.randint(self.s_n[i],
                                                    int(max(self.datas[len(self.integer_option) + i]) * 1.5))
                    else:
                        self.s_num2[i] = rd.randint(self.s_n[i], max(self.datas[len(self.integer_option) + i]))

                else:
                    if self.s_n[i] == 1:
                        self.s_num2[i] = rd.randint(self.s_n[i], self.s_n[i] * 5)
                    else:
                        self.s_num2[i] = rd.randint(self.s_n[i], self.s_max[i])
                self.datas[len(self.integer_option) + i].append(self.s_num2[i])
                parameter_values['space'][option][0] = ["%ds" % (self.s_num2[i])]
                self.s_r1[i] = value

            self.s_i[i] += 1

        return parameter_values


    def floats(self, options, parameter_values):
        for i in range(len(options)):
            option = options[i]
            new_value = rd.random()
            parameter_values['space'][option][0] = [new_value]
            self.datas[len(self.integer_option) + len(self.string_option) + i].append(new_value)

        return parameter_values


    def option_seperator(self, parameter_values):
        key = list(parameter_values['space'].keys())
        for i in range(len(parameter_values['space'].keys())):
            option = key[i]
            if len(parameter_values['space'][option][0]) >= 4:
                continue

            if parameter_values['space'][option][0] == []:
                continue

            if option == "-make-concrete-symbolic":
                continue

            elif isinstance(parameter_values['space'][option][0][-1], int) and parameter_values['space'][option][0][-1] != 1:
                self.integer_option.append(option)
            elif (isinstance(parameter_values['space'][option][0][-1], str)) and parameter_values['space'][option][0][0][
                -1] == 's' and parameter_values['space'][option][0][0] not in self.not_string:
                self.string_option.append(option)
            elif (parameter_values['space'][option][0][-1] == 1.0):
                self.float_option.append(option)
            else:
                pass

        self.i_i = [1] * len(self.integer_option)
        self.i_n = [0] * len(self.integer_option)
        self.i_r1 = [0] * len(self.integer_option)
        self.i_r2 = [0] * len(self.integer_option)
        self.i_num1 = [0] * len(self.integer_option)
        self.i_num2 = [0] * len(self.integer_option)
        self.i_max = [0] * len(self.integer_option)
        self.i_min = [0] * len(self.integer_option)
        self.i_flag = [0] * len(self.integer_option)

        self.s_i = [1] * len(self.string_option)
        self.s_n = [0] * len(self.string_option)
        self.s_r1 = [0] * len(self.string_option)
        self.s_r2 = [0] * len(self.string_option)
        self.s_num1 = [0] * len(self.string_option)
        self.s_num2 = [0] * len(self.string_option)
        self.s_max = [0] * len(self.string_option)
        self.s_min = [0] * len(self.string_option)
        self.s_flag = [0] * len(self.string_option)

        self.datas = [[] for _ in range(len(self.integer_option) + len(self.string_option) + len(self.float_option))]

        return [self.integer_option, self.string_option, self.float_option]


    def select_next_n(self, option, cov1, cov2, val1, val2, br1, br2, n):
        scores = [cov1, cov2]
        values = [val1, val2]
        branches = [br1, br2]
        p = rd.random()
        if cov1 == cov2 == 0:
            new_value = n
        else:
            port = cov1 / (cov1 + cov2)
            if p < port:
                new_value = val1
            elif p > port:
                new_value = val2
            else:
                new_value = n

        return new_value


    def scoring(self, coverage, total_cov):
        total_covered = sum(self.branch_count.values())
        for br in self.branch_count.keys():
            self.branch_scores[br] = total_covered / self.branch_count[br]

        br_score = 0
        for cov in coverage:
            br_score += self.branch_scores[cov]

        iter_score = len(coverage) / total_cov

        return br_score * iter_score


    def update_score(self, total_cov):
        for i in range(len(self.branches)):
            self.scores[i] = self.scoring(self.branches[i], total_cov)


    def put_init(self, parameter_values):
        options_all = self.integer_option + self.string_option + self.float_option

        for i in range(len(options_all)):
            if options_all[i] in self.string_option:
                n = parameter_values['space'][options_all[i]][0][-1]
                idx = n.find('s')
                self.datas[i].append(int(n[:idx]))
            else:
                self.datas[i].append(parameter_values['space'][options_all[i]][0][-1])
