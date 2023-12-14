import random as rd
import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth


class PVSample:
    def __init__(self):
        self.avg_cov = []
        self.avg_count = []
        self.select_K = []
        self.sort_data = []

    # Use MeanShift Clustering 
    def clustering(self, data):
        value = []
        cover = []

        # Extract coverage and parameter values from data, respectively
        for val, cov in data:
            value.append(val)
            cover.append(cov)

        # Convert data to numpy array
        data = np.array(cover).reshape(-1, 1)

        # Optimal bandwidth estimation
        bandwidth = estimate_bandwidth(data, quantile=0.1, n_samples=len(data))

        # Perform MeanShift clustering
        ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
        ms.fit(data)
        labels = ms.labels_
        cluster_centers = ms.cluster_centers_

        k_optimal = len(np.unique(labels))

        # Check cluster assignment for each data point
        labels = ms.labels_
        min_n = [float("inf")] * k_optimal
        max_n = [0] * k_optimal

        # Find min/max of cluster using data
        for i in range(len(value)):
            if value[i] < min_n[labels[i]]:
                min_n[labels[i]] = value[i]
            if value[i] > max_n[labels[i]]:
                max_n[labels[i]] = value[i]

        sorted_data = sorted(zip(min_n, max_n))  # Sort min_x and max_x in ascending order
        sorted_data = [list(range) for range in sorted_data]  # Convert sorted results to list

        return sorted_data

    def calcMean(self, sorted_data, coverage):
        avg_cov, avg_count = [0] * len(sorted_data), [0] * len(sorted_data)

        # Check which section each data belongs to and calculate the average coverage of the data in that section.
        for n, cov in coverage:
            for j in range(len(sorted_data)):
                if n >= sorted_data[j][0] and n <= sorted_data[j][1]:
                    if avg_cov[j] == 0:
                        avg_cov[j] = cov
                        avg_count[j] += 1
                    else:
                        avg_cov[j] = (avg_cov[j] * avg_count[j] + cov) // (avg_count[j] + 1)
                        avg_count[j] += 1

        return avg_cov, avg_count

    # Select section to sample new value + extract value
    def sample_value(self, option, parameter_values, avg_cov, integer_option, float_option, sorted_data, covs, datas):

        self.average = int(sum(covs) / len(covs))
        self.iters = len(covs)
        # Derive the CDF (cumulative distribution function) of each section (only sections larger than the average of the entire coverage can be selected)
        portion = []
        goods = []

        for i in range(len(avg_cov)):
            if avg_cov[i] >= self.average:
                goods.append(avg_cov[i])
            else:
                goods.append(0)

        if goods == [0] * len(avg_cov):
            avg_cov2 = avg_cov
        else:
            avg_cov2 = goods

        if avg_cov2 == [0] * len(avg_cov):
            portion = [1 / len(avg_cov)] * len(avg_cov)
        else:
            for k in range(len(avg_cov2)):
                if k == 0:
                    portion.append(avg_cov2[k] / sum(avg_cov2))
                else:
                    portion.append(avg_cov2[k] / sum(avg_cov2) + portion[k - 1])

        # Randomly select sampling section
        p = rd.random()
        select_k = 0

        for l in range(len(portion)):
            if p >= portion[l]:
                select_k = l + 1

        # Randomly extract value within the section and set it to Space
        if option in float_option:
            new_value = rd.uniform(sorted_data[select_k][0], sorted_data[select_k][1])
            parameter_values['space'][option][0] = [new_value]
        else:
            new_value = rd.randint(int(sorted_data[select_k][0]), int(sorted_data[select_k][1]))
            if option in integer_option:
                parameter_values['space'][option][0] = [new_value]
            else:
                parameter_values['space'][option][0] = ["%ds" % (new_value)]

        return select_k, parameter_values, new_value

    def new_sampling(self, parameter_values, options_all, integer_option, float_option, datas, covs):
        k_ranges = []
        coverage = []

        for z1 in range(len(options_all)):
            for a in range(len(covs)):
                coverage.append([datas[z1][a], covs[a]])

        i = 0
        # Proceed with each parameter
        for z in range(len(options_all)):
            # Generate feature vectors by combining data and coverage values
            if options_all[z] == "-make-concrete-symbolic":
                continue
            cov_z = z
            coverage_val = coverage[len(datas[i]) * cov_z: len(datas[i]) * (cov_z + 1)]
            sorted_data = self.clustering(coverage_val)
            self.sort_data.append(sorted_data)
            rangesCov, rangesCount = self.calcMean(sorted_data, coverage_val)
            select_k, parameter_values, new_value = self.sample_value(options_all[z], parameter_values, rangesCov,
                                                                  integer_option, float_option, sorted_data, covs,
                                                                  datas)
            datas[z].append(new_value)
            self.avg_cov.append(rangesCov)
            self.avg_count.append(rangesCount)
            self.select_K.append(select_k)
            i += 1

        return parameter_values, datas

    def after_clustering(self, parameter_values, cover, b, option, integer_option, float_option, datas):
        self.avg_cov[b][self.select_K[b]] = (self.avg_cov[b][self.select_K[b]] * self.avg_count[b][
            self.select_K[b]] + cover) // (self.avg_count[b][self.select_K[b]] + 1)
        self.avg_count[b][self.select_K[b]] += 1
        self.average = (self.average * self.iters + cover) / (self.iters + 1)
        self.iters += 1

        # Derivating CDF (cumulative distribution function) for each section
        avg_cov = self.avg_cov[b]
        portion = []
        goods = []
        for i in range(len(self.avg_cov[b])):
            if avg_cov[i] >= self.average:
                goods.append(avg_cov[i])
            else:
                goods.append(0)

        if goods == [0] * len(self.avg_cov[b]):
            avg_cov2 = avg_cov
        else:
            avg_cov2 = goods

        for k in range(len(avg_cov2)):
            if k == 0:
                portion.append(avg_cov2[k] / sum(avg_cov2))
            else:
                portion.append(avg_cov2[k] / sum(avg_cov2) + portion[k - 1])

        # Randomly select sampling section
        p = rd.random()
        select_k = 0

        for l in range(len(portion)):
            if p > portion[l]:
                select_k = l + 1

        self.select_K[b] = select_k

        # Randomly extract value within the section and set it to Space
        new_value = rd.randint(int(self.sort_data[b][select_k][0]), int(self.sort_data[b][select_k][1]))
        if option in float_option:
            new_value = rd.uniform(self.sort_data[b][select_k][0], self.sort_data[b][select_k][1])
            parameter_values['space'][option][0] = [new_value]
        else:
            if option in integer_option:
                parameter_values['space'][option][0] = [new_value]
            else:
                parameter_values['space'][option][0] = ["%ds" % (new_value)]

        datas[b].append(new_value)

        return parameter_values, datas

    def cov_gen(self):
        result = set()
        a = rd.randint(1, 100)
        for _ in range(a):
            val = rd.randint(1, 5000)
            result.add(val)

        return result