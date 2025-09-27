# Barcode + Manual OCR Scanner

A Windows 11 standalone GUI application that uses your webcam to scan **barcodes** automatically and **text manually** with OCR. Saves results to a file while preventing duplicates and provides clear visual feedback for scanning.

---

## Features

- **Automatic Barcode Scanning**  
  - Supports common barcode types except PDF417.  
  - Saves only stable barcodes (requires N consecutive frames).  
  - Prevents duplicates with a configurable timeout.  

- **Manual OCR (Text Reading)**  
  - Highlights detected text in the camera feed.  
  - Save highlighted text manually by pressing the **space bar**.  
  - Avoids glitches and shows bounding boxes around recognized text.  

- **Visual Feedback**  
  - **Yellow box** → counting down to stable  
  - **Green box** → ready to save  
  - **Blue box** → already saved recently  

- **Multi-Camera Support**  
  - Allows switching between available webcams.  

- **User Interface**  
  - GUI with **scrollable log** of scanned items.  
  - Clear log button.  
  - Asks for save file at startup and allows append/replace.  

- **Performance & Stability**  
  - Suppresses OpenCV warnings.  
  - Stable barcode detection prevents duplicates caused by jitter.  
  - Manual OCR uses a separate thread to avoid UI freeze.  

---

## Requirements

- Windows 11  
- Python 3.10+  
- Python packages:
  ```bash
  pip install opencv-python pyzbar pytesseract pillow
