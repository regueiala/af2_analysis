#!/usr/bin/env python3
# coding: utf-8

import os
import numpy as np
import pandas as pd
import json
import pdb_numpy
import seaborn as sns
import matplotlib.pyplot as plt
from cmcrameri import cm
from tqdm.auto import tqdm
import json

import ipywidgets as widgets

from .format import colabfold_1_5, af3_webserver, afpulldown, default
from . import sequence, plot
from .analysis import compute_LIS_matrix

class Data:
    """Data class

    Parameters
    ----------
    dir : str
        Path to the directory containing the `log.txt` file.
    format : str
        Format of the data.
    df : pandas.DataFrame
        Dataframe containing the information extracted from the `log.txt` file.
    chains : dict
        Dictionary containing the chains of each query.
    chain_length : dict
        Dictionary containing the length of each chain of each query.
    
    Methods
    -------
    read_directory(directory, keep_recycles=False)
        Read a directory.
    export_csv(path)
        Export the dataframe to a csv file.
    import_csv(path)
        Import a csv file to the dataframe.
    add_json()
        Add json files to the dataframe.
    extract_json()
        Extract json files to the dataframe.
    add_pdb()
        Add pdb files to the dataframe.
    add_fasta(csv)
        Add fasta sequence to the dataframe.
    keep_last_recycle()
        Keep only the last recycle for each query.
    plot_maxscore_as_col(score, col, hue='query')
        Plot the maxscore as a function of a column.
    plot_pae(index, cmap=cm.vik)
        Plot the PAE matrix.
    plot_plddt(index_list)
        Plot the pLDDT.
    show_3d(index)
        Show the 3D structure.
    compute_pdockq()
        Compute pdockq from the pdb file.
    compute_mpdockq()
        Compute mpdockq from the pdb file.
    compute_pdockq2()
        Compute pdockq2 from the pdb file.
    plot_msa(filter_qid=0.15, filter_cov=0.4)
        Plot the msa from the a3m file.
    show_plot_info()
        Show the plot info.
    extract_inter_chain_pae(fun=np.mean)
        Read the PAE matrix and extract the average inter chain PAE.
    
    """

    def __init__(self, directory=None, csv=None):
        """ """

        if directory is not None:
            self.read_directory(directory)
        elif csv is not None:
            self.format = 'csv'
            self.import_csv(csv)

    def read_directory(self, directory, keep_recycles=False):
        """Read a directory.

        If the directory contains a `log.txt` file, the format is set to `colabfold_1.5`.

        Parameters
        ----------
        directory : str
            Path to the directory containing the `log.txt` file.

        Returns
        -------
        None
        """
        self.dir = directory

        if os.path.isfile(os.path.join(directory, "log.txt")):
            self.format = "colabfold_1.5"
            self.df = colabfold_1_5.read_log(directory, keep_recycles)
            self.add_pdb()
            self.add_json()
        elif os.path.isfile(os.path.join(directory, "terms_of_use.md")):
            self.format = "AF3_webserver"
            self.df = af3_webserver.read_dir(directory)
        elif os.path.isfile(os.path.join(directory, 'ranking_debug.json')):
            self.format = "AlphaPulldown"
            self.df = afpulldown.read_dir(directory)
        else:
            self.format = "default"
            self.df = default.read_dir(directory)
            self.add_json()
            # self.extract_json()
        
        self.set_chain_length()

    def set_chain_length(self):
        """ Find chain information from the dataframe.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        self.chains = {}
        self.chain_length = {}
        for querie in self.df["query"].unique():
            # print(querie, self.df[self.df['query'] == querie])
            first_model = pdb_numpy.Coor(
                self.df[self.df["query"] == querie].iloc[0]["pdb"]
            )
            self.chains[querie] = list(np.unique(first_model.models[0].chain))
            self.chain_length[querie] = [
                len(
                    np.unique(
                        first_model.models[0].uniq_resid[
                            first_model.models[0].chain == chain
                        ]
                    )
                )
                for chain in self.chains[querie]
            ]

    def export_csv(self, path):
        """Export the dataframe to a csv file.

        Parameters
        ----------
        path : str
            Path to the csv file.

        Returns
        -------
        None
        """

        self.df.to_csv(path, index=False)

    def import_csv(self, path):
        """Import a csv file to the dataframe.

        Parameters
        ----------
        path : str
            Path to the csv file.

        Returns
        -------
        None
        """

        self.df = pd.read_csv(path)
        self.dir = os.path.dirname(self.df['pdb'][0])

        self.chains = {}
        self.chain_length = {}
        for querie in self.df["query"].unique():
            # print(querie, self.df[self.df['query'] == querie])
            first_model = pdb_numpy.Coor(
                self.df[self.df["query"] == querie].iloc[0]["pdb"]
            )
            self.chains[querie] = list(np.unique(first_model.models[0].chain))
            self.chain_length[querie] = [
                len(
                    np.unique(
                        first_model.models[0].uniq_resid[
                            first_model.models[0].chain == chain
                        ]
                    )
                )
                for chain in self.chains[querie]
            ]

    def add_json(self):
        """Add json files to the dataframe.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        if self.format == "colabfold_1.5":
            colabfold_1_5.add_json(self.df, self.dir)
        if self.format == "default":
            default.add_json(self.df, self.dir)

    def extract_json(self):
        """Extract json files to the dataframe.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        index_list = []
        json_list = []

        for i, row in self.df.iterrows():
            if row.json is not None:
                index_list.append(i)

                with open(row.json, "r") as f:
                    data = json.load(f)

                json_list.append(data)

        new_column = {}
        for keys in json_list[0].keys():
            new_column[keys] = []
        for data in json_list:
            for keys in data.keys():
                new_column[keys].append(data[keys])

        for keys in new_column.keys():
            self.df[keys] = None
            new_col = pd.Series(new_column[keys], index=index_list)
            self.df[keys].iloc[index_list] = new_col

    def add_pdb(self):
        """Add pdb files to the dataframe.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        if self.format == "colabfold_1.5":
            colabfold_1_5.add_pdb(self.df, self.dir)

    def add_fasta(self, csv):
        """Add fasta sequence to the dataframe.

        Parameters
        ----------
        csv : str
            Path to the csv file containing the fasta sequence.

        Returns
        -------
        None
        """

        if self.format == "colabfold_1.5":
            colabfold_1_5.add_fasta(self.df, csv)

    def keep_last_recycle(self):
        """Keep only the last recycle for each query."""

        idx = (
            self.df.groupby(["query", "seed", "model", "weight"])["recycle"].transform(
                "max"
            )
            == self.df["recycle"]
        )
        self.df = self.df[idx]

    def plot_maxscore_as_col(self, score, col, hue="query"):
        col_list = self.df[col].unique()
        query_list = self.df[hue].unique()
        # print(col_list)
        # print(query_list)

        out_list = []

        for query in query_list:
            # print(query)
            query_pd = self.df[self.df[hue] == query]

            for column in col_list:
                # print(column)
                # ~print()

                col_pd = query_pd[query_pd[col] <= column]
                # print(col_pd[score])
                # print(column, len(col_pd))
                # print(col, col_pd.columns)

                if len(col_pd) > 0:
                    out_list.append(
                        {hue: query, score: col_pd[score].max(), col: column}
                    )
                    # print(column, len(col_pd), col_pd[score].max())

        max_pd = pd.DataFrame(out_list)

        fig, ax = plt.subplots()
        sns.lineplot(max_pd, x=col, y=score, hue=hue)

        return (fig, ax)


    def plot_pae(self, index, cmap=cm.vik):

        row = self.df.iloc[index]
        pae_array = get_pae(row['json'])


        fig, ax = plt.subplots()
        res_max = sum(self.chain_length[row["query"]])

        img = ax.imshow(
            pae_array,
            cmap=cmap,
            vmin=0.0,
            vmax=30.0,
        )

        plt.hlines(
            np.cumsum(self.chain_length[row["query"]][:-1]) - 0.5,
            xmin=-0.5,
            xmax=res_max,
            colors="black",
        )

        plt.vlines(
            np.cumsum(self.chain_length[row["query"]][:-1])- 0.5,
            ymin=-0.5,
            ymax=res_max,
            colors="black",
        )

        plt.xlim(-0.5, res_max-0.5)
        plt.ylim(res_max-0.5, -0.5)
        chain_pos = []
        len_sum = 0
        for longueur in self.chain_length[row["query"]]:
            chain_pos.append(len_sum + longueur / 2)
            len_sum += longueur

        ax.set_yticks(chain_pos)
        ax.set_yticklabels(self.chains[row["query"]])
        cbar = plt.colorbar(img)
        cbar.set_label("Predicted Aligned Error (Å)", rotation=270)
        cbar.ax.get_yaxis().labelpad = 15

        return (fig, ax)

    def get_plddt(self, index):

        row = self.df.iloc[index]

        if self.format in ["AF3_webserver", 'csv', "AlphaPulldown"]:
            model = pdb_numpy.Coor(row['pdb'])
            plddt_array = model.models[0].beta[model.models[0].name == 'CA']
            return plddt_array


        if row["json"] is None:
            return (None, None)

        with open(row["json"]) as f:
            local_json = json.load(f)

        if "plddt" in local_json:
            plddt_array = np.array(local_json["plddt"])
        else:
            return (None, None)

        return plddt_array

    def plot_plddt(self, index_list):
        fig, ax = plt.subplots()

        for index in index_list:
            plddt_array = self.get_plddt(index)

            plt.plot(plddt_array)

        plt.vlines(
            np.cumsum(self.chain_length[self.df.iloc[index_list[0]]["query"]][:-1]),
            ymin=0,
            ymax=100.0,
            colors="black",
        )
        plt.ylim(0, 100)
        plt.xlim(0, sum(self.chain_length[self.df.iloc[index_list[0]]["query"]]))
        plt.xlabel("Residue")
        plt.ylabel("predicted LDDT")

        return (fig, ax)

    def show_3d(self, index):
        row = self.df.iloc[index]

        if row["pdb"] is None:
            return (None, None)

        import nglview as nv

        # Bug with show_file
        # view = nv.show_file(row['pdb'])
        view = nv.show_structure_file(row["pdb"])
        # view.add_component(ref_coor[0])
        # view.clear_representations(1)
        # view[1].add_cartoon(selection="protein", color='blue')
        # view[1].add_licorice(selection=":A", color='blue')
        # view[0].add_licorice(selection=":A")
        return view

    def compute_pdockq(self):
        """
        Compute the pdockq from the pdb file.
        """

        from pdb_numpy.analysis import compute_pdockQ

        pdockq_list = []

        for pdb in tqdm(self.df["pdb"], total=len(self.df["pdb"])):
            if pdb:
                model = pdb_numpy.Coor(pdb)
                pdockq_list += compute_pdockQ(model)
            else:
                pdockq_list.append(None)

        self.df["pdockq"] = pdockq_list


    def compute_mpdockq(self):
        """
        Compute mpdockq from the pdb file.

        """

        from pdb_numpy.analysis import compute_pdockQ

        pdockq_list = []

        for pdb in tqdm(self.df["pdb"], total=len(self.df["pdb"])):
            if (pdb is not None and pdb is not np.nan):
                model = pdb_numpy.Coor(pdb)
                pdockq_list += compute_pdockQ(
                    model,
                    cutoff=8.0,
                    L=0.728,
                    x0=309.375,
                    k=0.098,
                    b=0.262)
            else:
                pdockq_list.append(None)

        self.df.loc[:, "mpdockq"] = pdockq_list

    def compute_pdockq2(self):
        r"""
        Compute pdockq2 from the pdb file [1]_.

        .. math::
            pDockQ_2 = \frac{L}{1 + exp [-k*(X_i-X_0)]} + b

        with

        .. math::
            X_i = \langle \frac{1}{1+(\frac{PAE_{int}}{d_0})^2} \rangle - \langle pLDDT \rangle_{int}

        References:
        
        .. [1] : https://academic.oup.com/bioinformatics/article/39/7/btad424/7219714
        """

        from pdb_numpy.analysis import compute_pdockQ2

        pdockq_list = []

        max_chain_num = 0
        for query in self.chains:
            chain_num = len(self.chains[query])
            if chain_num > max_chain_num:
                max_chain_num = chain_num

        for i in range(max_chain_num):
            pdockq_list.append([])

        for pdb, json_path in tqdm(
            zip(self.df["pdb"], self.df["json"]), total=len(self.df["pdb"])
        ):
            if (pdb is not None and pdb is not np.nan and json_path is not None and json_path is not np.nan):
                model = pdb_numpy.Coor(pdb)
                # with open(json_path) as f:
                #     local_json = json.load(f)
                # pae_array = np.array(local_json["pae"]) 
                pae_array = get_pae(json_path)

                pdockq2 = compute_pdockQ2(model, pae_array)

                for i in range(max_chain_num):
                    if i < len(pdockq2):
                        pdockq_list[i].append(pdockq2[i][0])
                    else:
                        pdockq_list[i].append(None)

            else:
                for i in range(max_chain_num):
                    pdockq_list[i].append(None)

        # print(pdockq_list)
        for i in range(max_chain_num):
            self.df.loc[:, f"pdockq2_{chr(65+i)}"] = pdockq_list[i]


    def compute_LIS_matrix(self, pae_cutoff=12.0):
        """
        Compute the LIS score as define in [2]_.

        Implementation was inspired from implementation in:

        .. [2] https://github.com/flyark/AFM-LIS
        """
        LIS_matrix_list = []

        max_chain_num = 0
        for query in self.chains:
            chain_num = len(self.chains[query])
            if chain_num > max_chain_num:
                max_chain_num = chain_num

        for pdb, json_path in tqdm(
            zip(self.df["pdb"], self.df["json"]), total=len(self.df["pdb"])
        ):
            if (pdb is not None and pdb is not np.nan and json_path is not None and json_path is not np.nan):
                model = pdb_numpy.Coor(pdb)
                pae_array = get_pae(json_path)
                LIS_matrix = compute_LIS_matrix(model, pae_array, pae_cutoff)
                LIS_matrix_list.append(LIS_matrix)
            else:
                LIS_matrix_list.append(None)

        self.df.loc[:, "LIS"] = LIS_matrix_list

    def compute_piTM(self):
        r"""Compute the piTM score as define in [3]_.

        .. math::
            piTM = \max_{i \in \mathcal{I}} \frac{1}{I} \sum_{j \in \mathcal{I}}  \frac{1}{1 + [\langle e_{ij} \rangle / d_0 (I)]^2}

        with:

        .. math::
            d_0(I) = \begin{cases} 1.25 \sqrt[3]{I -15} -1.8\text{,} & \text{if } I \geq 22 \\ 0.02 I \text{,} & \text{if } I < 22  \end{cases}
        

        Implementation was inspired from `predicted_tm_score_v1()` in https://github.com/FreshAirTonight/af2complex/blob/main/src/alphafold/common/confidence.py

        References
        ----------
        .. [3] Mu Gao, Davi Nakajima An, Jerry M. Parks & Jeffrey Skolnick. 
            AF2Complex predicts direct physical interactions in multimeric proteins with deep learning
            *Nature Communications*. volume 13, Article number: 1744 (2022).
            https://www.nature.com/articles/s41467-022-29394-2
        
        .. warning::
            IT IS NOT WORKING !!
        """

        from pdb_numpy.analysis import compute_piTM

        piTM_chain_list = []
        piTM_list = []

        max_chain_num = 0
        for query in self.chains:
            chain_num = len(self.chains[query])
            if chain_num > max_chain_num:
                max_chain_num = chain_num

        for i in range(max_chain_num):
            piTM_chain_list.append([])

        for pdb, json_path in tqdm(
            zip(self.df["pdb"], self.df["json"]), total=len(self.df["pdb"])
        ):
            # print(pdb, json_path)
            if (pdb is not None and pdb is not np.nan and json_path is not None and json_path is not np.nan):
                model = pdb_numpy.Coor(pdb)
                with open(json_path) as f:
                    local_json = json.load(f)
                pae_array = np.array(local_json["pae"])

                piTM, piTM_chain = compute_piTM(model, pae_array)
                # print(piTM, piTM_chain)

                piTM_list.append(piTM[0])

                for i in range(max_chain_num):
                    # print(i, len(piTM_chain))
                    if i < len(piTM_chain):
                        piTM_chain_list[i].append(piTM_chain[i][0])
                    else:
                        piTM_chain_list[i].append(None)

            else:
                piTM_list.append(None)
                for i in range(max_chain_num):
                    piTM_chain_list[i].append(None)

        # print(piTM_chain_list)
        self.df.loc[:, "piTM"] = piTM_list
        for i in range(max_chain_num):
            self.df.loc[:, f"piTM_{chr(65+i)}"] = piTM_chain_list[i]


    def plot_msa(self, filter_qid=0.15, filter_cov=0.4):
        """
        Plot the msa from the a3m file.

        Parameters
        ----------
        filter_qid : float
            Minimal sequence identity to keep a sequence.
        filter_cov : float
            Minimal coverage to keep a sequence.

        Returns
        -------
        None

        ..Warning only tested with colabfold 1.5
        """

        raw_list = os.listdir(self.dir)
        file_list = []
        for file in raw_list:
            if file.endswith(".a3m"):
                file_list.append(file)

        for a3m_file in file_list:
            print(f"Reading MSA file:{a3m_file}")
            querie = a3m_file.split("/")[-1].split(".")[0]

            a3m_lines = open(os.path.join(self.dir, a3m_file), "r").readlines()[1:]
            seqs, mtx, nams = sequence.parse_a3m(
                a3m_lines=a3m_lines,
                filter_qid=filter_qid,
                filter_cov=filter_cov)
            print(f"- Keeping {len(seqs):6} sequences for plotting.")
            feature_dict = {}
            feature_dict["msa"] = sequence.convert_aa_msa(seqs)
            feature_dict["num_alignments"] = len(seqs)

            if len(seqs) == sum(self.chain_length[querie]):
                feature_dict["asym_id"] = []
                for i, chain_len in enumerate(self.chain_length[querie]):
                    feature_dict["asym_id"] += [i + 1.] * chain_len
                feature_dict["asym_id"] = np.array(feature_dict["asym_id"])

            fig = plot.plot_msa_v2(feature_dict)
            plt.show()


    def count_msa_seq(self):
        """
        Count for each chain the number of sequences in the MSA.

        Parameters
        ----------


        Returns
        -------
        None

        ..Warning only tested with colabfold 1.5
        """

        raw_list = os.listdir(self.dir)
        file_list = []
        for file in raw_list:
            if file.endswith(".a3m"):
                file_list.append(file)

        alignement_len = {}

        for a3m_file in file_list:
            print(f"Reading MSA file:{a3m_file}")
            querie = a3m_file.split("/")[-1].split(".")[0]

            a3m_lines = open(os.path.join(self.dir, a3m_file), "r").readlines()[1:]
            seqs, mtx, nams = sequence.parse_a3m(
                a3m_lines=a3m_lines,
                filter_qid=0,
                filter_cov=0)
            feature_dict = {}
            feature_dict["msa"] = sequence.convert_aa_msa(seqs)
            feature_dict["num_alignments"] = len(seqs)

            seq_dict = {}
            for chain in self.chains[querie]: seq_dict[chain] = 0
            

            chain_len_list = self.chain_length[querie]
            chain_list = self.chains[querie]
            seq_len = sum(chain_len_list)

            # Treat the cases of homomers
            # I compare the length of each sequence with the other ones
            # It is wrong and should be FIXED
            # The original sequence should be retrieved from eg. the pdb file
            if len(seqs[0]) != seq_len:
                new_chain_len = []
                new_chain_list = []
                for i, seq_len in enumerate(chain_len_list):
                    if seq_len not in chain_len_list[:i]:
                        new_chain_len.append(seq_len)
                        new_chain_list.append(chain_list[i])

                chain_len_list = new_chain_len
                chain_list = new_chain_list
                seq_len = sum(chain_len_list)

            assert len(seqs[0]) == seq_len, f"len(seqs[0])={len(seqs[0])} != seq_len={seq_len}"

            for seq in seqs:
                start = 0
                for i, num in enumerate(chain_len_list):
                    gap_num = seq[start:start+num].count("-")
                    if gap_num < num:
                        seq_dict[chain_list[i]] += 1
                    start += num

            alignement_len[querie] = seq_dict # [seq_dict[chain] for chain in self.chains[querie]]
        return alignement_len

    def show_plot_info(self, cmap=cm.vik):
        """
        Need to solve the issue with:

        ```
        %matplotlib ipympl
        ```

        plots don´t update when changing the model number.

        """

        model_widget = widgets.IntSlider(
            value=1,
            min=1,
            max=len(self.df),
            step=1,
            description='model:',
            disabled=False,
        )
        display(model_widget)
        
        
        def show_model(rank_num):

            fig, (ax_plddt, ax_pae) = plt.subplots(1, 2, figsize=(10, 4))
            plddt_array = self.get_plddt(rank_num-1)
            plddt_plot, = ax_plddt.plot(plddt_array)
            query = self.df.iloc[model_widget.value-1]['query']
            json_file = self.df.iloc[model_widget.value-1]['json']
            ax_plddt.vlines(
                np.cumsum(self.chain_length[query][:-1]),
                ymin=0,
                ymax=100.0,
                colors="black",
            )
            ax_plddt.set_ylim(0, 100)
            res_max = sum(self.chain_length[query])
            ax_plddt.set_xlim(0, res_max)
            ax_plddt.set_xlabel("Residue")
            ax_plddt.set_ylabel("predicted LDDT")

            pae_array = get_pae(json_file)
            ax_pae.imshow(
                pae_array,
                cmap=cmap,
                vmin=0.0,
                vmax=30.0,
            )
            ax_pae.vlines(
                np.cumsum(self.chain_length[query][:-1]),
                ymin=-0.5,
                ymax=res_max,
                colors="yellow",
            )
            ax_pae.hlines(
                np.cumsum(self.chain_length[query][:-1]),
                xmin=-0.5,
                xmax=res_max,
                colors="yellow",
            )
            ax_pae.set_xlim(-0.5, res_max-0.5)
            ax_pae.set_ylim(res_max-0.5, -0.5)
            chain_pos = []
            len_sum = 0
            for longueur in self.chain_length[query]:
                chain_pos.append(len_sum + longueur / 2)
                len_sum += longueur
            ax_pae.set_yticks(chain_pos)
            ax_pae.set_yticklabels(self.chains[query])
            plt.show(fig)

        
        output = widgets.Output(layout={'width': '95%'})
        display(output)

        with output:
            show_model(model_widget.value)
            #logger.info(results['metric'][0][rank_num - 1]['print_line'])

        def on_value_change(change):
            output.clear_output()
            with output:
                show_model(model_widget.value)

        model_widget.observe(on_value_change, names='value')


    def show_plot(self, cmap=cm.vik):
        """
        Use with
        ```
        %matplotlib widget
        ```
        """

        
        model_widget = widgets.IntSlider(
            value=1,
            min=1,
            max=len(self.df),
            step=1,
            description='model:',
            disabled=False,
        )
        display(model_widget)
        
        
        print("YO")
        rank_num = 1

        fig, (ax_plddt, ax_pae) = plt.subplots(1, 2, figsize=(10, 4))
        plddt_array = self.get_plddt(rank_num-1)
        plddt_plot, = ax_plddt.plot(plddt_array)
        query = self.df.iloc[model_widget.value-1]['query']
        json_file = self.df.iloc[model_widget.value-1]['json']
        vline_plot = ax_plddt.vlines(
            np.cumsum(self.chain_length[query][:-1]),
            ymin=0,
            ymax=100.0,
            colors="black",
        )
        ax_plddt.set_ylim(0, 100)
        res_max = sum(self.chain_length[query])
        ax_plddt.set_xlim(0, res_max)
        ax_plddt.set_xlabel("Residue")
        ax_plddt.set_ylabel("predicted LDDT")

        pae_array = get_pae(json_file)
        pae_plot = ax_pae.imshow(
            pae_array,
            cmap=cmap,
            vmin=0.0,
            vmax=30.0,
        )
        vline_pae = ax_pae.vlines(
            np.cumsum(self.chain_length[query][:-1]),
            ymin=-0.5,
            ymax=res_max,
            colors="yellow",
        )
        hline_pae = ax_pae.hlines(
            np.cumsum(self.chain_length[query][:-1]),
            xmin=-0.5,
            xmax=res_max,
            colors="yellow",
        )
        ax_pae.set_xlim(-0.5, res_max-0.5)
        ax_pae.set_ylim(res_max-0.5, -0.5)
        chain_pos = []
        len_sum = 0
        for longueur in self.chain_length[query]:
            chain_pos.append(len_sum + longueur / 2)
            len_sum += longueur
        ax_pae.set_yticks(chain_pos)
        ax_pae.set_yticklabels(self.chains[query])
        plt.show(fig)

        def update_model(change):
            rank_num = model_widget.value
            #print("Update")
            plddt_array = self.get_plddt(rank_num-1)
            res_num = len(plddt_array)
            plddt_plot.set_data(range(res_num), plddt_array)
            ax_plddt.set_xlim(0, len(plddt_array))

            query = self.df.iloc[rank_num-1]['query']
            vline_plot.set_segments(
                [np.array([[x, 0], [x, 100]]) for x in np.cumsum(self.chain_length[query][:-1])]
            )
            #ax_plddt.set_title(self.chain_length[query][:-1])
            
            json_file = self.df.iloc[rank_num-1]['json']
            pae_array = get_pae(json_file)
            pae_plot.set_extent((0, res_num,0, res_num))
            pae_plot.set_data(pae_array)
            ax_pae.set_xlim(0, res_num)
            ax_pae.set_ylim(0, res_num)

            vline_pae.set_segments(
                [np.array([[x, -0.5], [x, res_num]]) for x in np.cumsum(self.chain_length[query][:-1])]
            )
            hline_pae.set_segments(
                [np.array([[-0.5, res_num-x], [res_num, res_num-x]]) for x in np.cumsum(self.chain_length[query][:-1])]
            )
            chain_pos = []
            len_sum = 0
            for longueur in self.chain_length[query]:
                chain_pos.append(res_num - (len_sum + longueur / 2))
                len_sum += longueur
            ax_pae.set_yticks(chain_pos)
            ax_pae.set_yticklabels(self.chains[query])
            fig.canvas.draw()
        
        model_widget.observe(update_model, names='value')


    def extract_inter_chain_pae(self, fun=np.mean):
        """ Read the PAE matrix and extract the average inter chain PAE.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        pae_list = []
        
        for query, json_path in tqdm(
                        zip(self.df["query"], self.df["json"]), total=len(self.df["json"])
            ):
            if (json_path is not None and json_path is not np.nan):
                with open(json_path) as f:
                    local_json = json.load(f)
                pae_array = np.array(local_json["pae"])
                
                chain_lens = self.chain_length[query]
                chain_len_sums = np.cumsum([0] + chain_lens)
                pae_chain_array = np.empty((len(chain_lens), len(chain_lens)))
                chain_ids = self.chains[query]
                
                pae_dict = {}
                
                for i in range(len(chain_lens)):
                    for j in range(len(chain_lens)):
                        pae_val = fun(pae_array[chain_len_sums[i]:chain_len_sums[i+1],chain_len_sums[j]:chain_len_sums[j+1]])
                        pae_dict[f"PAE_{chain_ids[i]}_{chain_ids[j]}"] = pae_val
                
                pae_list.append(pae_dict)
            else:
                pae_list.append({})

        pae_df = pd.DataFrame(pae_list)
        
        for col in pae_df.columns:
            self.df.loc[:, col] = pae_df.loc[:, col].to_numpy()


def concat_data(data_list):
    """ Concatenate data from a list of Data objects.

    Parameters
    ----------
    data_list : list
        List of Data objects.

    Returns
    -------
    Data
        Concatenated Data object.   
    """

    concat = Data(directory=None, csv=None)

    concat.df = pd.concat([data.df for data in data_list], ignore_index=True)
    concat.chains = data_list[0].chains
    concat.chain_length = data_list[0].chain_length
    concat.format = data_list[0].format
    for i in range(1, len(data_list)):
        concat.chains.update(data_list[i].chains)
        concat.chain_length.update(data_list[i].chain_length)
    
    return concat

def read_multiple_alphapuldown(directory):
    """Read multiple directories containing AlphaPulldown data.

    Parameters
    ----------
    directory : str
        Path to the directory containing the directories.

    Returns
    -------
    Data
        Concatenated Data object.
    """

    dir_list = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    data_list = []

    for dir in dir_list:
        if 'ranking_debug.json' in os.listdir(os.path.join(directory, dir)):
            data_list.append(Data(os.path.join(directory, dir)))

    if len(data_list) == 0:
        raise ValueError("No AlphaPulldown data found in the directory.")
    return concat_data(data_list)


def get_pae(json_file):


    if json_file is None:
        return (None, None)

    with open(json_file) as f:
        local_json = json.load(f)

    if 'pae' in local_json:
        pae_array = np.array(local_json["pae"])
    elif 'predicted_aligned_error' in local_json[0]:
        pae_array = np.array(local_json[0]["predicted_aligned_error"])
    else:
        raise ValueError("No PAE found in the json file.")

    return pae_array
