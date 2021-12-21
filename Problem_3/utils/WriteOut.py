import pandas as pd
import os
from utils.utils import call_payoff, put_payoff
from utils.BlackScholesModel import Call, Put
from utils.TrinomialModel import TrinomialTreeModel
from utils.utils import newtons, bisection
import matplotlib.pyplot as plt

def save_am_call_put(filename):

    common_params = {'S':42, 'K':40, 'T':0.75, 'r':0.04, 'q':0.00, \
                     'sigma':0.35,}
    N = int(common_params['T']*365)

    american_call = {**common_params, **{'exercise':True,
                                         'payoff':call_payoff, 'n':N}}
    american_put = {**common_params, **{'exercise':True,
                                        'payoff':put_payoff, 'n':N}}

    # tree model, american call
    model = TrinomialTreeModel(**american_call)
    data = model.greeks()
    am_call_df = pd.DataFrame(data.values(),
                              columns=['Tree_American(call)'], index=data.keys())

    # tree model, american put
    model = TrinomialTreeModel(**american_put)
    data = model.greeks()
    am_put_df = pd.DataFrame(data.values(),
                             columns=['Tree_American(put)'], index=data.keys())


    # R packages, call
    Rpacakge_results = {'price':6.623595, 'delta':0.6596053,
                        'gamma':0.02881365,'theta':3528.627,'vega':13.36975,'rho':15.97369}
    r_am_df = pd.DataFrame(Rpacakge_results.values(),
                           columns=['R_results(call)'], index=Rpacakge_results.keys())


    df = pd.concat([am_call_df, am_put_df,r_am_df], axis=1)

    df.to_csv(filename)


def save_euro_call_put(filename):
    # tree
    common_params = {'S':42, 'K':40, 'T':0.75, 'r':0.04, 'q':0.08, \
                     'sigma':0.35,}

    euro_call = {**common_params, **{'exercise':False,
                                     'payoff':call_payoff, 'n':400}}
    euro_put = {**common_params, **{'exercise':False,
                                    'payoff':put_payoff, 'n':400}}

    # black schole call
    bs_call = Call(**common_params)
    data = bs_call.greeks()
    bs_call_df = pd.DataFrame(data.values(),
                              columns=['Black_schole(call)'], index=data.keys())

    # tree model call
    model = TrinomialTreeModel(**euro_call)
    data = model.greeks()
    tree_call_df = pd.DataFrame(data.values(),
                                columns=['Tree_Euro(call)'], index=data.keys())

    # black schole put
    bs_call = Put(**common_params)
    data = bs_call.greeks()
    bs_put_df = pd.DataFrame(data.values(),
                             columns=['Black_schole(put)'], index=data.keys())

    # tree model put
    model = TrinomialTreeModel(**euro_put)
    data = model.greeks()
    tree_put_df = pd.DataFrame(data.values(),
                               columns=['Tree_Euro(put)'], index=data.keys())


    # R result
    Rpacakge_results = {'price':5.098, 'delta':0.551, 'gamma':0.029,
                        'theta':-1.988,'vega':13.358,'rho':13.518}
    r_call_df = pd.DataFrame(Rpacakge_results.values(),
                             columns=['R_results(call)'],
                             index=Rpacakge_results.keys())

    Rpacakge_results = {'price':4.361, 'delta':-0.391,
                        'gamma':0.029,'theta':-3.600,'vega':13.358,'rho':-15.596}
    r_put_df = pd.DataFrame(Rpacakge_results.values(),
                            columns=['R_results(put)'],
                            index=Rpacakge_results.keys())

    df = pd.concat([bs_call_df, tree_call_df, r_call_df,
                    bs_put_df, tree_put_df, r_put_df], axis=1)

    for i in ['call','put']:
        df['Euro_%s_rel_error(%%)'%i] = ((df['Tree_Euro(%s)'%i] -
                                          df['Black_schole(%s)'%i])/
                                         df['Black_schole(%s)'%i] *100) \
            .astype(int)


    df.to_csv(filename)


def save_implied_vol(filename):
    test = [{'S':42, 'K':40, 'T':0.75, 'r':0.04, 'q':0.00, 'payoff':call_payoff},
            {'S':42, 'K':40, 'T':0.75, 'r':0.04, 'q':0.00, 'payoff':put_payoff},
            {'S':42, 'K':40, 'T':0.75, 'r':0.04, 'q':0.02, 'payoff':call_payoff},
            {'S':42, 'K':40, 'T':0.75, 'r':0.04, 'q':0.02, 'payoff':put_payoff},
            {'S':100, 'K':120, 'T':1, 'r':0.06, 'q':0.02, 'payoff':call_payoff},
            {'S':100, 'K':120, 'T':1, 'r':0.06, 'q':0.02, 'payoff':put_payoff}]

    true_sigmas = [0.06, 0.1, 0.2, 0.3, 0.4]
    dfs = []
    for idx,val in enumerate(test):
        bs_newton, bs_bisec = [], []
        tree_newton, tree_bisec = [None] * len(true_sigmas), []
        for true_sigma in true_sigmas:
            #print("true_vol", true_sigma)
            if val['payoff'] == call_payoff:
                option = Call(val['S'], val['K'], val['T'], val['r'], val['q'], true_sigma)
            else:
                option = Put(val['S'], val['K'], val['T'], val['r'], val['q'], true_sigma)

            price = option.f(true_sigma)

            vol_newton = newtons(option.f, option.fprime, price)
            vol_bisec = bisection(option.f, price)
            bs_newton.append(vol_newton)
            bs_bisec.append(vol_bisec)
            val['C'] = price
            model = TrinomialTreeModel(**val)
            vol_bisec = model.implied_vol('bisection')
            tree_bisec.append(vol_bisec)
        df = pd.DataFrame({'bs_newton_'+str(idx):bs_newton,
                           'bs_bisec_'+str(idx):bs_bisec,
                           'tree_bisec_'+str(idx):tree_bisec })
        dfs.append(df)
    dfs = pd.concat(dfs, axis=1)
    dfs['true_sigma'] = true_sigmas
    dfs.set_index('true_sigma').to_csv(filename)


def save_convergence_plots(path):

    def util_convergence_plot(steps, results, black_schole, test_input):
        plt.plot(steps, results, label='Trinomial tree model')
        plt.axhline(y=black_schole, xmin=0, xmax=steps[-1],
                    color='r', linestyle='-.', linewidth=3,
                    label='Black-Scholes')
        plt.xlabel("Steps (T/dt)")
        plt.ylabel("initial option value")
        plt.title("Black-Scholes vs Trinomial Tree Model")
        plt.legend()

        if test_input['payoff'] == call_payoff:
            test_input['payoff'] = "call"
        else:
            test_input['payoff'] = "put"

        prefix = "_".join([str(key)+"_"+str(val) for
                           key,val in test_input.items()])

        if not os.path.exists(path):
            os.makedirs(path)
        output = os.path.join(path, prefix + '.jpg')
        plt.savefig(output, bbox_inches='tight', dpi=150)
        if False:
            plt.show()
        plt.figure().clear()
        print("Black Schole formula {}".format(black_schole))

    # test-1 euro-call, with, N = 5, 10, 15, 20
    def util_steps(test_input):

        outstream = test_input.copy()


        bs_input = test_input.copy()
        bs_input.pop('payoff', None)
        bs_call = Call(**bs_input).price(**bs_input)
        bs_put = Put(**bs_input).price(**bs_input)

        results = []
        steps = range(5, 205, 5)
        for n in steps:
            test_input['n'] = n

            model = TrinomialTreeModel(**test_input)
            initial_opt = model.npv()
            results.append(initial_opt)
        if test_input.get('payoff', 0) == put_payoff:
            outstream['payoff'] = 'put'
            bs_result = bs_put
        else:
            bs_result = bs_call
            outstream['payoff'] = 'call'
        print(outstream)

        util_convergence_plot(steps, results, bs_result, test_input)


    def test_euro_call_convergence():

        test_input1 = {'S':20, 'T':3, 'r':0.05,
                       'sigma':0.3, 'q':0.02, 'K':25,
                       'payoff':call_payoff}
        # High stock price
        test_input2 = {'S':100, 'T':3, 'r':0.15,
                       'sigma':0.5, 'q':0.04, 'K':65,
                       'payoff':call_payoff}
        # Low stock price
        test_input3 = {'S':42, 'T':0.75, 'K':40, 'r':0.04,
                       'q':0.08, 'sigma':0.35,
                       'payoff':call_payoff}
        tests = [test_input1, test_input2, test_input3]
        for test in tests:
            util_steps(test)

    def test_euro_put_convergence():

        test_input1 = {'S':20, 'T':3, 'r':0.05, 'sigma':0.3,
                       'q':0.02, 'K':25, 'payoff':put_payoff}
        test_input2 = {'S':127, 'T':1, 'r':0.1, 'sigma':0.2,
                       'q':0.03, 'K':130, 'payoff':put_payoff}

        tests = [test_input1, test_input2]
        for test in tests:
            util_steps(test)

    # black-schole vs trinomial
    test_euro_call_convergence()
    test_euro_put_convergence()