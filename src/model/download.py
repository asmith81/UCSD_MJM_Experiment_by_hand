from pathlib import Path
from typing import Dict, Optional, TypedDict
import yaml
import torch
import logging
from huggingface_hub import snapshot_download
from src.path.repository import PathRepository, PathError

class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass

class DownloadResult(TypedDict):
    model_path: Path
    checksums: Dict[str, str]
    download_time: float
    total_size: int

class ModelDownloader:
    """Handles model download and verification."""
    
    def __init__(self, config_path: Path):
        """Initialize model downloader with configuration."""
        try:
            self.paths = PathRepository.get_instance()
            self.config = self._load_config(config_path)
            self.model_dir = self.paths.get_path("models_pixtral")
            self.cache_dir = self.paths.get_path("models_cache")
            self._validate_config()
        except Exception as e:
            raise DownloadError(f"Failed to initialize ModelDownloader: {str(e)}")
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load and validate model configuration."""
        try:
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['repo_id', 'loading', 'quantization']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field in config: {field}")
            
            return config
        except Exception as e:
            raise DownloadError(f"Failed to load config: {str(e)}")
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        try:
            # Validate repo_id
            if not isinstance(self.config['repo_id'], str):
                raise ValueError("repo_id must be a string")
            
            # Validate loading parameters
            loading = self.config['loading']
            if not isinstance(loading, dict):
                raise ValueError("loading must be a dictionary")
            
            # Validate quantization options
            quantization = self.config['quantization']
            if not isinstance(quantization, dict):
                raise ValueError("quantization must be a dictionary")
            
        except Exception as e:
            raise DownloadError(f"Invalid configuration: {str(e)}")
    
    def download_model(self) -> DownloadResult:
        """Download model from Hugging Face Hub with error handling."""
        try:
            # Create model directory if it doesn't exist
            self.model_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify disk space
            self._verify_disk_space()
            
            # Download model files
            model_path = snapshot_download(
                repo_id=self.config["repo_id"],
                local_dir=self.model_dir,
                cache_dir=self.cache_dir,
                local_dir_use_symlinks=False,
                resume_download=True,
                use_auth_token=self.config["loading"]["default_params"]["use_auth_token"]
            )
            
            # Calculate download size
            total_size = sum(f.stat().st_size for f in Path(model_path).rglob('*') if f.is_file())
            
            # Generate checksums
            checksums = self._generate_checksums(Path(model_path))
            
            return DownloadResult(
                model_path=Path(model_path),
                checksums=checksums,
                download_time=0.0,  # TODO: Implement timing
                total_size=total_size
            )
            
        except Exception as e:
            # Clean up on failure
            self.cleanup()
            raise DownloadError(f"Failed to download model: {str(e)}")
    
    def _verify_disk_space(self) -> None:
        """Verify sufficient disk space is available."""
        try:
            # Get free space in model directory
            free_space = self.model_dir.stat().st_fsize
            # TODO: Add actual space requirement check
            if free_space < 1024 * 1024 * 1024:  # 1GB minimum
                raise DownloadError("Insufficient disk space")
        except Exception as e:
            raise DownloadError(f"Failed to verify disk space: {str(e)}")
    
    def _generate_checksums(self, path: Path) -> Dict[str, str]:
        """Generate checksums for downloaded files."""
        try:
            checksums = {}
            for file in path.rglob('*'):
                if file.is_file():
                    # TODO: Implement actual checksum generation
                    checksums[str(file.relative_to(path))] = "TODO"
            return checksums
        except Exception as e:
            raise DownloadError(f"Failed to generate checksums: {str(e)}")
    
    def verify_download(self, download_result: DownloadResult) -> bool:
        """Verify downloaded model files."""
        try:
            # Check if model directory exists
            if not download_result["model_path"].exists():
                return False
            
            # Check if all required files are present
            required_files = [
                "config.json",
                "model.safetensors",
                "tokenizer.json",
                "tokenizer_config.json"
            ]
            
            for file in required_files:
                if not (download_result["model_path"] / file).exists():
                    return False
            
            # TODO: Verify checksums
            return True
            
        except Exception as e:
            logging.error(f"Download verification failed: {str(e)}")
            return False
    
    def cleanup(self) -> None:
        """Clean up temporary files and cache with error handling."""
        try:
            # Clean cache directory
            if self.cache_dir.exists():
                for file in self.cache_dir.glob("*"):
                    try:
                        if file.is_file():
                            file.unlink()
                    except Exception as e:
                        logging.error(f"Failed to delete cache file {file}: {str(e)}")
                        continue
        except Exception as e:
            logging.error(f"Cleanup failed: {str(e)}")
            raise DownloadError(f"Failed to cleanup: {str(e)}") 