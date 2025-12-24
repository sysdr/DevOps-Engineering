import optuna
from optuna.trial import Trial
from typing import Dict, Callable
import logging

logger = logging.getLogger(__name__)

class HyperparameterOptimizer:
    """Manages hyperparameter optimization studies"""
    
    def __init__(self, study_name: str = "training_optimization"):
        self.study_name = study_name
        self.study = None
        
    def create_study(self, direction: str = 'minimize'):
        """Create new optimization study"""
        self.study = optuna.create_study(
            study_name=self.study_name,
            direction=direction,
            sampler=optuna.samplers.TPESampler()
        )
        logger.info(f"Created optimization study: {self.study_name}")
    
    def define_search_space(self, trial: Trial) -> Dict:
        """Define hyperparameter search space"""
        return {
            'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-1, log=True),
            'batch_size': trial.suggest_categorical('batch_size', [16, 32, 64, 128]),
            'hidden_dim': trial.suggest_int('hidden_dim', 64, 512, step=64),
            'dropout': trial.suggest_float('dropout', 0.0, 0.5),
            'weight_decay': trial.suggest_float('weight_decay', 1e-6, 1e-3, log=True)
        }
    
    def optimize(self, objective: Callable, n_trials: int = 20):
        """Run optimization"""
        if self.study is None:
            self.create_study()
        
        self.study.optimize(objective, n_trials=n_trials)
        
        logger.info(f"Best trial: {self.study.best_trial.number}")
        logger.info(f"Best value: {self.study.best_value:.4f}")
        logger.info(f"Best params: {self.study.best_params}")
    
    def get_best_params(self) -> Dict:
        """Get best hyperparameters"""
        if self.study is None:
            return {}
        return self.study.best_params
    
    def get_trial_history(self) -> list:
        """Get all trials"""
        if self.study is None:
            return []
        
        return [
            {
                'number': trial.number,
                'value': trial.value,
                'params': trial.params,
                'state': trial.state.name
            }
            for trial in self.study.trials
        ]
