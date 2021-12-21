import numpy as np


class CompressedTree:
    """
    Used for underlying price tree. Only last branch is saved to
    compress the data.
    """

    def __init__(self, height, d, S0):

        self.data = S0 * np.cumprod(np.ones(shape=(2 * height + 1)) / d) * d ** (height + 1)
        self.data = np.array(self.data)
        self.height = height

    def __str__(self):
        strs = ""
        for i in range(self.height + 1):
            if i != 0:
                strs += "\n"
            for j in range(0, 2 * i + 1, 1):
                strs += str(self[i, j]) + ", "
        return strs

    def __getitem__(self, grid):
        t, j = grid
        return self.data[self.height - t + j]
