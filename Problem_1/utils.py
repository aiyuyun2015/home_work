import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib.pyplot import figure

TRADING_DAY = 260

def sharpe(x, r=0):
    return (np.mean(x) * TRADING_DAY - r) / (np.std(x, ddof=1) * np.sqrt(TRADING_DAY))


def maxdrawdown_utils(prices, cummax, date, thr_val, output):
    from matplotlib.pyplot import figure
    figure(figsize=(10, 7))

    plt.plot(prices, color='b', label='prices')
    plt.plot(cummax, color='r', label='cummax')
    plt.plot(date, thr_val, 'ro', label='through value')

    # Naming the x-axis, y-axis and the whole graph
    plt.xlabel("Date")
    plt.ylabel("Unit($)")
    plt.title("Price and their cummax")

    # Adding legend, which helps us recognize the curve according to it's color
    plt.legend()
    plt.savefig(output, bbox_inches='tight', dpi=150)


def sortino(x, r=0):
    downward = np.where(x < r,
                        x, 0)
    downward_std = np.sqrt((downward * downward).sum() / (len(downward) - 1))
    return (np.mean(x) * TRADING_DAY - r) / (downward_std * np.sqrt(TRADING_DAY))


def take_perc(ts, q):
    temp = ts.dropna()
    temp = temp.sort_values(ascending=True).reset_index(drop=True)
    loc = len(temp) * q
    if loc < 1:
        return "Extrapolation"

    loc_ceil = int(math.ceil(loc))
    loc_floor = int(loc_ceil - 1)

    result = temp[loc_floor - 1] + (temp[loc_ceil - 1] - temp[loc_floor - 1]) * (loc - loc_floor)
    return result


def robust_percentile(ts, q):
    if q >= 0.5:
        ts_temp = -ts.copy()
        q_temp = 1 - q
        return - take_perc(ts_temp, q_temp)
    else:
        return take_perc(ts, q)


def percentile(ts, q):
    '''
    Interpolated qunatile between the two adjacent points when len(ts) * q
    not integer (nan values ingored).

    Parameters
    ----------
    ts: array-like time series
    q: quantile

    Returns: quantile of array

    '''
    if q > 0.5: return -percentile(-ts, 1 - q)

    import math
    ts = (ts.dropna()
          .sort_values(ascending=True)
          .reset_index(drop=True))
    loc = len(ts) * q
    if loc < 1:
        raise ValueError("Length of series * quantile must be larger than 1")
    ceil = int(math.ceil(loc))
    floor = int(ceil - 1)
    result = ts[floor - 1] + (ts[ceil - 1] - ts[floor - 1]) * (loc - floor)
    return result

def plot_hist(pnl, label):
    figure(figsize=(10, 7))

    min_b, max_b = pnl.min(), pnl.max()
    N = 40
    bins = range(N) * (max_b - min_b)/N  + min_b
    pnl.hist(label=label, bins=bins)
    plt.xlabel("Daily PnL")
    plt.ylabel("Count")
    plt.title("Portfolio daily PnL histogram")

    plt.legend()

    # To load the display window
    plt.savefig(label+'.jpg', bbox_inches='tight', dpi=150)