import random as rd


class BoolSampling:
    def __init__(self, parameter_values, options):
        self.options = []
        for option in options:
            if option in parameter_values["space"].keys():
                self.options.append(option)
        self.values = [[] for _ in range(len(self.options))]
        for i in range(len(self.options)):
            self.values[i].append(parameter_values['space'][self.options[i]][0][-1])
        self.branches = []
        self.scores = []

    def save(self, parameter_values):
        for i in range(len(self.options)):
            option = self.options[i]
            self.values[i].append(parameter_values['space'][option][0][0])

    def explore(self, parameter_values, errored, isFix):
        for i in range(len(self.options)):
            option = self.options[i]
            rdRate = rd.random()
            if errored or isFix[option] == 0:
                if rdRate <= 0.5:
                    if option == "-make-concrete-symbolic":
                        value = 1
                    else:
                        value = "true"
                else:
                    if option == "-make-concrete-symbolic":
                        value = 0
                    else:
                        value = "false"

                parameter_values['space'][option][0] = [value]

        return parameter_values

    def exploit(self, parameter_values, scores):
        for i in range(len(self.options)):
            option = self.options[i]
            rdRate = rd.random()

            avgTrue = 0
            avgFalse = 0
            for j in range(len(scores)):
                if option == "-make-concrete-symbolic":
                    if self.values[i][j] == 1:
                        avgTrue += scores[j]
                    else:
                        avgFalse += scores[j]
                else:
                    if self.values[i][j] == "true":
                        avgTrue += scores[j]
                    else:
                        avgFalse += scores[j]

            if option == "-make-concrete-symbolic":
                avgTrue = avgTrue / self.values[i].count(1)
                avgFalse = avgFalse / self.values[i].count(0)
            else:
                avgTrue = avgTrue / self.values[i].count("true")
                avgFalse = avgFalse / self.values[i].count("false")
            threshold = avgTrue / (avgTrue + avgFalse)

            if rdRate <= threshold:
                if option == "-make-concrete-symbolic":
                    new_value = 1
                else:
                    new_value = "true"
            else:
                if option == "-make-concrete-symbolic":
                    new_value = 0
                else:
                    new_value = "false"

            parameter_values['space'][option][0] = [new_value]
            self.values[i].append(new_value)

        return parameter_values