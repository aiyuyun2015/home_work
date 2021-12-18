import numpy as np
import warnings


def call_payoff(x, K):
    return np.maximum(x - K, 0)


def put_payoff(x, K):
    return np.maximum(K - x, 0)


def first_order_derivative(up, down, shift):
    return (up - down) / (2 * shift)


def newtons(f, fprime, target, err=1e-3, start=0.25, max_iter=100):
    x1 = start
    counter = 0
    estimated = f(x1)
    while np.abs(estimated - target) > err:
        price, vega = f(x1), fprime(x1)
        x2 = x1 - (price - target) / vega
        x1 = x2
        counter += 1
        if counter > max_iter:
            warnings.warn("Iteration > max_iter %d" % max_iter)
            return x1
    return x1


def bisection(f, target, start=1e-3, end=1, err=1e-3, max_iter=100):
    mid = (start + end) / 2.0
    counter = 0
    while np.abs(f(mid) - target) > err:
        if counter > max_iter:
            warnings.warn("Iteration reach max_iter%d" % max_iter)
            return mid
        if f(mid) > target:
            end = mid
        else:
            start = mid
        mid = (start + end) / 2.0
        counter += 1
    return mid
