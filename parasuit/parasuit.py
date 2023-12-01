# Default Setting
from parasuit.setdefault import SetDefault

# Parameter Selecting
from parasuit.keyword_filter import Filter
from parasuit.parameters import KLEEParameters
from parasuit.paramselect import PSelect

# Parameter Space Selecting
from parasuit.symparams import SymParams
from parasuit.errcheck import errHandler
from parasuit.psconstruct import PSConstruct
from parasuit.pvsample import PVSample
from parasuit.boolean import BoolSampling
from parasuit.string import StrSampling


class ParaSuit:
    def __init__(self, budget, parameter_values, tuneSize, clust):
        # Initialize Default Setting Tools
        self.setD = SetDefault(parameter_values)
        
        self.tuningSize = tuneSize
        self.budget = budget
        self.clust_iter = clust
        
        self.startSetD = 0
        self.startSelP = 0
        self.startConstS = 0
        self.selP_flag = 0
        self.clust_flag = 0
        self.max_score = 0
        


    def sample(self, elapsed, n_total, cov_iter, parameter_values, output_dir, run_dir, iteration):
        if (len(self.setD.select_list) == 0) and not self.startSetD:
            self.default_filtering(cov_iter, parameter_values, iteration, output_dir)
            self.init_selP()
            self.startSetD = 1

        # Defining Default Parameters
        if (len(self.setD.select_list) > 0):
            parameter_values = self.setD.removing(len(cov_iter), parameter_values, iteration + 1, output_dir, run_dir)
        
        else:
            if len(self.selP.select_list) > 0:
                self.selP.branch_datas(cov_iter)
                score = self.selP.score(cov_iter, n_total)
                if score > self.max_score:
                    self.max_score = score

                if (len(self.selP.default_scores) < self.tuningSize):
                    if self.selP_flag == 0:
                        self.selP_flag = 1
                    else:
                        self.selP.default_scores.append(score)
                        self.selP.default_branches.append(cov_iter)

                else:
                    if not self.startSelP:
                        self.selP.tune(self.params.integer_parameters, self.params.stringTime_parameters)
                        self.startSelP = 1
                    else:
                        self.selP.tuned_scores.append(score)
                        self.selP.tuned_branches.append(cov_iter)
                        parameter_values = self.selP.compare(parameter_values, self.params.integer_parameters,
                                                             self.params.stringTime_parameters, n_total)
            else:
                self.selP.branch_datas(cov_iter)
                score = self.selP.score(cov_iter, n_total)
                if not self.startConstS:
                    parameter_values = self.init_sampleV(elapsed, parameter_values)
                    self.startConstS = 1

                self.constS.scores.append(score)
                self.constS.branches.append(cov_iter)
                self.constS.branch_datas(cov_iter)

                if (elapsed <= ((self.timeOUT * 0.5) + self.runned)):
                    parameter_values = self.constS.solver(self.options, parameter_values, score, cov_iter, iteration, n_total)
                    parameter_values = self.tuneSym.randomSymArg(parameter_values)
                    parameter_values = self.tuneSym.randomSymFile(parameter_values)

                    isGood = (score >= self.max_score * 0.8)
                    if isGood:
                        self.errHandle.fixing = 1

                    if self.errHandle.fixing:
                        errored = 0
                        if self.errHandle.good_count == 0:
                            self.errHandle.good_count += 0.5
                        else:
                            self.errHandle.search_from_good_params(isGood)

                        parameter_values = self.tuneB.explore(parameter_values, errored, self.errHandle.fix)
                        parameter_values = self.tuneS.explore(parameter_values, errored, self.errHandle.fix)
                        self.tuneB.save(parameter_values)
                        self.tuneS.save(parameter_values)

                    else:
                        if score <= 1000:
                            self.errHandle.save_errcase(parameter_values)

                        errored = 1

                        while errored:
                            parameter_values = self.tuneB.explore(parameter_values, errored, self.errHandle.fix)
                            parameter_values = self.tuneS.explore(parameter_values, errored, self.errHandle.fix)
                            errored = self.errHandle.check_errcase(parameter_values)
                            if not errored:
                                self.tuneB.save(parameter_values)
                                self.tuneS.save(parameter_values)

                else:
                    try:
                        # Clustering
                        self.clust_flag += 1
                        if (self.clust_flag % self.clust_iter == 1):
                            print("[INFO] ParaSuit : Clustering Start.")
                            self.constS.update_score(n_total)
                            parameter_values, self.constS.datas = self.sampleV.new_sampling(parameter_values, self.options_all,
                                                                                self.constS.integer_option,
                                                                                self.constS.float_option, self.constS.datas,
                                                                                self.constS.scores)
                            print("[INFO] ParaSuit : Clustering Finished.")


                        # Exploitation
                        else:
                            for c in range(len(self.options_all)):
                                parameter_values, self.constS.datas = self.sampleV.after_clustering(parameter_values, score, c,
                                                                                        self.options_all[c],
                                                                                        self.constS.integer_option,
                                                                                        self.constS.float_option,
                                                                                        self.constS.datas)
                        parameter_values = self.tuneSym.dataSymArg(parameter_values, self.constS.scores)
                        parameter_values = self.tuneSym.dataSymFile(parameter_values, self.constS.scores)
                        parameter_values = self.tuneB.exploit(parameter_values, self.constS.scores)
                        parameter_values = self.tuneS.exploit(parameter_values, self.constS.scores)

                    except:
                        parameter_values = self.constS.solver(self.options, parameter_values, score, cov_iter, i, n_total)
                        parameter_values = self.tuneSym.randomSymArg(parameter_values)
                        parameter_values = self.tuneSym.randomSymFile(parameter_values)

                        isGood = (score >= self.max_score * 0.8)
                        if isGood:
                            self.errHandle.fixing = 1

                        if self.errHandle.fixing:
                            errored = 0
                            if self.errHandle.good_count == 0:
                                self.errHandle.good_count += 0.5
                            else:
                                self.errHandle.search_from_good_params(isGood)

                            parameter_values = self.tuneB.explore(parameter_values, errored, self.errHandle.fix)
                            parameter_values = self.tuneS.explore(parameter_values, errored, self.errHandle.fix)
                            self.tuneB.save(parameter_values)
                            self.tuneS.save(parameter_values)

                        else:
                            if score <= 1000:
                                self.errHandle.save_errcase(parameter_values)

                            errored = 1

                            while errored:
                                parameter_values = self.tuneB.explore(parameter_values, errored, self.errHandle.fix)
                                parameter_values = self.tuneS.explore(parameter_values, errored, self.errHandle.fix)
                                errored = self.errHandle.check_errcase(parameter_values)
                                if not errored:
                                    self.tuneB.save(parameter_values)
                                    self.tuneS.save(parameter_values)

        return parameter_values



    def default_filtering(self, cov_iter, parameter_values, i, output_dir):
        parameter_values = self.setD.removing(len(cov_iter), parameter_values, i + 1, output_dir, run_dir)
        parameter_values = self.setD.optimizing(parameter_values)
        self.params = KLEEParameters()
        paramFilter = Filter(self.params, parameter_values)

        self.params = paramFilter.filtering(self.params)
        self.opt_names = [opts[0] for opts in self.params.totalParams]
        

        
    def init_selP(self):
        typeSizes = [len(self.params.boolean_parameters), len(self.params.integer_parameters), len(self.params.float_parameters),
                        len(self.params.stringTime_parameters), len(self.params.string_parameters)]
        self.selP = PSelect(self.opt_names, self.params.totalParams, typeSizes, self.params.integer_parameters,
                                    self.params.stringTime_parameters)

        # Initialize Parameter Space Sampling Tools
        self.sampleV = PVSample()
        self.tuneSym = SymParams()
        self.boolean_option = self.opt_names[:typeSizes[0]]
        self.str_option = self.opt_names[len(self.opt_names) - len(self.params.string_parameters):]
    

    def init_sampleV(self, elapsed, parameter_values):
        parameter_values = self.selP.final_select(parameter_values)

        self.constS = PSConstruct(self.selP.branch_count, self.selP.branch_scores)
        self.options = self.constS.option_seperator(parameter_values)
        self.options_all = self.constS.integer_option + self.constS.string_option + self.constS.float_option
        self.constS.put_init(parameter_values)
        self.tuneB = BoolSampling(parameter_values, self.boolean_option)
        self.tuneS = StrSampling(parameter_values, self.str_option, self.params.string_parameters)

        self.errHandle = errHandler(parameter_values)

        self.runned = elapsed
        self.timeOUT = self.budget - elapsed

        return parameter_values