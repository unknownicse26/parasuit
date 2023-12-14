import random as rd


class SymParams:
    def __init__(self):
        self.sym_arg_data = []
        self.sym_file_num_data = []
        self.sym_file_size_data = []

    def countingValues(self, data_list, covs):
        values = []
        count = []
        total = []

        for i in range(len(data_list)):
            if data_list[i] in values:
                idx = values.index(data_list[i])
                count[idx] += 1
                total[idx] += covs[i]
            else:
                values.append(data_list[i])
                count.append(1)
                total.append(covs[i])

        scores = []
        for j in range(len(values)):
            score = total[j] / count[j]
            scores.append(score)

        portion = []
        if sum(scores) == 0:
            for k in range(len(scores)):
                portion.append(1 / len(scores) * (k + 1))
        else:
            for k in range(len(values)):
                if k == 0:
                    portion.append(scores[k] / sum(scores))
                else:
                    portion.append(scores[k] / sum(scores) + portion[k - 1])

        p = rd.random()
        selected = 0

        for l in range(len(portion)):
            if p >= portion[l]:
                selected = l + 1

        return values[selected]

    def randomSymArg(self, parameter_values):
        size_list = []
        num = rd.randint(1, 7)
        self.sym_arg_data.append(num)
        for i in range(num):
            size_list.append(rd.randint(1, 20))
        parameter_values['space']['-sym-arg'] = [size_list, num]

        return parameter_values

    def dataSymArg(self, parameter_values, covs):
        size_list = []
        num = self.countingValues(self.sym_arg_data, covs)
        self.sym_arg_data.append(num)
        for i in range(num):
            size_list.append(rd.randint(1, 20))
        parameter_values['space']['-sym-arg'] = [size_list, num]

        return parameter_values

    def randomSymFile(self, parameter_values):
        size = rd.randint(1, 30)
        self.sym_file_size_data.append(size)
        num = rd.randint(1, 2)
        self.sym_file_num_data.append(num)

        new_value = ["%d %d" % (num, size)]
        parameter_values['space']['-sym-files'] = [new_value, 1]

        return parameter_values

    def dataSymFile(self, parameter_values, covs):
        size = self.countingValues(self.sym_file_size_data, covs)
        self.sym_file_size_data.append(size)
        num = self.countingValues(self.sym_file_num_data, covs)
        self.sym_file_num_data.append(num)

        new_value = ["%d %d" % (num, size)]
        parameter_values['space']['-sym-files'] = [new_value, 1]

        return parameter_values