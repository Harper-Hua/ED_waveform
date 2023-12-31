# 
# Adapted from: https://github.com/meta00/vital_sqi/tree/main/vital_sqi
#

import warnings

import numpy as np
import datetime as dt
import os
import json

import pandas as pd

OPERAND_MAPPING_DICT = {
    ">": 5,
    ">=": 4,
    "=": 3,
    "<=": 2,
    "<": 1
}


def check_valid_signal(x):
    """Check whether signal is valid, i.e. an array_like numeric, or raise errors.

    Parameters
    ----------
    x :
        array_like, array of signal

    Returns
    -------


    """
    if isinstance(x, dict) or isinstance(x, tuple):
        raise ValueError("Expected array_like input, instead found {"
                         "0}:".format(type(x)))
    if len(x) == 0:
        raise ValueError("Empty signal")
    types = []
    for i in range(len(x)):
        types.append(str(type(x[i])))
    type_unique = np.unique(np.array(types))
    if len(type_unique) != 1 and (type_unique[0].find("int") != -1 or
                                  type_unique[0].find("float") != -1):
        raise ValueError("Invalid signal: Expect numeric array, instead found "
                         "array with types {0}: ".format(type_unique))
    if type_unique[0].find("int") == -1 and type_unique[0].find("float") == -1:
        raise ValueError("Invalid signal: Expect numeric array, instead found "
                         "array with types {0}: ".format(type_unique))
    return True


def get_moving_average(q, w):
    q_padded = np.pad(q, (w // 2, w - 1 - w // 2), mode='edge')
    convole = np.convolve(q_padded, np.ones(w) / w, 'valid')
    return convole


def parse_rule(name, source):
    assert os.path.isfile(source) is True, 'Source file not found'
    with open(source) as json_file:
        all = json.load(json_file)
        try:
            sqi = all[name]
        except:
            raise Exception("SQI {0} not found".format(name))
        rule_def, boundaries, label_list = update_rule(sqi['def'],
                                                       is_update=False)
    return rule_def, \
           boundaries, \
           label_list


def update_rule(rule_def, threshold_list=[], is_update=True):
    if rule_def is None or is_update:
        all_rules = []
    else:
        all_rules = list(np.copy(rule_def))
    for threshold in threshold_list:
        all_rules.append(threshold)
    df = sort_rule(all_rules)
    df = decompose_operand(df.to_dict('records'))
    boundaries = np.sort(df["value"].unique())
    inteveral_label_list = get_inteveral_label_list(df, boundaries)
    value_label_list = get_value_label_list(df, boundaries, inteveral_label_list)

    label_list = []
    for i in range(len(value_label_list)):
        label_list.append(inteveral_label_list[i])
        label_list.append(value_label_list[i])
    label_list.append(inteveral_label_list[-1])
    return all_rules, boundaries, label_list


def sort_rule(rule_def):
    df = pd.DataFrame(rule_def)
    df["value"] = pd.to_numeric(df["value"])
    df['operand_order'] = df['op'].map(OPERAND_MAPPING_DICT)
    df.sort_values(by=['value', 'operand_order'],
                   inplace=True,
                   ascending=[True, True],
                   ignore_index=True)

    return df


def decompose_operand(rule_dict):
    df = pd.DataFrame(rule_dict)
    df["value"] = pd.to_numeric(df["value"])
    df['operand_order'] = df['op'].map(OPERAND_MAPPING_DICT)

    single_operand = df[(df["operand_order"] == 5)
                        | (df["operand_order"] == 3)
                        | (df["operand_order"] == 1)].to_dict('records')

    df_gte_operand = df[(df["operand_order"] == 4)]
    gte_g_operand = df_gte_operand.replace(">=", ">").to_dict('records')
    gte_e_operand = df_gte_operand.replace(">=", "=").to_dict('records')

    df_lte_operand = df[(df["operand_order"] == 2)]
    lte_l_operand = df_lte_operand.replace("<=", "<").to_dict('records')
    lte_e_operand = df_lte_operand.replace("<=", "=").to_dict('records')

    all_operand = single_operand + gte_g_operand + gte_e_operand + \
                  lte_l_operand + lte_e_operand

    df_all_operand = sort_rule(all_operand)

    return df_all_operand


def check_unique_pair(pair):
    assert len(pair) <= 1, "Duplicated decision at '" + str(pair["value"]) + " " + pair["op"] + "'"
    return True


def check_conflict(decision_lt, decision_gt):
    if len(decision_lt) == 0:
        label_lt = None
    else:
        label_lt = decision_lt["label"].values[0]
    if len(decision_gt) == 0:
        label_gt = None
    else:
        label_gt = decision_gt["label"].values[0]

    if label_lt == None:
        return label_gt
    if label_gt == None:
        return label_lt
    # Check conflict
    if not label_lt == label_gt:
        raise ValueError("Rules raise a conflict at x " + decision_lt.iloc[0]["op"] + " " +
                         str(decision_lt.iloc[0]["value"]) + " is " + decision_lt.iloc[0]["label"]
                         + ", but x " + decision_gt.iloc[0]["op"] + " " +
                         str(decision_gt.iloc[0]["value"]) + " is " + decision_gt.iloc[0]["label"])
    return label_gt


def get_decision(df, boundaries, idx):
    start_value = boundaries[idx]
    end_value = boundaries[idx + 1]
    decision_lt = \
        df[(df["value"] == end_value) &
           (df["op"] == "<")]
    check_unique_pair(decision_lt)
    decision_gt = \
        df[(df["value"] == start_value) &
           (df["op"] == ">")]
    check_unique_pair(decision_gt)

    decision = check_conflict(decision_lt, decision_gt)
    while (decision == None and idx <= (len(df) - 1)):
        decision = get_decision(df, boundaries, idx + 1)
    return decision


def get_inteveral_label_list(df, boundaries):
    inteveral_label_list = np.array([None] * (len(boundaries) + 1))

    assert df["op"].iloc[0] == "<", \
        "The rule is missing a decision from -inf to " + str(df["value"].iloc[0])
    inteveral_label_list[0] = df.iloc[0]["label"]
    for idx in range(len(boundaries) - 1):
        decision = get_decision(df, boundaries, idx)
        inteveral_label_list[idx + 1] = decision
    assert df["op"].iloc[-1] == ">", \
        "The rule is missing a decision from " + str(df["value"].iloc[-1]) + " to inf"
    inteveral_label_list[-1] = df.iloc[-1]["label"]
    return inteveral_label_list


def get_value_label_list(df, boundaries, interval_label_list):
    value_label_list = np.array([None] * (len(boundaries)))
    for idx in range(len(boundaries)):
        decision = df[(df["value"] == boundaries[idx]) &
                      (df["op"] == "=")]
        check_unique_pair(decision)
        if len(decision) == 0:
            value_label_list[idx] = interval_label_list[idx + 1]
        else:
            value_label_list[idx] = decision.iloc[0]["label"]
    return value_label_list
