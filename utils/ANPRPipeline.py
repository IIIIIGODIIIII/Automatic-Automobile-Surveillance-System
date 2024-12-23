import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO

class ANPRPipeline:
    def __init__(self, plate_model_path, char_model_path, confidence_threshold=0.5):
        # Load the YOLO models
        self.plate_model = YOLO(plate_model_path)  # Model for detecting number plates
        self.char_model = YOLO(char_model_path)    # Model for detecting characters
        self.confidence_threshold = confidence_threshold

    def preprocess_image(self, image):
        """Preprocess the input image (resize, normalize, etc.) if necessary."""
        # Implement any preprocessing if required (resizing, normalization, etc.)
        # This can be specific to how the models expect the input.
        return image

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

                    # Add padding of 20 pixels
                    padding = 20

                    # Extend the bounding box by the padding, ensuring we don't go out of image bounds
                    x1 = max(0, x1 - padding)  # Ensure x1 is not less than 0
                    y1 = max(0, y1 - padding)  # Ensure y1 is not less than 0
                    x2 = min(image.shape[1], x2 + padding)  # Ensure x2 doesn't exceed image width
                    y2 = min(image.shape[0], y2 + padding)  # Ensure y2 doesn't exceed image height

                    plates.append((x1, y1, x2, y2, confidence))


                    return plates

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

            # Sort by x-coordinate to maintain left-to-right order
            sorted_indices = np.argsort(boxes[:, 0])
            sorted_boxes = boxes[sorted_indices]
            sorted_texts = class_ids[sorted_indices]

            # Collect detected characters
            for box, text in zip(sorted_boxes, sorted_texts):
                char = names[int(text)]
                characters.append(char)

        return characters
    
    def get_plate_text(self, image,plates) -> list:
        """Get the text detected on the number plate."""
        plate_text_arr =[]
        for x1, y1, x2, y2, confidence in plates:
            # Draw the bounding box for the number plate
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Crop the number plate region and process characters
            plate_image = image[y1:y2, x1:x2]
            characters = self.detect_characters(plate_image)
            plate_text = ''.join(characters)
            plate_text_arr.append(plate_text)
        return plate_text_arr

    def draw_bounding_boxes(self, image, plates):
        """Draw bounding boxes around the detected number plates and their characters."""
        for x1, y1, x2, y2, confidence in plates:
            # Draw the bounding box for the number plate
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Crop the number plate region and process characters
            plate_image = image[y1:y2, x1:x2]
            # plate_text = self.get_plate_text(plate_image)[0]


            # Display the detected text on the image
            cv2.putText(image, "license plate", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # print(f"Detected Number Plate: {plate_text}")

        return image

    def show_results(self, image, plates):
        """Visualize the detected number plates with bounding boxes and characters on the image."""
        # Draw bounding boxes around number plates and their detected text
        result_image = self.draw_bounding_boxes(image, plates)
        
        # Show the final image with bounding boxes and detected text
        cv2.imshow("Detected Number Plates", result_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def process_video(self, video_path):
        """Process a video file with the full pipeline."""
        cap = cv2.VideoCapture(video_path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect number plates and draw bounding boxes
            plates = self.detect_number_plate(frame)

            # Show the results (number plates with bounding boxes and characters)
            self.show_results(frame, plates)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

    def process_image(self, image_path):
        """Process a single image."""
        image = cv2.imread(image_path)
        plates = self.detect_number_plate(image)
        self.show_results(image, plates)


# Example Usage
if __name__ == "__main__":
    # Define the paths to the YOLO model weights
    plate_model_path = "best_l.pt"  # Replace with your plate detection model path
    char_model_path = "best_charseg.pt"  # Replace with your character segmentation model path

    # Initialize the ANPR pipeline
    anpr_pipeline = ANPRPipeline(plate_model_path, char_model_path)

    # Process a single image
    image_path = r"number_plates_realworld/number_plate_18.jpg"  # Replace with the path to your test image
    anpr_pipeline.process_image(image_path)

    # Optionally, process a video
    video_path = r"videos/192.168.1.108_IP Camera_main_20241115154700.mp4"  # Replace with your video file path
    anpr_pipeline.process_video(video_path)
