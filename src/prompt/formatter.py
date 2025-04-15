from pathlib import Path
from typing import Dict, Optional, TypedDict, Any
import logging
from PIL import Image
from src.path.repository import PathRepository, PathError
from src.prompt.loader import PromptTemplate, PromptError

class FormattedPrompt(TypedDict):
    text: str
    image: Image.Image
    validation_rules: Dict[str, Any]

class PromptFormatter:
    """Handles formatting prompts with images and validation."""
    
    def __init__(self):
        """Initialize prompt formatter with path repository."""
        try:
            self.paths = PathRepository.get_instance()
        except Exception as e:
            raise PromptError(f"Failed to initialize PromptFormatter: {str(e)}")
    
    def format_prompt(self, template: PromptTemplate, image_path: Path) -> FormattedPrompt:
        """
        Format a prompt template with an image.
        
        Args:
            template: Prompt template to format
            image_path: Path to the image to include
            
        Returns:
            FormattedPrompt: Formatted prompt with image
            
        Raises:
            PromptError: If formatting fails
        """
        try:
            # Load and validate image
            image = self._load_image(image_path)
            
            # Format prompt text
            formatted_text = self._format_text(template['template'])
            
            return FormattedPrompt(
                text=formatted_text,
                image=image,
                validation_rules=template['validation_rules']
            )
            
        except Exception as e:
            raise PromptError(f"Failed to format prompt: {str(e)}")
    
    def _load_image(self, image_path: Path) -> Image.Image:
        """Load and validate image file."""
        try:
            # Validate image path
            if not image_path.exists():
                raise PromptError(f"Image not found: {image_path}")
            
            # Load image
            image = Image.open(image_path)
            
            # Validate image format
            if image.format not in ['JPEG', 'PNG']:
                raise PromptError(f"Unsupported image format: {image.format}")
            
            # Validate image size
            max_size = (4032, 3024)  # From config
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                raise PromptError(f"Image too large: {image.size}")
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            raise PromptError(f"Failed to load image: {str(e)}")
    
    def _format_text(self, template: str) -> str:
        """Format prompt text with image placeholder."""
        try:
            # Validate template format
            if '[IMG]' not in template:
                raise PromptError("Template must contain [IMG] placeholder")
            
            # Replace image placeholder with actual image reference
            # In practice, this would be handled by the model's processor
            return template
            
        except Exception as e:
            raise PromptError(f"Failed to format text: {str(e)}")
    
    def validate_result(self, result: Dict[str, Any], validation_rules: Dict[str, Any]) -> bool:
        """
        Validate extraction result against rules.
        
        Args:
            result: Extraction result to validate
            validation_rules: Rules to validate against
            
        Returns:
            bool: True if validation passes
        """
        try:
            # Check required fields
            for field in validation_rules['required_fields']:
                if field not in result:
                    logging.error(f"Missing required field: {field}")
                    return False
            
            # Check field types
            for field, expected_type in validation_rules['field_types'].items():
                if field in result:
                    if not self._validate_type(result[field], expected_type):
                        logging.error(f"Invalid type for field {field}: {type(result[field])}")
                        return False
            
            # Check confidence
            if 'confidence' in result:
                if result['confidence'] < validation_rules['min_confidence']:
                    logging.error(f"Confidence too low: {result['confidence']}")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Validation failed: {str(e)}")
            return False
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type matches expected type."""
        try:
            if expected_type == 'string':
                return isinstance(value, str)
            elif expected_type == 'float':
                return isinstance(value, (float, int))
            elif expected_type == 'integer':
                return isinstance(value, int)
            else:
                logging.error(f"Unknown type: {expected_type}")
                return False
        except Exception as e:
            logging.error(f"Type validation failed: {str(e)}")
            return False 