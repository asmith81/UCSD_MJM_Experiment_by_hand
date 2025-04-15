from pathlib import Path
from typing import Dict, Optional, TypedDict, Any
import logging
import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
from src.path.repository import PathRepository, PathError
from src.prompt.loader import PromptTemplate, PromptError
from src.prompt.formatter import FormattedPrompt

class InferenceResult(TypedDict):
    result: Dict[str, Any]
    confidence: float
    processing_time: float

class PromptRunner:
    """Handles running prompts through the model and processing results."""
    
    def __init__(self, model_path: Path):
        """
        Initialize prompt runner with model.
        
        Args:
            model_path: Path to the model directory
        """
        try:
            self.paths = PathRepository.get_instance()
            self.model_path = model_path
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._load_model()
        except Exception as e:
            raise PromptError(f"Failed to initialize PromptRunner: {str(e)}")
    
    def _load_model(self):
        """Load model and processor."""
        try:
            # Load model configuration
            config_path = self.model_path / "config.yaml"
            if not config_path.exists():
                raise PromptError(f"Model config not found: {config_path}")
            
            # Load model and processor
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                torch_dtype=torch.float16,
                device_map="auto"
            )
            self.processor = AutoProcessor.from_pretrained(str(self.model_path))
            
            # Move model to device
            self.model.to(self.device)
            
        except Exception as e:
            raise PromptError(f"Failed to load model: {str(e)}")
    
    def run_inference(self, formatted_prompt: FormattedPrompt) -> InferenceResult:
        """
        Run inference on formatted prompt.
        
        Args:
            formatted_prompt: Formatted prompt with image
            
        Returns:
            InferenceResult: Inference results with confidence
            
        Raises:
            PromptError: If inference fails
        """
        try:
            import time
            start_time = time.time()
            
            # Process inputs
            inputs = self.processor(
                images=formatted_prompt['image'],
                text=formatted_prompt['text'],
                return_tensors="pt"
            ).to(self.device)
            
            # Generate output
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9
                )
            
            # Process output
            result = self.processor.decode(outputs[0], skip_special_tokens=True)
            processed_result = self._process_result(result)
            
            # Calculate confidence
            confidence = self._calculate_confidence(processed_result)
            
            # Validate result
            if not formatted_prompt['validation_rules'].validate_result(processed_result):
                raise PromptError("Result validation failed")
            
            return InferenceResult(
                result=processed_result,
                confidence=confidence,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            raise PromptError(f"Failed to run inference: {str(e)}")
    
    def _process_result(self, raw_result: str) -> Dict[str, Any]:
        """Process raw model output into structured result."""
        try:
            # Parse JSON-like output
            # This is a simplified example - actual implementation would depend on model output format
            import json
            result = json.loads(raw_result)
            return result
            
        except Exception as e:
            raise PromptError(f"Failed to process result: {str(e)}")
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for result."""
        try:
            # This is a simplified example - actual implementation would depend on model capabilities
            if 'confidence' in result:
                return float(result['confidence'])
            return 0.8  # Default confidence
            
        except Exception as e:
            logging.error(f"Failed to calculate confidence: {str(e)}")
            return 0.0
    
    def cleanup(self):
        """Clean up model resources."""
        try:
            if hasattr(self, 'model'):
                del self.model
            if hasattr(self, 'processor'):
                del self.processor
            torch.cuda.empty_cache()
        except Exception as e:
            logging.error(f"Failed to cleanup: {str(e)}") 