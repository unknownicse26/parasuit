import random as rd


class StrSampling:
    def __init__(self, parameter_values, options, parameters):
        self.parameters = parameters
        self.options = []
        for option in options:
            if option in parameter_values["space"].keys():
                self.options.append(option)
        self.values = [[] for _ in range(len(self.options))]
        for i in range(len(self.options)):
            if parameter_values['space'][self.options[i]][0] == []:
                self.values[i].append(None)
            else:
                self.values[i].append(parameter_values['space'][self.options[i]][0][-1])

        self.branches = []
        self.scores = []

    def save(self, parameter_values):
        for i in range(len(self.options)):
            option = self.options[i]

            if parameter_values['space'][option][0] == []:
                self.values[i].append(None)
            else:
                self.values[i].append(parameter_values['space'][option][0][0])

    def explore(self, parameter_values, errored, isFix):
        for i in range(len(self.options)):
            option = self.options[i]
            if errored or (isFix[option] == 0):
                if parameter_values['space'][option][0] == []:
                    new_value = None
                else:
                    new_value = parameter_values['space'][option][0][0]

                while [new_value] == parameter_values['space'][option][0]:
                    for data in self.parameters:
                        if data[0] == option:
                            if data[1] not in data[2]:
                                data[2].append(data[1])
                            choiceSet = data[2]
                    new_value = rd.choice(choiceSet)

                if new_value == None:
                    parameter_values['space'][option][0] = []
                else:
                    parameter_values['space'][option][0] = [new_value]

        return parameter_values

    def exploit(self, parameter_values, scores):
        for i in range(len(self.options)):
            option = self.options[i]
            for data in self.parameters:
                if data[0] == option:
                    if data[1] not in data[2]:
                        data[2].append(data[1])
                    choiceSet = data[2]

            rdRate = rd.random()
            sums = [0] * len(choiceSet)
            counts = [0] * len(choiceSet)
            avgs = [0] * len(choiceSet)
            goods = []
            portion = []

            for j in range(len(scores)):
                idx = choiceSet.index(self.values[i][j])
                sums[idx] += scores[j]
                counts[idx] += 1
                avgs[idx] = sums[idx] / counts[idx]

            average = sum(sums) / sum(counts)

            for k in range(len(avgs)):
                if avgs[k] >= average:
                    goods.append(avgs[k])
                else:
                    goods.append(0)

            if goods == [0] * len(avgs):
                avgs2 = avgs
            else:
                avgs2 = goods

            if avgs2 == [0] * len(avgs):
                portion = [1 / len(avgs)] * len(avgs)
            else:
                for l in range(len(avgs2)):
                    if l == 0:
                        portion.append(avgs2[l] / sum(avgs2))
                    else:
                        portion.append(avgs2[l] / sum(avgs2) + portion[l - 1])

            p = rd.random()
            select_k = 0

            for m in range(len(portion)):
                if p >= portion[m]:
                    select_k = m + 1

            new_value = choiceSet[select_k]
            if new_value == None:
                parameter_values['space'][option][0] = []
            else:
                parameter_values['space'][option][0] = [new_value]
            self.values[i].append(new_value)

        return parameter_values
