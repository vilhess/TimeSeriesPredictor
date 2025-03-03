import torch 
import torch.nn as nn 
import math

class myLayerNorm(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.layernorm = nn.LayerNorm(channels)
    def forward(self, x):
        x_hat = self.layernorm(x)
        bias = torch.mean(x_hat, dim=1).unsqueeze(1).repeat(1, x.shape[1], 1)
        return x_hat - bias

class moving_avg(nn.Module):
    def __init__(self, kernel_size):
        super().__init__()
        self.kernel_size = kernel_size
        self.avg = nn.AvgPool1d(kernel_size=kernel_size, stride=1, padding=0)
        
    def forward(self, x):
        front = x[:, 0:1, :].repeat(1, self.kernel_size-1 - math.floor((self.kernel_size - 1)//2) , 1)
        end = x[:, -1:, :].repeat(1, math.floor((self.kernel_size - 1)//2) , 1)
        x = torch.cat([front, x, end], dim=1)
        x = self.avg(x.permute(0, 2, 1)).permute(0, 2, 1)
        return x
    
class series_decomp(nn.Module):
    def __init__(self, kernel_size):
        super().__init__()
        self.moving_avg = moving_avg(kernel_size=kernel_size)
    def forward(self, x):
        moving_mean = self.moving_avg(x)
        res = x - moving_mean
        return res, moving_mean
    
class series_decomp_multi(nn.Module):
    def __init__(self, kernel_sizes):
        super().__init__()
        self.moving_avg = [moving_avg(kernel_size=kernel) for kernel in kernel_sizes]
        self.layer = nn.Linear(1, len(kernel_sizes))
    def forward(self, x):
        moving_mean = []
        for func in self.moving_avg:
            moving_avg = func(x)
            moving_mean.append(moving_avg.unsqueeze(-1))
        moving_mean = torch.cat(moving_mean, dim=-1)
        moving_mean = torch.sum(moving_mean*nn.Softmax(-1)(self.layer(x.unsqueeze(-1))), dim=-1)
        res = x - moving_mean
        return res, moving_mean