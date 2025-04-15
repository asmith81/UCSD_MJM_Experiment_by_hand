import unittest
from unittest.mock import patch, MagicMock, call
from src.prompt.config import PromptConfigurationManager, PromptConfig

class TestPromptConfigurationManager(unittest.TestCase):
    """Test cases for PromptConfigurationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = PromptConfigurationManager()
    
    def test_initialization(self):
        """Test that the manager initializes with correct options."""
        self.assertEqual(list(self.config_manager.field_options), 
                        ['invoice_number', 'date', 'total_amount', 'vendor_name'])
        self.assertEqual(list(self.config_manager.prompt_options),
                        ['basic_extraction', 'detailed', 'few_shot', 'step_by_step', 'locational'])
        self.assertEqual(list(self.config_manager.quantization_options),
                        ['bfloat16', 'int8', 'int4'])
    
    def test_widget_creation(self):
        """Test that widgets are created with correct properties."""
        # Test field dropdown
        self.assertEqual(list(self.config_manager.field_dropdown.options), 
                        list(self.config_manager.field_options))
        self.assertEqual(self.config_manager.field_dropdown.value,
                        self.config_manager.field_options[0])
        self.assertEqual(self.config_manager.field_dropdown.description,
                        'Field to Extract:')
        
        # Test prompt dropdown
        self.assertEqual(list(self.config_manager.prompt_dropdown.options),
                        list(self.config_manager.prompt_options))
        self.assertEqual(self.config_manager.prompt_dropdown.value,
                        self.config_manager.prompt_options[0])
        self.assertEqual(self.config_manager.prompt_dropdown.description,
                        'Prompt Template:')
        
        # Test quantization dropdown
        self.assertEqual(list(self.config_manager.quantization_dropdown.options),
                        list(self.config_manager.quantization_options))
        self.assertEqual(self.config_manager.quantization_dropdown.value,
                        self.config_manager.quantization_options[0])
        self.assertEqual(self.config_manager.quantization_dropdown.description,
                        'Quantization:')
    
    def test_display(self):
        """Test the display method."""
        with patch('IPython.display.display') as mock_display, \
             patch('IPython.display.Markdown') as mock_markdown:
            
            # Set up mock markdown to return itself
            mock_markdown.side_effect = lambda x: x
            
            # Call display method
            self.config_manager.display()
            
            # Verify markdown creation calls
            mock_markdown.assert_has_calls([
                call("### 🛠️ Configuration"),
                call("Select your extraction settings:")
            ])
            
            # Verify display was called 5 times (2 markdown + 3 widgets)
            self.assertEqual(mock_display.call_count, 5)
            
            # Verify the order of display calls
            mock_display.assert_has_calls([
                call("### 🛠️ Configuration"),
                call("Select your extraction settings:"),
                call(self.config_manager.field_dropdown),
                call(self.config_manager.prompt_dropdown),
                call(self.config_manager.quantization_dropdown)
            ])
    
    def test_get_config(self):
        """Test getting configuration returns correct structure."""
        config = self.config_manager.get_config()
        
        # Verify t