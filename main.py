from utils.WriteOut import save_implied_vol, save_am_call_put, save_euro_call_put, save_convergence_plots


def main():

    # Compute euro call and put, greeks from BS, trinomial tree model, comparing with R results
    print("Save euro result...")
    save_euro_call_put('euro_call_put.csv')

    # Compute american call and put greeks, from trinomial, compare with a R packaged
    print("Save am result...")
    save_am_call_put('am_call_put.csv')

    # Compute implied vol from BS and tree model, summarize with 6 different tests
    print("Save implied result...")
    save_implied_vol('implied_vol.csv')

    # Plot convergence test (BS vs different steps in tree)
    print("Save convergence plots")
    save_convergence_plots()


if __name__ == "__main__":
    main()
    print("goodbye~")