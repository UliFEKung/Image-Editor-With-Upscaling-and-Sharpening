"""
Drawing operations for the Image Editor.
"""

from PIL import ImageDraw


def draw_dot(pencil_layer, x, y, color, size, current_zoom):
    """
    Draw a circle dot on the pencil layer.
    
    Args:
        pencil_layer: PIL Image RGBA layer for pencil strokes
        x: Image x coordinate (already converted from canvas)
        y: Image y coordinate (already converted from canvas)
        color: Hex color string (e.g., "#FF0000")
        size: Brush size in canvas pixels
        current_zoom: Current zoom level (use 1.0 if coords already converted)
    """
    if pencil_layer is None:
        return
    
    # If zoom is provided, convert canvas coords to image coords
    if current_zoom != 1.0:
        img_x = int(x / current_zoom)
        img_y = int(y / current_zoom)
        radius = int(size / 2 / current_zoom) or 1
    else:
        img_x = x
        img_y = y
        radius = size // 2 or 1
    
    draw = ImageDraw.Draw(pencil_layer)
    draw.ellipse(
        [(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
        fill=color + "FF"
    )


def erase_dot(pencil_layer, x, y, size, current_zoom):
    """
    Erase a circle area from the pencil layer.
    
    Args:
        pencil_layer: PIL Image RGBA layer for pencil strokes
        x: Image x coordinate (already converted from canvas)
        y: Image y coordinate (already converted from canvas)
        size: Eraser size in canvas pixels
        current_zoom: Current zoom level (use 1.0 if coords already converted)
    """
    if pencil_layer is None:
        return
    
    # If zoom is provided, convert canvas coords to image coords
    if current_zoom != 1.0:
        img_x = int(x / current_zoom)
        img_y = int(y / current_zoom)
        radius = int(size / 2 / current_zoom) or 1
    else:
        img_x = x
        img_y = y
        radius = size // 2 or 1
    
    draw = ImageDraw.Draw(pencil_layer)
    draw.ellipse(
        [(img_x - radius, img_y - radius), (img_x + radius, img_y + radius)],
        fill=(0, 0, 0, 0)
    )


def pick_color_from_image(image, x, y, current_zoom):
    """
    Pick a color from the image at given coordinates.
    
    Args:
        image: PIL Image to sample from
        x: Image x coordinate (already converted from canvas)
        y: Image y coordinate (already converted from canvas)
        current_zoom: Current zoom level (use 1.0 if coords already converted)
    
    Returns:
        Tuple of (r, g, b) values
    """
    if image is None:
        return (0, 0, 0)
    
    # If zoom is provided, convert canvas coords to image coords
    if current_zoom != 1.0:
        img_x = int(x / current_zoom)
        img_y = int(y / current_zoom)
    else:
        img_x = x
        img_y = y
    
    img_x = max(0, min(img_x, image.width - 1))
    img_y = max(0, min(img_y, image.height - 1))
    
    pixel = image.getpixel((img_x, img_y))
    
    if isinstance(pixel, tuple):
        r, g, b = pixel[:3]
    else:
        r = g = b = pixel
    
    return (r, g, b)
