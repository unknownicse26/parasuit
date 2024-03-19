import random as rd


class errHandler:
    def __init__(self, parameter_values):
        self.err_values = []
        self.param_type = {}
        for p in parameter_values['space'].keys():
            if parameter_values['space'][p][0] == []:
                self.param_type[p] = "str"
            else:
                try:
                    if isinstance(parameter_values['space'][p][0][0], int):
                        self.param_type[p] = "int"
                    elif isinstance(parameter_values['space'][p][0][0], float):
                        self.param_type[p] = "float"
                    else:
                        if parameter_values['space'][p][0][0] == "true" or parameter_values['space'][p][0][0] == "false":
                            self.param_type[p] = "bool"
                        elif parameter_values['space'][p][0][0][:-1].isdigit():
                            self.param_type[p] = "time"
                        else:
                            self.param_type[p] = "str"
                except:
                    pass

        self.good_param = [0] * len(self.param_type.keys())
        self.fix = {key: 0 for key in self.param_type.keys()}
        self.fixing = 0
        self.good_count = 0

    def check_errcase(self, parameter_values):
        for case in self.err_values:
            match = [0] * len(self.param_type.keys())
            for i, p in enumerate(self.param_type.keys()):
                if self.param_type[p] == "int" or self.param_type[p] == "float":
                    if (parameter_values['space'][p][0][0] >= case[i][0]) and (
                            parameter_values['space'][p][0][0] <= case[i][1]):
                        match[i] = 1

                elif self.param_type[p] == "time":
                    value = int(parameter_values['space'][p][0][0][:-1])
                    if (value >= case[i][0]) and (value <= case[i][1]):
                        match[i] = 1

                else:
                    if (parameter_values['space'][p][0] == []):
                        if (case[i] == None):
                            match[i] = 1
                    else:
                        if (parameter_values['space'][p][0][0] == case[i]):
                            match[i] = 1

                if sum(match) >= (len(parameter_values['space'].keys()) * 0.7):
                    return 1

        return 0

    def save_errcase(self, parameter_values):
        tmp_list = []
        for p in self.param_type.keys():
            if self.param_type[p] == "int":
                value = parameter_values['space'][p][0][0]
                tmp_list.append((value - int(value / 8), value + int(value / 8)))

            elif self.param_type[p] == "float":
                value = parameter_values['space'][p][0][0]
                tmp_list.append((value - value / 8, value + value / 8))

            elif self.param_type[p] == "time":
                value = int(parameter_values['space'][p][0][0][:-1])
                tmp_list.append((value - int(value / 8), value + int(value / 8)))
            else:
                if parameter_values['space'][p][0] == []:
                    tmp_list.append(None)
                else:
                    tmp_list.append(parameter_values['space'][p][0][0])

        self.err_values.append(tmp_list)

    def search_from_good_params(self, isGood):
        self.fixing = 1
        if isGood:
            fixx = [i for i, x in enumerate(self.good_param) if x == 1]

            # If there is an element with value 1
            if fixx:
                # Set the number of elements to randomly change
                if (len(fixx) - 2) < 1:
                    num_to_change = 1
                else:
                    num_to_change = rd.randint(1, len(fixx) - 2)

                # Randomly selects an element without allowing duplicates and changes it to 0
                selected_indices = rd.sample(fixx, num_to_change)

                for random_index in selected_indices:
                    self.good_param[random_index] = 0

            for i, p in enumerate(self.param_type.keys()):
                self.fix[p] = self.good_param[i]

            self.good_count = 0


        else:
            self.good_param = [1 - x for x in self.good_param]  # Swapping 1 and 0
            # Create a list of indices of elements with a value of 0
            fixx = [i for i, x in enumerate(self.good_param) if x == 0]

            # If there is an element with value 0
            if fixx:
                # Set the number of elements to be randomized (e.g. 2)
                if (len(fixx) - 1) < 0:
                    num_to_change = 0
                else:
                    num_to_change = rd.randint(0, len(fixx) - 1)

                # Randomly selects an element without allowing duplicates and changes it to 1
                selected_indices = rd.sample(fixx, num_to_change)

                for random_index in selected_indices:
                    self.good_param[random_index] = 1

            for i, p in enumerate(self.param_type.keys()):
                self.fix[p] = self.good_param[i]

            self.good_count += 1

        if self.good_count >= 3:
            self.good_param = self.good_param = [0] * len(self.param_type.keys())
            self.fix = {key: 0 for key in self.param_type.keys()}
            self.fixing = 0
            self.good_count = 0