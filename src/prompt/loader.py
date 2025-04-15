from pathlib import Path
from typing import Dict, Optional, TypedDict, Any
import yaml
import logging
from src.path.repository import PathRepository, PathError

class PromptError(Exception):
    """Custom exception for prompt-related errors."""
    pass

class PromptTemplate(TypedDict):
    name: str
    description: str
    template: str
    field: str
    validation_rules: Dict[str, Any]

class PromptLoader:
    """Handles loading and validation of prompt templates."""
    
    def __init__(self):
        """Initialize prompt loader with path repository."""
        try:
            self.paths = PathRepository.get_instance()
            self.prompt_dir = self.paths.get_path("config") / "prompts"
            self._validate_prompt_dir()
        except Exception as e:
            raise PromptError(f"Failed to initialize PromptLoader: {str(e)}")
    
    def _validate_prompt_dir(self) -> None:
        """Validate prompt directory exists and is accessible."""
        try:
            if not self.prompt_dir.exists():
                self.prompt_dir.mkdir(parents=True, exist_ok=True)
            if not self.prompt_dir.is_dir():
                raise PromptError(f"Prompt directory is not a directory: {self.prompt_dir}")
        except Exception as e:
            raise PromptError(f"Failed to validate prompt directory: {str(e)}")
    
    def load_prompt(self, prompt_name: str) -> PromptTemplate:
        """
        Load and validate a prompt template.
        
        Args:
            prompt_name: Name of the prompt template to load
            
        Returns:
            PromptTemplate: Validated prompt template
            
        Raises:
            PromptError: If template loading or validation fails
        """
        try:
            # Construct prompt path
            prompt_path = self.prompt_dir / f"{prompt_name}.yaml"
            if not prompt_path.exists():
                raise PromptError(f"Prompt template not found: {prompt_path}")
            
            # Load prompt template
            template = self._load_template(prompt_path)
            
            # Validate template
            self._validate_template(template)
            
            return template
            
        except Exception as e:
            raise PromptError(f"Failed to load prompt {prompt_name}: {str(e)}")
    
    def _load_template(self, prompt_path: Path) -> Dict:
        """Load prompt template from YAML file."""
        try:
            with open(prompt_path) as f:
                template = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['name', 'description', 'template', 'field', 'validation_rules']
            for field in required_fields:
                if field not in template:
                    raise ValueError(f"Missing required field in template: {field}")
            
            return template
            
        except yaml.YAMLError as e:
            raise PromptError(f"Invalid YAML in prompt template: {str(e)}")
        except Exception as e:
            raise PromptError(f"Failed to load template: {str(e)}")
    
    def _validate_template(self, template: Dict) -> None:
        """Validate prompt template structure and content."""
        try:
            # Validate name
            if not isinstance(template['name'], str):
                raise ValueError("name must be a string")
            
            # Validate description
            if not isinstance(template['description'], str):
                raise ValueError("description must be a string")
            
            # Validate template format
            if not isinstance(template['template'], str):
                raise ValueError("template must be a string")
            if '[IMG]' not in template['template']:
                raise ValueError("template must contain [IMG] placeholder")
            
            # Validate field
            if not isinstance(template['field'], str):
                raise ValueError("field must be a string")
            
            # Validate validation rules
            if not isinstance(template['validation_rules'], dict):
                raise ValueError("validation_rules must be a dictionary")
            
            # Validate required validation fields
            required_rules = ['required_fields', 'field_types', 'min_confidence']
            for rule in required_rules:
                if rule not in template['validation_rules']:
                    raise ValueError(f"Missing required validation rule: {rule}")
            
        except Exception as e:
            raise PromptError(f"Template validation failed: {str(e)}")
    
    def list_available_prompts(self) -> Dict[str, str]:
        """List all available prompt templates."""
        try:
            prompts = {}
            for file in self.prompt_dir.glob("*.yaml"):
                try:
                    with open(file) as f:
                        template = yaml.safe_load(f)
                        prompts[file.stem] = template.get('description', 'No description')
                except Exception as e:
                    logging.error(f"Failed to load prompt {file}: {str(e)}")
                    continue
            return prompts
        except Exception as e:
            raise PromptError(f"Failed to list prompts: {str(e)}")
    
    def get_prompt_path(self, prompt_name: str) -> Path:
        """Get the path to a prompt template."""
        try:
            path = self.prompt_dir / f"{prompt_name}.yaml"
            if not path.exists():
                raise PromptError(f"Prompt template not found: {path}")
            return path
        except Exception as e:
            raise PromptError(f"Failed to get prompt path: {str(e)}") 