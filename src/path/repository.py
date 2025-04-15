from pathlib import Path
from typing import ClassVar, Dict, Optional
import os
import yaml
from dataclasses import dataclass
from typing import TypedDict
import logging

class EnvConfig(TypedDict):
    project_root: Path
    config_dir: Path
    model_dir: Path
    cache_dir: Path
    data_dir: Path
    log_dir: Path
    temp_dir: Path

class PathError(Exception):
    """Custom exception for path-related errors."""
    pass

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
        self._validate_paths()
    
    def _load_environment(self) -> Dict:
        """Load and validate environment configuration."""
        try:
            env_path = Path("config/environment.yaml")
            if not env_path.exists():
                raise PathError(f"Environment config not found: {env_path}")
            
            with open(env_path) as f:
                config = yaml.safe_load(f)
            
            # Validate required environment variables
            required_vars = ['PROJECT_ROOT', 'USER_HOME', 'TEMP_DIR']
            for var in required_vars:
                if var not in os.environ:
                    raise PathError(f"Required environment variable not set: {var}")
            
            return config
        except Exception as e:
            raise PathError(f"Failed to load environment: {str(e)}")
    
    def _resolve_all_paths(self) -> Dict[str, Path]:
        """Resolve all paths from configuration with validation."""
        try:
            paths = {}
            
            # Core paths
            paths["project_root"] = self._resolve_path(self._config["project_root"])
            paths["src"] = self._resolve_path(self._config["src"])
            paths["config"] = self._resolve_path(self._config["config"])
            paths["tests"] = self._resolve_path(self._config["tests"])
            
            # Data paths
            paths["data_input"] = self._resolve_path(self._config["data"]["input"])
            paths["data_output"] = self._resolve_path(self._config["data"]["output"])
            paths["data_processed"] = self._resolve_path(self._config["data"]["processed"])
            
            # Model paths
            paths["models_base"] = self._resolve_path(self._config["models"]["base"])
            paths["models_pixtral"] = self._resolve_path(self._config["models"]["pixtral"])
            paths["models_cache"] = self._resolve_path(self._config["models"]["cache"])
            
            # System paths
            paths["logs"] = self._resolve_path(self._config["logs"])
            paths["temp"] = self._resolve_path(self._config["temp"])
            paths["cache"] = self._resolve_path(self._config["cache"])
            
            return paths
        except KeyError as e:
            raise PathError(f"Missing required path configuration: {str(e)}")
        except Exception as e:
            raise PathError(f"Failed to resolve paths: {str(e)}")
    
    def _resolve_path(self, path_str: str) -> Path:
        """Resolve a path string to a Path object with validation."""
        try:
            # Replace environment variables
            path = Path(os.path.expandvars(path_str))
            
            # Validate path
            if not self._is_valid_path(path):
                raise PathError(f"Invalid path: {path}")
            
            return path
        except Exception as e:
            raise PathError(f"Failed to resolve path {path_str}: {str(e)}")
    
    def _is_valid_path(self, path: Path) -> bool:
        """Validate path meets project requirements."""
        try:
            # Check path length
            if len(str(path)) > 4096:
                return False
            
            # Check for parent directory references
            if ".." in path.parts:
                return False
            
            # Check for invalid characters
            if any(not c.isprintable() for c in str(path)):
                return False
            
            return True
        except Exception:
            return False
    
    def _validate_paths(self) -> None:
        """Validate all resolved paths."""
        for key, path in self._paths.items():
            try:
                if not self._is_valid_path(path):
                    raise PathError(f"Invalid path for {key}: {path}")
            except Exception as e:
                logging.error(f"Path validation failed for {key}: {str(e)}")
                raise
    
    def get_path(self, path_key: str) -> Path:
        """Get a resolved path by its key with validation."""
        if path_key not in self._paths:
            raise KeyError(f"Unknown path key: {path_key}")
        
        path = self._paths[path_key]
        if not self._is_valid_path(path):
            raise PathError(f"Invalid path for {path_key}: {path}")
        
        return path
    
    def get_all_paths(self) -> Dict[str, Path]:
        """Get all resolved paths."""
        return self._paths.copy()
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist with proper permissions."""
        for key, path in self._paths.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                # Set appropriate permissions
                path.chmod(0o755)  # rwxr-xr-x
            except Exception as e:
                logging.error(f"Failed to create directory {key}: {str(e)}")
                raise PathError(f"Failed to create directory {key}: {str(e)}") 