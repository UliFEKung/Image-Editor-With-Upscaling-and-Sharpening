"""
UI component creation for Image Editor.
"""

import tkinter as tk
from tkinter import Scale
from config import *

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


def build_ui_components(app):
    """Build all UI components for the application."""
    root = app.root
    
    # Main frames
    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)
    
    left_frame = tk.Frame(main_frame)
    left_frame.pack(side="left", anchor="n", padx=(0, 10))
    
    # Canvas area
    image_box = tk.LabelFrame(left_frame, text="Canvas", bd=2, relief="groove")
    image_box.pack(fill="both", padx=0, pady=0)
    
    app.canvas = tk.Canvas(
        image_box, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
        bg="#f8f8f8", highlightthickness=0, cursor="crosshair"
    )
    app.canvas.pack(fill="both", expand=True)
    
    # Canvas control frame (between canvas and tools)
    canvas_control_frame = tk.Frame(left_frame, bg="#e8e8e8")
    canvas_control_frame.pack(fill="x", pady=(5, 5), padx=0)
    
    tk.Button(canvas_control_frame, text="Select Image", command=app.open_image_file).pack(side="left", padx=2, pady=3)
    tk.Button(canvas_control_frame, text="🔍 Zoom to Fit", command=app.zoom_to_fit).pack(side="left", padx=2, pady=3)
    
    app.undo_btn = tk.Button(canvas_control_frame, text="↶ Undo", command=app.undo, state="disabled")
    app.undo_btn.pack(side="left", padx=2, pady=3)
    
    app.redo_btn = tk.Button(canvas_control_frame, text="↷ Redo", command=app.redo, state="disabled")
    app.redo_btn.pack(side="left", padx=2, pady=3)
    
    # Tools frame
    tools_frame = tk.LabelFrame(left_frame, text="Tools", bd=2, relief="groove", padx=5, pady=5)
    tools_frame.pack(fill="x", pady=(0, 0))
    
    tk.Button(tools_frame, text="✏️ Pencil", 
             command=lambda: app.set_tool("pencil"), width=10).grid(row=0, column=0, padx=2, pady=2)
    tk.Button(tools_frame, text="🧹 Eraser",
             command=lambda: app.set_tool("eraser"), width=10).grid(row=0, column=1, padx=2, pady=2)
    tk.Button(tools_frame, text="🎨 Dropper",
             command=lambda: app.set_tool("dropper"), width=10).grid(row=0, column=2, padx=2, pady=2)
    
    tk.Label(tools_frame, text="Brush Size:").grid(row=1, column=0, sticky="w", padx=2, pady=(5, 0))
    
    app.brush_size = tk.IntVar(value=DEFAULT_BRUSH_SIZE)
    Scale(tools_frame, from_=MIN_BRUSH_SIZE, to=MAX_BRUSH_SIZE,
         orient="horizontal", variable=app.brush_size).grid(row=1, column=1, columnspan=2, sticky="ew", padx=2)
    
    # Color frame
    color_frame = tk.LabelFrame(left_frame, text="Color Selection", bd=2, relief="groove", padx=5, pady=5)
    color_frame.pack(fill="x", pady=(10, 0))
    
    rgb_frame = tk.Frame(color_frame)
    rgb_frame.pack(fill="x", expand=True)
    
    app.r_val = tk.IntVar(value=DEFAULT_R)
    app.g_val = tk.IntVar(value=DEFAULT_G)
    app.b_val = tk.IntVar(value=DEFAULT_B)
    
    def update_rgb(*args):
        r = app.r_val.get()
        g = app.g_val.get()
        b = app.b_val.get()
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        app.current_color.set(hex_color)
        app.color_circle.delete("all")
        app.color_circle.create_oval(2, 2, 48, 48, fill=hex_color, outline="#000", width=2)
    
    app.r_val.trace("w", update_rgb)
    app.g_val.trace("w", update_rgb)
    app.b_val.trace("w", update_rgb)
    
    tk.Label(rgb_frame, text="R:").grid(row=0, column=0, sticky="w", padx=2)
    Scale(rgb_frame, from_=0, to=255, orient="horizontal", variable=app.r_val,
         bg="red", fg="white", length=120).grid(row=0, column=1, sticky="ew", padx=2)
    
    app.color_circle = tk.Canvas(rgb_frame, width=50, height=50, bg="white", relief="solid", bd=1)
    app.color_circle.grid(row=0, column=2, padx=(10, 2), rowspan=3)
    app.color_circle.create_oval(2, 2, 48, 48, fill=DEFAULT_COLOR, outline="#000", width=2)
    
    tk.Label(rgb_frame, text="G:").grid(row=1, column=0, sticky="w", padx=2)
    Scale(rgb_frame, from_=0, to=255, orient="horizontal", variable=app.g_val,
         bg="green", fg="white", length=120).grid(row=1, column=1, sticky="ew", padx=2)
    
    tk.Label(rgb_frame, text="B:").grid(row=2, column=0, sticky="w", padx=2)
    Scale(rgb_frame, from_=0, to=255, orient="horizontal", variable=app.b_val,
         bg="blue", fg="white", length=120).grid(row=2, column=1, sticky="ew", padx=2)
    
    # Right panel
    right_frame = tk.Frame(main_frame, bg="#f5f5f5")
    right_frame.pack(side="left", fill="both", expand=True, padx=0, pady=0)
    
    info_text = (
        "Instructions:\n"
        "- Select or drop an image to edit.\n"
        "- Use mouse wheel to zoom.\n"
        "- Use middle-click drag to pan.\n"
        "- Select a tool and click/drag on image.\n"
        "- Eraser only affects pencil strokes.\n"
        "- Use RGB sliders or dropper to change color.\n"
        "- Ctrl+Z: Undo, Ctrl+Y: Redo\n"
        "- Ctrl+U: Open upscale dialog\n"
        "- Ctrl+H: Open sharpen dialog\n"
        "- Ctrl+S: Save image\n"
        "- Press F11 for fullscreen."
    )
    
    info_label = tk.Label(right_frame, text=info_text, justify="left",
                         bg="#f5f5f5", anchor="nw", padx=5, pady=5)
    info_label.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Status bar
    app.filename_label = tk.Label(root, text="", anchor="w")
    app.filename_label.pack(fill="x", padx=5, pady=(10, 5))
    
    # Button bar
    button_frame = tk.Frame(root)
    button_frame.pack(fill="x", pady=(0, 5))
    
    app.save_btn = tk.Button(button_frame, text="💾 Save", command=app.save_image_file, state="disabled")
    app.save_btn.pack(side="right")

    app.sharpen_btn = tk.Button(button_frame, text="🛠️ Sharpen", command=app.open_sharpen_dialog, state="disabled")
    app.sharpen_btn.pack(side="right", padx=(0, 5))
    
    app.upscale_btn = tk.Button(button_frame, text="📈 Upscale", command=app.open_upscale_dialog, state="disabled")
    app.upscale_btn.pack(side="right", padx=(0, 5))
    
    supported_text = "Drag and drop is available." if DND_AVAILABLE else "Drag and drop not available (install tkinterdnd2)."
    support_label = tk.Label(button_frame, text=supported_text, anchor="e")
    support_label.pack(side="right", padx=(10, 0))
