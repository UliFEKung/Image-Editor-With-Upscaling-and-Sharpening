"""
Main application module for Image Editor.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, Scale
from PIL import Image

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from config import *
from drawing import draw_dot, erase_dot, pick_color_from_image
from image_ops import load_image, combine_images, resize_image_for_display, convert_to_tk_photo, save_image
from history import EditHistory
from upscaling import upscale_image, UpscaleMethod
from upscale_dialog import UpscaleDialog
from sharpening import sharpen_image, SharpenMethod
from sharpen_dialog import SharpenDialog


class ImageEditorApp:
    """Main Image Editor Application."""
    
    def __init__(self, root):
        """Initialize the application."""
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.config(padx=10, pady=10)
        self.root.resizable(True, True)
        
        # State variables
        self.current_image = None
        self.current_image_copy = None
        self.pencil_layer = None
        self.current_path = None
        self.current_zoom = 1.0
        self.current_tool = tk.StringVar(value="select")
        self.current_color = tk.StringVar(value=DEFAULT_COLOR)
        
        # Drawing state
        self.drawing = False
        self.last_x = 0
        self.last_y = 0
        self.scroll_x = 0.0
        self.scroll_y = 0.0
        
        # History
        self.history = EditHistory(MAX_HISTORY)
        
        # UI elements
        self.canvas = None
        self.image_item = None
        self.border_item = None
        self.canvas_text = None
        self.filename_label = None
        self.undo_btn = None
        self.redo_btn = None
        self.save_btn = None
        self.color_circle = None
        self.r_val = None
        self.g_val = None
        self.b_val = None
        self.brush_size = None
        
        # Build UI
        self.build_ui()
        
        # Bind events
        self.bind_events()
        
        # Setup drag and drop
        if DND_AVAILABLE:
            self.setup_dnd()
        
        # Show initial placeholder text
        self.update_image_display()
    
    def build_ui(self):
        """Build the user interface."""
        from ui import build_ui_components
        build_ui_components(self)
    
    def bind_events(self):
        """Bind all event handlers."""
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.canvas.bind('<Button-4>', lambda event: self.change_zoom(1, event))
        self.canvas.bind('<Button-5>', lambda event: self.change_zoom(-1, event))
        self.canvas.bind('<ButtonPress-2>', self.start_pan)
        self.canvas.bind('<B2-Motion>', self.pan_image)
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_press)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.root.bind('<F11>', self.toggle_fullscreen)
        
        # Keybinds
        self.root.bind('<Control-z>', lambda event: self.undo())
        self.root.bind('<Control-y>', lambda event: self.redo())
        self.root.bind('<Control-u>', lambda event: self.open_upscale_dialog())
        self.root.bind('<Control-h>', lambda event: self.open_sharpen_dialog())
        self.root.bind('<Control-s>', lambda event: self.save_image_file())
    
    def setup_dnd(self):
        """Setup drag and drop support."""
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.handle_drop)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode."""
        state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not state)
    
    def set_tool(self, tool_name):
        """Set the current drawing tool."""
        self.current_tool.set(tool_name)
        cursor = "crosshair" if tool_name != "select" else "arrow"
        self.canvas.config(cursor=cursor)
        self.update_filename_label()
    
    def update_image_display(self, keep_mouse_point=False, mouse_x=None, mouse_y=None, keep_scroll=False):
        """Update the canvas display."""
        if self.current_image_copy is None:
            # Display placeholder text when no image is loaded
            self.canvas.delete("all")
            self.canvas_text = self.canvas.create_text(
                CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2,
                text="Select an image file or drop one here.",
                anchor="center",
                font=("Arial", 14),
                fill="#666666"
            )
            self.canvas.configure(scrollregion=(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT))
            return
        
        # Save current scroll position if needed
        if keep_scroll:
            self.scroll_x = self.canvas.xview()[0]
            self.scroll_y = self.canvas.yview()[0]
        
        # Combine images
        display_img = combine_images(self.current_image_copy, self.pencil_layer)
        if display_img is None:
            return
        
        # Resize for display
        img = resize_image_for_display(display_img, self.current_zoom)
        
        # Get dimensions
        width = img.width
        height = img.height
        
        # Convert to PhotoImage
        self.canvas.delete("all")
        self.canvas_text = None
        
        photo = convert_to_tk_photo(img)
        
        # Calculate position to center the image if it's smaller than canvas
        if width <= CANVAS_WIDTH and height <= CANVAS_HEIGHT:
            # Image fits in canvas - center it
            x_offset = (CANVAS_WIDTH - width) // 2
            y_offset = (CANVAS_HEIGHT - height) // 2
            scroll_width = CANVAS_WIDTH
            scroll_height = CANVAS_HEIGHT
        else:
            # Image is larger than canvas - position at top-left
            x_offset = 0
            y_offset = 0
            scroll_width = width
            scroll_height = height
        
        self.image_item = self.canvas.create_image(x_offset, y_offset, image=photo, anchor="nw")
        self.canvas.image = photo  # Keep reference
        
        # Draw border around the entire canvas
        self.border_item = self.canvas.create_rectangle(
            1, 1, CANVAS_WIDTH - 1, CANVAS_HEIGHT - 1, width=0
        )
        
        # Configure scroll region
        self.canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))
        
        # Handle mouse point tracking
        if keep_mouse_point and mouse_x is not None and mouse_y is not None:
            img_x = int(mouse_x / self.current_zoom)
            img_y = int(mouse_y / self.current_zoom)
            img_x = max(0, min(img_x, self.current_image.width - 1))
            img_y = max(0, min(img_y, self.current_image.height - 1))
            
            if scroll_width > CANVAS_WIDTH:
                scroll_pos_x = img_x / (scroll_width - CANVAS_WIDTH) if scroll_width > CANVAS_WIDTH else 0
                self.canvas.xview_moveto(scroll_pos_x)
            if scroll_height > CANVAS_HEIGHT:
                scroll_pos_y = img_y / (scroll_height - CANVAS_HEIGHT) if scroll_height > CANVAS_HEIGHT else 0
                self.canvas.yview_moveto(scroll_pos_y)
        elif keep_scroll:
            # Restore scroll position
            self.canvas.xview_moveto(self.scroll_x)
            self.canvas.yview_moveto(self.scroll_y)
        else:
            # Center scroll position for centered images
            if width <= CANVAS_WIDTH and height <= CANVAS_HEIGHT:
                self.canvas.xview_moveto(0)
                self.canvas.yview_moveto(0)
            else:
                self.canvas.xview_moveto(0)
                self.canvas.yview_moveto(0)
        
        # Update filename label
        if self.current_path:
            zoom_pct = int(self.current_zoom * 100)
            tool = self.current_tool.get().upper()
            self.filename_label.config(
                text=f"{os.path.basename(self.current_path)}   Zoom: {zoom_pct}%   Tool: {tool}"
            )
        else:
            zoom_pct = int(self.current_zoom * 100)
            self.filename_label.config(text=f"Zoom: {zoom_pct}%")
    
    def display_image(self, path):
        """Load and display an image."""
        result = load_image(path)
        if result is None:
            return
        
        self.current_image, self.current_image_copy, self.pencil_layer, self.current_path = result
        self.history.reset(self.current_image_copy, self.pencil_layer)
        self.zoom_to_fit()  # Zoom to fit and center the image
        self.update_button_states()
    
    def change_zoom(self, delta, event=None):
        """Change zoom level."""
        if self.current_image is None:
            return
        
        self.current_zoom += delta * ZOOM_STEP
        self.current_zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.current_zoom))
        
        if event:
            self.update_image_display(keep_mouse_point=True, mouse_x=event.x, mouse_y=event.y)
        else:
            self.update_image_display()
    
    def zoom_to_fit(self):
        """Zoom image to fit the canvas."""
        if self.current_image is None:
            return
        
        # Calculate zoom level to fit image in canvas
        zoom_x = CANVAS_WIDTH / self.current_image.width
        zoom_y = CANVAS_HEIGHT / self.current_image.height
        
        # Use the smaller zoom to fit entire image
        self.current_zoom = min(zoom_x, zoom_y, MAX_ZOOM)
        self.current_zoom = max(self.current_zoom, MIN_ZOOM)
        
        # Center the image
        self.update_image_display()
    
    def update_filename_label(self):
        """Update the filename label with current status."""
        if self.current_path:
            zoom_pct = int(self.current_zoom * 100)
            tool = self.current_tool.get().upper()
            resolution = f"{self.current_image.width}x{self.current_image.height}" if self.current_image else ""
            self.filename_label.config(
                text=f"{os.path.basename(self.current_path)}   {resolution}   Zoom: {zoom_pct}%   Tool: {tool}"
            )
        else:
            zoom_pct = int(self.current_zoom * 100)
            tool = self.current_tool.get().upper()
            resolution = f"{self.current_image.width}x{self.current_image.height}" if self.current_image else ""
            self.filename_label.config(text=f"{resolution}   Zoom: {zoom_pct}%   Tool: {tool}")
    
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """
        Convert canvas coordinates to image coordinates.
        Accounts for zoom level, scroll position, and image centering.
        
        Args:
            canvas_x: X coordinate on canvas
            canvas_y: Y coordinate on canvas
        
        Returns:
            (image_x, image_y) tuple
        """
        if self.current_image is None:
            return canvas_x, canvas_y
        
        # Get scroll region dimensions
        try:
            scroll_region = self.canvas.cget('scrollregion').split()
            total_width = float(scroll_region[2])
            total_height = float(scroll_region[3])
        except (ValueError, IndexError):
            total_width = self.current_image.width * self.current_zoom if self.current_image else CANVAS_WIDTH
            total_height = self.current_image.height * self.current_zoom if self.current_image else CANVAS_HEIGHT
        
        # Calculate displayed image dimensions
        display_width = self.current_image.width * self.current_zoom
        display_height = self.current_image.height * self.current_zoom
        
        # Calculate centering offsets (same logic as update_image_display)
        if display_width <= CANVAS_WIDTH and display_height <= CANVAS_HEIGHT:
            # Image is centered
            x_offset = (CANVAS_WIDTH - display_width) // 2
            y_offset = (CANVAS_HEIGHT - display_height) // 2
        else:
            # Image is positioned at top-left
            x_offset = 0
            y_offset = 0
        
        # Get current scroll position in pixels
        view_x = self.canvas.xview()[0] * total_width
        view_y = self.canvas.yview()[0] * total_height
        
        # Adjust canvas coordinates for centering and scroll position
        adjusted_x = canvas_x - x_offset + view_x
        adjusted_y = canvas_y - y_offset + view_y
        
        # Convert to image coordinates
        image_x = int(adjusted_x / self.current_zoom)
        image_y = int(adjusted_y / self.current_zoom)
        
        # Clamp to image bounds
        image_x = max(0, min(image_x, self.current_image.width - 1))
        image_y = max(0, min(image_y, self.current_image.height - 1))
        
        return image_x, image_y
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scroll."""
        if event.delta > 0:
            self.change_zoom(1, event)
        else:
            self.change_zoom(-1, event)
    
    def open_image_file(self):
        """Open image file dialog."""
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=SUPPORTED_IMAGES
        )
        if path:
            self.display_image(path)
    
    def handle_drop(self, event):
        """Handle drag and drop."""
        if event.data:
            path = event.data
            if path.startswith('{') and path.endswith('}'):
                path = path[1:-1]
            path = path.strip()
            if os.path.isfile(path):
                self.display_image(path)
            else:
                messagebox.showwarning("Drop Image", "Please drop a valid file.")
    
    def start_pan(self, event):
        """Start panning."""
        self.canvas.scan_mark(event.x, event.y)
    
    def pan_image(self, event):
        """Pan image."""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def on_canvas_press(self, event):
        """Handle canvas press."""
        if self.current_image_copy is None:
            return
        
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
        
        # Convert to image coordinates
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        
        tool = self.current_tool.get()
        if tool == "dropper":
            self.pick_color(img_x, img_y)
        elif tool == "pencil":
            draw_dot(self.pencil_layer, img_x, img_y, self.current_color.get(), 
                    self.brush_size.get(), 1.0)
        elif tool == "eraser":
            erase_dot(self.pencil_layer, img_x, img_y, self.brush_size.get(), 1.0)
    
    def on_canvas_drag(self, event):
        """Handle canvas drag."""
        if not self.drawing or self.current_image_copy is None:
            return
        
        # Interpolate between points
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        distance = (dx**2 + dy**2)**0.5
        
        tool = self.current_tool.get()
        if distance > 0:
            steps = max(1, int(distance / 2))
            for i in range(steps + 1):
                canvas_x = self.last_x + (dx * i / steps)
                canvas_y = self.last_y + (dy * i / steps)
                
                # Convert to image coordinates
                img_x, img_y = self.canvas_to_image_coords(canvas_x, canvas_y)
                
                if tool == "pencil":
                    draw_dot(self.pencil_layer, img_x, img_y, self.current_color.get(),
                            self.brush_size.get(), 1.0)
                elif tool == "eraser":
                    erase_dot(self.pencil_layer, img_x, img_y, self.brush_size.get(), 1.0)
        
        self.last_x = event.x
        self.last_y = event.y
        self.update_image_display(keep_scroll=True)
    
    def on_canvas_release(self, event):
        """Handle canvas release."""
        if self.drawing:
            self.history.save_state(self.current_image_copy, self.pencil_layer)
            self.update_button_states()
        self.drawing = False
    
    def pick_color(self, img_x, img_y):
        """Pick color from image."""
        r, g, b = pick_color_from_image(self.current_image_copy, img_x, img_y, 1.0)
        self.r_val.set(r)
        self.g_val.set(g)
        self.b_val.set(b)
    
    def undo(self):
        """Undo last action."""
        state = self.history.undo()
        if state is not None:
            self.current_image_copy = state['base']
            self.pencil_layer = state['pencil']
            self.update_image_display()
            self.update_button_states()
    
    def redo(self):
        """Redo last undone action."""
        state = self.history.redo()
        if state is not None:
            self.current_image_copy = state['base']
            self.pencil_layer = state['pencil']
            self.update_image_display()
            self.update_button_states()
    
    def save_image_file(self):
        """Save edited image to file."""
        if self.current_image_copy is None or self.pencil_layer is None:
            messagebox.showwarning("Save Image", "No image to save.")
            return
        
        save_path = filedialog.asksaveasfilename(
            title="Save Edited Image",
            defaultextension=".png",
            filetypes=SAVE_FILETYPES
        )
        
        if save_path:
            save_image(self.current_image_copy, self.pencil_layer, save_path)
    
    def open_upscale_dialog(self):
        """Open the upscaling dialog."""
        if self.current_image_copy is None:
            messagebox.showwarning("Upscale Image", "Please load an image first.")
            return
        
        UpscaleDialog(self.root, self.perform_upscale, self.current_image_copy, self.pencil_layer)

    def open_sharpen_dialog(self):
        """Open the sharpening dialog."""
        if self.current_image_copy is None:
            messagebox.showwarning("Sharpen Image", "Please load an image first.")
            return
        
        SharpenDialog(self.root, self.perform_sharpen, self.current_image_copy, self.pencil_layer)
    
    def perform_upscale(self, scale_factor, method):
        """
        Perform image upscaling.
        
        Args:
            scale_factor: Factor to upscale by
            method: UpscaleMethod enum
        """
        try:
            # Save current state before upscaling
            self.history.save_state(self.current_image_copy, self.pencil_layer)
            
            # Show progress message
            messagebox.showinfo(
                "Upscaling",
                f"Upscaling image by {scale_factor}x using {method.value}...\n\nThis may take a moment."
            )
            
            # Combine current image state before upscaling
            current_display = combine_images(self.current_image_copy, self.pencil_layer)
            if current_display is None:
                messagebox.showerror("Upscale Image", "Failed to prepare image for upscaling.")
                return
            
            # Perform upscaling
            upscaled = upscale_image(current_display, scale_factor, method)
            
            # Update image dimensions
            self.current_zoom = 1.0
            
            # Split back into original and pencil layers (since we upscaled combined)
            # For now, we'll treat the entire upscaled image as the new base
            self.current_image = upscaled.convert("RGB")
            self.current_image_copy = self.current_image.copy()
            
            # Create new transparent pencil layer for upscaled image
            self.pencil_layer = Image.new("RGBA", upscaled.size, (0, 0, 0, 0))
            
            # Update display
            self.update_image_display()
            self.update_button_states()
            
            # Save the new state after successful upscaling
            self.history.save_state(self.current_image_copy, self.pencil_layer)
            
            messagebox.showinfo(
                "Upscale Complete",
                f"Image upscaled successfully!\n"
                f"New size: {self.current_image.width}x{self.current_image.height}"
            )
        except Exception as exc:
            messagebox.showerror("Upscale Error", f"Failed to upscale image:\n{exc}")

    def perform_sharpen(self, intensity, method):
        """
        Perform image sharpening.
        
        Args:
            intensity: Sharpen intensity factor
            method: SharpenMethod enum
        """
        try:
            # Save current state before sharpening
            self.history.save_state(self.current_image_copy, self.pencil_layer)
            
            messagebox.showinfo(
                "Sharpening",
                f"Applying {method.value} sharpening with intensity {intensity:.1f}...\n\nThis may take a moment."
            )

            current_display = combine_images(self.current_image_copy, self.pencil_layer)
            if current_display is None:
                messagebox.showerror("Sharpen Image", "Failed to prepare image for sharpening.")
                return

            sharpened = sharpen_image(current_display, intensity, method)
            self.current_zoom = 1.0

            self.current_image = sharpened.convert("RGB")
            self.current_image_copy = self.current_image.copy()
            self.pencil_layer = Image.new("RGBA", sharpened.size, (0, 0, 0, 0))

            # Update display
            self.update_image_display()
            self.update_button_states()

            # Save the new state after successful sharpening
            self.history.save_state(self.current_image_copy, self.pencil_layer)

            messagebox.showinfo(
                "Sharpen Complete",
                f"Sharpening complete!\nNew size: {self.current_image.width}x{self.current_image.height}"
            )
        except Exception as exc:
            messagebox.showerror("Sharpen Error", f"Failed to sharpen image:\n{exc}")
    
    def update_button_states(self):
        """Update button enabled/disabled states."""
        self.undo_btn.config(state="normal" if self.history.can_undo() else "disabled")
        self.redo_btn.config(state="normal" if self.history.can_redo() else "disabled")
        has_image = self.current_image_copy is not None
        self.save_btn.config(state="normal" if has_image else "disabled")
        self.upscale_btn.config(state="normal" if has_image else "disabled")
        self.sharpen_btn.config(state="normal" if has_image else "disabled")


def main():
    """Main entry point."""
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = ImageEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
