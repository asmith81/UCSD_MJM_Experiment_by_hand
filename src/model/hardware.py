from pathlib import Path
from typing import Dict, TypedDict
import torch
import psutil
import yaml

class HardwareStatus(TypedDict):
    gpu_available: bool
    gpu_memory: int
    compute_capability: float
    disk_space: int
    network_available: bool
    temp_dir: Path

class HardwareVerifier:
    """Verifies system meets model requirements."""
    
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load model configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def verify_hardware(self) -> HardwareStatus:
        """Verify system meets model requirements."""
        try:
            # Check GPU availability
            gpu_available = torch.cuda.is_available()
            gpu_memory = 0
            compute_capability = 0.0
            
            if gpu_available:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # Convert to GB
                compute_capability = float(torch.cuda.get_device_capability()[0] + 
                                        torch.cuda.get_device_capability()[1] / 10)
            
            # Check disk space
            disk_space = psutil.disk_usage('/').free / (1024**3)  # Convert to GB
            
            # Check network availability (simple check)
            network_available = True  # TODO: Implement proper network check
            
            # Get temp directory
            temp_dir = Path('/tmp')  # TODO: Use system temp directory
            
            return HardwareStatus(
                gpu_available=gpu_available,
                gpu_memory=gpu_memory,
                compute_capability=compute_capability,
                disk_space=disk_space,
                network_available=network_available,
                temp_dir=temp_dir
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to verify hardware: {str(e)}")
    
    def meets_requirements(self, status: HardwareStatus) -> bool:
        """Check if hardware status meets model requirements."""
        try:
            # Check GPU requirements
            if self.config["hardware"]["gpu_required"] and not status["gpu_available"]:
                return False
            
            if status["gpu_available"]:
                min_memory = float(self.config["hardware"]["gpu_memory_min"].replace("GB", ""))
                if status["gpu_memory"] < min_memory:
                    return False
                
                min_compute = float(self.config["hardware"]["minimum_compute_capability"])
                if status["compute_capability"] < min_compute:
                    return False
            
            # Check disk space (require at least 2x model size)
            min_disk = 50  # GB, TODO: Calculate from model size
            if status["disk_space"] < min_disk:
                return False
            
            # Check network
            if not status["network_available"]:
                return False
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"Failed to check requirements: {str(e)}") 