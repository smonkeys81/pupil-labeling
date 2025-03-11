import os
import sys
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import os


# Check OS
if os.name == "nt":  # Windows 
    print("This program runs at Linux(Ubuntu) only.")
    sys.exit(1)

# Mount remote folder by using SSHFS
remote_server = "127.0.0.1"
remote_path = "/dataset/pupil/face_crop/"
#local_mount = "/home/jayden/mnt/svr_ko"
local_mount = "/mnt/svr_ko"
os.system(f"sshfs jayden@{remote_server}:{remote_path} {local_mount}")

class LabelTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Labeling Tool")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.image_folder = os.path.join(local_mount, "blind_png")
        self.label_folder = os.path.join(local_mount, "total_txt")
        self.image_list = self.load_images()
        
        self.scale_factor = 2.0
        
        self.init_ui()
    
    def on_closing(self):
        self.root.destroy()  # Terminate Tkinter window
        os.system(f"fusermount -u {local_mount}")  # unmount SSHFS
        self.root.quit()

    def load_images(self):
        images = []
        for root, _, files in os.walk(self.image_folder):
            for f in files:
                if f.endswith((".png", ".jpg")):
                    images.append(os.path.relpath(os.path.join(root, f), self.image_folder))
        return images
    
    def init_ui(self):
        self.frame_left = tk.Frame(self.root, width=250)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y)
        
        self.listbox = tk.Listbox(self.frame_left, width=40)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        self.scrollbar = tk.Scrollbar(self.frame_left, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        
        for img in self.image_list:
            self.listbox.insert(tk.END, img)
        
        self.listbox.bind("<<ListboxSelect>>", self.load_selected_image)
        
        self.frame_main = tk.Frame(self.root)
        self.frame_main.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        self.canvas = tk.Canvas(self.frame_main, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        self.canvas.bind("<MouseWheel>", self.zoom_image)  # Windows, Mac
        self.canvas.bind("<Button-4>", lambda event: self.zoom_image(event, direction=1))  # Linux Scroll Up
        self.canvas.bind("<Button-5>", lambda event: self.zoom_image(event, direction=-1))  # Linux Scroll Down

        
        self.btn_save = tk.Button(self.frame_main, text="Save", command=self.save_labels)
        self.btn_save.pack(side=tk.LEFT)
        
        self.btn_reset = tk.Button(self.frame_main, text="Reset", command=self.reset_labels)
        self.btn_reset.pack(side=tk.RIGHT)
        
        self.current_image = None
        self.image_on_canvas = None
        self.label_data = None
        self.markers = []
        self.original_positions = []
    
    def load_selected_image(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        
        img_name = self.image_list[selection[0]]
        img_path = os.path.join(self.image_folder, img_name)
        label_path = os.path.join(self.label_folder, os.path.splitext(img_name)[0] + ".txt")
        
        self.current_image = Image.open(img_path).convert("RGB")
        self.scale_factor = 1.0
        
        self.display_image()
        self.load_labels(label_path)
        
    def display_image(self):
        width, height = self.current_image.size
        new_size = (int(width * self.scale_factor), int(height * self.scale_factor))
        self.resized_image = self.current_image.resize(new_size, Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.resized_image)
        
        self.canvas.delete("all")
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
    
    def zoom_image(self, event, direction=None):
        scale_step = 0.1
    
        # Ubuntu에서는 direction 인자를 사용, Windows/Mac에서는 event.delta 사용
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
        if not os.path.exists(label_path):
            return
        
        with open(label_path, "r") as f:
            data = list(map(float, f.readline().split()))
        
        self.label_data = data
        img_w, img_h = self.current_image.size
        
        self.markers.clear()
        self.original_positions.clear()
        
        eye_right = (data[0] * img_w, data[1] * img_h)
        eye_left = (data[2] * img_w, data[3] * img_h)
        
        self.markers.append(self.canvas.create_text(*eye_right, text="X", fill="red", font=("Arial", 12, "bold")))
        self.markers.append(self.canvas.create_text(*eye_left, text="X", fill="blue", font=("Arial", 12, "bold")))
        
        self.original_positions.append(eye_right)
        self.original_positions.append(eye_left)
        
        self.canvas.tag_bind(self.markers[0], "<B1-Motion>", lambda event: self.move_marker(event, 0))
        self.canvas.tag_bind(self.markers[1], "<B1-Motion>", lambda event: self.move_marker(event, 1))
    
    def move_marker(self, event, index):
        self.canvas.coords(self.markers[index], event.x, event.y)
    
    def save_labels(self):
        if not self.label_data:
            return
        
        img_w, img_h = self.current_image.size
        new_positions = [
            self.canvas.coords(self.markers[0]),
            self.canvas.coords(self.markers[1])
        ]
        
        self.label_data[0] = new_positions[0][0] / img_w
        self.label_data[1] = new_positions[0][1] / img_h
        self.label_data[2] = new_positions[1][0] / img_w
        self.label_data[3] = new_positions[1][1] / img_h
        
        img_name = self.listbox.get(tk.ACTIVE)
        label_path = os.path.join(self.label_folder, os.path.splitext(img_name)[0] + ".txt")
        
        with open(label_path, "w") as f:
            f.write(" ".join(map(str, self.label_data)))
        
        messagebox.showinfo("Success", "Labels saved successfully!")
    
    def reset_labels(self):
        if not self.original_positions:
            return
        
        for i, pos in enumerate(self.original_positions):
            self.canvas.coords(self.markers[i], *pos)
        
if __name__ == "__main__":
    root = tk.Tk()
    app = LabelTool(root)
    root.mainloop()
