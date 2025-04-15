"""
Model setup and environment configuration module.
Handles environment setup, hardware verification, and model download.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, TypedDict, List
import yaml
import torch
from transformers import AutoModelForCausalLM, AutoProcessor
from huggingface_hub import snapshot_download

from src.path.repository import PathRepository
from src.config.environment import load_environment

# Type definitions as per documentation
class ConfigDict(TypedDict):
    name: str
    repo_id: str
    hardware: Dict[str, Any]
    loading: Dict[str, Any]
    quantization: Dict[str, Any]
    prompt: Dict[str, Any]
    inference: Dict[str, Any]
    model_path: Path
    cache_path: Path

class HardwareStatus(TypedDict):
    gpu_available: bool
    gpu_memory: int
    compute_capability: float
    disk_space: int
    network_available: bool
    temp_dir: Path

class DownloadResult(TypedDict):
    model_path: Path
    checksums: Dict[str, str]
    download_time: float
    total_size: int

class VerificationStatus(TypedDict):
    verified: bool
    checksum_matches: bool
    file_count: int
    total_size: int

class ModelInstance:
    model: Any  # Actual model object
    processor: Any  # Model processor
    device: str
    dtype: str

class OptimizedModel(ModelInstance):
    memory_usage: int
    gpu_utilization: float
    inference_time: float

def load_config(config_path: Path) -> ConfigDict:
    """
    Loads and validates model configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        ConfigDict: Validated configuration dictionary
    
    Raises:
        ConfigError: If configuration is invalid
        FileNotFoundError: If config file doesn't exist
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required_fields = ['name', 'repo_id', 'hardware', 'loading', 'quantization', 
                      'prompt', 'inference']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field in config: {field}")
    
    # Get paths from repository
    paths = PathRepository.get_instance()
    config['model_path'] = paths.get_path("models_pixtral")
    config['cache_path'] = paths.get_path("models_cache")
    
    return config

def verify_hardware(config: ConfigDict) -> HardwareStatus:
    """
    Verifies system meets model requirements.
    
    Args:
        config: Model configuration dictionary
    
    Returns:
        HardwareStatus: Contains GPU info, memory status, etc.
    
    Raises:
        HardwareError: If requirements not met
    """
    hardware_config = config['hardware']
    paths = PathRepository.get_instance()
    
    status: HardwareStatus = {
        'gpu_available': torch.cuda.is_available(),
        'gpu_memory': 0,
        'compute_capability': 0.0,
        'disk_space': 0,
        'network_available': True,
        'temp_dir': paths.get_path("temp")
    }
    
    if hardware_config['gpu_required'] and not status['gpu_available']:
        raise RuntimeError("GPU is required but not available")
    
    if status['gpu_available']:
        status['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory
        status['compute_capability'] = torch.cuda.get_device_capability(0)[0] + \
                                     torch.cuda.get_device_capability(0)[1] / 10
        
        min_memory = int(hardware_config['gpu_memory_min'].replace('GB', '')) * 1024**3
        if status['gpu_memory'] < min_memory:
            raise RuntimeError(f"GPU memory insufficient. Required: {hardware_config['gpu_memory_min']}")
        
        min_compute = float(hardware_config['minimum_compute_capability'])
        if status['compute_capability'] < min_compute:
            raise RuntimeError(f"GPU compute capability insufficient. Required: {min_compute}")
    
    return status

def download_model(config: ConfigDict, hw_status: HardwareStatus) -> DownloadResult:
    """
    Downloads model files from Hugging Face.
    
    Args:
        config: Model configuration
        hw_status: Hardware verification results
    
    Returns:
        DownloadResult: Contains download path, checksums, etc.
    
    Raises:
        DownloadError: If download fails
    """
    try:
        # Get paths from repository
        paths = PathRepository.get_instance()
        model_path = paths.get_path("models_pixtral")
        cache_path = paths.get_path("models_cache")
        
        # Create model directory if it doesn't exist
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Download model files
        snapshot_download(
            repo_id=config['repo_id'],
            local_dir=model_path,
            local_dir_use_symlinks=False,
            resume_download=True,
            cache_dir=cache_path
        )
        
        # Create download result
        result: DownloadResult = {
            'model_path': model_path,
            'checksums': {},  # TODO: Implement checksum verification
            'download_time': 0.0,  # TODO: Implement timing
            'total_size': 0  # TODO: Implement size calculation
        }
        
        return result
        
    except Exception as e:
        raise RuntimeError(f"Model download failed: {str(e)}")

def setup_environment() -> Dict[str, Any]:
    """
    Main function to set up environment and download model.
    
    Returns:
        Dict[str, Any]: Setup status information
    
    Raises:
        RuntimeError: If setup fails
    """
    try:
        # Load environment configuration
        env_config = load_environment(Path("config/environment.yaml"))
        
        # Load model configuration
        config = load_config(Path("config/models/pixtral.yaml"))
        
        # Verify hardware
        hardware_status = verify_hardware(config)
        
        # Download model
        download_result = download_model(config, hardware_status)
        
        return {
            'status': 'success',
            'config': config,
            'hardware_status': hardware_status,
            'download_result': download_result
        }
        
    except Exception as e:
        raise RuntimeError(f"Environment setup failed: {str(e)}")

if __name__ == "__main__":
    try:
        status = setup_environment()
        print("Environment setup successful!")
        print(f"Model path: {status['download_result']['model_path']}")
        print(f"Hardware status: {status['hardware_status']}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 