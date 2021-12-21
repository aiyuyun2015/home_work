import numpy as np
from utils.CompressedTree import CompressedTree
from utils.utils import call_payoff, first_order_derivative, bisection

class TrinomialTreeModel:
    def __init__(self, S, K, T, r, q, sigma=None, C=None,
                 exercise=False, payoff=call_payoff, n=100):
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.q = q
        self.sigma = sigma
        self.C = C
        self.n = n
        self.exercise = exercise
        self.payoff = payoff
        self.op_tree = np.zeros([1 + self.n, 2 * self.n + 1])
        self.early_optimal = None
        self.dt = None
        self.u = None
        self.d = None
        self.m = None
        self.p_u = None
        self.p_d = None
        self.p_m = None
        self.underlying = None

    @staticmethod
    def specify_condition(price_tree, K, payoff):
        return payoff(price_tree.data, K)

    def compute_probs(self):
        # T, sigma, r, q, will trigger the call
        self.dt = self.T / self.n
        self.u = np.exp(self.sigma * np.sqrt(2 * self.dt))
        self.d = 1 / self.u
        self.m = 1
        e1 = np.exp((self.r - self.q) * self.dt / 2.)
        e2 = np.exp(self.sigma * np.sqrt(self.dt / 2.))
        self.p_u = ((e1 - 1 / e2) / (e2 - 1 / e2)) ** 2
        self.p_d = ((e2 - e1) / (e2 - 1 / e2)) ** 2
        self.p_m = 1 - (self.p_u + self.p_d)

    def compute_probs_approx(self):
        # Alternatively, use the approxmiation
        self.dt = self.T / self.n
        self.u = np.exp(self.sigma * np.sqrt(3 * self.dt))
        self.d = 1 / self.u
        self.m = 1
        e1 = np.sqrt(self.dt / (12 * self.sigma ** 2)) * (self.r - self.q - 0.5 * self.sigma ** 2)
        e2 = 1.0 / 6
        self.p_u = e1 + e2
        self.p_d = -e1 + e2
        self.p_m = 1 - (self.p_u + self.p_d)
        print(self.d, self.u)

    def calc_underlying_price_tree(self):
        self.underlying = CompressedTree(self.n, self.d, self.S)

    def adjust_american(self, i, j):
        exercied = self.payoff(self.underlying[i, j], self.K)
        if self.op_tree[i, j] < exercied:
            self.early_optimal = True
            self.op_tree[i, j] = exercied
        else:
            self.early_optimal = False
            self.op_tree[i, j] = self.op_tree[i, j]

    def stepback(self, to=0):
        for i in np.arange(self.n - 1, to - 1, -1):
            for j in np.arange(0, 2 * i + 1):
                u_p = self.op_tree[i + 1, j + 2]
                m_p = self.op_tree[i + 1, j + 1]
                d_p = self.op_tree[i + 1, j]
                self.op_tree[i, j] = np.exp(-self.r * self.dt) \
                                     * (self.p_u * u_p + self.p_m * m_p + self.p_d * d_p)
                if self.exercise:
                    self.adjust_american(i, j)
        return self.op_tree

    def npv(self):
        self.compute_probs()
        self.calc_underlying_price_tree()
        self.op_tree[-1:] = self.specify_condition(
            self.underlying, self.K,
            self.payoff)
        self.stepback()
        self.C = self.op_tree[0, 0]
        return self.op_tree[0, 0]

    def implied_vol(self, algo='bisection', C=None, start=1e-3, end=1, err=1e-3, max_iter=100):
        if self.C is None:
            raise RuntimeEerror("Option price missing.")
        if C is None: C = self.C

        def f_sigma(sigma):
            self.adjust_prop('sigma', sigma)
            return self.npv()

        def fprime_sigma(sigma):
            self.adjust_prop('sigma', sigma)
            return self.vega()

        if algo == "bisection":
            return bisection(f_sigma, C, start, end, err, max_iter)
        elif algo == "newton":
            return newtons(f_sigma, fprime_sigma, C, err=err, start=start, max_iter=max_iter)
        else:
            raise RuntimeError("Support bisection or newton.")

    def delta_approx(self):
        self.npv()
        return (self.op_tree[1, 1] - self.op_tree[1, 0]) \
               / (self.underlying[1, 1] - self.underlying[1, 0])

    def delta(self, shift=0.01):
        return self._vary('S', shift)

    def gamma_approx(self):
        # reset tree
        self.npv()

        delta_11 = (self.op_tree[2, 2] - self.op_tree[2, 1]) \
                   / (self.underlying[2, 2] - self.underlying[2, 1])

        delta_10 = (self.op_tree[2, 1] - self.op_tree[2, 0]) \
                   / (self.underlying[2, 1] - self.underlying[2, 0])

        shift = 0.5 * (self.underlying[2, 2] - self.underlying[2, 0])

        return (delta_11 - delta_10) / shift

    def gamma(self, shift=0.01):
        return self._vary2('S', shift)

    def theta_approx(self):
        self.npv()
        return (self.op_tree[2, 1] - self.op_tree[0, 0]) / (2 * self.dt)

    def theta(self, shift=0.01):
        return -self._vary('T', shift)

    def vega(self, shift=0.01):
        return self._vary('sigma', shift)

    def rho(self, shift=0.01):
        return self._vary('r', shift)

    def adjust_prop(self, prop, val):
        setattr(self, prop, val)

    def _vary(self, prop, shift=0.01):
        val = getattr(self, prop)
        self.adjust_prop(prop, val + shift)
        up = self.npv()
        self.adjust_prop(prop, val - shift)
        down = self.npv()
        self.adjust_prop(prop, val)

        return first_order_derivative(up, down, shift)

    def _vary2(self, prop, shift=0.01):
        mid = self.npv()
        val = getattr(self, prop)
        self.adjust_prop(prop, val + shift)
        up = self.npv()
        self.adjust_prop(prop, val - shift)
        down = self.npv()
        self.adjust_prop(prop, val)
        print("up", up, 'donw', down, 'mid', mid, 'shift', shift)
        return (up - 2 * mid + down) / (shift ** 2)

    def greeks(self, shift=0.01):
        hedges = {'price': self.npv(), 'delta': self.delta(shift), 'gamma': self.gamma_approx(),
                'theta': self.theta(shift), 'rho': self.rho(shift), 'vega': self.vega(shift)}
        return hedges