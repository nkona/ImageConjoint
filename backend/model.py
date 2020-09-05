## IMPORTS ------------------------------------------------------

import torch
import torch.autograd as autograd
import torch.optim as optim
from torch.distributions import constraints, transform_to

torch.set_default_dtype(torch.float64)

import pyro
import pyro.contrib.gp as gp
pyro.set_rng_seed(1) ### Fixed seed value for testing purposes



## MODEL --------------------------------------------------------

class PrefOptim():

    def __init__(self, X, y, gp_noise, nd):
        self.gpmodel = gp.models.GPRegression(X, y, gp.kernels.Matern52(input_dim=nd), noise=torch.tensor(gp_noise), jitter=1.0e-6)
        self.optimizer = torch.optim.Adam(self.gpmodel.parameters(), lr=0.001)
        gp.util.train(self.gpmodel, self.optimizer)
        

    def ucb(self, x, kappa):
        mu, variance = self.gpmodel(x, full_cov=False, noiseless=False)
        sigma = variance.sqrt()
        return mu + kappa * sigma  


    def info_gain(self, x):
        variance = self.gpmodel(x, full_cov=False, noiseless=False)[1]
        return variance
    

    def acquisition_fn(self, x):
        return self.info_gain(x)
    

    def update_posterior(self, y_new, x_new):
        if x_new.dim() == 1:
            x_new = x_new.unsqueeze(0)
        X = torch.cat([self.gpmodel.X, x_new], 0) 
        y = torch.cat([self.gpmodel.y, y_new])
        self.gpmodel.set_data(X, y)
        self.optimizer = torch.optim.Adam(self.gpmodel.parameters(), lr=0.001)
        gp.util.train(self.gpmodel, self.optimizer)


    def find_a_candidate(self, x_init, lower_bound=0, upper_bound=1):
        constraint = constraints.interval(lower_bound, upper_bound)
        unconstrained_x_init = transform_to(constraint).inv(x_init)
        unconstrained_x = unconstrained_x_init.clone().detach().requires_grad_(True)
        minimizer = optim.LBFGS([unconstrained_x], line_search_fn='strong_wolfe')

        def closure():
            minimizer.zero_grad()
            x = transform_to(constraint)(unconstrained_x)
            y = self.acquisition_fn(x)
            autograd.backward(unconstrained_x, autograd.grad(y, unconstrained_x))
            return y

        minimizer.step(closure)
        x = transform_to(constraint)(unconstrained_x)
        return x.detach()


    def next_x(self, lower_bound=0, upper_bound=1, num_candidates=5):
        candidates = []
        values = []

        x_init = self.gpmodel.X[-1:]
        for i in range(num_candidates):
            x = self.find_a_candidate(x_init, lower_bound, upper_bound)
            y = self.acquisition_fn(x)
            candidates.append(x)
            values.append(y)
            x_init = x.new_empty(x.shape).uniform_(lower_bound, upper_bound)

        argmin = torch.min(torch.cat(values), dim=0)[1].item()
        return candidates[argmin]
