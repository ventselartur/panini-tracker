# panini-tracker
Track your collection and compare with others for exchange

Fork the repo to start tracking your collection. I've started to populate the `collection.csv` file, you need to make it empty in your fork (leave only headers).

## Main program

```cmd
usage: panini_tracker.py [-h] (-a ADD | -m | -o | -s | -c COMPARE | -d)

Panini Album Progress Tracker

options:
  -h, --help            show this help message and exit
  -a, --add ADD         Add stickers to collection (comma-separated list)
  -m, --missing         Print missing sticker numbers
  -o, --owned           Print owned sticker numbers
  -s, --stats           Print collection stats
  -c, --compare COMPARE URL to another CSV file for exchange comparison
  -d, --duplicates      Print duplicate stickers and their quantities
```

## Auto Scanner

The `auto_scanner.py` script provides an automated way to scan and recognize Panini sticker numbers using your webcam.

### Requirements

- Python 3.6+
- OpenCV
- pytesseract
- Tesseract OCR engine installed on your system

See `requirements.txt` for all dependencies.

### Setup

1. Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki
2. Install Python dependencies: `pip install -r requirements.txt`
3. Make sure the path to Tesseract executable in `auto_scanner.py` matches your installation

### Usage

Run the scanner:

```cmd
python auto_scanner.py
```

Controls:
- **D** - Detect a sticker number
- **N** - Accept current number and prepare for next (max 8)
- **A** - Add all captured numbers to your collection
- **C** - Clear captured numbers list
- **Q** - Quit

### Workflow

1. Place a sticker in the red rectangle
2. Press **D** to detect the number
3. If the number is correct, press **N** to add it to the list
4. Repeat steps 1-3 for up to 8 stickers
5. Press **A** to add all captured numbers to your collection
6. The scanner will automatically handle duplicates

The scanner displays a processed image with the detected numbers and the list of captured stickers.
