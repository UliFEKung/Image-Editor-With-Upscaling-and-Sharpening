"""
Sharpening dialog for the Image Editor.
Provides UI for selecting sharpening method and intensity.
"""

import tkinter as tk
from tkinter import Scale, Checkbutton, Canvas, Scrollbar
from PIL import Image, ImageTk
from sharpening import SharpenMethod, get_method_description, sharpen_image
from image_ops import combine_images, resize_image_for_display, convert_to_tk_photo


class SharpenDialog:
    """Dialog for configuring and performing image sharpening."""

    def __init__(self, parent, callback, current_image, pencil_layer):
        self.callback = callback
        self.current_image = current_image
        self.pencil_layer = pencil_layer
        self.preview_enabled = tk.BooleanVar(value=True)
        
        # Preview state
        self.original_zoom = 1.0
        self.sharpened_zoom = 1.0
        self.preview_scroll_x = 0.0
        self.preview_scroll_y = 0.0
        self.preview_image = None
        self.original_image = None
        
        # Pan state
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Preview cache
        self.cached_intensity = None
        self.cached_method = None
        self.cached_preview_image = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Sharpen Image")
        self.dialog.geometry("700x850")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self.build_ui()
        self.update_previews()
        parent.wait_window(self.dialog)

    def build_ui(self):
        # Preview canvases
        preview_container = tk.Frame(self.dialog)
        preview_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Original image preview
        original_frame = tk.LabelFrame(preview_container, text="Original", padx=5, pady=5)
        original_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # Original resolution label
        self.original_resolution_label = tk.Label(original_frame, text="", font=("Arial", 10))
        self.original_resolution_label.pack(anchor="w", padx=5, pady=2)
        
        # Create canvas container for original
        original_canvas_frame = tk.Frame(original_frame)
        original_canvas_frame.pack(fill="both", expand=True)
        
        # Configure grid for canvas and scrollbars
        original_canvas_frame.grid_rowconfigure(0, weight=1)
        original_canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.original_canvas = Canvas(original_canvas_frame, bg="gray", width=300, height=300)
        self.original_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbars for original
        original_h_scroll = Scrollbar(original_canvas_frame, orient="horizontal", command=self.original_canvas.xview)
        original_v_scroll = Scrollbar(original_canvas_frame, orient="vertical", command=self.original_canvas.yview)
        self.original_canvas.configure(xscrollcommand=original_h_scroll.set, yscrollcommand=original_v_scroll.set)
        
        original_h_scroll.grid(row=1, column=0, sticky="ew")
        original_v_scroll.grid(row=0, column=1, sticky="ns")
        
        # Bind mouse events for original canvas
        self.original_canvas.bind("<MouseWheel>", lambda e: self.on_preview_zoom(e, "original"))
        self.original_canvas.bind("<ButtonPress-1>", lambda e: self.on_preview_pan_start(e, "original"))
        self.original_canvas.bind("<B1-Motion>", lambda e: self.on_preview_pan_motion(e, "original"))
        self.original_canvas.bind("<ButtonPress-2>", lambda e: self.on_preview_pan_start(e, "original"))
        self.original_canvas.bind("<B2-Motion>", lambda e: self.on_preview_pan_motion(e, "original"))
        
        # Sharpened image preview
        sharpened_frame = tk.LabelFrame(preview_container, text="Sharpened", padx=5, pady=5)
        sharpened_frame.pack(side="right", fill="both", expand=True, padx=5)
        
        # Sharpened resolution label
        self.sharpened_resolution_label = tk.Label(sharpened_frame, text="", font=("Arial", 10))
        self.sharpened_resolution_label.pack(anchor="w", padx=5, pady=2)
        
        # Create canvas container for sharpened
        sharpened_canvas_frame = tk.Frame(sharpened_frame)
        sharpened_canvas_frame.pack(fill="both", expand=True)
        
        # Configure grid for canvas and scrollbars
        sharpened_canvas_frame.grid_rowconfigure(0, weight=1)
        sharpened_canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.sharpened_canvas = Canvas(sharpened_canvas_frame, bg="gray", width=300, height=300)
        self.sharpened_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbars for sharpened
        sharpened_h_scroll = Scrollbar(sharpened_canvas_frame, orient="horizontal", command=self.sharpened_canvas.xview)
        sharpened_v_scroll = Scrollbar(sharpened_canvas_frame, orient="vertical", command=self.sharpened_canvas.yview)
        self.sharpened_canvas.configure(xscrollcommand=sharpened_h_scroll.set, yscrollcommand=sharpened_v_scroll.set)
        
        sharpened_h_scroll.grid(row=1, column=0, sticky="ew")
        sharpened_v_scroll.grid(row=0, column=1, sticky="ns")
        
        # Bind mouse events for sharpened canvas
        self.sharpened_canvas.bind("<MouseWheel>", lambda e: self.on_preview_zoom(e, "sharpened"))
        self.sharpened_canvas.bind("<ButtonPress-1>", lambda e: self.on_preview_pan_start(e, "sharpened"))
        self.sharpened_canvas.bind("<B1-Motion>", lambda e: self.on_preview_pan_motion(e, "sharpened"))
        self.sharpened_canvas.bind("<ButtonPress-2>", lambda e: self.on_preview_pan_start(e, "sharpened"))
        self.sharpened_canvas.bind("<B2-Motion>", lambda e: self.on_preview_pan_motion(e, "sharpened"))
        
        # Preview toggle (below canvas)
        preview_frame = tk.Frame(self.dialog)
        preview_frame.pack(fill="x", padx=10, pady=5)
        
        Checkbutton(preview_frame, text="Enable Preview", variable=self.preview_enabled, 
                   command=self.on_preview_toggle).pack(side="left")
        
        tk.Button(preview_frame, text="Zoom to Fit", command=self.zoom_previews_to_fit).pack(side="right", padx=5)
        
        # Control panel
        control_frame = tk.Frame(self.dialog)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Intensity controls
        intensity_frame = tk.LabelFrame(control_frame, text="Intensity", padx=10, pady=10)
        intensity_frame.pack(fill="x", pady=(0, 10))

        tk.Label(intensity_frame, text="Sharpen intensity:").pack(anchor="w")
        self.intensity_var = tk.DoubleVar(value=1.5)

        intensity_input_frame = tk.Frame(intensity_frame)
        intensity_input_frame.pack(fill="x", pady=5)

        self.intensity_slider = Scale(intensity_input_frame, from_=0.5, to=3.0, orient="horizontal",
                                      variable=self.intensity_var, resolution=0.1,
                                      command=self.on_intensity_change)
        self.intensity_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.intensity_label = tk.Label(intensity_input_frame, text="1.5")
        self.intensity_label.pack(side="right")
        self.intensity_var.trace("w", self.update_intensity_label)

        # Method selection
        method_frame = tk.LabelFrame(control_frame, text="Sharpening Method", padx=10, pady=10)
        method_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.method_var = tk.StringVar(value=SharpenMethod.UNSHARP_MASK.value)

        for method in SharpenMethod:
            tk.Radiobutton(method_frame, text=method.value,
                          variable=self.method_var, value=method.value,
                          command=self.on_method_change).pack(anchor="w")

        # Description
        desc_frame = tk.LabelFrame(control_frame, text="Method Description", padx=10, pady=10)
        desc_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.desc_label = tk.Label(desc_frame, text="", justify="left", wraplength=450)
        self.desc_label.pack(anchor="w")
        self.update_description()

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(button_frame, text="Apply", command=self.on_ok,
                  bg="#4CAF50", fg="white", padx=20).pack(side="right", padx=5)
        tk.Button(button_frame, text="Cancel", command=self.on_cancel, padx=20).pack(side="right")

    def update_intensity_label(self, *args):
        self.intensity_label.config(text=f"{self.intensity_var.get():.1f}")
        if self.preview_enabled.get():
            self.update_previews()

    def update_description(self):
        method_name = self.method_var.get()
        for method in SharpenMethod:
            if method.value == method_name:
                self.desc_label.config(text=get_method_description(method))
                break

    def on_intensity_change(self, value):
        # Clear cache when intensity changes
        self.cached_intensity = None
        self.cached_preview_image = None
        if self.preview_enabled.get():
            self.update_previews()

    def on_method_change(self):
        # Clear cache when method changes
        self.cached_method = None
        self.cached_preview_image = None
        self.update_description()
        if self.preview_enabled.get():
            self.update_previews()

    def on_preview_toggle(self):
        if self.preview_enabled.get():
            self.update_previews()
        else:
            self.clear_previews()

    def update_previews(self):
        """Update both preview canvases with caching."""
        if not self.current_image:
            return
            
        # Prepare original image
        self.original_image = combine_images(self.current_image, self.pencil_layer)
        if self.original_image is None:
            return
            
        # Get current parameters
        intensity = self.intensity_var.get()
        method_name = self.method_var.get()
        method = None
        for m in SharpenMethod:
            if m.value == method_name:
                method = m
                break
        
        # Check if we can use cached image
        if (self.cached_preview_image is not None and
            self.cached_intensity == intensity and
            self.cached_method == method):
            self.preview_image = self.cached_preview_image
        else:
            # Process new image and cache it
            if method:
                self.preview_image = sharpen_image(self.original_image, intensity, method)
            else:
                self.preview_image = self.original_image.copy()
            
            # Update cache
            self.cached_intensity = intensity
            self.cached_method = method
            self.cached_preview_image = self.preview_image
            
        # Update canvases
        self.update_preview_canvas(self.original_canvas, self.original_image, self.original_zoom)
        self.update_preview_canvas(self.sharpened_canvas, self.preview_image, self.sharpened_zoom)
        
        # Update resolution labels
        if self.original_image:
            self.original_resolution_label.config(text=f"{self.original_image.width}x{self.original_image.height}")
        if self.preview_image:
            self.sharpened_resolution_label.config(text=f"{self.preview_image.width}x{self.preview_image.height}")

    def update_preview_canvas(self, canvas, image, zoom_level):
        """Update a single preview canvas."""
        if image is None:
            canvas.delete("all")
            return
            
        # Resize for display
        display_img = resize_image_for_display(image, zoom_level)
        
        # Convert to PhotoImage
        canvas.delete("all")
        photo = convert_to_tk_photo(display_img)
        
        # Calculate position to center the image
        canvas_width = canvas.winfo_width() or 300
        canvas_height = canvas.winfo_height() or 300
        
        if display_img.width <= canvas_width and display_img.height <= canvas_height:
            # Center small images
            x_offset = (canvas_width - display_img.width) // 2
            y_offset = (canvas_height - display_img.height) // 2
            scroll_width = canvas_width
            scroll_height = canvas_height
        else:
            # Large images
            x_offset = 0
            y_offset = 0
            scroll_width = display_img.width
            scroll_height = display_img.height
        
        canvas.create_image(x_offset, y_offset, image=photo, anchor="nw")
        canvas.image = photo
        canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))

    def clear_previews(self):
        """Clear both preview canvases."""
        self.original_canvas.delete("all")
        self.sharpened_canvas.delete("all")

    def zoom_previews_to_fit(self):
        """Zoom both previews to fit their canvases."""
        if not self.original_image:
            return
            
        # Calculate zoom to fit both images
        canvas_width = self.original_canvas.winfo_width() or 300
        canvas_height = self.original_canvas.winfo_height() or 300
        
        zoom_x = canvas_width / self.original_image.width
        zoom_y = canvas_height / self.original_image.height
        self.original_zoom = min(zoom_x, zoom_y, 1.0)  # Don't zoom above 100%
        self.sharpened_zoom = self.original_zoom  # Start with same zoom level
        
        self.update_previews()

    def on_preview_zoom(self, event, canvas_type):
        """Handle mouse wheel zoom on preview canvases with linked zoom."""
        # Apply zoom to both canvases (linked zoom)
        if event.delta > 0:
            self.original_zoom *= 1.1
            self.sharpened_zoom *= 1.1
        else:
            self.original_zoom /= 1.1
            self.sharpened_zoom /= 1.1
        
        # Clamp zoom levels
        self.original_zoom = max(0.1, min(self.original_zoom, 5.0))
        self.sharpened_zoom = max(0.1, min(self.sharpened_zoom, 5.0))
        
        self.update_previews()

    def on_preview_pan_start(self, event, canvas_type):
        """Start panning on preview canvas."""
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_preview_pan_motion(self, event, canvas_type):
        """Handle panning motion on preview canvas with linked movement."""
        canvas = self.original_canvas if canvas_type == "original" else self.sharpened_canvas
        other_canvas = self.sharpened_canvas if canvas_type == "original" else self.original_canvas
        
        # Calculate pixel movement
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        # Update pan start position
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        # Get current scroll positions
        x_view = canvas.xview()
        y_view = canvas.yview()
        
        # Get scroll region dimensions
        scroll_region = canvas.cget('scrollregion').split()
        if scroll_region and len(scroll_region) >= 4:
            total_width = float(scroll_region[2])
            total_height = float(scroll_region[3])
            
            if total_width > 0 and total_height > 0:
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                
                # Convert pixel movement to scroll position
                if canvas_width > 0:
                    new_x = max(0, min(1, x_view[0] - (dx / total_width)))
                else:
                    new_x = x_view[0]
                    
                if canvas_height > 0:
                    new_y = max(0, min(1, y_view[0] - (dy / total_height)))
                else:
                    new_y = y_view[0]
                
                # Apply pan to both canvases
                canvas.xview_moveto(new_x)
                canvas.yview_moveto(new_y)
                other_canvas.xview_moveto(new_x)
                other_canvas.yview_moveto(new_y)

    def on_ok(self):
        # Clear cache when applying
        self.cached_intensity = None
        self.cached_method = None
        self.cached_preview_image = None
        
        intensity = self.intensity_var.get()
        method_name = self.method_var.get()
        for method in SharpenMethod:
            if method.value == method_name:
                self.callback(intensity, method)
                break
        self.dialog.destroy()

    def on_cancel(self):
        self.dialog.destroy()
