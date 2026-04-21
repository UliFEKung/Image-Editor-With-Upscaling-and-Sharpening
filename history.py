"""
Undo/Redo history management for the Image Editor.
"""


class EditHistory:
    """Manages undo/redo history for all editing operations."""
    
    def __init__(self, max_history=50):
        """
        Initialize history manager.
        
        Args:
            max_history: Maximum number of states to keep
        """
        self.history = []
        self.index = -1
        self.max_history = max_history
    
    def save_state(self, base_image, pencil_layer):
        """
        Save current image state to history.
        
        Args:
            base_image: PIL Image base layer
            pencil_layer: PIL Image RGBA pencil layer
        """
        if base_image is None or pencil_layer is None:
            return
        
        # Remove any redo states
        self.history = self.history[:self.index + 1]
        
        # Add current state
        self.history.append({
            'base': base_image.copy(),
            'pencil': pencil_layer.copy()
        })
        self.index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.index -= 1
    
    def undo(self):
        """
        Undo last action.
        
        Returns:
            Dict with 'base' and 'pencil' keys or None
        """
        if self.index > 0:
            self.index -= 1
            state = self.history[self.index]
            return {
                'base': state['base'].copy(),
                'pencil': state['pencil'].copy()
            }
        return None
    
    def redo(self):
        """
        Redo last undone action.
        
        Returns:
            Dict with 'base' and 'pencil' keys or None
        """
        if self.index < len(self.history) - 1:
            self.index += 1
            state = self.history[self.index]
            return {
                'base': state['base'].copy(),
                'pencil': state['pencil'].copy()
            }
        return None
    
    def can_undo(self):
        """Check if undo is available."""
        return self.index > 0
    
    def can_redo(self):
        """Check if redo is available."""
        return self.index < len(self.history) - 1
    
    def reset(self, base_image, pencil_layer):
        """
        Reset history with an initial state.
        
        Args:
            base_image: Initial base image
            pencil_layer: Initial pencil layer
        """
        self.history = [{
            'base': base_image.copy(),
            'pencil': pencil_layer.copy()
        }]
        self.index = 0
