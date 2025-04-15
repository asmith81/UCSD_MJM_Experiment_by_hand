from typing import Dict, List, TypedDict
import ipywidgets as widgets
from IPython.display import display, Markdown

class PromptConfig(TypedDict):
    field: str
    prompt: str
    quantization: str

class PromptConfigurationManager:
    """Manages the configuration state and UI for prompt execution."""
    
    def __init__(self):
        self.field_options = ['invoice_number', 'date', 'total_amount', 'vendor_name']
        self.prompt_options = ['basic_extraction', 'detailed', 'few_shot', 'step_by_step', 'locational']
        self.quantization_options = ['bfloat16', 'int8', 'int4']
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create configuration widgets."""
        self.field_dropdown = widgets.Dropdown(
            options=self.field_options,
            value=self.field_options[0],
            description='Field to Extract:',
            style={'description_width': 'initial'}
        )
        
        self.prompt_dropdown = widgets.Dropdown(
            options=self.prompt_options,
            value=self.prompt_options[0],
            description='Prompt Template:',
            style={'description_width': 'initial'}
        )
        
        self.quantization_dropdown = widgets.Dropdown(
            options=self.quantization_options,
            value=self.quantization_options[0],
            description='Quantization:',
            style={'description_width': 'initial'}
        )
    
    def display(self):
        """Display the configuration interface."""
        display(Markdown("### 🛠️ Configuration"))
        display(Markdown("Select your extraction settings:"))
        display(self.field_dropdown)
        display(self.prompt_dropdown)
        display(self.quantization_dropdown)
    
    def get_config(self) -> PromptConfig:
        """Get the current configuration."""
        return {
            'field': self.field_dropdown.value,
            'prompt': self.prompt_dropdown.value,
            'quantization': self.quantization_dropdown.value
        } 