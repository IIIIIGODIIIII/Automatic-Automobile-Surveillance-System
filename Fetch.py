import cv2
import numpy as np

# Replace with the actual IP address of your ESP32 camera
url = "https://youtu.be/aYP1Oo1V4EY"

# Create a video capture object using the URL
cap = cv2.VideoCapture(url)

# Check if the video capture object was successfully created
if not cap.isOpened():
    print("Error opening video stream or file")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Handle potential errors during frame capture
    if not ret:
        print("Error capturing frame")
        break

    # Display the resulting frame
    cv2.imshow('ESP32 Camera Stream', frame)

    # Exit if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close all windows
cap.release()
cv2.destroyAllWindows()
