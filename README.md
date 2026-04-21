# Image Editor Application

A feature-rich image editor built with Tkinter and PIL (Pillow).

## Features

- **Image Editing**: Load and edit images with pencil and eraser tools
- **Color Picker**: RGB sliders and color dropper tool
- **Zoom & Pan**: Mouse wheel zoom with mouse-following, middle-click pan
- **Undo/Redo**: Full history support with up to 50 steps
- **Drag & Drop**: Support for drag and drop image loading (requires tkinterdnd2)
- **Fullscreen Mode**: Press F11 to toggle fullscreen
- **Export**: Save edited images as PNG or JPEG

## Project Structure

```
├── main.py              # Main application entry point
├── config.py            # Configuration and constants
├── drawing.py           # Drawing operations (pencil, eraser, dropper)
├── image_ops.py         # Image manipulation operations
├── history.py           # Undo/redo history management
├── ui.py                # UI component building
└── requirements.txt     # Python dependencies
```

## Installation

1. Install required packages:
```bash
pip install Pillow
pip install tkinterdnd2  # Optional: for drag and drop support
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### Keyboard Shortcuts

- **F11**: Toggle fullscreen mode
- **Mouse Wheel**: Zoom in/out (follows mouse position)
- **Middle Click + Drag**: Pan the image
- **Left Click + Drag**: Draw with selected tool

### Tools

1. **Pencil**: Draw colored dots on the image (selected color from RGB sliders)
2. **Eraser**: Remove pencil strokes (doesn't affect original image)
3. **Dropper**: Sample colors from the image

### Color Selection

- Use RGB sliders to select a color
- Use the dropper tool to sample colors from the image
- The color circle displays the current selected color

## Code Organization

The application is organized into functional modules:

- **main.py**: Main `ImageEditorApp` class containing all logic
- **config.py**: Constants and configuration defaults
- **drawing.py**: Low-level drawing functions
- **image_ops.py**: Image loading, saving, and manipulation
- **history.py**: `EditHistory` class for undo/redo management
- **ui.py**: UI component creation and layout

This modular structure makes the code maintainable and allows easy addition of new features.

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- Pillow
- tkinterdnd2 (optional, for drag and drop)
