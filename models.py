import torch
import torch.nn as nn

torch.set_default_dtype(torch.float64)

class BoW(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        # the following two assignment was adjusted during tuning
        self.vocab_size = vocab_size
        self.dropout_rate = 0.1
        self.num_neurons1 = 512
        self.num_neurons2 = 64
        self.hidden1 = nn.Linear(vocab_size, self.num_neurons1)
        self.dropout1 = nn.Dropout(self.dropout_rate)
        if self.num_neurons2 > 0:
            self.hidden2 = nn.Linear(self.num_neurons1, self.num_neurons2)
            self.dropout2 = nn.Dropout(self.dropout_rate)
            self.out = nn.Linear(self.num_neurons2, 2)
        else:
            self.out = nn.Linear(self.num_neurons1, 2)

    def forward(self, x):
        if x.dtype != torch.float64:
            x = x.double()
        x = nn.ReLU()(self.hidden1(x))
        # x = self.dropout1(x)
        if self.num_neurons2 > 0:
            x = nn.ReLU()(self.hidden2(x))
            x = self.dropout2(x)
        x = self.out(x)
        return x


    def get_config(self):
        if self.num_neurons2 == 0:
            return str(self.num_neurons1)
        else:
            return str(self.num_neurons1) + "-" + str(self.num_neurons2)

