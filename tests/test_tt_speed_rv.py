import numpy as np

l = 1000  # m
mu = 36 / 3.6  # m/s
cv = 0.2  # 20%
sigma = cv*mu  # m/s
mean_tt = l/mu
print(mean_tt)

norma_std = np.sqrt(np.log(1 + (sigma / mu) ** 2))
norma_mean = np.log(mu) - norma_std ** 2 / 2
v = np.random.lognormal(norma_mean,  norma_std, 10000000)
print('speed:', v.mean(), v.std())

tt = l/v
print('real tt:', tt.mean(), tt.std())

estim_tt_mean = np.exp(-norma_mean + norma_std ** 2 / 2)
estim_tt_std = np.sqrt(np.exp(norma_std ** 2) - 1) * \
    np.exp(-norma_mean + norma_std ** 2/2)

print('estimated tt:', estim_tt_mean * l, estim_tt_std * l)
