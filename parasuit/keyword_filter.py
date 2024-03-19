class Filter:
    def __init__(self, pClass, parameter_values):
        self.bool_opts = [lst[0] for lst in pClass.boolean_parameters]
        self.int_opts = [lst[0] for lst in pClass.integer_parameters]
        self.float_opts = [lst[0] for lst in pClass.float_parameters]
        self.time_opts = [lst[0] for lst in pClass.stringTime_parameters]
        self.str_opts = [lst[0] for lst in pClass.string_parameters]

        self.keywords = ["write", "debug", "log", "pc", "print", "replay", "stop", "close"]
        self.escape = ["pct"]

        self.description = pClass.description

        self.defaults = list(parameter_values["defaults"].keys())


    def filtering(self, pClass):
        ft_list = []

        # BOOLEAN PARAMETERS
        for b_opt in self.bool_opts:
            filtered = 0
            for key in self.keywords :
                if (key in b_opt) or (key in pClass.description[b_opt].lower()):
                    filtered = 1
                
            for esc in self.escape:
                if esc in b_opt:
                    filtered = 0

            if b_opt in self.defaults:
                filtered = 1

            if filtered:
                ft_list.append(b_opt)
                idx_b = next((idx_b for idx_b, sublist in enumerate(pClass.boolean_parameters) if sublist[0] == b_opt), None)
                pClass.boolean_parameters.remove(pClass.boolean_parameters[idx_b])


        # INTEGER PARAMETERS
        for i_opt in self.int_opts:
            filtered = 0
            for key in self.keywords:
                if (key in i_opt) or (key in pClass.description[i_opt].lower()):
                    filtered = 1
                    
            for esc in self.escape:
                if esc in i_opt:
                    filtered = 0

            if i_opt in self.defaults:
                filtered = 1

            if filtered:
                ft_list.append(i_opt)
                idx_i = next((idx_i for idx_i, sublist in enumerate(pClass.integer_parameters) if sublist[0] == i_opt), None)
                pClass.integer_parameters.remove(pClass.integer_parameters[idx_i])


        # FLOAT PARAMETERS
        for f_opt in self.float_opts:
            filtered = 0
            for key in self.keywords:
                if (key in f_opt) or (key in pClass.description[f_opt].lower()):
                    filtered = 1
        
            for esc in self.escape:
                if esc in f_opt:
                    filtered = 0

            if f_opt in self.defaults:
                filtered = 1

            if filtered:
                ft_list.append(f_opt)
                idx_f = next((idx_f for idx_f, sublist in enumerate(pClass.float_parameters) if sublist[0] == f_opt), None)
                pClass.float_parameters.remove(pClass.float_parameters[idx_f])


        # TIME PARAMETERS
        for t_opt in self.time_opts:
            filtered = 0
            for key in self.keywords:
                if (key in t_opt) or (key in pClass.description[t_opt].lower()):
                    filtered = 1

            for esc in self.escape:
                if esc in t_opt:
                    filtered = 0

            if t_opt in self.defaults:
                filtered = 1

            if filtered:
                ft_list.append(t_opt)
                idx_t = next((idx_t for idx_t, sublist in enumerate(pClass.stringTime_parameters) if sublist[0] == t_opt), None)
                pClass.stringTime_parameters.remove(pClass.stringTime_parameters[idx_t])

        # STRING PARAMETERS
        for s_opt in self.str_opts:
            filtered = 0
            for key in self.keywords:
                if (key in s_opt) or (key in pClass.description[s_opt].lower()):
                    filtered = 1
                    
            for esc in self.escape:
                if esc in s_opt:
                    filtered = 0
            
            if s_opt in self.defaults:
                filtered = 1

            if filtered:
                ft_list.append(s_opt)
                idx_s = next((idx_s for idx_s, sublist in enumerate(pClass.string_parameters) if sublist[0] == s_opt), None)
                pClass.string_parameters.remove(pClass.string_parameters[idx_s])

        pClass.totalParams = pClass.boolean_parameters + pClass.integer_parameters + pClass.float_parameters + pClass.stringTime_parameters + pClass.string_parameters

        
        return pClass

            