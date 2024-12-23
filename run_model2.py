import cv2
from ultralytics import YOLO
from utils.utils import preprocess_for_ocr, concat_number_plate
import easyocr

# Step 1: Load the YOLO model with the best weights
model = YOLO("best_l.pt")

# Initialize EasyOCR
reader = easyocr.Reader(["en"])

# Step 2: Load the video file
video_path = r"C:\Users\samar\Desktop\capstone\anprtest4\videos\192.168.1.108_IP Camera_main_20241115162510.mp4"
# video_path = r"C:\Users\samar\Downloads\192.168.1.108_IP Camera_main_20241115173437.dav"
cap = cv2.VideoCapture(video_path)

# Initialize a counter to track frames without detected number plates
no_plate_counter = 0
print('Processing video file...')

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

        # Step 5: Draw bounding boxes and labels on the frame only if confidence > 0.5
        for box, confidence, class_id in zip(boxes, confidences, class_ids):
            if confidence > 0.5:  # Only process detections with confidence > 0.5
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

                # Step 6: Clip the detected number plate region
                roi = frame[y1:y2, x1:x2]
                roi = cv2.resize(roi, (roi.shape[1] * 2, roi.shape[0] * 2))

                # Preprocess the ROI for OCR
                preprocessed_img = preprocess_for_ocr(roi)
                if preprocessed_img is not None:
                    plate_detected = True
                    # Use EasyOCR to detect the text on the number plate
                    ocr_result = reader.readtext(roi)
                    number_plate_text = concat_number_plate(ocr_result)
                    print("Number Plate Detected: ", number_plate_text)
                    cv2.imshow("Preprocessed Plate", preprocessed_img)

                # Display the extracted number plate region
                cv2.imshow("Number Plate", roi)

    # Check if a number plate was detected in this frame
    if plate_detected:
        no_plate_counter = 0  # Reset the counter if a plate was detected
    else:
        no_plate_counter += 1  # Increment the counter if no plate was detected

    # Step 8: Display the frame with bounding boxes and labels
    frame = cv2.resize(frame, (1280, 720))
    cv2.imshow("YOLO Video", frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(5) & 0xFF == ord("q"):
        break

# Release the capture and close windows
cap.release()
cv2.destroyAllWindows()
