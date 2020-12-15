# -*- coding: utf-8 -*-
import os
import time
from tqdm import tqdm
from apriori import load_data, save_rule


class Apriori_compress():
    # 遍历整个数据集生成c1候选集
    def create_c1(self, dataset):
        c1 = set()
        for i in dataset:
            for j in i:
                item = frozenset([j])
                c1.add(item)
        return c1

    # 连接步
    # 通过频繁项集Lk-1创建ck候选项集
    def create_ck(self, Lk_1, size):
        Ck = set()
        l = len(Lk_1)
        lk_list = list(Lk_1)
        for i in range(l):
            for j in range(i + 1, l):  # 两次遍历Lk-1，找出前n-1个元素相同的项
                l1 = list(lk_list[i])
                l2 = list(lk_list[j])
                l1.sort()
                l2.sort()
                if l1[0:size - 2] == l2[0:size - 2]:  # 只有最后一项不同时，生成下一候选项
                    Ck_item = lk_list[i] | lk_list[j]
                    if self.has_infrequent_subset(Ck_item, Lk_1):  # 检查该候选项的子集是否都在Lk-1中
                        Ck.add(Ck_item)
        return Ck

    # 检查候选项Ck_item的子集是否都在Lk-1中
    def has_infrequent_subset(self, Ck_item, Lk_1):
        for item in Ck_item:
            sub_Ck = Ck_item - frozenset([item])
            if sub_Ck not in Lk_1:
                return False
        return True

    # 事务压缩，上次不包含频繁项的事务这次不遍历
    # 通过候选项ck生成lk，并将各频繁项的支持度保存到support_data字典中
    def generate_lk_by_ck(self, data_set, ck, min_support, support_data, flag):
        item_count = {}  # 用于标记各候选项在数据集出现的次数
        Lk = set()
        index = -1
        for t in tqdm(data_set):
            index += 1
            if not flag[index]:
                continue  # 上次迭代时不包含频繁项，这次迭代选择跳过
            item_flag = False  # 标记该事务是否包含频繁项
            for item in ck:
                if item.issubset(t):
                    item_flag = True  # 该事务中含有频繁项
                    if item not in item_count:
                        item_count[item] = 1
                    else:
                        item_count[item] += 1
            # 不包含频繁项，flag相应位置置为False，下次遍历时跳过
            if not item_flag:
                flag[index] = False
        for item in item_count:  # 将满足支持度的候选项添加到频繁项集中
            if item_count[item] >= min_support:
                Lk.add(item)
                support_data[item] = item_count[item]
        return Lk

    # 用于生成所有频繁项集的主函数，k为最大频繁项的大小
    def generate_L(self, data_set, min_support):
        support_data = {}  # 用于保存各频繁项的支持度
        flag = [True for _ in range(len(data_set))]  # 用于事务压缩的标记数组
        C1 = self.create_c1(data_set)  # 生成C1
        L1 = self.generate_lk_by_ck(data_set, C1, min_support, support_data, flag)  # 根据C1生成L1
        Lk_1 = L1.copy()  # 初始时Lk-1=L1
        L = [Lk_1]
        i = 2
        while True:
            Ci = self.create_ck(Lk_1, i)  # 根据Lk-1生成Ck
            Li = self.generate_lk_by_ck(data_set, Ci, min_support, support_data, flag)  # 根据Ck生成Lk
            if len(Li) == 0:
                break
            Lk_1 = Li.copy()  # 下次迭代时Lk-1=Lk
            L.append(Lk_1)
            i += 1
        for i in range(len(L)):
            print("frequent item {}：{}".format(i + 1, len(L[i])))
        return L, support_data

    def generate_R(self, dataset, min_support, min_confidence):
        L, support_data = self.generate_L(dataset, min_support)  # 根据频繁项集和支持度生成关联规则
        rule_list = []  # 保存满足置信度的规则
        sub_set_list = []  # 该数组保存检查过的频繁项
        for i in range(0, len(L)):
            for freq_set in L[i]:  # 遍历Lk
                for sub_set in sub_set_list:  # sub_set_list中保存的是L1到Lk-1
                    if sub_set.issubset(freq_set):  # 检查sub_set是否是freq_set的子集
                        # 检查置信度是否满足要求，是则添加到规则
                        conf = support_data[freq_set] / support_data[freq_set - sub_set]
                        big_rule = (freq_set - sub_set, sub_set, conf)
                        if conf >= min_confidence and big_rule not in rule_list:
                            rule_list.append(big_rule)
                sub_set_list.append(freq_set)
        rule_list = sorted(rule_list, key=lambda x: (x[2]), reverse=True)
        return rule_list


if __name__ == "__main__":

    filename="处方数据.xls"
    # filename = "groceries.csv"

    current_path = os.getcwd()
    if not os.path.exists(current_path + "/output"):
        os.mkdir("output")
    path = current_path + "/dataset/" + filename
    save_path = current_path + "/output/" + filename.split(".")[0] + "_apriori_compress.txt"

    data = load_data(path)
    apriori_com = Apriori_compress()
    # groceries数据集 该参数下频繁项最大为5
    # rule_list = apriori_com.generate_R(data, min_support=15, min_confidence=0.7)
    # 处方数据数据集 该参数下频繁项最大为8
    rule_list = apriori_com.generate_R(data, min_support=600, min_confidence=0.9)
    save_rule(rule_list, save_path)
