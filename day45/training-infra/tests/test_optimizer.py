import pytest
from src.optimizer import HyperparameterOptimizer

def test_study_creation():
    """Test optimization study creation"""
    optimizer = HyperparameterOptimizer(study_name="test_study")
    optimizer.create_study(direction='minimize')
    
    assert optimizer.study is not None

def test_hyperparameter_search():
    """Test hyperparameter optimization"""
    optimizer = HyperparameterOptimizer()
    optimizer.create_study()
    
    def objective(trial):
        params = optimizer.define_search_space(trial)
        # Simulate training with these params
        return params['learning_rate'] * 100
    
    optimizer.optimize(objective, n_trials=5)
    
    best_params = optimizer.get_best_params()
    assert 'learning_rate' in best_params
    
    history = optimizer.get_trial_history()
    assert len(history) == 5

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
