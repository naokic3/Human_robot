import torch
import torch.nn as nn
import torch.distributions as Categorical
class actor_critic(nn.Module):
    def __init__(self, state_size, action_size):
        super(actor_critic, self).__init__()
        hidden_size = 64
        self.actor = nn.Sequential(
                nn.Linear(state_size,hidden_size),
                nn.Tanh()
                nn.Linear(hidden_size,hidden_size),
                nn.Tanh(),
                nn.Linear(64, action_size)
        )
        self.critic = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
            )
    
    def get_action_and_value(self,state,action=None):
        logits = self.actor(state)
        dist = Categorical(logits=logits)

        if action is None
            action = dist.sample()
        
        return action,dist.log_prob(action), dist.entropy(), self.critic(state)