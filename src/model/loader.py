from pathlib import Path
from typing import Dict, Any, Optional
import logging
import torch
from transformers import AutoModelForCausalLM, AutoProcessor
from src.path.repository import PathRepository, PathError

logger = logging.getLogger(__name__)

class ModelLoader:
    """Handles model loading with quantization options."""
    
    def __init__(self, model_path: Path):
        """
        Initialize model loader.
        
        Args:
            model_path: Path to model directory
            
        Raises:
            PathError: If model path is invalid
        """
        try:
            self.paths = PathRepository.get_instance()
            self.model_path = model_path
            
            # Validate model path
            if not model_path.exists():
                raise PathError(f"Model path does not exist: {model_path}")
            
            # Set device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
            
        except Exception as e:
            raise PathError(f"Failed to initialize ModelLoader: {str(e)}")
    
    def load_model(self, quantization: str = "bfloat16") -> Dict[str, Any]:
        """
        Load model with specified quantization.
        
        Args:
            quantization: Quantization option (bfloat16, int8, int4)
            
        Returns:
            Dict containing model, processor, and metadata
            
        Raises:
            ValueError: If quantization is invalid
            RuntimeError: If model loading fails
        """
        try:
            # Validate quantization
            valid_quantizations = ["bfloat16", "int8", "int4"]
            if quantization not in valid_quantizations:
                raise ValueError(f"Invalid quantization: {quantization}. Must be one of {valid_quantizations}")
            
            # Set torch dtype based on quantization
            if quantization == "bfloat16":
                torch_dtype = torch.bfloat16
            elif quantization == "int8":
                torch_dtype = torch.int8
            else:  # int4
                torch_dtype = torch.int4
            
            logger.info(f"Loading model with {quantization} quantization...")
            
            # Load model and processor
            model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                torch_dtype=torch_dtype,
                device_map="auto"
            )
            processor = AutoProcessor.from_pretrained(str(self.model_path))
            
            # Move model to device
            model.to(self.device)
            
            return {
                'model': model,
                'processor': processor,
                'device': self.device,
                'quantization': quantization
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")
    
    def cleanup(self, model_dict: Dict[str, Any]) -> None:
        """
        Clean up model resources.
        
        Args:
            model_dict: Dictionary containing model and processor
        """
        try:
            if 'model' in model_dict:
                del model_dict['model']
            if 'processor' in model_dict:
                del model_dict['processor']
            torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Failed to cleanup model resources: {str(e)}") 