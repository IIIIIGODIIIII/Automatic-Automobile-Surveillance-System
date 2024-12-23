import cv2
from ultralytics import YOLO
from utils.utils import preprocess_for_ocr, concat_number_plate
import easyocr
import os
import glob

# Step 1: Load the YOLO model with the best weights
model = YOLO("best_l.pt")

# Initialize EasyOCR
reader = easyocr.Reader(["en"])

# Step 2: Set the video folder path
video_folder = r"C:\Users\samar\Desktop\capstone\anprtest4\videos"  # Path to your video folder
video_files = glob.glob(os.path.join(video_folder, "*.mp4")) + glob.glob(os.path.join(video_folder, "*.dav"))  # Include .mp4 and .dav files

# Create the directory to save the images if it doesn't exist
output_folder = r"number_plates_realworld"
os.makedirs(output_folder, exist_ok=True)

image_counter = 0  # To name the saved images sequentially

# Step 3: Process each video file
for video_path in video_files:
    cap = cv2.VideoCapture(video_path)
    print(f"Processing video: {video_path}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Step 4: Run inference on the frame
        results = model(frame, verbose=False)

        plate_detected = False

        # Step 5: Extract bounding box coordinates and labels
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()  # Bounding box coordinates
            confidences = result.boxes.conf.cpu().numpy()  # Confidence scores
            class_ids = result.boxes.cls.cpu().numpy()  # Class IDs

            # Step 6: Draw bounding boxes and labels on the frame only if confidence > 0.4
            for box, confidence, class_id in zip(boxes, confidences, class_ids):
                if confidence > 0.5:  # Only process detections with confidence > 0.4
                    x1, y1, x2, y2 = map(int, box)
                    label = f"{model.names[int(class_id)]} {confidence:.2f}"

                    # Step 7: Clip the detected number plate region
                    roi = frame[y1:y2, x1:x2]

                    image_filename = os.path.join(output_folder, f"number_plate_{image_counter}.jpg")
                    cv2.imwrite(image_filename, roi)
                    image_counter += 1

        # Step 8: Increment the counter if no plate was detected
        # No need to display the frame since we're not showing anything

    cap.release()

print("Processing complete. Number plates have been saved.")
