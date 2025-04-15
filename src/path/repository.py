from pathlib import Path
from typing import ClassVar, Dict, Optional
import os
import yaml
from dataclasses import dataclass
from typing import TypedDict

class EnvConfig(TypedDict):
    project_root: Path
    config_dir: Path
    model_dir: Path
    cache_dir: Path
    data_dir: Path
    log_dir: Path
    temp_dir: Path

@dataclass
class ResolvedPath:
    absolute: Path
    relative: str
    base: Path
    components: list[str]

class PathRepository:
    """Centralized repository for all project paths."""
    
    _instance: ClassVar[Optional['PathRepository']] = None
    
    @classmethod
    def get_instance(cls) -> 'PathRepository':
        """Get the singleton instance of the path repository."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the path repository with resolved paths."""
        self._config = self._load_environment()
        self._paths = self._resolve_all_paths()
    
    def _load_environment(self) -> EnvConfig:
        """Load environment configuration from YAML file."""
        config_path = Path("config/environment.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Environment config not found at {config_path}")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Resolve environment variables
        project_root = Path(os.getenv("PROJECT_ROOT", os.getcwd()))
        user_home = Path(os.getenv("USER_HOME", os.path.expanduser("~")))
        temp_dir = Path(os.getenv("TEMP_DIR", "/tmp"))
        
        return {
            "project_root": project_root,
            "config_dir": project_root / "config",
            "model_dir": project_root / "models",
            "cache_dir": project_root / "cache",
            "data_dir": project_root / "data",
            "log_dir": project_root / "logs",
            "temp_dir": temp_dir / "project"
        }
    
    def _resolve_all_paths(self) -> Dict[str, Path]:
        """Resolve all paths from configuration."""
        return {
            # Core paths
            "project_root": self._config["project_root"],
            "src": self._config["project_root"] / "src",
            "config": self._config["config_dir"],
            "tests": self._config["project_root"] / "tests",
            
            # Data paths
            "data_input": self._config["data_dir"] / "input",
            "data_output": self._config["data_dir"] / "output",
            "data_processed": self._config["data_dir"] / "processed",
            
            # Model paths
            "models_base": self._config["model_dir"],
            "models_pixtral": self._config["model_dir"] / "pixtral-12b",
            "models_cache": self._config["model_dir"] / "cache",
            
            # System paths
            "logs": self._config["log_dir"],
            "temp": self._config["temp_dir"],
            "cache": self._config["cache_dir"],
        }
    
    def get_path(self, path_key: str) -> Path:
        """Get a resolved path by its key."""
        if path_key not in self._paths:
            raise KeyError(f"Unknown path key: {path_key}")
        return self._paths[path_key]
    
    def get_all_paths(self) -> Dict[str, Path]:
        """Get all resolved paths."""
        return self._paths.copy()
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for path in self._paths.values():
            path.mkdir(parents=True, exist_ok=True) 