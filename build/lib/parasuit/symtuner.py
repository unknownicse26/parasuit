'''Common components for SymTuner

This module contains common componets for SymTuner. This module includes time budget hander
and SymTuner interface (with implementation of common algorithm).
'''

from abc import ABC
from abc import abstractclassmethod
from abc import abstractmethod
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import json
import numpy as np
import random

from parasuit.logger import get_logger


class SymTuner(ABC):
    '''SymTuner interface with common algorithm implemented

    SymTUner interface with common algorirhm implemented. Symbolic executor specific SymTuner
    needs 2 abstract methods to be re-implemented: `SymTuner.evaluate` and
    `SymTuner.get_space`.
    '''

    def __init__(self, parameter_space=None):
        self.data = []


    def budget_handler(elapsed, total_budget, iter_budget):
        if (total_budget - elapsed) >= iter_budget:
            return iter_budget
        else:
            return total_budget - elapsed


    def convert(self, parameter_space, budget):
        print("Parameter Before : ", parameter_space)
        '''Sample a set of parameters to use

        Sampling with 2 policies: exploit and eplore.

        Args:
            policy: Sampling policy. One of 'exploit' and 'explore'. If not set, sampling with
            [exploit_portion, 1 - exploit_portion] internally.

        Returns:
            A dictionary of sampled parameters.
        '''

        self.space = parameter_space['space']
        self.default = parameter_space['defaults']
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

        print()
        print("Parameter After : ", parameters)

        return parameters


    def add(self, target, parameters, testcases, evaluation_kwargs=None):
        '''Evaluate and update data

        Evaluate and update data.

        Args:
            target: A target program to evaluate with.
            paramters: A set of parameters used to generated testcases.
            testcases: Testcases genereted with parameters.
            evaluation_kwargs: A dictionary of keyword arguments pass to evaluate method.

        Returns:
            Self object for chaining. All updates is recorded in the object.
        '''

        self.data2 = []
        if evaluation_kwargs is None:
            evaluation_kwargs = {}

        # self.count_used_parameters(parameters)
        for testcase in testcases:
            coverage, bug = self.evaluate(target, testcase,
                                          **evaluation_kwargs)
            self.data.append((coverage, bug, testcase, parameters))
            self.data2.append((coverage, bug, testcase, parameters))
        return self

    def get_space_json(self):
        '''Get tuning space and default parameters

        Get tuning space and default parameters.

        Returns:
            A dictionary of tuning space and default parameters.
        '''

        json_dict = {
            'space': self.space,
            'defaults': self.defaults,
        }
        return json_dict

    def get_coverage_and_bugs(self):
        '''Get total coverage and bugs

        Get total coverage and bugs collected.

        Returns:
            A tuple of coverage and bugs found in total. The first element of the tuple is a set
            of coverage and the second element is a set of bugs.
        '''

        coverage = set()

        coverage2 = set()

        for cov, _, _, _ in self.data:
            coverage = coverage | cov

        for cov2, _, _, _ in self.data2:
            coverage2 = coverage2 | cov2

        return coverage, coverage2

    def get_testcase_causing_bug(self, bug):
        '''Get testcase causing the given bug

        Get testcase causing the given bug. If there are multiple testcases, return the latest one.

        Args:
            bug: A bug interested in.

        Returns:
            A latest testcase causes the given bug. Returns None if no testcase is found.
        '''

        for _, bugs, tc, _ in self.data[::-1]:
            if bug in bugs:
                return tc
        return None

    @abstractmethod
    def evaluate(self, target, testcase, **kwargs):
        '''Evaluate the given testcase

        Evaluate the given testcase and report the coverage (i.e. branch coverage) and a bug
        if found. This part should be written for each symbolic executor to handle the testcases
        generated in different format.

        Args:
            testcase: A testcase to evaluate.

        Returns:
            A tuple of bugs if found and the coverage (i.e. branch coverage). If bug are not found,
            the first element of the return tuple will be an empty set.
        '''

    @abstractclassmethod
    def get_space(cls):
        '''Make a default parameter space

        Make a default parameter space. This part should be written for each symbolic executor.

        Returns:
            A dictionary whose keys are the name of the parameters and values are the possible
            space for each parameter.
        '''

    @classmethod
    def get_default_params(cls):
        '''Make a default default parameter set

        Make a default default parameter set. The parameters included in this set always will be
        sampled. This part may be written for each symbolic executor. By default, the return value
        is an empty list.

        Returns:
            A dictionary of parameters that should be included in every symbolic executor calls.
        '''

        return {}

    @classmethod
    def get_space_json(cls):
        '''Get default tuning space and default default parameters

        Get default tuning space and default default parameters.

        Returns:
            A dictionary of tuning space and default parameters.
        '''

        json_dict = {
            'space': cls.get_space(),
            'defaults': cls.get_default_params(),
        }
        return json_dict
