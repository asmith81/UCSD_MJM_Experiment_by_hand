import os
from pathlib import Path
from typing import Dict, Optional
import yaml

def setup_runpod_paths() -> Dict[str, str]:
    """
    Set up paths for RunPod environment.
    
    Returns:
        Dict containing environment variables to set
    """
    # In RunPod, the current directory is already the project root
    project_root = Path.cwd()
    
    # Set up environment variables
    env_vars = {
        "PROJECT_ROOT": str(project_root),
        "USER_HOME": str(Path.home()),
        "TEMP_DIR": str(Path(os.getenv("TEMP", "/tmp")))
    }
    
    # Update environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
    
    return env_vars

def validate_runpod_paths() -> bool:
    """
    Validate that all required paths exist in RunPod environment.
    
    Returns:
        bool: True if all paths are valid, False otherwise
    """
    project_root = Path(os.environ["PROJECT_ROOT"])
    
    # Check required directories
    required_dirs = [
        project_root / "src",
        project_root / "config",
        project_root / "data" / "images",
        project_root / "models",
        project_root / "logs"
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            print(f"❌ Required directory does not exist: {dir_path}")
            return False
    
    return True

def ensure_runpod_directories() -> None:
    """Create all required directories in RunPod environment."""
    project_root = Path(os.environ["PROJECT_ROOT"])
    
    # Create base directories first
    base_dirs = [
        project_root / "data",
        project_root / "models",
        project_root / "logs",
        project_root / "cache"
    ]
    
    for dir_path in base_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created base directory: {dir_path}")
    
    # Create subdirectories
    subdirs = [
        # Data subdirectories
        project_root / "data" / "images",
        
        # Model subdirectories
        project_root / "models" / "pixtral-12b",
        project_root / "models" / "cache"
    ]
    
    for dir_path in subdirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created subdirectory: {dir_path}") 