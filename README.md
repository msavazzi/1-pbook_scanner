# Barcode + Manual OCR Scanner

A Windows 11 standalone GUI application that uses your webcam to scan **barcodes** automatically and **text manually** with OCR. Saves results to a file while preventing duplicates and provides clear visual feedback for scanning.

## Features

- Automatic Barcode Scanning (except PDF417)
- Manual OCR with spacebar save
- Visual Feedback: Yellow=Counting, Green=Ready, Blue=Recently saved
- Multi-Camera Support
- Scrollable GUI log, Clear log button
- Prevent duplicates with timeout
- Default save file name suggested as YYYYMMDD-HHMM.txt

## Requirements

- Windows 11, Python 3.10+
- Packages: opencv-python, pyzbar, pytesseract, pillow
- Tesseract OCR installed

## Usage

1. Run `scanner.py`
2. Select save file (default: YYYYMMDD-HHMM.txt)
3. Select camera
4. Barcode scans automatically; Text OCR with spacebar
5. Clear log with button

## File Saving

- Format: `timestamp[TAB]scanned_text`
- Duplicate prevention with configurable timeout (default 15s)

## Notes

- Works best with stable camera feed
- PDF417 barcodes are ignored intentionally

## License

MIT License