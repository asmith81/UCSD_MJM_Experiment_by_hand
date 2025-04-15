from pathlib import Path
from typing import Dict, Optional, TypedDict
import yaml
from .download import ModelDownloader, DownloadResult
from .init import ModelInitializer, ModelInstance, OptimizedModel
from .hardware import HardwareVerifier, HardwareStatus
from src.path.repository import PathRepository

class ModelManager:
    """Orchestrates model download and initialization process."""
    
    def __init__(self, config_path: Path):
        self.paths = PathRepository.get_instance()
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.downloader = ModelDownloader(config_path)
        self.initializer = ModelInitializer(config_path)
        self.hardware_verifier = HardwareVerifier(config_path)
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load model configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def setup_model(self, quantization: Optional[str] = None) -> OptimizedModel:
        """Complete model setup process."""
        try:
            # Verify hardware
            hardware_status = self.hardware_verifier.verify_hardware()
            if not self.hardware_verifier.meets_requirements(hardware_status):
                raise RuntimeError("System does not meet model requirements")
            
            # Download model
            download_result = self.downloader.download_model()
            if not self.downloader.verify_download(download_result):
                raise RuntimeError("Model download verification failed")
            
            # Initialize model
            model_instance = self.initializer.initialize_model(quantization)
            
            # Optimize model
            optimized_model = self.initializer.optimize_model(model_instance)
            
            return optimized_model
            
        except Exception as e:
            # Cleanup on failure
            self.downloader.cleanup()
            raise RuntimeError(f"Failed to setup model: {str(e)}")
    
    def cleanup(self) -> None:
        """Clean up all temporary files and resources."""
        try:
            self.downloader.cleanup()
        except Exception as e:
            raise RuntimeError(f"Failed to cleanup: {str(e)}") 