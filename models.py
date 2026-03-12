import torch

from torch import nn
    

class BERTSalaryPredictor(nn.Module):
    def __init__(self,  bert, n_cat_features=1206, hid_size=100):
        super().__init__()
        self.bert = bert
        self.fc = nn.Sequential(
            nn.Linear(2 * hid_size, hid_size),
            nn.ReLU(),
            nn.Linear(hid_size, 1)
        )
        self.cat_linear = nn.Sequential(
            nn.Linear(n_cat_features, hid_size),
            nn.ReLU()
        )
        
    def forward(self, batch):
        device = self.bert.device
    
        title_and_description = batch['name_and_description'].to(device)
        categorical = batch['categorical'].to(device)

        title_and_desrc_features = self.bert(**title_and_description).logits
        cat_features = self.cat_linear(categorical)
        
        all_features = torch.concatenate([title_and_desrc_features, cat_features], axis=1)
        result = self.fc(all_features).squeeze(1)
        return result