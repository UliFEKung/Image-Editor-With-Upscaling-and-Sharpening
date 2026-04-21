"""
Upscaling dialog for the Image Editor.
Provides UI for selecting upscaling method and scale factor.
"""

import tkinter as tk
from tkinter import messagebox, Scale, Checkbutton, Canvas, Scrollbar
from PIL import Image, ImageTk
from upscaling import UpscaleMethod, get_method_description, upscale_image
from image_ops import combine_images, resize_image_for_display, convert_to_tk_photo


class UpscaleDialog:
    """Dialog for configuring and performing image upscaling."""
    
    def __init__(self, parent, callback, current_image, pencil_layer):
        """
        Initialize upscale dialog.
        
        Args:
            parent: Parent Tkinter widget
            callback: Function to call with (scale_factor, method) on OK
        """
        self.callback = callback
        self.current_image = current_image
        self.pencil_layer = pencil_layer
        self.preview_enabled = tk.BooleanVar(value=True)
        
        # Preview state
        self.original_zoom = 1.0
        self.upscaled_zoom = 1.0
        self.zoom_level_var = tk.StringVar(value="compare")
        self.preview_scroll_x = 0.0
        self.preview_scroll_y = 0.0
        self.preview_image = None
        self.original_image = None
        
        # Pan state
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Preview cache
        self.cached_scale_factor = None
        self.cached_method = None
        self.cached_preview_image = None
        
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Upscale Image")
        self.dialog.geometry("700x950")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Build UI
        self.build_ui()
        self.on_zoom_level_change()  # Initialize zoom level
        self.update_previews()
        
        # Wait for dialog to close
        parent.wait_window(self.dialog)
    
    def build_ui(self):
        """Build the dialog UI."""
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
        
        # Upscaled image preview
        upscaled_frame = tk.LabelFrame(preview_container, text="Upscaled", padx=5, pady=5)
        upscaled_frame.pack(side="right", fill="both", expand=True, padx=5)
        
        # Upscaled resolution label
        self.upscaled_resolution_label = tk.Label(upscaled_frame, text="", font=("Arial", 10))
        self.upscaled_resolution_label.pack(anchor="w", padx=5, pady=2)
        
        # Create canvas container for upscaled
        upscaled_canvas_frame = tk.Frame(upscaled_frame)
        upscaled_canvas_frame.pack(fill="both", expand=True)
        
        # Configure grid for canvas and scrollbars
        upscaled_canvas_frame.grid_rowconfigure(0, weight=1)
        upscaled_canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.upscaled_canvas = Canvas(upscaled_canvas_frame, bg="gray", width=300, height=300)
        self.upscaled_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbars for upscaled
        upscaled_h_scroll = Scrollbar(upscaled_canvas_frame, orient="horizontal", command=self.upscaled_canvas.xview)
        upscaled_v_scroll = Scrollbar(upscaled_canvas_frame, orient="vertical", command=self.upscaled_canvas.yview)
        self.upscaled_canvas.configure(xscrollcommand=upscaled_h_scroll.set, yscrollcommand=upscaled_v_scroll.set)
        
        upscaled_h_scroll.grid(row=1, column=0, sticky="ew")
        upscaled_v_scroll.grid(row=0, column=1, sticky="ns")
        
        # Bind mouse events for upscaled canvas
        self.upscaled_canvas.bind("<MouseWheel>", lambda e: self.on_preview_zoom(e, "upscaled"))
        self.upscaled_canvas.bind("<ButtonPress-1>", lambda e: self.on_preview_pan_start(e, "upscaled"))
        self.upscaled_canvas.bind("<B1-Motion>", lambda e: self.on_preview_pan_motion(e, "upscaled"))
        self.upscaled_canvas.bind("<ButtonPress-2>", lambda e: self.on_preview_pan_start(e, "upscaled"))
        self.upscaled_canvas.bind("<B2-Motion>", lambda e: self.on_preview_pan_motion(e, "upscaled"))
        
        # Preview toggle (below canvas)
        preview_frame = tk.Frame(self.dialog)
        preview_frame.pack(fill="x", padx=10, pady=5)
        
        Checkbutton(preview_frame, text="Enable Preview", variable=self.preview_enabled, 
                   command=self.on_preview_toggle).pack(side="left")
        
        tk.Button(preview_frame, text="Zoom to Fit", command=self.zoom_previews_to_fit).pack(side="right", padx=5)
        
        # Control panel
        control_frame = tk.Frame(self.dialog)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Scale factor section
        scale_frame = tk.LabelFrame(control_frame, text="Scale Factor", padx=10, pady=10)
        scale_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(scale_frame, text="Upscale by factor of:").pack(anchor="w")
        
        scale_input_frame = tk.Frame(scale_frame)
        scale_input_frame.pack(fill="x", pady=5)
        
        self.scale_var = tk.DoubleVar(value=2.0)
        scale_slider = Scale(scale_input_frame, from_=1.5, to=4.0, orient="horizontal",
                            variable=self.scale_var, resolution=0.5,
                            command=self.on_scale_change)
        scale_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.scale_label = tk.Label(scale_input_frame, text="2.0x", width=5)
        self.scale_label.pack(side="right")
        
        self.scale_var.trace("w", self.update_scale_label)
        
        # Container frame for Method and Zoom Level sections side by side
        method_zoom_container = tk.Frame(control_frame)
        method_zoom_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Method selection section
        method_frame = tk.LabelFrame(method_zoom_container, text="Upscaling Method", padx=10, pady=10)
        method_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.method_var = tk.StringVar(value=UpscaleMethod.LANCZOS.value)
        
        for method in UpscaleMethod:
            tk.Radiobutton(method_frame, text=method.value,
                          variable=self.method_var, value=method.value,
                          command=self.on_method_change).pack(anchor="w")
        
        # Zoom level section for upscaled preview
        zoom_frame = tk.LabelFrame(method_zoom_container, text="Upscaled Preview Zoom", padx=10, pady=10)
        zoom_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        tk.Label(zoom_frame, text="Compare upscaled quality:").pack(anchor="w")
        
        self.zoom_level_var = tk.StringVar(value="compare")
        
        zoom_options_frame = tk.Frame(zoom_frame)
        zoom_options_frame.pack(fill="x", pady=5)
        
        tk.Radiobutton(zoom_options_frame, text="Compare (same size)", 
                      variable=self.zoom_level_var, value="compare",
                      command=self.on_zoom_level_change).pack(anchor="w")
        tk.Radiobutton(zoom_options_frame, text="Actual (100%)", 
                      variable=self.zoom_level_var, value="actual",
                      command=self.on_zoom_level_change).pack(anchor="w")
        tk.Radiobutton(zoom_options_frame, text="Detail (200%)", 
                      variable=self.zoom_level_var, value="detail",
                      command=self.on_zoom_level_change).pack(anchor="w")
        
        # Description
        desc_frame = tk.LabelFrame(control_frame, text="Method Description", padx=10, pady=10)
        desc_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.desc_label = tk.Label(desc_frame, text="", justify="left", wraplength=450)
        self.desc_label.pack(anchor="w")
        
        self.update_description()
        
        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(button_frame, text="Upscale", command=self.on_ok,
                 bg="#4CAF50", fg="white", padx=20).pack(side="right", padx=5)
        tk.Button(button_frame, text="Cancel", command=self.on_cancel, padx=20).pack(side="right")
    
    def update_scale_label(self, *args):
        """Update scale factor display."""
        scale = self.scale_var.get()
        self.scale_label.config(text=f"{scale:.1f}x")
        if self.preview_enabled.get():
            self.update_previews()
    
    def update_description(self):
        """Update method description."""
        method_name = self.method_var.get()
        for method in UpscaleMethod:
            if method.value == method_name:
                desc = get_method_description(method)
                self.desc_label.config(text=desc)
                break
    
    def on_scale_change(self, value):
        # Clear cache when scale factor changes
        self.cached_scale_factor = None
        self.cached_preview_image = None
        # Update zoom level since scale factor affects the compare zoom
        self.on_zoom_level_change()
    
    def on_method_change(self):
        # Clear cache when method changes
        self.cached_method = None
        self.cached_preview_image = None
        self.update_description()
        if self.preview_enabled.get():
            self.update_previews()
    
    def on_zoom_level_change(self):
        """Set upscaled zoom level to preset values based on selected zoom level and scale factor."""
        zoom_level = self.zoom_level_var.get()
        scale_factor = self.scale_var.get()
        
        if zoom_level == "compare":
            # Show upscaled image at apparent size of original (zoom = 1.0 / scale_factor)
            self.upscaled_zoom = 1.0 / scale_factor
        elif zoom_level == "actual":
            # Show upscaled image at 100% (actual upscaled size)
            self.upscaled_zoom = 1.0
        elif zoom_level == "detail":
            # Show upscaled image at 200% (for detail inspection)
            self.upscaled_zoom = 2.0
        
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
        scale_factor = self.scale_var.get()
        method_name = self.method_var.get()
        method = None
        for m in UpscaleMethod:
            if m.value == method_name:
                method = m
                break
        
        # Check if we can use cached image
        if (self.cached_preview_image is not None and
            self.cached_scale_factor == scale_factor and
            self.cached_method == method):
            self.preview_image = self.cached_preview_image
        else:
            # Process new image and cache it
            if method:
                self.preview_image = upscale_image(self.original_image, scale_factor, method)
            else:
                self.preview_image = self.original_image.copy()
            
            # Update cache
            self.cached_scale_factor = scale_factor
            self.cached_method = method
            self.cached_preview_image = self.preview_image
            
        # Update canvases
        self.update_preview_canvas(self.original_canvas, self.original_image, self.original_zoom)
        self.update_preview_canvas(self.upscaled_canvas, self.preview_image, self.upscaled_zoom)
        
        # Update resolution labels
        if self.original_image:
            self.original_resolution_label.config(text=f"{self.original_image.width}x{self.original_image.height}")
        if self.preview_image:
            self.upscaled_resolution_label.config(text=f"{self.preview_image.width}x{self.preview_image.height}")
    
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
        self.upscaled_canvas.delete("all")
    
    def zoom_previews_to_fit(self):
        """Zoom both previews to fit their canvases."""
        if not self.original_image:
            return
            
        # Calculate zoom to fit original image
        canvas_width = self.original_canvas.winfo_width() or 300
        canvas_height = self.original_canvas.winfo_height() or 300
        
        zoom_x = canvas_width / self.original_image.width
        zoom_y = canvas_height / self.original_image.height
        self.original_zoom = min(zoom_x, zoom_y, 1.0)  # Don't zoom above 100%
        
        # Calculate zoom to fit upscaled image
        if self.preview_image:
            zoom_x = canvas_width / self.preview_image.width
            zoom_y = canvas_height / self.preview_image.height
            self.upscaled_zoom = min(zoom_x, zoom_y, 1.0)  # Don't zoom above 100%
        
        self.update_previews()
    
    def on_preview_zoom(self, event, canvas_type):
        """Handle mouse wheel zoom on preview canvases with linked zoom."""
        # Apply zoom to both canvases (linked zoom)
        if event.delta > 0:
            self.original_zoom *= 1.1
            self.upscaled_zoom *= 1.1
        else:
            self.original_zoom /= 1.1
            self.upscaled_zoom /= 1.1
        
        # Clamp zoom levels
        self.original_zoom = max(0.1, min(self.original_zoom, 5.0))
        self.upscaled_zoom = max(0.1, min(self.upscaled_zoom, 5.0))
        
        self.update_previews()
    
    def on_preview_pan_start(self, event, canvas_type):
        """Start panning on preview canvas."""
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_preview_pan_motion(self, event, canvas_type):
        """Handle panning motion on preview canvas with linked movement."""
        canvas = self.original_canvas if canvas_type == "original" else self.upscaled_canvas
        other_canvas = self.upscaled_canvas if canvas_type == "original" else self.original_canvas
        
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
        """Handle OK button."""
        # Clear cache when applying
        self.cached_scale_factor = None
        self.cached_method = None
        self.cached_preview_image = None
        
        scale_factor = self.scale_var.get()
        method_name = self.method_var.get()
        
        # Find matching method enum
        for method in UpscaleMethod:
            if method.value == method_name:
                self.callback(scale_factor, method)
                break
        
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle Cancel button."""
        self.dialog.destroy()
