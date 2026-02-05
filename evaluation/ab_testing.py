"""
A/B Testing Framework for Recommendation Systems.
Allows comparing different models, strategies, or parameters.
"""
import hashlib
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperimentManager:
    """
    Manages A/B testing experiments for recommendation systems.
    
    Features:
    - Deterministic user assignment to experiment groups
    - Support for multiple concurrent experiments
    - Experiment configuration management
    - Metrics tracking per experiment group
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the experiment manager.
        
        Args:
            config_path: Path to experiment configuration JSON
        """
        self.experiments = {}
        self.config_path = config_path
        
        if config_path and Path(config_path).exists():
            self.load_experiments(config_path)
        else:
            logger.info("No experiment config provided, using default setup")
    
    def load_experiments(self, config_path: str):
        """
        Load experiment configurations from JSON file.
        
        Expected format:
        {
            "experiment_1": {
                "name": "Hybrid vs Collaborative",
                "description": "Testing hybrid model against pure collaborative",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "groups": {
                    "control": {"model": "collaborative", "weight": 0.5},
                    "treatment": {"model": "hybrid", "weight": 0.5}
                }
            }
        }
        """
        try:
            with open(config_path, 'r') as f:
                self.experiments = json.load(f)
            logger.info(f"Loaded {len(self.experiments)} experiments from {config_path}")
        except Exception as e:
            logger.error(f"Error loading experiment config: {e}")
    
    def create_experiment(self, experiment_id: str, name: str, 
                         groups: Dict[str, Dict], 
                         description: str = "",
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None):
        """
        Create a new experiment.
        
        Args:
            experiment_id: Unique experiment identifier
            name: Human-readable experiment name
            groups: Dictionary of group configurations
                    e.g., {"control": {"model": "collaborative", "weight": 0.5}}
            description: Experiment description
            start_date: Experiment start date (YYYY-MM-DD)
            end_date: Experiment end date (YYYY-MM-DD)
        """
        # Validate group weights sum to 1.0
        total_weight = sum(g.get('weight', 0) for g in groups.values())
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Group weights must sum to 1.0, got {total_weight}")
        
        self.experiments[experiment_id] = {
            'name': name,
            'description': description,
            'start_date': start_date or datetime.now().strftime('%Y-%m-%d'),
            'end_date': end_date,
            'groups': groups,
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Created experiment '{name}' with {len(groups)} groups")
    
    def get_user_group(self, user_id: int, experiment_id: str) -> Optional[str]:
        """
        Assign user to an experiment group using deterministic hashing.
        
        This ensures:
        - Same user always gets same group (consistency)
        - Approximately equal distribution across groups
        - No need to store assignments
        
        Args:
            user_id: User ID
            experiment_id: Experiment ID
            
        Returns:
            Group name (e.g., "control", "treatment") or None if experiment not found
        """
        if experiment_id not in self.experiments:
            logger.warning(f"Experiment {experiment_id} not found")
            return None
        
        experiment = self.experiments[experiment_id]
        
        # Check if experiment is active
        if not self._is_experiment_active(experiment):
            logger.info(f"Experiment {experiment_id} is not active")
            return None
        
        # Create deterministic hash from user_id and experiment_id
        hash_input = f"{user_id}:{experiment_id}".encode('utf-8')
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        
        # Normalize to [0, 1]
        normalized_hash = (hash_value % 10000) / 10000.0
        
        # Assign to group based on cumulative weights
        cumulative_weight = 0.0
        groups = experiment['groups']
        
        for group_name, group_config in groups.items():
            cumulative_weight += group_config.get('weight', 0)
            if normalized_hash <= cumulative_weight:
                return group_name
        
        # Fallback (shouldn't happen if weights sum to 1.0)
        return list(groups.keys())[0]
    
    def _is_experiment_active(self, experiment: Dict) -> bool:
        """Check if an experiment is currently active based on dates."""
        now = datetime.now().date()
        
        # Check start date
        if experiment.get('start_date'):
            start = datetime.strptime(experiment['start_date'], '%Y-%m-%d').date()
            if now < start:
                return False
        
        # Check end date
        if experiment.get('end_date'):
            end = datetime.strptime(experiment['end_date'], '%Y-%m-%d').date()
            if now > end:
                return False
        
        return True
    
    def get_group_config(self, user_id: int, experiment_id: str) -> Optional[Dict]:
        """
        Get the complete configuration for a user's assigned group.
        
        Args:
            user_id: User ID
            experiment_id: Experiment ID
            
        Returns:
            Group configuration dictionary or None
        """
        group_name = self.get_user_group(user_id, experiment_id)
        if not group_name:
            return None
        
        experiment = self.experiments[experiment_id]
        group_config = experiment['groups'][group_name].copy()
        group_config['group_name'] = group_name
        group_config['experiment_id'] = experiment_id
        group_config['experiment_name'] = experiment['name']
        
        return group_config
    
    def get_active_experiments(self) -> List[str]:
        """Get list of currently active experiment IDs."""
        active = []
        for exp_id, exp_config in self.experiments.items():
            if self._is_experiment_active(exp_config):
                active.append(exp_id)
        return active
    
    def get_experiment_info(self, experiment_id: str) -> Optional[Dict]:
        """Get information about a specific experiment."""
        if experiment_id not in self.experiments:
            return None
        
        exp = self.experiments[experiment_id]
        return {
            'experiment_id': experiment_id,
            'name': exp['name'],
            'description': exp.get('description', ''),
            'start_date': exp.get('start_date'),
            'end_date': exp.get('end_date'),
            'groups': list(exp['groups'].keys()),
            'is_active': self._is_experiment_active(exp)
        }
    
    def get_all_experiments_info(self) -> List[Dict]:
        """Get information about all experiments."""
        return [self.get_experiment_info(exp_id) for exp_id in self.experiments.keys()]


# Default experiment configuration
DEFAULT_EXPERIMENTS = {
    "model_comparison": {
        "name": "Hybrid vs Collaborative Filtering",
        "description": "Compare hybrid model performance against pure collaborative filtering",
        "start_date": "2024-01-01",
        "end_date": None,  # No end date = runs indefinitely
        "groups": {
            "control": {
                "model": "collaborative",
                "weight": 0.5,
                "description": "Pure collaborative filtering"
            },
            "treatment": {
                "model": "hybrid",
                "weight": 0.5,
                "description": "Hybrid model (collaborative + content + popularity)"
            }
        }
    }
}


def create_default_config(output_path: str = "evaluation/experiments.json"):
    """Create a default experiment configuration file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(DEFAULT_EXPERIMENTS, f, indent=2)
    
    logger.info(f"Created default experiment config at {output_path}")
    return output_path


if __name__ == "__main__":
    # Example usage
    manager = ExperimentManager()
    
    # Create an experiment
    manager.create_experiment(
        experiment_id="test_exp_1",
        name="Model Comparison Test",
        groups={
            "control": {"model": "collaborative", "weight": 0.5},
            "treatment": {"model": "hybrid", "weight": 0.5}
        },
        description="Testing hybrid vs collaborative"
    )
    
    # Assign some users
    for user_id in [1, 2, 3, 4, 5, 10, 20, 50, 100]:
        group = manager.get_user_group(user_id, "test_exp_1")
        config = manager. get_group_config(user_id, "test_exp_1")
        print(f"User {user_id}: {group} -> {config}")
    
    # Test consistency
    print("\nConsistency test:")
    user_id = 42
    for _ in range(3):
        group = manager.get_user_group(user_id, "test_exp_1")
        print(f"User {user_id} (attempt {_+1}): {group}")
