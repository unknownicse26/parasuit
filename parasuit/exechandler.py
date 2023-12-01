from abc import ABC
from abc import abstractclassmethod
from abc import abstractmethod
import json
import random



class ExecHandler(ABC):
    def __init__(self, parameter_values=None):
        self.space = parameter_values['space']
        self.cnts = {}
        self.len_cnts = {}
        for param, (space, n_sample) in self.space.items():
            self.cnts[param] = {}
            for val in space:
                self.cnts[param][val] = 0
            self.len_cnts[param] = {}
            for i in range(1, n_sample + 1):
                self.len_cnts[param][i] = 0
        self.data = []


    def budget_handler(self, elapsed, total_budget, iter_budget):
        if (total_budget - elapsed) >= iter_budget:
            return iter_budget
        else:
            return total_budget - elapsed


    def convert(self, parameter_values, budget):
        self.space = parameter_values['space']
        self.default = parameter_values['defaults']
        parameters = dict()


        for param, value in self.default.items():
            parameters[param] = value

        for param, (space, n_sample) in self.space.items():
            if n_sample == 1:
                parameters[param] = space
            else:
                tmp_list = []
                for _ in range(n_sample):
                    tmp_list.append(random.choice(space))
                parameters[param] = tmp_list

        return parameters


    def add(self, target, parameters, testcases, evaluation_kwargs=None):
        self.data2 = []
        if evaluation_kwargs is None:
            evaluation_kwargs = {}

        for testcase in testcases:
            coverage, bug = self.evaluate(target, testcase,
                                          **evaluation_kwargs)
            self.data.append((coverage, bug, testcase, parameters))
            self.data2.append((coverage, bug, testcase, parameters))
        return self

    def get_space_json(self):
        json_dict = {
            'space': self.space,
            'defaults': self.defaults,
        }
        return json_dict

    def get_coverage_and_bugs(self):
        coverage = set()
        coverage2 = set()

        for cov, _, _, _ in self.data:
            coverage = coverage | cov

        for cov2, _, _, _ in self.data2:
            coverage2 = coverage2 | cov2

        return coverage, coverage2


    def get_testcase_causing_bug(self, bug):
        for _, bugs, tc, _ in self.data[::-1]:
            if bug in bugs:
                return tc
        return None

    @abstractmethod
    def evaluate(self, target, testcase, **kwargs):
        pass

    @abstractclassmethod
    def get_space(cls):
        pass
        

    @classmethod
    def get_default_params(cls):

        return {}

    @classmethod
    def get_space_json(cls):
        json_dict = {
            'space': cls.get_space(),
            'defaults': cls.get_default_params(),
        }
        return json_dict
