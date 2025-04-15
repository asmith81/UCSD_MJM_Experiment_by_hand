"""
Environment configuration module.
Handles loading and validation of environment settings.
"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml

def load_environment(config_path: Path) -> Dict[str, Any]:
    """
    Load and validate environment configuration.
    
    Args:
        config_path: Path to the environment configuration file
        
    Returns:
        Dict containing environment configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    # Get project root from environment
    project_root = Path(os.environ.get("PROJECT_ROOT", Path.cwd()))
    
    # Load environment config
    if not config_path.exists():
        raise FileNotFoundError(f"Environment config not found: {config_path}")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Validate required environment variables
    required_vars = ['PROJECT_ROOT', 'USER_HOME', 'TEMP_DIR']
    for var in required_vars:
        if var not in os.environ:
            raise ValueError(f"Required environment variable not set: {var}")
    
    return config 