def d1(S, K, T, r, q, sigma):
    return (np.log(S/K) + (r-q + sigma*sigma/2)*T)/(sigma*np.sqrt(T))

def d2(S, K, T, r, q, sigma):
    return d1(S, K, T, r, q, sigma) - sigma*np.sqrt(T)

class Call:
    def __init__(self, S, K, T, r, q, sigma):
        self.params = {'S':S,'K':K,'T':T,'r':r,'q':q,'sigma':sigma}
        self.d1 = d1(S, K, T, r, q, sigma)
        self.d2 = d2(S, K, T, r, q, sigma)
        self.exp_q = np.exp(-q*T)

    def price(self, S, K, T, r, q, sigma):
        return S*self.exp_q *scistat.norm.cdf(d1(S, K, T, r, q, sigma)) - \
               K*np.exp(-r*T)*scistat.norm.cdf(d2(S, K, T, r, q, sigma))

    def delta(self, S, K, T, r, q, sigma):
        return self.exp_q*scistat.norm.cdf(self.d1)

    def gamma(self, S, K, T, r, q, sigma):
        return self.exp_q*scistat.norm.pdf(self.d1)/(S*sigma*np.sqrt(T))

    def theta(self, S, K, T, r, q, sigma):
        aux1 =  S*self.exp_q*q*scistat.norm.cdf(self.d1)
        aux2 = -S*self.exp_q*sigma*scistat.norm.pdf(self.d1)/(2*np.sqrt(T))
        aux3 = -r*K*np.exp(-r*T)*scistat.norm.cdf(self.d2)

        return aux1 + aux2 + aux3

    def rho(self, S, K, T, r, q, sigma):
        return K*T*np.exp(-r*T)*scistat.norm.cdf(self.d2)

    def vega(self, S, K, T, r, q, sigma):
        return np.sqrt(T)*S*self.exp_q*scistat.norm.pdf(d1(S, K, T, r, q, sigma))

    def greeks(self):
        dict = {}
        dict['price'] = self.price(**self.params)
        dict['delta'] = self.delta(**self.params)
        dict['gamma'] = self.gamma(**self.params)
        dict['theta'] = self.theta(**self.params)
        dict['rho']   = self.rho(**self.params)
        dict['vega']  = self.vega(**self.params)
        return dict

    def f(self, sigma):
        self.params['sigma'] = sigma

        return self.price(**self.params)

    def fprime(self, sigma):
        self.params['sigma'] = sigma

        return self.vega(**self.params)


class Put:
    def __init__(self, S, K, T, r, q, sigma):
        self.params = {'S':S,'K':K,'T':T,'r':r,'q':q,'sigma':sigma}

        self.d1 = d1(S, K, T, r, q, sigma)
        self.d2 = d2(S, K, T, r, q, sigma)
        self.exp_q = np.exp(-q*T)

    def price(self, S, K, T, r, q, sigma):
        return -S*np.exp(-q*T) *scistat.norm.cdf(- d1(S, K, T, r, q, sigma)) \
               + K*np.exp(-r*T)*scistat.norm.cdf(-d2(S, K, T, r, q, sigma))

    def delta(self, S, K, T, r, q, sigma):
        return self.exp_q*(scistat.norm.cdf(self.d1) -1 )

    def gamma(self, S, K, T, r, q, sigma):
        return self.exp_q*scistat.norm.pdf(self.d1)/(S*sigma*np.sqrt(T))

    def theta(self, S, K, T, r, q, sigma):
        aux1 = -S*self.exp_q*q*scistat.norm.cdf(-self.d1)
        aux2 = -S*self.exp_q*sigma*scistat.norm.pdf(self.d1)/(2*np.sqrt(T))
        aux3 = r*K*np.exp(-r*T)*scistat.norm.cdf(-self.d2)

        return aux1 + aux2 + aux3

    def rho(self, S, K, T, r, q, sigma):
        return -K*T*np.exp(-r*T)*scistat.norm.cdf(-self.d2)

    def vega(self, S, K, T, r, q, sigma):
        return np.sqrt(T)*S*self.exp_q*scistat.norm.pdf(d1(S, K, T, r, q, sigma))

    def greeks(self):
        dict = {}
        dict['price'] = self.price(**self.params)
        dict['delta'] = self.delta(**self.params)
        dict['gamma'] = self.gamma(**self.params)
        dict['theta'] = self.theta(**self.params)
        dict['rho']   = self.rho(**self.params)
        dict['vega']  = self.vega(**self.params)
        return dict

    def f(self, sigma):
        self.params['sigma'] = sigma
        return self.price(**self.params)

    def fprime(self, sigma):
        self.params['sigma'] = sigma
        return self.vega(**self.params)