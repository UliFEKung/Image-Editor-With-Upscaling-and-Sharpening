"""
Image operations for the Image Editor.
"""

from PIL import Image, ImageTk
import os
from tkinter import messagebox


def load_image(path):
    """
    Load an image from file.
    
    Args:
        path: Path to image file
    
    Returns:
        Tuple of (original_image, working_copy, pencil_layer, path) or None on error
    """
    try:
        img = Image.open(path).convert("RGB")
        img_copy = img.copy()
        pencil_layer = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
        return (img, img_copy, pencil_layer, path)
    except Exception as exc:
        messagebox.showerror("Open Image", f"Unable to open image:\n{exc}")
        return None


def combine_images(original_image, pencil_layer):
    """
    Combine original image with pencil layer.
    
    Args:
        original_image: PIL Image
        pencil_layer: PIL Image RGBA layer
    
    Returns:
        Combined PIL Image
    """
    if original_image is None:
        return None
    
    combined = original_image.copy()
    if pencil_layer is not None:
        combined.paste(pencil_layer, (0, 0), pencil_layer)
    return combined


def resize_image_for_display(image, zoom_level):
    """
    Resize image for display based on zoom level.
    
    Args:
        image: PIL Image
        zoom_level: Zoom factor
    
    Returns:
        Resized PIL Image
    """
    width = max(1, int(image.width * zoom_level))
    height = max(1, int(image.height * zoom_level))
    return image.resize((width, height), Image.LANCZOS)


def convert_to_tk_photo(image):
    """
    Convert PIL Image to Tkinter PhotoImage.
    
    Args:
        image: PIL Image
    
    Returns:
        ImageTk.PhotoImage
    """
    return ImageTk.PhotoImage(image)


def save_image(original_image, pencil_layer, save_path):
    """
    Save the edited image to file.
    
    Args:
        original_image: PIL Image
        pencil_layer: PIL Image RGBA layer
        save_path: Path to save to
    
    Returns:
        True if successful, False otherwise
    """
    try:
        combined = combine_images(original_image, pencil_layer)
        if combined:
            combined.save(save_path)
            messagebox.showinfo("Save Image", f"Image saved to {save_path}")
            return True
    except Exception as exc:
        messagebox.showerror("Save Image", f"Failed to save image:\n{exc}")
    return False


def get_image_filename(path):
    """Get filename from path."""
    return os.path.basename(path) if path else ""
