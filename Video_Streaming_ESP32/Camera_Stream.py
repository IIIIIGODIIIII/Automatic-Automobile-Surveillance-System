import cv2
import numpy as np

# Replace with full IP camera URL including protocol and port if needed
url = 'rtsp://admin:123456@192.168.1.188/stream'  # Replace with actual stream URL
cv2.namedWindow("Live Camera Testing", cv2.WINDOW_AUTOSIZE)

cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Failed to open the IP camera stream")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to retrieve frame")
        break
    
    # Display the live video stream
    cv2.imshow('Live Stream', frame)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()