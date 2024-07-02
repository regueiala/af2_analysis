#!/usr/bin/env python3
# coding: utf-8

import os
import numpy as np
import pytest

import af2_analysis
from af2_analysis import analysis
from .data_files import TEST_FILE_PATH

def test_cf_1_5_5_relax():
    data_path = os.path.join(TEST_FILE_PATH, "beta_amyloid_dimer_cf_1.5.5")

    my_data = af2_analysis.Data(data_path)

    assert my_data.format == "colabfold_1.5"
    assert len(my_data.df) == 40
    print(my_data.df.columns)
    assert (
        my_data.df.columns
        == np.array(
            [
                "query",
                "seed",
                "model",
                "weight",
                "recycle",
                "pLDDT",
                "pTM",
                "ipTM",
                "ranking_confidence",
                "pdb",
                "relaxed_pdb",
                "json",
            ]
        )
    ).all()

    query = my_data.df.iloc[0]["query"]

    assert my_data.chain_length[query] == [42, 42]
    assert my_data.chains[query] == ["A", "B"]

    # There should be only 5 relaxed structures

    relaxed_num = sum(my_data.df["relaxed_pdb"].notna())

    assert relaxed_num == 5
    assert list(my_data.df["recycle"]) == [
        9,
        16,
        3,
        5,
        5,
        14,
        15,
        15,
        48,
        12,
        7,
        14,
        7,
        8,
        9,
        4,
        18,
        6,
        10,
        8,
        11,
        14,
        7,
        11,
        9,
        11,
        7,
        7,
        19,
        9,
        30,
        7,
        5,
        9,
        7,
        12,
        7,
        6,
        6,
        6,
    ]

    assert list(my_data.df["ipTM"]) == [
        0.0812,
        0.0685,
        0.161,
        0.158,
        0.541,
        0.117,
        0.0698,
        0.239,
        0.0648,
        0.331,
        0.0789,
        0.0815,
        0.145,
        0.306,
        0.604,
        0.0997,
        0.0662,
        0.143,
        0.219,
        0.589,
        0.0794,
        0.0684,
        0.15,
        0.299,
        0.559,
        0.0797,
        0.0662,
        0.147,
        0.0609,
        0.318,
        0.0964,
        0.0683,
        0.151,
        0.274,
        0.584,
        0.0776,
        0.0693,
        0.14,
        0.199,
        0.598,
    ]

def test_af3_webserver():
    data_path = os.path.join(TEST_FILE_PATH, "fold_2024_07_01_12_14_prot_dna_zn")

    my_data = af2_analysis.Data(data_path)

    assert my_data.format == "AF3_webserver"


    analysis.pdockq(my_data)

    expected_pdockq = [0.2756, 0.2621, 0.2755, 0.2754, 0.2758]

    assert 2.2 == pytest.approx(2.3, 0.1)
    #print([round(i, 4) for i in my_data.df["pdockq"]])
    precision = 0.001
    assert np.all(
        [
            my_data.df.iloc[i]["pdockq"] == pytest.approx(expected_pdockq[i], precision)
            for i in range(len(my_data.df))
        ]
    )

    analysis.pdockq2(my_data)
    # print([round(i, 4) for i in my_data.df["pdockq2_A"]])
    expected_pdockq2 = [0.9148, 0.9187, 0.9151, 0.913, 0.9154]
    assert np.all(
        [
            my_data.df.iloc[i]["pdockq2_A"] == pytest.approx(expected_pdockq2[i], precision)
            for i in range(len(my_data.df))
        ]
    )
    # print([round(i, 4) for i in my_data.df["pdockq2_D"]])
    expected_pdockq2 = [0.8972, 0.8925, 0.8884, 0.889, 0.8785]
    assert np.all(
        [
            my_data.df.iloc[i]["pdockq2_D"] == pytest.approx(expected_pdockq2[i], precision)
            for i in range(len(my_data.df))
        ]
    )

    analysis.LIS_matrix(my_data)
    expected_LIS_0 = [[0.83139, 0.8075 , 0.85381, 0.85251, 0.85559, 0.85551],
                      [0.82717, 0.93666, 0.7975 , 0.83166, 0.84568, 0.83962],
                      [0.80911, 0.745  , 0.93666, 0.82333, 0.83409, 0.83060],
                      [0.84268, 0.84166, 0.84   , 0.93666, 0.865  , 0.85886],
                      [0.83427, 0.84507, 0.83712, 0.84522, 0.87633, 0.87050],
                      [0.81519, 0.79833, 0.83053, 0.82   , 0.85831, 0.86331],]

    np.testing.assert_allclose(
        np.array(my_data.df["LIS"][0]),
        np.array(expected_LIS_0),
        atol=precision)

    analysis.inter_chain_pae(my_data)

    expected_PAE_A_B = [2.8373, 2.6611, 2.8013, 2.8286, 2.7292]
    # print([round(i, 4) for i in my_data.df["PAE_A_B"]])
    assert np.all(
        [
            my_data.df.iloc[i]["PAE_A_B"]
            == pytest.approx(expected_PAE_A_B[i], precision)
            for i in range(len(my_data.df))
        ]
    )

    expected_PAE_A_E = [2.7772, 2.6177, 2.8398, 2.8672, 2.7849]
    # print([round(i, 4) for i in my_data.df["PAE_A_E"]])
    assert np.all(
        [
            my_data.df.iloc[i]["PAE_A_E"]
            == pytest.approx(expected_PAE_A_E[i], precision)
            for i in range(len(my_data.df))
        ]
    )

