from pathlib import Path
from typing import Dict, List, Any, Generator, Optional
import logging
from PIL import Image
from src.path.repository import PathRepository, PathError
from src.prompt.loader import PromptLoader, PromptError
from src.prompt.formatter import PromptFormatter
from src.model.loader import ModelLoader

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Handles batch processing of images with a model."""
    
    def __init__(self, model_path: Path):
        """
        Initialize batch processor.
        
        Args:
            model_path: Path to model directory
            
        Raises:
            PathError: If paths are invalid
        """
        try:
            self.paths = PathRepository.get_instance()
            self.model_path = model_path
            
            # Initialize components
            self.prompt_loader = PromptLoader()
            self.prompt_formatter = PromptFormatter()
            self.model_loader = ModelLoader(model_path)
            
        except Exception as e:
            raise PathError(f"Failed to initialize BatchProcessor: {str(e)}")
    
    def process_images(
        self,
        image_dir: Path,
        prompt_name: str,
        quantization: str = "bfloat16"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process all images in directory with specified prompt.
        
        Args:
            image_dir: Directory containing images
            prompt_name: Name of prompt template to use
            quantization: Model quantization option
            
        Yields:
            Dict containing results for each image
            
        Raises:
            PathError: If image directory is invalid
            PromptError: If prompt loading fails
        """
        try:
            # Validate image directory
            if not image_dir.exists() or not image_dir.is_dir():
                raise PathError(f"Invalid image directory: {image_dir}")
            
            # Load prompt template
            template = self.prompt_loader.load_prompt(prompt_name)
            
            # Load model
            model_dict = self.model_loader.load_model(quantization)
            
            try:
                # Process each image
                for image_path in image_dir.glob("*.jpg"):
                    try:
                        # Format prompt with image
                        formatted_prompt = self.prompt_formatter.format_prompt(
                            template,
                            image_path
                        )
                        
                        # Run inference
                        inputs = model_dict['processor'](
                            images=formatted_prompt['image'],
                            text=formatted_prompt['text'],
                            return_tensors="pt"
                        ).to(model_dict['device'])
                        
                        with torch.no_grad():
                            outputs = model_dict['model'].generate(
                                **inputs,
                                max_new_tokens=512,
                                do_sample=True,
                                temperature=0.7,
                                top_p=0.9
                            )
                        
                        # Process output
                        result = model_dict['processor'].decode(
                            outputs[0],
                            skip_special_tokens=True
                        )
                        
                        yield {
                            'status': 'success',
                            'filename': image_path.name,
                            'result': result,
                            'processing_time': 0.0  # TODO: Add timing
                        }
                        
                    except Exception as e:
                        logger.error(f"Failed to process {image_path.name}: {str(e)}")
                        yield {
                            'status': 'error',
                            'filename': image_path.name,
                            'error': str(e)
                        }
            
            finally:
                # Cleanup model resources
                self.model_loader.cleanup(model_dict)
            
        except Exception as e:
            raise PromptError(f"Batch processing failed: {str(e)}")
    
    def process_and_log(
        self,
        image_dir: Path,
        prompt_name: str,
        quantization: str = "bfloat16",
        log_file: Optional[Path] = None
    ) -> None:
        """
        Process images and log results.
        
        Args:
            image_dir: Directory containing images
            prompt_name: Name of prompt template to use
            quantization: Model quantization option
            log_file: Optional path to log file
        """
        try:
            # Set up logging
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.INFO)
                logger.addHandler(file_handler)
            
            # Process images
            for result in self.process_images(image_dir, prompt_name, quantization):
                if result['status'] == 'success':
                    logger.info(f"Processed {result['filename']}: {result['result']}")
                else:
                    logger.error(f"Failed {result['filename']}: {result['error']}")
            
        finally:
            if log_file and 'file_handler' in locals():
                logger.removeHandler(file_handler) 