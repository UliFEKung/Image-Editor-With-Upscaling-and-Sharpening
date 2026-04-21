"""
Configuration and constants for Image Editor application.
"""

# Window settings
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 850
WINDOW_TITLE = "Image Editor With Upscaling and Sharpening"

# Canvas settings
CANVAS_WIDTH = 520
CANVAS_HEIGHT = 420

# Zoom settings
MIN_ZOOM = 0.01
MAX_ZOOM = 5.0
ZOOM_STEP = 0.05

# History settings
MAX_HISTORY = 50

# Color settings
DEFAULT_COLOR = "#FF0000"
DEFAULT_R = 255
DEFAULT_G = 0
DEFAULT_B = 0

# Brush settings
DEFAULT_BRUSH_SIZE = 5
MIN_BRUSH_SIZE = 1
MAX_BRUSH_SIZE = 50

# File types
SUPPORTED_IMAGES = [
    ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
    ("PNG files", "*.png"),
    ("JPEG files", "*.jpg"),
    ("All files", "*.*"),
]

SAVE_FILETYPES = [
    ("PNG files", "*.png"),
    ("JPEG files", "*.jpg"),
    ("All files", "*.*"),
]
