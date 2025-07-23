#!/usr/bin/env python3
import cv2
import pytesseract
import numpy as np
import time
import re
import subprocess
import os

# Set the path to Tesseract OCR executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def enhance_image(image):
    """Process the image to enhance text recognition using Otsu's method."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply milder Gaussian blur
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Apply Otsu's thresholding without inverting (black text on white background)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Apply gentler morphological operations
    kernel = np.ones((2, 2), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # Lighter dilation
    dilated = cv2.dilate(opening, kernel, iterations=1)
    
    return dilated

def extract_number(image):
    """Extract numbers from the image using OCR."""
    # Use the configuration that works best
    config = '--psm 1 --oem 3 -c tessedit_char_whitelist=0123456789'  # Assume a single uniform block of text
    
    # Perform OCR with the working configuration
    text = pytesseract.image_to_string(image, config=config)

    # Clean and validate the extracted text
    text = text.strip()
    
    # Use regex to extract numbers
    numbers = re.findall(r'\d+', text)
    
    if numbers:
        # Get the first number
        try:
            number = int(numbers[0])
            # Validate the range (1-720)
            if 1 <= number <= 720:
                return number
        except ValueError:
            pass
    
    return None

def run_panini_tracker_add(numbers):
    """Run the panini_tracker.py script with the -a flag to add numbers."""
    if not numbers:
        print("No numbers to add.")
        return False
    
    numbers_str = ",".join(map(str, numbers))
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panini_tracker.py")
    
    try:
        # Use Popen instead of run to handle interactive prompts
        print(f"Running command: python {script_path} -a {numbers_str}")
        process = subprocess.Popen(
            ["python", script_path, "-a", numbers_str],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Automatically respond with 'y' to any prompts
        stdout, stderr = process.communicate(input='y\n')
        
        if process.returncode == 0:
            print("Successfully added numbers to collection.")
            print(stdout)
            return True
        else:
            print(f"Error adding numbers: {stderr}")
            return False
    except Exception as e:
        print(f"Error running panini_tracker.py: {e}")
        return False

def main():
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
    
    # Set resolution to 480p (640x480)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Initialize variables
    last_detected_number = None
    captured_numbers = []  # List to store captured sticker numbers
    
    print("Panini Sticker Scanner Started")
    print("Controls:")
    print("  D - Detect a sticker")
    print("  N - Accept current number and prepare for next (max 8)")
    print("  A - Add all captured numbers to collection")
    print("  C - Clear captured numbers")
    print("  Q - Quit")
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Could not read frame.")
            break
        
        # Make a copy of the frame for processing
        process_frame = frame.copy()
        
        # Enhance the image for better OCR
        enhanced = enhance_image(process_frame)
        
        # Get key press
        key = cv2.waitKey(1) & 0xFF
        
        # Define a smaller rectangle for more precise scanning
        h, w = frame.shape[:2]
        # Small rectangle (30% of frame size)
        small_rect_x1 = w//2 - (w//6)
        small_rect_y1 = h//2 - (h//6)
        small_rect_x2 = w//2 + (w//6)
        small_rect_y2 = h//2 + (h//6)
        
        # Draw both rectangles - large green one and small red one for precise targeting
        cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
        cv2.rectangle(frame, (small_rect_x1, small_rect_y1), (small_rect_x2, small_rect_y2), (0, 0, 255), 2)
        
        # Manual detection when 'D' is pressed
        if key == ord('d') or key == ord('D'):
            # Display a message to indicate detection in progress
            processing_frame = frame.copy()
            cv2.putText(processing_frame, "Processing...", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.imshow('Panini Sticker Scanner', processing_frame)
            cv2.waitKey(1)  # Update the display
            
            # Crop to the smaller rectangle for more precise recognition
            small_crop = process_frame[small_rect_y1:small_rect_y2, small_rect_x1:small_rect_x2]
            enhanced_small = enhance_image(small_crop)
            
            # Try to extract number from the small crop first
            number = extract_number(enhanced_small)
            
            # If no number found, try the full enhanced frame
            if not number:
                number = extract_number(enhanced)
                
            if number:
                print(f"Detected sticker number: {number}")
                last_detected_number = number
            else:
                print("No number detected. Try adjusting lighting or position.")
        
        # Add to captured list when 'N' is pressed
        elif key == ord('n') or key == ord('N'):
            if last_detected_number and len(captured_numbers) < 8:
                if last_detected_number not in captured_numbers:
                    captured_numbers.append(last_detected_number)
                    print(f"Added {last_detected_number} to capture list. Total: {len(captured_numbers)}")
                    last_detected_number = None
                else:
                    print(f"Number {last_detected_number} already in capture list.")
            elif last_detected_number:
                print("Maximum of 8 numbers already captured. Use 'A' to add or 'C' to clear.")
            else:
                print("No number detected to add. Use 'D' to detect first.")
        
        # Add all captured numbers to collection when 'A' is pressed
        elif key == ord('a') or key == ord('A'):
            if captured_numbers:
                success = run_panini_tracker_add(captured_numbers)
                if success:
                    print(f"Added {len(captured_numbers)} numbers to collection.")
                    captured_numbers = []  # Clear the list after adding
                else:
                    print("Failed to add numbers to collection.")
            else:
                print("No captured numbers to add.")
        
        # Clear captured numbers when 'C' is pressed
        elif key == ord('c') or key == ord('C'):
            captured_numbers = []
            print("Cleared captured numbers list.")
        
        # Display the last detected number on the frame
        if last_detected_number:
            cv2.putText(frame, f"Detected: {last_detected_number}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Display captured numbers
        cv2.putText(frame, f"Captured: {len(captured_numbers)}/8", (10, h - 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display the list of captured numbers
        if captured_numbers:
            numbers_text = ", ".join(map(str, captured_numbers))
            # Split into multiple lines if too long
            if len(numbers_text) > 40:
                lines = []
                current_line = ""
                for num in captured_numbers:
                    if len(current_line + str(num) + ", ") > 40:
                        lines.append(current_line)
                        current_line = str(num) + ", "
                    else:
                        current_line += str(num) + ", "
                if current_line:
                    lines.append(current_line.rstrip(", "))
                
                for i, line in enumerate(lines):
                    cv2.putText(frame, line, (10, h - 30 + i * 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, numbers_text, (10, h - 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add all UI elements to the enhanced image
        enhanced_display = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        # Copy all text and rectangles from frame to enhanced_display
        # Draw rectangles on enhanced display
        cv2.rectangle(enhanced_display, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
        cv2.rectangle(enhanced_display, (small_rect_x1, small_rect_y1), (small_rect_x2, small_rect_y2), (0, 0, 255), 2)
        
        # Display the last detected number on enhanced display
        if last_detected_number:
            cv2.putText(enhanced_display, f"Detected: {last_detected_number}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Copy captured numbers info to enhanced display
        cv2.putText(enhanced_display, f"Captured: {len(captured_numbers)}/8", (10, h - 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Copy captured numbers list to enhanced display
        if captured_numbers:
            numbers_text = ", ".join(map(str, captured_numbers))
            if len(numbers_text) > 40:
                lines = []
                current_line = ""
                for num in captured_numbers:
                    if len(current_line + str(num) + ", ") > 40:
                        lines.append(current_line)
                        current_line = str(num) + ", "
                    else:
                        current_line += str(num) + ", "
                if current_line:
                    lines.append(current_line.rstrip(", "))
                
                for i, line in enumerate(lines):
                    cv2.putText(enhanced_display, line, (10, h - 30 + i * 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(enhanced_display, numbers_text, (10, h - 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Only display the enhanced image with all overlays
        cv2.imshow('Panini Sticker Scanner', enhanced_display)
        
        # Break the loop on 'q' press
        if key == ord('q'):
            break
    
    # Release the capture and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
