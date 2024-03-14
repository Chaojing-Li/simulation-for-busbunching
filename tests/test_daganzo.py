

alpha = 0.2
sigma = 15

sigma_h = 0.95*sigma*(alpha*(1-alpha))**(-0.5)
# sigma_h = 47
slack = 3*(alpha+0.03)*sigma_h
