import torch
import pickle
import json
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from vocab import Vocab
from model import ToxicCNNBiLSTM  

class ModelHandler:
    def __init__(self, model_path: str ="data/best_model.pt", vocab_path: str ="data/vocab.pkl", config_path: str ="data/config.json"):
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        with open(vocab_path, "rb") as f:
            self.vocab = pickle.load(f)
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        self.model = ToxicCNNBiLSTM(
            vocab_size=len(self.vocab),
            embedding_dim=config["embedding_dim"],
            hidden_dim=config["hidden_dim"],
            num_filters=config["num_filters"],
            kernel_size=config["kernel_size"],
            dropout=config["dropout"],
            padding=self.vocab.pad_id
        )
        
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
    
    def predict(self, text: str) -> float:
        tokens = text.lower().split()
        ids = self.vocab.encode(tokens)
        tensor = torch.tensor(ids, dtype=torch.long).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.model(tensor).squeeze(1)
            prob = torch.sigmoid(logits).item()
        
        return prob

# Создаём глобальный экземпляр
model = ModelHandler()