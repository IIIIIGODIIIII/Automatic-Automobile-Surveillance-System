import cv2
import numpy as np
import torch
from ultralytics import YOLO
from collections import defaultdict, deque

# Initialize video capture
video_path = 'e:\\Tech\\Python\\Projects\\Automobile Automobile Surveillance System\\Speed Detection\\vehicles.mp4'
cap = cv2.VideoCapture(video_path)

# Check if the video file opened successfully
if not cap.isOpened():
    print(f"Error: Could not open video file {video_path}")
    exit()

# Load YOLOv8 model on GPU if available
model_path = "e:\\Tech\\Python\\Projects\\Automobile Automobile Surveillance System\\Speed Detection\\yolov8s.pt"
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = YOLO(model_path).to(device)

# Parameters for Lucas-Kanade optical flow
lk_params = dict(winSize=(15, 15),
                 maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# Create a named window
cv2.namedWindow('frame', cv2.WINDOW_NORMAL)

# Initialize variables for tracking
prev_gray = None
prev_points = None
vehicle_speeds = defaultdict(lambda: deque(maxlen=60))  # Track speed over time for each vehicle

# Confidence threshold for filtering detections
confidence_threshold = 0.5

frame_count = 0  # Track frames to refresh detections periodically
detection_refresh_rate = 10  # Refresh detection every 10 frames

# Conversion factors (adjust based on your camera setup)
pixels_to_meters = 0.05  # Example scale: each pixel represents 0.05 meters
fps = 60  # Frames per second of the video

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Resize the frame for faster processing
    frame = cv2.resize(frame, (640, 480))

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Periodically re-run YOLO detection to detect new vehicles
    if frame_count % detection_refresh_rate == 0 or prev_points is None:
        print(f"Running YOLO detection on frame {frame_count}")  # Debugging message
        # Detect vehicles using YOLOv8
        results = model(frame)
        boxes = results[0].boxes.xyxy.cpu().numpy()  # Get bounding boxes
        confidences = results[0].boxes.conf.cpu().numpy()  # Get confidences
        class_ids = results[0].boxes.cls.cpu().numpy()  # Get class IDs

        # Filter for cars (class ID for car in COCO dataset is 2) with confidence threshold
        vehicle_boxes = []
        new_points = []
        for i, class_id in enumerate(class_ids):
            if int(class_id) == 2 and confidences[i] > confidence_threshold:  # Class ID for car is 2
                vehicle_boxes.append(boxes[i])
                print(f"Detected vehicle at {boxes[i]} with confidence {confidences[i]}")  # Debugging message
                # Calculate the center of each vehicle box
                x, y, x2, y2 = boxes[i]
                new_points.append([[(x + x2) // 2, (y + y2) // 2]])  # center point of box

                # Draw a bounding box around the detected vehicle (debug)
                cv2.rectangle(frame, (int(x), int(y)), (int(x2), int(y2)), (0, 255, 0), 2)  # Green box for detected vehicles

        # Convert new points to the format required by optical flow
        new_points = np.array(new_points, dtype=np.float32)

        if prev_points is None:
            prev_points = new_points
        else:
            # Combine new points with previous ones for tracking
            prev_points = np.vstack((prev_points, new_points))

    # Run optical flow to track points
    if prev_points is not None and len(prev_points) > 0:
        if prev_gray is not None:
            next_points, status, err = cv2.calcOpticalFlowPyrLK(prev_gray, gray, prev_points, None, **lk_params)

            # Keep good points
            good_new = next_points[status == 1]
            good_old = prev_points[status == 1]

            for i, (new, old) in enumerate(zip(good_new, good_old)):
                a, b = int(new.ravel()[0]), int(new.ravel()[1])
                c, d = int(old.ravel()[0]), int(old.ravel()[1])
                
                # Calculate speed in pixels/frame
                pixel_distance = np.linalg.norm(new - old)
                
                # Convert speed to meters/second and then to KMPH
                speed_mps = (pixel_distance * pixels_to_meters * fps)  # meters per second
                speed_kmph = speed_mps * 3.6  # Convert mps to km/h
                
                vehicle_speeds[i].append(speed_kmph)
                avg_speed_kmph = np.mean(vehicle_speeds[i])  # Take the average speed over time

                # Debugging message for speed
                print(f"Vehicle {i} speed: {avg_speed_kmph:.2f} KMPH")

                # Display the speed and draw bounding boxes
                for (x, y, x2, y2) in vehicle_boxes:
                    if x < a < x2 and y < b < y2:  # Ensure point is inside the vehicle bounding box
                        # Draw a blue bounding box with thickness
                        cv2.rectangle(frame, (int(x), int(y)), (int(x2), int(y2)), (255, 0, 0), 2)
                        
                        # Display the speed in KMPH
                        cv2.putText(frame, f'Speed: {avg_speed_kmph:.2f} KMPH', (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Update the previous points with the current good points
            prev_points = good_new.reshape(-1, 1, 2)

    prev_gray = gray.copy()
    frame_count += 1

    # Display the frame with bounding boxes and speed
    cv2.imshow('frame', frame)

    # Exit loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
