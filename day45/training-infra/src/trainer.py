import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Dict, Callable
import logging

logger = logging.getLogger(__name__)

class SimpleDataset(Dataset):
    """Simple dataset for demonstration"""
    def __init__(self, size: int = 1000, input_dim: int = 784):
        self.size = size
        self.input_dim = input_dim
    
    def __len__(self):
        return self.size
    
    def __getitem__(self, idx):
        # Generate random data
        x = torch.randn(self.input_dim)
        y = torch.randint(0, 10, (1,)).item()
        return x, y

class SimpleModel(nn.Module):
    """Simple neural network for demonstration"""
    def __init__(self, input_dim: int = 784, hidden_dim: int = 256, num_classes: int = 10):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, num_classes)
        
    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.fc3(x)
        return x

class DistributedTrainer:
    """Handles model training with distributed support"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.device = torch.device('cpu')  # Use CPU for demo
        self.model = self._build_model()
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=config.get('learning_rate', 0.001)
        )
        
    def _build_model(self) -> nn.Module:
        """Build model based on config"""
        model_type = self.config.get('model_type', 'simple')
        
        if model_type == 'simple':
            model = SimpleModel(
                input_dim=self.config.get('input_dim', 784),
                hidden_dim=self.config.get('hidden_dim', 256),
                num_classes=self.config.get('num_classes', 10)
            )
        else:
            model = SimpleModel()
        
        return model.to(self.device)
    
    def train_epoch(self, dataloader: DataLoader, epoch: int) -> Dict:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (data, target) in enumerate(dataloader):
            data, target = data.to(self.device), target.to(self.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()
        
        avg_loss = total_loss / len(dataloader)
        accuracy = correct / total
        
        return {
            'epoch': epoch,
            'loss': avg_loss,
            'accuracy': accuracy
        }
    
    def save_checkpoint(self, path: str, epoch: int, metrics: Dict):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'metrics': metrics
        }
        torch.save(checkpoint, path)
        logger.info(f"Checkpoint saved to {path}")
    
    def load_checkpoint(self, path: str) -> int:
        """Load model checkpoint"""
        checkpoint = torch.load(path, weights_only=False)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        logger.info(f"Checkpoint loaded from {path}")
        return checkpoint['epoch']
