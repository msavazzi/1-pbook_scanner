# Barcode + Manual OCR Scanner

A Windows 11 standalone GUI application that uses your webcam to scan **barcodes** automatically and **text manually** with OCR. Saves results to a file while preventing duplicates and provides clear visual feedback for scanning.

## Features

- Automatic Barcode Scanning (except PDF417)
- Manual OCR with spacebar save
- Visual Feedback: Yellow=Counting, Green=Ready, Blue=Recently saved
- Multi-Camera Support
- Scrollable GUI log, Clear log button
- Prevent duplicates with timeout
- Default save file name suggested as YYYYMMDD-HHMM.txt and printed before dialog
- Default camera index printed before opening camera

## Requirements

- Windows 11, Python 3.10+
- Packages: opencv-python, pyzbar, pytesseract, pillow
- Tesseract OCR installed

## Usage

1. Run `scanner.py`
2. Console will print default save file and camera index
3. Select save file (default: YYYYMMDD-HHMM.txt)
4. Select camera
5. Barcode scans automatically; Text OCR with spacebar
6. Clear log with button

## File Saving

- Format: `timestamp[TAB]scanned_text`
- Duplicate prevention with configurable timeout (default 15s)

## Notes

- Works best with stable camera feed
- PDF417 barcodes are ignored intentionally

## License

MIT License
