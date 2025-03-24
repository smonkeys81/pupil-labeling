import os
import sys
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import os
import inspect

# Check OS
if os.name == "nt":  # Windows 
    print("This program runs at Linux(Ubuntu) only.")
    sys.exit(1)

local_mount = "/home/jayden/repo/dataset/pupil/face_crop_v1.5/v1.51/train/aimmo_0"

class LabelTool:
    def __init__(self, root):
        """ """
        print(inspect.currentframe().f_code.co_name)

        self.root = root
        self.root.title("Pupil Labeling Tool Ver. 0.1")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.image_folder = os.path.join(local_mount, "blind_png")
        self.label_folder = os.path.join(local_mount, "total_txt")
        self.image_list = self.load_images()

        self.initial_scale = 4.0
        self.scale_factor = self.initial_scale
        self.markers = []
        self.pos_origin = []

        # Initialize the image canvas variable to avoid AttributeError
        self.image_on_canvas = None

        self.init_ui()
    
    def on_closing(self):
        """ """
        print(inspect.currentframe().f_code.co_name)

        self.root.destroy()  # Terminate Tkinter window
        self.root.quit()

    def load_images(self):
        print(inspect.currentframe().f_code.co_name)

        images = []
        for root, _, files in os.walk(self.image_folder):
            for f in files:
                if f.endswith((".png", ".jpg")):
                    images.append(os.path.relpath(os.path.join(root, f), self.image_folder))
        return images
    def init_ui(self):
        print(inspect.currentframe().f_code.co_name)
        
        # Set initial window size
        self.root.geometry("1200x1024")

        # Configure grid weights to allow resizing
        self.root.grid_rowconfigure(1, weight=1)  # Main content row
        self.root.grid_columnconfigure(1, weight=1)  # Main content column

        # Left frame (Image list)
        self.frame_left = tk.Frame(self.root, width=250, bg="lightgray")
        self.frame_left.grid(row=0, column=0, rowspan=3, sticky="ns")  # Occupies full height (north-south)

        self.listbox = tk.Listbox(self.frame_left, width=40)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        self.scrollbar = tk.Scrollbar(self.frame_left, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        for img in self.image_list:
            self.listbox.insert(tk.END, img)

        self.listbox.bind("<<ListboxSelect>>", self.load_selected_image)

        # Top control frame (Save, Reset buttons)
        self.frame_controls = tk.Frame(self.root, bg="darkgray")
        self.frame_controls.grid(row=0, column=1, sticky="ew")

        self.btn_reset = tk.Button(self.frame_controls, text="Reset", command=self.reset_labels)
        self.btn_reset.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_save = tk.Button(self.frame_controls, text="Save", command=self.save_labels)
        self.btn_save.pack(side=tk.LEFT, padx=5, pady=5)

        # Main frame (Image display)
        self.frame_main = tk.Frame(self.root, bg="white")
        self.frame_main.grid(row=1, column=1, sticky="nsew")  # Expands in all directions

        self.canvas = tk.Canvas(self.frame_main, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<MouseWheel>", self.zoom_image)  # Windows, Mac
        self.canvas.bind("<Button-4>", lambda event: self.zoom_image(event, direction=1))  # Linux Scroll Up
        self.canvas.bind("<Button-5>", lambda event: self.zoom_image(event, direction=-1))  # Linux Scroll Down

        # Bottom frame (Image size and coordinates)
        self.frame_bottom = tk.Frame(self.root, bg="darkgray")
        self.frame_bottom.grid(row=2, column=1, sticky="ew")

        self.label_image_size = tk.Label(self.frame_bottom, text="Image Size:")
        self.label_image_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_coordinates = tk.Label(self.frame_bottom, text="Coordinates:")
        self.label_coordinates.pack(side=tk.LEFT, padx=5, pady=5)

    def update_image_info(self):
        """Update the image size and coordinates in the bottom frame."""
        
        img_size_text = f"Image Size: {self.img_w} x {self.img_h}"
        self.label_image_size.config(text=img_size_text)

    def update_coord_info(self):
        if self.label_data:
            coords_text = f"Coordinates: R({self.label_data[0]:.3f}, {self.label_data[1]:.3f}), L({self.label_data[2]:.3f}, {self.label_data[3]:.3f})"
            self.label_coordinates.config(text=coords_text)
        else:
            self.label_coordinates.config(text="Coordinates: N/A")


    def load_selected_image(self, event):
        """ """

        selection = self.listbox.curselection()
        if not selection:
            return
        
        img_name = self.image_list[selection[0]]
        img_path = os.path.join(self.image_folder, img_name)
        label_path = os.path.join(self.label_folder, os.path.splitext(img_name)[0] + ".txt")
        print(f'  {img_path}')
        print(f'  {label_path}')
        
        self.image = Image.open(img_path).convert("RGB")
        self.img_w, self.img_h = self.image.size

        self.scale_factor = self.initial_scale
        
        self.load_labels(label_path)

        self.display_image()        
        
    def display_image(self):
        """ """

        new_size = (int(self.img_w * self.scale_factor), int(self.img_h * self.scale_factor))
        self.resized_image = self.image.resize(new_size, Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.resized_image)

        # Remove the previous image and markers
        if self.image_on_canvas:
            self.canvas.delete(self.image_on_canvas)

        # Draw the image first
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        # Update scroll region
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        self.update_markers()

        self.update_image_info()
        self.update_coord_info()
    
    def zoom_image(self, event, direction=None):
        """ """

        scale_step = 0.1
    
        if direction is not None:  
            if direction > 0:  # Scroll Up
                self.scale_factor *= 1.1
            elif direction < 0:  # Scroll Down
                self.scale_factor /= 1.1
        else:
            if event.delta > 0:  # Scroll Up (Windows, Mac)
                self.scale_factor *= 1.1
            elif event.delta < 0:  # Scroll Down
                self.scale_factor /= 1.1

        self.display_image()
    
    def load_labels(self, label_path):
        """ """

        if not os.path.exists(label_path):
            print("Unable to locate file:", label_path)
            return
        
        with open(label_path, "r") as f:
            data = list(map(float, f.readline().split()))
        
        print(f'  {data}')
        self.label_data = [data[0] * self.img_w, data[1] * self.img_h,  # eye_right
                           data[2] * self.img_w, data[3] * self.img_h,
                           data[4], data[5]]  # eye_left
        
        # Clear markers if they exist
        if hasattr(self, "markers"):
            for marker in self.markers:
                self.canvas.delete(marker)
        else:
            self.markers = []

        if hasattr(self, "pos_origin"):
            self.pos_origin.clear()
        else:
            self.pos_origin = []

        self.pos_origin.append((self.label_data[0], self.label_data[1]))  # eye_right
        self.pos_origin.append((self.label_data[2], self.label_data[3]))  # eye_left

    def update_markers(self):
        """Draw markers after image is properly displayed."""

        if self.markers:
            for marker in self.markers:
                self.canvas.delete(marker)
            self.markers.clear()

        data = self.label_data
        
        eye_right = (data[0] * self.scale_factor, data[1] * self.scale_factor) 
        eye_left = (data[2] * self.scale_factor, data[3] * self.scale_factor)
        
        self.markers.clear()  # Clear previous markers

        rad = 5
        self.markers.append(self.canvas.create_oval(
            eye_right[0] - rad, eye_right[1] - rad, eye_right[0] + rad, eye_right[1] + rad,
            outline="red", width=2))
        self.markers.append(self.canvas.create_oval(
            eye_left[0] - rad, eye_left[1] - rad, eye_left[0] + rad, eye_left[1] + rad,
            outline="blue", width=2))

        # Allow markers to be dragged
        self.canvas.tag_bind(self.markers[0], "<B1-Motion>", lambda event: self.move_marker(event, 0))
        self.canvas.tag_bind(self.markers[1], "<B1-Motion>", lambda event: self.move_marker(event, 1))

    def move_marker(self, event, index):
        """Move the marker and update its position relative to the scale factor."""
        #print(inspect.currentframe().f_code.co_name)        
        #print(f"  Event: {event.x}, {event.y}")
        self.canvas.coords(self.markers[index], event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        
        self.label_data[index*2] = event.x / self.scale_factor
        self.label_data[index*2 + 1] = event.y / self.scale_factor

        self.update_coord_info()

    def save_labels(self):
        if not self.label_data:
            return

        new_label_data = [self.label_data[0] / self.img_w, 
                          self.label_data[1] / self.img_h,
                          self.label_data[2] / self.img_w,
                          self.label_data[3] / self.img_h,
                          self.label_data[4], 
                          self.label_data[5]]
        
        img_name = self.listbox.get(tk.ACTIVE)
        label_path = os.path.join(self.label_folder, os.path.splitext(img_name)[0] + ".txt")
        
        with open(label_path, "w") as f:
            print(f'  (update) {new_label_data}')
            f.write(" ".join(map(str, new_label_data)))
        
        messagebox.showinfo("Success", "Labels saved successfully!")

        #update original
        self.pos_origin.clear()
        self.pos_origin.append((self.label_data[0], self.label_data[1]))  # eye_right
        self.pos_origin.append((self.label_data[2], self.label_data[3]))  # eye_left
    
    def reset_labels(self):
        """Reset marker positions based on the original positions and current scale."""
        if not self.pos_origin:
            return
        
        # Restore original positions adjusted to the current scale
        self.label_data[0], self.label_data[1] = self.pos_origin[0]  # eye_right
        self.label_data[2], self.label_data[3] = self.pos_origin[1]  # eye_left

        self.update_markers()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = LabelTool(root)
    root.mainloop()
