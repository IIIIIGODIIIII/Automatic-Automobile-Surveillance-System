import cv2
from ultralytics import YOLO
from utils.utils import segment_characters_2, show_results
from utils.utils import preprocess_for_ocr, concat_number_plate
from utils.NumberPlatePredictor import NumberPlatePredictor

# from tensorflow.keras.models import load_model
import easyocr
import os

# Step 1: Load the YOLO model with the best weights
model = YOLO("best.pt")

# Load your models
reader = easyocr.Reader(["en"])
numberPlatePredictor = NumberPlatePredictor()

# Step 2: Capture video from webcam
cap = cv2.VideoCapture(0)  # 0 is the default camera
# cap = cv2.VideoCapture("http://100.88.234.2:4747/video")
# cap = cv2.VideoCapture("http://192.168.29.40/cam-hi.jpg")
# Initialize a counter to track frames without detected number plates
no_plate_counter = 0
print('cam on')


while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Step 3: Run inference on the frame
    results = model(frame, verbose=False)

    plate_detected = False

    # Step 4: Extract bounding box coordinates and labels
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()  # Bounding box coordinates
        confidences = result.boxes.conf.cpu().numpy()  # Confidence scores
        class_ids = result.boxes.cls.cpu().numpy()  # Class IDs

        # Step 5: Draw bounding boxes and labels on the frame
        for box, confidence, class_id in zip(boxes, confidences, class_ids):
            x1, y1, x2, y2 = map(int, box)
            label = f"{model.names[int(class_id)]} {confidence:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

            # Step 6: Clip the detected number plate
            roi = frame[y1:y2, x1:x2]

            # Preprocess the ROI for OCR
            preprocessed_img = preprocess_for_ocr(roi)
            if preprocessed_img is not None:
                plate_detected = True
                numberplate = concat_number_plate(reader.readtext(preprocessed_img))
                numberPlatePredictor.update_stream(numberplate)
                print("Number Plate: ", numberPlatePredictor.get_most_likely_plate())

            cv2.imshow("Number Plate", roi)

    # Check if a number plate was detected in this frame
    if plate_detected:
        no_plate_counter = 0  # Reset the counter if a plate was detected
    else:
        no_plate_counter += 1  # Increment the counter if no plate was detected

    # Reset the number plate predictor if no plates detected for the last 10 frames
    if no_plate_counter >= 50:
        numberPlatePredictor = NumberPlatePredictor()  # Reset the predictor
        no_plate_counter = 0  # Reset the counter
        print("Number Plate Detector reset due to inactivity.")

    # Step 8: Display the frame with bounding boxes and labels
    cv2.imshow("YOLO Webcam", frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the capture and close windows
cap.release()
cv2.destroyAllWindows()
