from pathlib import Path
from typing import List, Dict
import os

class PathValidationError(Exception):
    """Exception raised when path validation fails."""
    pass

class PathValidator:
    """Validates paths against security and project rules."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.max_path_length = 4096
    
    def validate_path(self, path: Path) -> Dict[str, bool]:
        """
        Validate a path against security and project rules.
        
        Args:
            path: Path to validate
            
        Returns:
            Dict containing validation results
            
        Raises:
            PathValidationError: If path is invalid
        """
        results = {
            "is_within_project": self._is_within_project(path),
            "no_parent_reference": self._no_parent_reference(path),
            "valid_length": self._valid_length(path),
            "valid_characters": self._valid_characters(path),
            "exists": path.exists()
        }
        
        if not all(results.values()):
            raise PathValidationError(
                f"Path validation failed: {path}\n"
                f"Results: {results}"
            )
        
        return results
    
    def _is_within_project(self, path: Path) -> bool:
        """Check if path is within project boundaries."""
        try:
            path.resolve().relative_to(self.project_root)
            return True
        except ValueError:
            return False
    
    def _no_parent_reference(self, path: Path) -> bool:
        """Check if path contains parent directory references."""
        return ".." not in path.parts
    
    def _valid_length(self, path: Path) -> bool:
        """Check if path length is within limits."""
        return len(str(path)) <= self.max_path_length
    
    def _valid_characters(self, path: Path) -> bool:
        """Check if path contains only valid characters."""
        # Basic check for common invalid characters
        invalid_chars = set('<>:"|?*')
        return not any(char in str(path) for char in invalid_chars)
    
    def validate_all_paths(self, paths: Dict[str, Path]) -> Dict[str, Dict[str, bool]]:
        """
        Validate all paths in a dictionary.
        
        Args:
            paths: Dictionary of path keys to Path objects
            
        Returns:
            Dictionary of validation results for each path
        """
        results = {}
        for key, path in paths.items():
            try:
                results[key] = self.validate_path(path)
            except PathValidationError as e:
                results[key] = {"error": str(e)}
        return results 