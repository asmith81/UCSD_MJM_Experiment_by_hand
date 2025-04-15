from pathlib import Path
from typing import Dict, Any
import logging
from src.prompt.loader import PromptLoader, PromptError
from src.prompt.formatter import PromptFormatter
from src.prompt.runner import PromptRunner

logger = logging.getLogger(__name__)

class PromptPipeline:
    """Handles the complete prompt execution pipeline."""
    
    def __init__(self, model_path: Path):
        """
        Initialize the prompt pipeline.
        
        Args:
            model_path: Path to the model directory
        """
        self.model_path = model_path
        self.loader = PromptLoader()
        self.formatter = PromptFormatter()
        self.runner = PromptRunner(model_path)
    
    def run(self, prompt_name: str, image_path: Path) -> Dict[str, Any]:
        """
        Run the complete prompt pipeline.
        
        Args:
            prompt_name: Name of the prompt template to use
            image_path: Path to the input image
            
        Returns:
            Dict containing pipeline results and metadata
        """
        try:
            # Load prompt template
            logger.info(f"Loading prompt template: {prompt_name}")
            template = self.loader.load_prompt(prompt_name)
            
            # Format prompt with image
            logger.info(f"Formatting prompt with image: {image_path}")
            formatted_prompt = self.formatter.format_prompt(template, image_path)
            
            # Run inference
            logger.info("Running inference...")
            result = self.runner.run_inference(formatted_prompt)
            
            return {
                'status': 'success',
                'result': result['result'],
                'confidence': result['confidence'],
                'processing_time': result['processing_time']
            }
            
        except PromptError as e:
            logger.error(f"Prompt pipeline error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'status': 'error',
                'error': f"Unexpected error: {str(e)}"
            }
    
    def cleanup(self):
        """Clean up resources."""
        self.runner.cleanup() 