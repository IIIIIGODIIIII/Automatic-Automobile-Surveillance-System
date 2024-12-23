import argparse
import cv2
import numpy as np
from ultralytics import YOLO  # Import YOLO from ultralytics
import supervision as sv  # Supervision library for tracking, annotations, and detection
from collections import defaultdict, deque  # For tracking object coordinates
from utils.ANPRPipelineWithTracking import ANPRPipelineWithTracking
from utils.NumberPlatePredictor import NumberPlatePredictor
# Define the polygon area for zone-based detection (adjust as per video resolution)
SOURCE = np.array([[891, 215], [1060, 201], [197, 1177], [-79, 978]])

# Define dimensions for the target rectangle after perspective transformation
TARGET_WIDTH = 5.6
TARGET_HEIGHT = 41.5

# Define the target rectangle's corner points for transformation
TARGET = np.array(
    [
        [0, 0],
        [TARGET_WIDTH - 1, 0],
        [TARGET_WIDTH - 1, TARGET_HEIGHT - 1],
        [0, TARGET_HEIGHT],
    ]
)
# Define the paths to the YOLO model weights
plate_model_path = "best_l.pt"
char_model_path = "best_char_200.pt"

# video_path = r"C:\Users\samar\Desktop\capstone\anprtest4\videos\192.168.1.108_IP Camera_main_20241115162510.mp4"
# video_path = "rtsp://admin:123456@192.168.1.14/stream"
video_path = r"E:\Tech\Python\Projects\Automobile Automobile Surveillance System\Capstone Data\2.mp4"

# define example numberplates or fetch from DB
number_plate_db = [
    "HR01AR4949",
    "PB01A4470",
    "PB01D4802",
    "PB11DB4699",
    "PB11DF1112",
    "PB11DG8713",
    "PB11V0012",
    "PB13AN9198",
    "PB13AW0055",
    "PB23U1292",
    "PB31N1297",
    "PB39B0002",
    "HP02Z1086",
    "PB11DC0012",
    "PB91D2222",
    "PB11DB5138",
    "PB91N0593",
    "PB11DD2667",
    "T1024PB0311G",
    "CH02AA8347",
    "CH01AM1485",
    "UP15CX4041",
    "PB23U1292",
    "PB11DC0012",
    "PB11BB9800",
]

# Initialize the ANPR pipeline with tracking
anpr_pipeline = ANPRPipelineWithTracking(plate_model_path, char_model_path)
number_plate_predictor = NumberPlatePredictor(number_plate_db)
# Class for performing perspective transformation
class ViewTransformer:
    def __init__(self, source: np.ndarray, target: np.ndarray):
        """
        Initialize the perspective transformation matrix.

        Parameters:
        - source: Points in the original view.
        - target: Points in the transformed view.
        """
        # Compute the perspective transformation matrix
        self.m = cv2.getPerspectiveTransform(source.astype(np.float32), target.astype(np.float32))

    def transform_points(self, points: np.ndarray) -> np.ndarray:
        """
        Transform points from source perspective to target perspective.

        Parameters:
        - points: Array of points in the original view.

        Returns:
        - Transformed points in the target view.
        """
        if points is None or len(points) == 0:
            return None
        reshaped_points = np.array([points], dtype=np.float32)
        transformed_points = cv2.perspectiveTransform(reshaped_points, self.m)
        if transformed_points is not None and len(transformed_points) > 0:
            return transformed_points[0]
        else:
            return None

# Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Speed Detection")
    return parser.parse_args()

# Main program execution
if __name__ == "__main__":
    args = parse_arguments()  # Parse command-line arguments

    # Load video information (e.g., resolution, frame rate)
    video_info = sv.VideoInfo.from_video_path(video_path
       
    )

    # Load the YOLOv8 model using the ultralytics library
    model = YOLO("yolov8n.pt")  # or replace with your model path if needed

    # Initialize ByteTrack for object tracking
    byte_track = sv.ByteTrack(frame_rate=video_info.fps)

    # Calculate optimal thickness for bounding boxes and text based on video resolution
    thickness = sv.calculate_optimal_line_thickness(
        resolution_wh=video_info.resolution_wh
    )
    text_scale = sv.calculate_optimal_text_scale(resolution_wh=video_info.resolution_wh)

    # Create annotators for bounding boxes, labels, and object traces
    bounding_box_annotator = sv.BoxAnnotator(
        thickness=thickness, color_lookup=sv.ColorLookup.TRACK
    )
    label_annotator = sv.LabelAnnotator(
        text_scale=text_scale,
        text_thickness=thickness,
        text_position=sv.Position.BOTTOM_CENTER,
        color_lookup=sv.ColorLookup.TRACK,
    )
    trace_annotator = sv.TraceAnnotator(
        thickness=thickness,
        trace_length=video_info.fps * 2,
        position=sv.Position.BOTTOM_CENTER,
        color_lookup=sv.ColorLookup.TRACK,
    )

    # Generator to fetch frames from the video
    frame_generator = sv.get_video_frames_generator(
        video_path
    )

    # Define a polygon zone to restrict detections to a specific area
    polygone_zone = sv.PolygonZone(SOURCE)

    # Initialize the view transformer with the source and target points
    view_transformer = ViewTransformer(SOURCE, TARGET)

    # Dictionary to store object coordinates with a rolling window of max length = video FPS
    coordinates = defaultdict(lambda: deque(maxlen=video_info.fps))

    # Process each frame in the video
    for frame_idx, frame in enumerate(frame_generator):
        print(f"Processing frame {frame_idx}")

        # Perform inference on the current frame using the YOLO model from ultralytics
        results = model.predict(frame, classes = [2,3,5,7])  # Inference for each frame

        # Extract detections from the results
        detections = results[0].boxes  # Get bounding boxes from the first result

        # Extract bounding box coordinates, confidence, and class IDs
        xywh = (
            detections.xyxy.cpu().numpy()
        )  # Move tensor to CPU and convert to NumPy array
        confidence = detections.conf.cpu().numpy()  # Same for confidence
        class_id = detections.cls.cpu().numpy()  # Same for class IDs

        # Create a Supervision Detections object from the YOLO results
        detections_sv = sv.Detections(
            xyxy=xywh,  # Bounding boxes in xywh format
            confidence=confidence,  # Confidence scores
            class_id=class_id,  # Class IDs
        )

        # Filter detections to include only those inside the polygon zone
        detections_sv = detections_sv[polygone_zone.trigger(detections_sv)]

        # Update the tracker with the filtered detections
        detections_sv = byte_track.update_with_detections(detections=detections_sv)

        # Get anchor points (e.g., bottom-center) of detections
        points = detections_sv.get_anchors_coordinates(anchor=sv.Position.BOTTOM_CENTER)

        # Transform the anchor points to the target view
        points = view_transformer.transform_points(points=points)
        if points is not None:
            plates = anpr_pipeline.detect_number_plate(frame)
            number_plate_text = ""
            if plates:
                tracked_plates = anpr_pipeline.track_number_plates1(detections_sv, plates)

                number_plates = anpr_pipeline.get_plate_text(frame, tracked_plates)
                result_image = anpr_pipeline.draw_bounding_boxes(frame, plates)
                # anpr_pipeline.show_results(frame, plates)
                for number_plate in number_plates:
                    # print(number_plate)
                    # print(number_plate)
                    number_plate_text = number_plate_predictor.update_history(
                        number_plate[0], number_plate[1]
                    )


            points = points.astype(int)

            # Update tracked object coordinates and calculate speeds
            labels = []
            for tracker_id, [_, y] in zip(detections_sv.tracker_id, points):
                coordinates[tracker_id].append(y)

                # Calculate speed if sufficient data points are available
                if len(coordinates[tracker_id]) >= video_info.fps / 2:
                    coordinates_start = coordinates[tracker_id][-1]
                    coordinates_end = coordinates[tracker_id][0]
                    distance = abs(coordinates_start - coordinates_end)
                    time = len(coordinates[tracker_id]) / video_info.fps
                    speed = distance / time * 3.6  # Convert m/s to km/h
                    labels.append(f"# {tracker_id} {int(speed)} km/h")
                else:
                    labels.append(f"# {tracker_id}")  # Display ID until speed is calculated

            # Create a copy of the frame for annotations
            annotated_frame = frame.copy()

            # Annotate traces of objects
            annotated_frame = trace_annotator.annotate(
                scene=annotated_frame, detections=detections_sv
            )

            # Annotate the frame with bounding boxes
            annotated_frame = bounding_box_annotator.annotate(
                scene=annotated_frame, detections=detections_sv
            )

            # Draw the polygon zone on the frame
            annotated_frame = sv.draw_polygon(
                annotated_frame, polygon=SOURCE, color=sv.Color.RED
            )

            # Annotate the frame with labels (transformed coordinates and speeds)
            annotated_frame = label_annotator.annotate(
                scene=annotated_frame, detections=detections_sv, labels=labels
            )

            frame = annotated_frame

        # Resize the window dynamically to match the frame size
        cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
        cv2.imshow("Frame", frame)
        cv2.resizeWindow("Frame", frame.shape[1], frame.shape[0])

        # Exit loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release resources and close the display window
    cv2.destroyAllWindows()