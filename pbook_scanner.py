import cv2
from pyzbar.pyzbar import decode
import pytesseract
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image, ImageTk
import datetime
import os
import time
import threading

# Suppress OpenCV warnings
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class ScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Barcode + Manual OCR Scanner")

        # Camera selection
        self.camera_index = 0
        self.available_cameras = self.get_available_cameras()
        print(f"Default camera index: {self.camera_index}")  # Print default
        camera_frame = tk.Frame(root)
        camera_frame.pack(pady=5)
        tk.Label(camera_frame, text="Camera:").pack(side="left")
        self.camera_combo = ttk.Combobox(camera_frame, values=self.available_cameras, state="readonly")
        self.camera_combo.current(0)
        self.camera_combo.pack(side="left")
        self.camera_combo.bind("<<ComboboxSelected>>", self.change_camera)

        # Webcam preview
        self.video_label = tk.Label(root)
        self.video_label.pack()

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)
        self.clear_button = tk.Button(button_frame, text="Clear Log", command=self.clear_log)
        self.clear_button.pack(side="left", padx=5)

        # Current result
        self.result_label = tk.Label(root, text="Highlighted: None", font=("Arial", 14))
        self.result_label.pack(pady=5)

        # Scrollable log
        self.log_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15, state="disabled")
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)

        # Webcam
        self.cap = self.open_camera(self.camera_index)
        if not self.cap:
            messagebox.showerror("Camera Error", f"Cannot open camera {self.camera_index}")
            self.root.destroy()
            return

        # File handling with default filename YYYYMMDD-HHMM.txt
        self.save_path = self.ask_save_file()

        # Barcode stability tracking
        self.stable_count = {}
        self.stable_threshold = 3
        self.current_frame_barcodes = set()
        self.recent_saves = {}  # barcode_data -> last saved timestamp
        self.duplicate_timeout = 15  # seconds before same barcode can be saved again

        # OCR highlighted text
        self.highlighted_text = None
        self.highlighted_boxes = []
        self.show_ocr_boxes = False

        # OCR throttling
        self.last_ocr_time = 0
        self.ocr_interval = 2

        # Bind space bar
        self.root.bind("<space>", self.save_highlighted_text)

        # OCR thread lock
        self.ocr_lock = threading.Lock()

        self.update_frame()

    # Robust camera opening
    def open_camera(self, index):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            return cap
        cap.release()
        cap = cv2.VideoCapture(index)  # fallback
        if cap.isOpened():
            return cap
        cap.release()
        return None

    # List only usable cameras
    def get_available_cameras(self, max_tested=5):
        cameras = []
        for i in range(max_tested):
            cap = self.open_camera(i)
            if cap:
                cameras.append(i)
                cap.release()
        if not cameras:
            messagebox.showerror("Camera Error", "No cameras found")
            self.root.destroy()
        return cameras

    def change_camera(self, event=None):
        try:
            index = int(self.camera_combo.get())
            if index in self.available_cameras:
                self.camera_index = index
                if hasattr(self, "cap"):
                    self.cap.release()
                self.cap = self.open_camera(self.camera_index)
                if not self.cap:
                    messagebox.showerror("Camera Error", f"Cannot open camera {self.camera_index}")
                    self.root.destroy()
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to switch camera: {e}")

    # Ask save file with default timestamped name
    def ask_save_file(self):
        default_name = datetime.datetime.now().strftime("%Y%m%d-%H%M.txt")
        print(f"Default save file: {default_name}")  # Print default

        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv")],
            initialfile=default_name,
            title="Select Save File"
        )

        # Fallback to default if user cancels
        if not file:
            file = default_name
            print(f"No file selected. Using default: {file}")

        if os.path.exists(file):
            choice = messagebox.askyesno("File Exists", "File already exists.\nYes = Replace, No = Append")
            if choice:
                open(file, "w", encoding="utf-8").close()
        return file

    # Save and log methods
    def save_result(self, text):
        with open(self.save_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()}\t{text}\n")

    def log_result(self, text):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, f"{datetime.datetime.now()}\t{text}\n")
        self.log_box.yview(tk.END)
        self.log_box.config(state="disabled")

    def clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete(1.0, tk.END)
        self.log_box.config(state="disabled")

    # OCR save
    def save_highlighted_text(self, event=None):
        with self.ocr_lock:
            if self.highlighted_text:
                self.save_result(self.highlighted_text)
                self.log_result(self.highlighted_text)
                self.result_label.config(text=f"Saved: {self.highlighted_text}")
                self.show_ocr_boxes = True
                self.root.after(1000, self.clear_ocr_boxes)
            else:
                self.result_label.config(text="No highlighted text to save.")

    def clear_ocr_boxes(self):
        with self.ocr_lock:
            self.highlighted_boxes = []
            self.highlighted_text = None
            self.show_ocr_boxes = False

    # OCR thread
    def run_ocr_thread(self, gray_frame):
        try:
            data = pytesseract.image_to_data(gray_frame, output_type=pytesseract.Output.DICT)
            n_boxes = len(data['level'])
            text_blocks = []
            boxes = []
            for i in range(n_boxes):
                conf = int(data['conf'][i])
                if conf > 50:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    text = data['text'][i].strip()
                    if text:
                        text_blocks.append(text)
                        boxes.append((x, y, w, h))
            if text_blocks:
                with self.ocr_lock:
                    self.highlighted_text = " ".join(text_blocks)
                    self.highlighted_boxes = boxes
        except Exception as e:
            print(f"OCR thread error: {e}")

    # Main update loop
    def update_frame(self):
        if not hasattr(self, "cap") or not self.cap.isOpened():
            self.cap = self.open_camera(self.camera_index)
            with self.ocr_lock:
                self.clear_ocr_boxes()
            self.current_frame_barcodes.clear()
            self.stable_count.clear()
            self.root.after(100, self.update_frame)
            return

        ret, frame = self.cap.read()
        if not ret:
            if hasattr(self, "cap"):
                self.cap.release()
            self.cap = self.open_camera(self.camera_index)
            with self.ocr_lock:
                self.clear_ocr_boxes()
            self.current_frame_barcodes.clear()
            self.stable_count.clear()
            self.root.after(100, self.update_frame)
            return

        boxes_to_draw = []
        highlighted_text = None
        current_detected = set()
        current_time = time.time()

        # Barcode detection
        try:
            barcodes = decode(frame)
        except Exception as e:
            barcodes = []
            print(f"ZBar decode error: {e}")

        for barcode in barcodes:
            if barcode.type == "PDF417":
                continue
            barcode_data = barcode.data.decode("utf-8")
            current_detected.add(barcode_data)
            x, y, w, h = barcode.rect

            # Stability counting
            count = self.stable_count.get(barcode_data, 0) + 1
            self.stable_count[barcode_data] = count
            remaining = max(0, self.stable_threshold - count)

            # Determine box color
            last_saved = self.recent_saves.get(barcode_data, 0)
            elapsed = current_time - last_saved
            if remaining > 0:
                color = (0, 255, 255)  # Yellow = counting down
                cv2.putText(frame, str(remaining), (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            else:
                if elapsed < self.duplicate_timeout:
                    color = (255, 0, 0)  # Blue = saved recently
                else:
                    color = (0, 255, 0)  # Green = ready to save

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            # Save if stable & not recently saved
            if count >= self.stable_threshold and elapsed > self.duplicate_timeout:
                self.save_result(barcode_data)
                self.log_result(barcode_data)
                self.recent_saves[barcode_data] = current_time
                self.result_label.config(text=f"Barcode Scanned: {barcode_data}")

        # Remove stable counts for barcodes that disappeared
        for old in list(self.stable_count.keys()):
            if old not in current_detected:
                self.stable_count.pop(old)

        # OCR detection (manual)
        if not barcodes and current_time - self.last_ocr_time >= self.ocr_interval:
            self.last_ocr_time = current_time
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            threading.Thread(target=self.run_ocr_thread, args=(gray,), daemon=True).start()

        with self.ocr_lock:
            if self.show_ocr_boxes and self.highlighted_boxes:
                boxes_to_draw = self.highlighted_boxes.copy()
                highlighted_text = self.highlighted_text

        # Draw OCR boxes (blue)
        for (x, y, w, h) in boxes_to_draw:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        if highlighted_text:
            self.result_label.config(text=f"Highlighted Text: {highlighted_text}")
        elif not barcodes:
            self.result_label.config(text="Highlighted: None")

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        self.root.after(30, self.update_frame)

    def __del__(self):
        if hasattr(self, "cap"):
            self.cap.release()


if __name__ == "__main__":
    root = tk.Tk()
    app = ScannerApp(root)
    root.mainloop()
