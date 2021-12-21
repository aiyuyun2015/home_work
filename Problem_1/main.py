import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import chi2_contingency
from matplotlib.pyplot import figure
import statsmodels.formula.api as smf
from utils import sharpe, maxdrawdown_utils, sortino, plot_hist, robust_percentile

TRADING_DAY = 260


class Calculator:
    def __init__(self):
        self.pnl_a = None
        self.pnl_b = None
        self.df = None
        self.a_ret = None
        self.b_ret = None
        self.pls = ['Portfolio A', 'Portfolio B']
        self.mdd_a, self.date_a = None, None
        self.mdd_b, self.date_b = None, None
        self.output_path = 'outputs'

    def compute(self):
        self.price_a, self.price_b = self.df[self.pls[0]], self.df[self.pls[1]]
        self.pnl_a, self.pnl_b = self.price_a.diff(), self.price_b.diff()
        self.a_ret = self.price_a.pct_change()
        self.b_ret = self.price_b.pct_change()
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def open_file(self, filename):
        self.df = pd.read_csv(filename)

        self.df = self.df.dropna(axis=0, how='all')
        self.df.Date = pd.to_datetime(self.df.Date)
        self.df = self.df.sort_values(by='Date')
        self.df = self.df.set_index(['Date'])
        return self.df

    def compute_ret(self):
        annual_ret = self.df.apply(lambda prices: np.sqrt(prices[-1] / prices[0]) - 1, axis=0)
        return annual_ret

    def comptue_vol(self):
        annual_vol = self.df.apply(lambda x: np.sqrt(TRADING_DAY) * x.std(ddof=1), axis=0)
        return annual_vol

    def max_drawdown(self, prices):
        cummax = prices.cummax()
        drawdown = prices / cummax - 1
        mdd = min(drawdown)
        # save date for plotting
        return mdd, prices[drawdown == mdd].index

    def compute_mdd(self):
        self.mdd_a, self.date_a = self.max_drawdown(self.df[self.pls[0]])
        self.mdd_b, self.date_b = self.max_drawdown(self.df[self.pls[1]])
        return self.mdd_a, self.date_a, self.mdd_b, self.date_b

    def plot_maxdrawdonw(self):
        cummax_a = self.price_a.cummax()
        thr_val_a = self.price_a.loc[self.date_a]

        cummax_b = self.price_b.cummax()
        thr_val_b = self.price_b.loc[self.date_b]

        maxdrawdown_utils(self.price_a, cummax_a, self.date_a, thr_val_a,
                          os.path.join(self.output_path,'mdd_a.jpg'))
        maxdrawdown_utils(self.price_b, cummax_b, self.date_b, thr_val_b,
                          os.path.join(self.output_path,'mdd_b.jpg'))

    def compute_sharpe(self, r=0.02):
        return sharpe(self.a_ret, r), sharpe(self.b_ret, r)

    def compute_sortino(self, r=0.02):
        return sortino(self.a_ret, r), sortino(self.b_ret, r)

    def compute_vars(self, q=0.05):
        return robust_percentile(self.pnl_a, q), robust_percentile(self.pnl_b, q)

    def make_hists(self):
        plot_hist(self.pnl_a, 'Portfolio A',
                  output=os.path.join(self.output_path, 'hist_b.jpg'))
        plot_hist(self.pnl_b, 'Portfolio B',
                  output=os.path.join(self.output_path, 'hist_b.jpg'))

    def plot_pnls(self):
        figure(figsize=(10, 7))
        plt.plot(self.pnl_a, color='b', label='pnl_a')
        plt.plot(self.pnl_b, color='r', label='pnl_b')
        plt.xlabel("Date")
        plt.ylabel("Daily PnL")
        plt.title("Daily PnLs of Two Portfolios")
        plt.legend()
        plt.savefig(os.path.join(self.output_path, 'pnls.jpg'), bbox_inches='tight', dpi=150)

    def corr(self):
        spearman_corr = self.pnl_a.corr(self.pnl_b, method='spearman')
        pearson_corr = self.pnl_a.corr(self.pnl_b, method='pearson')
        return spearman_corr, pearson_corr

    def plot_scatter(self):
        self.linear_regression()

        figure(figsize=(10, 7))
        plt.scatter(self.pnl_b, self.pnl_a, label='scatter of two pnls')
        x = np.linspace(-0.07,0.07)
        plt.plot(x, self.k * x + self.incerpt, c='r')

        plt.xlabel("pnl_b")
        plt.ylabel("pnl_a")
        plt.legend(loc='upper left')
        plt.text(0.02, 0 , "pnl_b * {:.2f} + {:.2f} = pnl_a".format(self.k, self.incerpt))
        plt.savefig(os.path.join(self.output_path, 'scatter.jpg'), bbox_inches='tight', dpi=150)

    def ks_test(self):
        # H0: from same distribution samplings
        return stats.ks_2samp(self.pnl_a, self.pnl_b)

    # Chi-squared test
    def chi_square_test(self):
        BIN_NUM = 10
        min_bin = min(self.pnl_a.min(), self.pnl_b.min())
        max_bin = max(self.pnl_a.max(), self.pnl_b.max())
        bins = np.arange(min_bin, max_bin, step=(max_bin - min_bin) / BIN_NUM)
        hist_a, _ = np.histogram(self.pnl_a, bins=bins)
        hist_b, _ = np.histogram(self.pnl_b, bins=bins)

        # H0: two independent distributions
        # H1: distributions dependent

        data = [hist_a, hist_b]
        stat, p, dof, expected = chi2_contingency(data)

        # interpret p-value
        alpha = 0.05
        # print("p value is " + str(p))
        if p <= alpha:
            print('Chi-square: Dependent (reject H0)')
        else:
            print('Chi-square: Independent (H0 holds true)')

    def linear_regression(self):
        data = pd.DataFrame()
        data['pnl_A'] = self.pnl_a
        data['pnl_B'] = self.pnl_b
        mlr = smf.ols(formula="pnl_A ~ pnl_B", data=data).fit()
        self.incerpt = mlr.params.Intercept
        self.k = mlr.params.pnl_B

        return mlr


def main():
    calc = Calculator()
    calc.open_file('portfolio.csv')
    calc.compute()
    # compute ret
    annual_ret = calc.compute_ret()
    print("annual return:\n", annual_ret)

    annual_vol = calc.comptue_vol()
    print("annual vol:\n", annual_vol)

    mdd_A, date_A, mdd_B, date_B = calc.compute_mdd()
    print("maximum drawdown A:{:.2f}, B:{:.2f}\n".format(mdd_A, mdd_B))

    calc.plot_maxdrawdonw()

    sharpe_A, sharpe_B = calc.compute_sharpe(r=0.02)
    print("Portfolio A: {}={:.2f}".format('sharpe', sharpe_A))
    print("Portfolio B: {}={:.2f}".format('sharpe', sharpe_B))

    sortino_A, sortino_B = calc.compute_sortino(r=0.02)
    print("Portfolio A: {}={:.2f}".format('sortino', sortino_A))
    print("Portfolio B: {}={:.2f}\n".format('sortino', sortino_B))


    for q in [0.05, 0.01]:
        var_a, var_b = calc.compute_vars(q)
        print("{}% confidence, A portfolio will not exceed {:.2f}".format((1 - q) * 100, var_a))
        print("{}% confidence, B portfolio will not exceed {:.2f}".format((1 - q) * 100, var_b))
    calc.make_hists()

    calc.plot_pnls()

    spearman_corr, pearson_corr = calc.corr()
    print("\n")
    print("Spearman corr:{:.2f}".format(spearman_corr))
    print("Pearson corr:{:.2f}".format(pearson_corr))



    calc.plot_scatter()

    ks_ret = calc.ks_test()
    print(ks_ret, '\n')

    ols = calc.linear_regression()
    print(ols.summary(),'\n')

    calc.chi_square_test()


if __name__ == "__main__":
    main()
