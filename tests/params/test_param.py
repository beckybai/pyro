from copy import copy

import numpy as np
import torch
import torch.optim
from torch import nn as nn
from torch.autograd import Variable

import pyro
from tests.common import TestCase


class ParamStoreDictTests(TestCase):

    def setUp(self):
        pyro.get_param_store().clear()
        self.linear_module = nn.Linear(3, 2)
        self.linear_module2 = nn.Linear(3, 2)
        self.linear_module3 = nn.Linear(3, 2)

    def test_save_and_load(self):
        lin = pyro.module("mymodule", self.linear_module)
        lin2 = pyro.module("mymodule2", self.linear_module2)  # noqa: F841
        x = Variable(torch.randn(1, 3))
        myparam = pyro.param("myparam", Variable(1.234 * torch.ones(1), requires_grad=True))

        cost = torch.sum(torch.pow(lin(x), 2.0)) * torch.pow(myparam, 4.0)
        cost.backward()
        params = list(self.linear_module.parameters()) + [myparam]
        optim = torch.optim.Adam(params, lr=.01)
        myparam_copy_stale = copy(pyro.param("myparam").data.numpy())

        optim.step()

        myparam_copy = copy(pyro.param("myparam").data.numpy())
        param_store_params = copy(pyro.get_param_store()._params)
        param_store_param_to_name = copy(pyro.get_param_store()._param_to_name)
        assert len(list(param_store_params.keys())) == 5
        assert len(list(param_store_param_to_name.values())) == 5

        pyro.get_param_store().save('paramstore.unittest.out')
        pyro.get_param_store().clear()
        assert len(list(pyro.get_param_store()._params)) == 0
        assert len(list(pyro.get_param_store()._param_to_name)) == 0
        pyro.get_param_store().load('paramstore.unittest.out')

        def modules_are_equal():
            weights_equal = np.sum(np.fabs(self.linear_module3.weight.data.numpy() -
                                   self.linear_module.weight.data.numpy())) == 0.0
            bias_equal = np.sum(np.fabs(self.linear_module3.bias.data.numpy() -
                                self.linear_module.bias.data.numpy())) == 0.0
            return (weights_equal and bias_equal)

        assert not modules_are_equal()
        pyro.module("mymodule", self.linear_module3)
        assert modules_are_equal()

        myparam = pyro.param("myparam")
        store = pyro.get_param_store()
        assert myparam_copy_stale != myparam.data.numpy()
        assert myparam_copy == myparam.data.numpy()
        assert sorted(param_store_params.keys()) == sorted(store._params.keys())
        assert sorted(param_store_param_to_name.values()) == sorted(store._param_to_name.values())
        assert sorted(store._params.keys()) == sorted(store._param_to_name.values())