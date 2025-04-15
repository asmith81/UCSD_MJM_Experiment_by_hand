from pathlib import Path
from typing import Dict, Optional, TypedDict
import torch
from transformers import AutoModelForCausalLM, AutoProcessor
from src.path.repository import PathRepository

class ModelInstance(TypedDict):
    model: AutoModelForCausalLM
    processor: AutoProcessor
    device: str
    dtype: str

class OptimizedModel(ModelInstance):
    memory_usage: int
    gpu_utilization: float
    inference_time: float

class ModelInitializer:
    """Handles model initialization and optimization."""
    
    def __init__(self, config_path: Path):
        self.paths = PathRepository.get_instance()
        self.config = self._load_config(config_path)
        self.model_dir = self.paths.get_path("models_pixtral")
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load model configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def _verify_hardware(self) -> bool:
        """Verify hardware meets model requirements."""
        if not torch.cuda.is_available():
            return False
        
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # Convert to GB
        if gpu_memory < float(self.config["hardware"]["gpu_memory_min"].replace("GB", "")):
            return False
        
        return True
    
    def initialize_model(self, quantization: Optional[str] = None) -> ModelInstance:
        """Initialize model with specified configuration."""
        if not self._verify_hardware():
            raise RuntimeError("Hardware does not meet model requirements")
        
        try:
            # Load processor
            processor = AutoProcessor.from_pretrained(
                self.model_dir,
                trust_remote_code=True
            )
            
            # Determine quantization parameters
            if quantization is None:
                quantization = self.config["quantization"]["default"]
            
            quant_config = self.config["quantization"]["options"][quantization]
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                self.model_dir,
                torch_dtype=getattr(torch, quant_config["torch_dtype"]),
                device_map=quant_config["device_map"],
                use_flash_attention_2=quant_config.get("use_flash_attention_2", False),
                attn_implementation=quant_config.get("attn_implementation", "eager"),
                trust_remote_code=True
            )
            
            return ModelInstance(
                model=model,
                processor=processor,
                device=quant_config["device_map"],
                dtype=quant_config["torch_dtype"]
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize model: {str(e)}")
    
    def optimize_model(self, model_instance: ModelInstance) -> OptimizedModel:
        """Apply optimization settings to model."""
        try:
            # Get memory usage
            memory_usage = torch.cuda.memory_allocated() / (1024**3)  # Convert to GB
            
            # Create optimized model instance
            optimized = OptimizedModel(
                **model_instance,
                memory_usage=memory_usage,
                gpu_utilization=0.0,  # TODO: Implement GPU utilization tracking
                inference_time=0.0  # TODO: Implement inference time tracking
            )
            
            return optimized
            
        except Exception as e:
            raise RuntimeError(f"Failed to optimize model: {str(e)}") 