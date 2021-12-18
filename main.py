# tree
common_params = {'S':42, 'K':40, 'T':0.75, 'r':0.04, 'q':0.08, \
                 'sigma':0.35,}

euro_call = {**common_params, **{'exercise':False, 'payoff':call_payoff, 'n':400}}
euro_put = {**common_params, **{'exercise':False, 'payoff':put_payoff, 'n':400}}

# black schole call
bs_call = Call(**common_params)
data = bs_call.greeks()
bs_call_df = pd.DataFrame(data.values(), columns=['Black_schole(call)'], index=data.keys())

# tree model call
model = TrinomialTreeModel(**euro_call)
data = model.greeks()
tree_call_df = pd.DataFrame(data.values(), columns=['Tree_Euro(call)'], index=data.keys())


# black schole put
bs_call = Put(**common_params)
data = bs_call.greeks()
bs_put_df = pd.DataFrame(data.values(), columns=['Black_schole(put)'], index=data.keys())

# tree model put
model = TrinomialTreeModel(**euro_put)
data = model.greeks()
tree_put_df = pd.DataFrame(data.values(), columns=['Tree_Euro(put)'], index=data.keys())


# R result
Rpacakge_results = {'price':5.098, 'delta':0.551, 'gamma':0.029,'theta':-1.988,'vega':13.358,'rho':13.518}
r_call_df = pd.DataFrame(Rpacakge_results.values(), columns=['R_results(call)'], index=Rpacakge_results.keys())

Rpacakge_results = {'price':4.361, 'delta':-0.391, 'gamma':0.029,'theta':-3.600,'vega':13.358,'rho':-15.596}
r_put_df = pd.DataFrame(Rpacakge_results.values(), columns=['R_results(put)'], index=Rpacakge_results.keys())

df = pd.concat([bs_call_df, tree_call_df, r_call_df, bs_put_df, tree_put_df, r_put_df], axis=1)

for i in ['call','put']:
    df['Euro_%s_rel_error(%%)'%i]  = ((df['Tree_Euro(%s)'%i] - df['Black_schole(%s)'%i])/df['Black_schole(%s)'%i] *100).astype(int)


df.to_csv("bs_vs_tree_euro.csv")