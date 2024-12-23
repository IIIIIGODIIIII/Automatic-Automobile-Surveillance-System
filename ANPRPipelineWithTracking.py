import torch
import cv2
import numpy as np

from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
from torch.cuda import is_available as is_gpu_available


class ANPRPipelineWithTracking:
    def __init__(
        self,
        plate_model_path,
        char_model_path,
        confidence_threshold=0.55,
        self_track=True,
    ):
        # Check if GPU is available
        device = "cuda" if is_gpu_available() else "cpu"
        print(f"Using device: {device}")  # Print the device being used

        # Load the YOLO models on the appropriate device (GPU or CPU)
        self.plate_model = YOLO(plate_model_path).to(
            device
        )  # Model for detecting number plates
        self.char_model = YOLO(char_model_path).to(
            device
        )  # Model for detecting characters
        self.confidence_threshold = confidence_threshold

        # Initialize the DeepSORT tracker
        if self_track:
            self.deepsort = DeepSort()

    def detect_number_plate(self, image):
        """Detect the number plate using the first YOLO model."""
        results = self.plate_model(image, verbose=False)
        plates = []

        # Process the results to extract bounding boxes
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()  # Bounding box coordinates
            confidences = result.boxes.conf.cpu().numpy()  # Confidence scores
            class_ids = result.boxes.cls.cpu().numpy()  # Class IDs (for number plates)

            for box, confidence, class_id in zip(boxes, confidences, class_ids):
                if confidence > self.confidence_threshold:
                    x1, y1, x2, y2 = map(int, box)

                    # # Add padding of 20 pixels
                    # padding = 20

                    # # Extend the bounding box by the padding, ensuring we don't go out of image bounds
                    # x1 = max(1, x1 - padding)  # Ensure x1 is not less than 0
                    # y1 = max(1, y1 - padding)  # Ensure y1 is not less than 0
                    # x2 = min(image.shape[1], x2 + padding)  # Ensure x2 doesn't exceed image width
                    # y2 = min(image.shape[0], y2 + padding)  # Ensure y2 doesn't exceed image height

                    plates.append((x1, y1, x2, y2, confidence))

        return plates

    def track_number_plates(self, image, plates):
        """Track number plates using DeepSORT."""
        # Convert plates to the required format for DeepSORT ([left, top, width, height], confidence, detection_class)
        detections = []

        for x1, y1, x2, y2, confidence in plates:
            # Ensure the detection is formatted correctly as ([left, top, width, height], confidence, detection_class)
            if (
                confidence > self.confidence_threshold
            ):  # Optional: Check for confidence threshold
                # The class_id is generally needed to indicate the detection class; for plates, it could be a fixed class (e.g., 0)
                detection_class = 0  # Assuming class '0' corresponds to number plates
                width = max(x2 - x1, x1 - x2)
                height = max(y2 - y1, y1 - y2)
                detections.append(
                    ([x1, y1, width, height], confidence, detection_class)
                )

        # Ensure detections are passed as a list of tuples in the correct format
        if len(detections) > 0:
            trackers = self.deepsort.update_tracks(detections, frame=image)
        else:
            trackers = []

        # Collect the tracked plates with their IDs
        # print(detections)
        # print(len(trackers))
        # print(len(plates))
        tracked_plates = []
        for track in trackers:
            track_id = (
                track.track_id
            )  # Unique ID for each track (DeepSORT assigns this)
            x1, y1, x2, y2 = track.to_tlbr()  # Get the bounding box coordinates
            # x1, y1, x2, y2 = plate[:4]  # Get the bounding box coordinates

            # Append the tracked plate information (ID, bounding box coordinates)
            tracked_plates.append((track_id, int(x1), int(y1), int(x2), int(y2)))

        return tracked_plates

    def track_numer_plates_vehical_data(self, vehicle_data, plates):
        """
        Detections(xyxy=array([[     779.57,      427.78,      999.77,      587.01]], dtype=float32), mask=None, confidence=array([    0.55693], dtype=float32), class_id=array([          2], dtype=float32), tracker_id=array([1]), data={})
        plates = [(x1, y1, x2, y2, confidence)]
        """
        tracked_plates_with_vehicle_id = []
        # print(vehicle_data)
        # print(vehicle_data[0])
        for vehicle in vehicle_data:

            # print(vehicle)
            vehicle_id = vehicle[4]
            vehicle_bbox = list(
                map(int, vehicle[0])
            )  # Assuming vehicle_data contains bounding boxes as [x1, y1, x2, y2]

            for plate in plates:
                px1, py1, px2, py2, confidence = plate

                # Check if the plate is inside the vehicle bounding box
                if (
                    vehicle_bbox[0] <= px1 <= vehicle_bbox[2]
                    and vehicle_bbox[1] <= py1 <= vehicle_bbox[3]
                    and vehicle_bbox[0] <= px2 <= vehicle_bbox[2]
                    and vehicle_bbox[1] <= py2 <= vehicle_bbox[3]
                ):
                    tracked_plates_with_vehicle_id.append(
                        (vehicle_id, px1, py1, px2, py2)
                    )

        return tracked_plates_with_vehicle_id

    def detect_characters(self, plate_image):
        """Detect characters in the number plate using the second YOLO model."""
        results = self.char_model(plate_image, verbose=False)
        characters = []

        # Process character detection results
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()  # Bounding boxes
            confidences = result.boxes.conf.cpu().numpy()  # Confidence scores
            class_ids = result.boxes.cls.cpu().numpy()  # Character class IDs
            names = result.names  # Character class names

            # Sort by x-coordinate first, then by y-coordinate to maintain top-to-bottom and left-to-right order
            sorted_indices = np.lexsort((boxes[:, 1], boxes[:, 0]))
            sorted_boxes = boxes[sorted_indices]
            sorted_texts = class_ids[sorted_indices]

            # Collect detected characters
            for box, text in zip(sorted_boxes, sorted_texts):
                char = names[int(text)]
                characters.append(char)

        return characters

    def get_plate_text(self, image, tracked_plates) -> list:
        """Get the text detected on the number plate along with the ID."""
        plate_info = []
        for track_id, x1, y1, x2, y2 in tracked_plates:
            # Crop the number plate region and process characters
            plate_image = image[y1:y2, x1:x2]
            if plate_image.shape[0] == 0 or plate_image.shape[1] == 0:
                # print("Invalid plate image dimensions:", plate_image.shape)
                continue
            characters = self.detect_characters(plate_image)
            plate_text = "".join(characters)

            # Add the ID and text of the plate to the result
            plate_info.append((track_id, plate_text))

        return plate_info

    def draw_bounding_boxes(self, image, plates):
        """Draw bounding boxes around the detected number plates and their characters."""
        for x1, y1, x2, y2, confidence in plates:
            # Draw the bounding box for the number plate
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Crop the number plate region and process characters
            plate_image = image[y1:y2, x1:x2]
            # plate_text = self.get_plate_text(plate_image)[0]

            # Display the detected text on the image
            cv2.putText(
                image,
                "license plate",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
            # print(f"Detected Number Plate: {plate_text}")

        return image

    def show_results(self, image, tracked_plates):
        """Visualize the detected number plates with bounding boxes and IDs on the image."""
        for track_id, x1, y1, x2, y2 in tracked_plates:
            # Draw the bounding box for the number plate
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Display the ID
            cv2.putText(
                image,
                f"ID: {track_id}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        result_image = cv2.resize(image, (1280, 720))
        cv2.imshow("Detected Number Plates with Tracking", result_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def process_video(self, video_path):
        """Process a video file with the full pipeline."""
        cap = cv2.VideoCapture(video_path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect number plates
            plates = self.detect_number_plate(frame)

            # Track number plates
            tracked_plates = self.track_number_plates(frame, plates)

            # Get plate text along with their IDs
            plate_info = self.get_plate_text(frame, tracked_plates)

            # Show the results (number plates with bounding boxes and IDs)
            self.show_results(frame, tracked_plates)

            # Print plate text with ID
            for track_id, plate_text in plate_info:
                print(f"Plate ID: {track_id}, Plate Text: {plate_text}")

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
