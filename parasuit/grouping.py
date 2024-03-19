from parasuit.parameters import KLEEParameters
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, manhattan_distances
from gensim.models import Word2Vec
import copy


class Grouping:
    def __init__(self, params, threshold):
        self.param_original = KLEEParameters()
        self.param_backup = copy.deepcopy(params)
        self.params = copy.deepcopy(params)
        pnames = [p[0] for p in self.params.totalParams]
        self.sents = self.opt_to_sentence(pnames)
        self.groups, self.rep_sents = self.grouping(threshold)


    def opt_to_sentence(self, pnames):
        sentences = []
        for param in pnames:
            if param[0] == '-':
                param = param[1:]
            
            p_sen = param.replace('-', ' ')
            p_sen = p_sen + '.'

            sentences.append(p_sen)

        return sentences


    def grouping(self, threshold):
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(self.sents)

        # Calculate Manhattan_distance matrix.
        similarities = manhattan_distances(tfidf_matrix)
        similarities = 1 - (1 / (1 + similarities))

        # Group Sentences.
        groups = []    
        selected = set()

        for i in range(len(self.sents)):
            if self.sents[i] not in selected:
                group = [self.sents[i]]
                selected.add(self.sents[i])
                for j in range(len(self.sents)):
                    if j != i and similarities[i][j] < threshold:
                        if self.sents[j] not in selected:
                            group.append(self.sents[j])
                            selected.add(self.sents[j])
                groups.append(group)

        # Define representative sentence for each group.
        representative_sentences = []
        for i, group in enumerate(groups):
            if len(group) == 1:
                rep_sent = group[0]
            else:
                min_similar = float("inf")
                rep_sent = str()
                for s1 in group:
                    sum = 0
                    for s2 in group:
                        tfidf_matrix = vectorizer.fit_transform([s1, s2])
                        similarity = manhattan_distances(tfidf_matrix[0].reshape(1, -1), tfidf_matrix[1].reshape(1, -1))
                        similarity = 1 - (1 / (1 + similarity))

                        sum += similarity[0][0]
                        
                    if sum < min_similar:
                        min_similar = sum
                        rep_sent = s1
            
            representative_sentences.append(rep_sent)

        groups, representative_sentences = self.sent_to_opt(groups, representative_sentences)

        return groups, representative_sentences


    def sent_to_opt(self, groups, rep_sents):
        for group in groups:
            for i in range(len(group)):
                tmp = group[i]
                tmp = "-" + tmp[:-1]
                group[i] = tmp.replace(' ', '-')

        for j in range(len(rep_sents)):
            tmp2 = rep_sents[j]
            tmp2 = "-" + tmp2[:-1]
            rep_sents[j] = tmp2.replace(' ', '-')

        return groups, rep_sents


    def make_data(self):
        bools = []
        ints = []
        floats = []
        times = []
        strings = []
        for db in self.params.boolean_parameters:
            if db[0] in self.rep_sents:
                bools.append(db)

        for di in self.params.integer_parameters:
            if di[0] in self.rep_sents:
                ints.append(di)

        for df in self.params.float_parameters:
            if df[0] in self.rep_sents:
                floats.append(df)

        for dt in self.params.stringTime_parameters:
            if dt[0] in self.rep_sents:
                times.append(dt)

        for ds in self.params.string_parameters:
            if ds[0] in self.rep_sents:
                strings.append(ds)

        self.params.boolean_parameters = bools
        self.params.integer_parameters = ints
        self.params.float_parameters = floats
        self.params.stringTime_parameters = times
        self.params.string_parameters = strings

        self.params.totalParams = self.params.boolean_parameters + self.params.integer_parameters + self.params.float_parameters + self.params.stringTime_parameters + self.params.string_parameters

        return self.params


    def make_pvs(self, result, parameter_values):
        bools = []
        ints = []
        floats = []
        times = []
        strings = []

        new_pvs = dict()
        new_pvs['space'] = parameter_values['space']
        new_pvs['defaults'] = parameter_values['defaults']

        haveValue_i = []
        for data in self.param_original.integer_parameters:
            if data[1] != data[2]:
                haveValue_i.append(data)

        haveValue_t = []
        for data2 in self.param_original.stringTime_parameters:
            if data2[1] != data2[2]:
                haveValue_t.append(data2)

        for i in range(len(result)):
            if result[i] == 1:             
                tune_list = self.groups[i]
                for ob in self.param_original.boolean_parameters:
                    if ob[0] in tune_list:
                        bools.append(ob)
                        new_pvs['space'][ob[0]] = [[ob[1]], 1]

                for oi in self.param_original.integer_parameters:
                    if oi[0] in tune_list:
                        ints.append(oi)
                        if oi[2] is not None:  # Parameter with OFF function
                            if oi[1] == oi[2]:  # Parameter with the same default and OFF values
                                default = self.similarity(haveValue_i, oi)
                            else:  # Parameter with different default and OFF values
                                default = oi[1]
                        else:  # Parameter without OFF function
                            default = oi[1]
                        new_pvs['space'][oi[0]] = [[default], 1]

                for of in self.param_original.float_parameters:
                    if of[0] in tune_list:
                        floats.append(of)
                        new_pvs['space'][of[0]] = [[of[1]], 1]                    

                for ot in self.param_original.stringTime_parameters:
                    if ot[0] in tune_list:
                        times.append(ot)
                        if ot[2] is not None:  # Parameter with OFF function
                            if ot[1] == ot[2]:  # Parameter with the same default and OFF values
                                default = self.similarity(haveValue_t, ot)
                            else:  # Parameter with different default and OFF values
                                default = ot[1]
                        else:  # Parameter without OFF function
                            default = ot[1]
                        new_pvs['space'][ot[0]] = [[default], 1]

                for os in self.param_original.string_parameters:
                    if os[0] in tune_list:
                        strings.append(os)
                        new_pvs['space'][os[0]] = [[os[1]], 1]

        self.param_backup.boolean_parameters = bools
        self.param_backup.integer_parameters = ints
        self.param_backup.float_parameters = floats
        self.param_backup.stringTime_parameters = times
        self.param_backup.string_parameters = strings

        self.param_backup.totalParams = self.param_backup.boolean_parameters + self.param_backup.integer_parameters + self.param_backup.float_parameters + self.param_backup.stringTime_parameters + self.param_backup.string_parameters

        return new_pvs, self.param_backup


    def similarity(self, haveValue, given_opt):
        similar_score = []
        for data in haveValue:
            # Split a sentence into words
            tokens1 = given_opt[0].split('-')
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