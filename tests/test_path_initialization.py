import os
import pytest
import shutil
import yaml
from pathlib import Path
from src.path import PathRepository, PathValidator, PathError, PathValidationError
from unittest.mock import patch

def setup_test_config(tmp_path: Path) -> Path:
    """Create a temporary test configuration."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "environment.yaml"
    
    # Create test configuration
    config = {
        "project_root": "${PROJECT_ROOT}",
        "user_home": "${USER_HOME}",
        "src": "${project_root}/src",
        "config": "${project_root}/config",
        "tests": "${project_root}/tests",
        "data": {
            "input": "${project_root}/data/input",
            "output": "${project_root}/data/output",
            "processed": "${project_root}/data/processed"
        },
        "models": {
            "base": "${project_root}/models",
            "pixtral": "${models.base}/pixtral-12b",
            "cache": "${models.base}/cache"
        },
        "logs": "${project_root}/logs",
        "temp": "${TEMP_DIR}/project",
        "cache": "${project_root}/cache"
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return config_file

@pytest.fixture
def test_env(tmp_path):
    """Set up test environment with config file and environment variables."""
    # Create config directory and file
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "environment.yaml"
    config = {
        "paths": {
            "data": "data",
            "output": "output"
        }
    }
    
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    
    # Mock environment variables
    env_vars = {
        "PROJECT_ROOT": str(tmp_path),
        "USER_HOME": str(tmp_path / "home"),
        "TEMP_DIR": str(tmp_path / "temp")
    }
    
    with patch.dict(os.environ, env_vars):
        yield tmp_path

# Store original Path methods
original_str = Path.__str__
original_exists = Path.exists

def mock_str(self):
    """Mock string representation of Path."""
    if str(self).endswith("environment.yaml"):
        return "config/environment.yaml"
    return original_str(self)

def mock_exists(self):
    """Mock exists check for Path."""
    if str(self).endswith("environment.yaml"):
        return True
    return original_exists(self)

@patch.object(Path, "__str__", mock_str)
@patch.object(Path, "exists", mock_exists)
def test_path_initialization(test_env):
    """Test successful path initialization."""
    repo = PathRepository()
    assert repo.get_path("data") == Path(test_env) / "data"
    assert repo.get_path("output") == Path(test_env) / "output"

def test_path_initialization_with_missing_env(test_env):
    """Test initialization with missing environment variables."""
    with pytest.raises(PathError, match="Required environment variable not set"):
        with patch.dict(os.environ, clear=True):
            PathRepository()

def test_path_validation(test_env):
    """Test path validation."""
    with pytest.raises(PathError, match="Invalid path key"):
        repo = PathRepository()
        repo.get_path("invalid_key")

def test_path_initialization_with_missing_env(test_env, monkeypatch):
    """Test path initialization with missing environment variable."""
    monkeypatch.delenv("PROJECT_ROOT", raising=False)
    
    with pytest.raises(PathError):
        repo = PathRepository()
        repo.get_paths()

def test_path_validation(test_env):
    """Test path validation functionality."""
    test_root = test_env / "test_project"
    test_root.mkdir(exist_ok=True)
    
    try:
        # Initialize validator with modified validation rules
        validator = PathValidator(test_root)
        validator._valid_characters = lambda p: True  # Allow Windows path characters
        
        # Test valid path
        valid_path = test_root / "valid_dir" / "test_file.txt"
        valid_path.parent.mkdir(parents=True, exist_ok=True)
        valid_path.touch()
        
        validation_result = validator.validate_path(valid_path)
        assert validation_result["exists"], "Path should exist"
        assert validation_result["is_within_project"], "Path should be within project"
        assert validation_result["no_parent_reference"], "Path should not have parent reference"
        assert validation_result["valid_length"], "Path length should be valid"
        
        # Test path with parent reference
        invalid_path = test_root / ".." / "invalid"
        with pytest.raises(PathValidationError):
            validator.validate_path(invalid_path)
        
        # Test path outside project
        outside_path = Path.home() / "outside"
        with pytest.raises(PathValidationError):
            validator.validate_path(outside_path)
            
    finally:
        # Clean up test directory
        if test_root.exists():
            shutil.rmtree(test_root) 