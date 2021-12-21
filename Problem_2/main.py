import pandas as pd
import numpy as np
import h5py
import os

class Converter():
    def __init__(self):
        self.datasets = {}
        self.tree = []
        self.df = None
        self.checksum = {} # for sanity check

    def __call__(self, name, node):
        if isinstance(node, h5py.Dataset):
            self.datasets[name] = node
        # Save to print like a direcotry tree
        shift = name.count('/') * '    '
        item_name = name.split("/")[-1]
        self.tree.append(shift + item_name + "\n")
        return None

    def __str__(self):
        return "".join(self.tree)

    def to_dataframe(self):
        if self.df:
            return self.df
        dfs = []
        for name, node in self.datasets.items():
            df = pd.DataFrame(node, dtype=None) # infer float/int 64
            self.checksum[name] = df.sum(axis=0)
            new_cols = [name.split('/')[-1] +
                        "_" + str(col) for col in df.columns]
            df = df.rename(columns=dict(zip(df.columns, new_cols)))
            dfs.append(df)
        self.df = pd.concat(dfs, axis=1)
        return self.df


def main():
    filename = "sample.h5"

    with h5py.File(filename, "r") as f:
        data = Converter()
        f.visititems(data)
        print("Tree hierachy:")
        print(data)
        df = data.to_dataframe()

    print('sample output', '\n', df.head(3))
    print('columns', '\n', df.columns)
    output_path = 'outputs'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    output = os.path.join(output_path, "sample.csv")
    df.to_csv(output, index=False)

    # checksum includes sum of each column in h5, df.sum()
    # returns the sum in the combined dataframe
    checksum = pd.Series([col_sum for i in data.checksum.values() for col_sum in i.values])

    assert ((checksum - df.sum().values) == np.zeros_like(29)).all()

if __name__ == "__main__":
    main()

