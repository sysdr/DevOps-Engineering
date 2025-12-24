import pytest
import torch
from src.trainer import DistributedTrainer, SimpleModel, SimpleDataset

def test_model_creation():
    """Test model initialization"""
    config = {'model_type': 'simple', 'learning_rate': 0.001}
    trainer = DistributedTrainer(config)
    
    assert trainer.model is not None
    assert isinstance(trainer.model, SimpleModel)

def test_training_epoch():
    """Test single training epoch"""
    config = {'model_type': 'simple', 'learning_rate': 0.001}
    trainer = DistributedTrainer(config)
    
    dataset = SimpleDataset(size=100)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=16)
    
    metrics = trainer.train_epoch(dataloader, epoch=0)
    
    assert 'loss' in metrics
    assert 'accuracy' in metrics
    assert metrics['loss'] > 0

def test_checkpoint_save_load():
    """Test checkpoint saving and loading"""
    config = {'model_type': 'simple'}
    trainer = DistributedTrainer(config)
    
    # Save checkpoint
    metrics = {'loss': 0.5, 'accuracy': 0.8}
    trainer.save_checkpoint('test_checkpoint.pt', epoch=5, metrics=metrics)
    
    # Load checkpoint
    epoch = trainer.load_checkpoint('test_checkpoint.pt')
    assert epoch == 5

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
