import os
from utils.WriteOut import save_implied_vol, save_am_call_put, save_euro_call_put, save_convergence_plots

def join_with_path(basename, output_path = 'outputs'):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    return os.path.join(output_path, basename)

def main():
    output_path = 'outputs'
    euro_out = join_with_path('euro_call_put.csv', output_path)
    am_out = join_with_path('am_call_put.csv', output_path)
    implied_out = join_with_path('implied_vol.csv', output_path)

    # Compute euro call and put, greeks from BS, trinomial tree model, comparing with R results
    print("Save euro result...")
    save_euro_call_put(euro_out)

    # Compute american call and put greeks, from trinomial, compare with a R packaged
    print("Save am result...")
    save_am_call_put(am_out)

    # Compute implied vol from BS and tree model, summarize with 6 different tests
    print("Save implied result...")
    save_implied_vol(implied_out)

    # Plot convergence test (BS vs different steps in tree)
    print("Save convergence plots")
    save_convergence_plots(output_path)


if __name__ == "__main__":
    main()
    print("goodbye~")