import argparse
import cv2
import numpy as np
from ultralytics import YOLO  # Import YOLO from ultralytics
import supervision as sv  # Supervision library for tracking, annotations, and detection
from collections import defaultdict, deque  # For tracking object coordinates
from utils.ANPRPipelineWithTracking import ANPRPipelineWithTracking
from utils.NumberPlatePredictor import NumberPlatePredictor

# from utils.VehicleStateExporter import VehicleStateExporter

# Define the polygon area for zone-based detection (adjust as per video resolution)
# SOURCE = np.array([[576, 555], [1054, 512], [2651, 1205], [1017, 1493]])
SOURCE = np.array([[576, 555], [1054, 512], [3080, 1155], [1017, 1493]])
MASK = np.array([(567, 520), (1224, 1921), (3080, 1155), (1300, 200)])

# Define dimensions for the target rectangle after perspective transformation
# TARGET_WIDTH = 3
TARGET_WIDTH = 3
TARGET_HEIGHT = 38
# TARGET_HEIGHT = 40

# Define the target rectangle's corner points for transformation
TARGET = np.array(
    [
        [0, 0],
        [TARGET_WIDTH - 1, 0],
        [TARGET_WIDTH - 1, TARGET_HEIGHT - 1],
        [0, TARGET_HEIGHT],
    ]
)

# ANPR
plate_model_path = "best_l.pt"
char_model_path = "best_char_200.pt"


# Initialize the ANPR pipeline with tracking
anpr_pipeline = ANPRPipelineWithTracking(plate_model_path, char_model_path)
number_plate_predictor = NumberPlatePredictor()

# Define a dictionary to store state information for each tracker ID
vehicle_states = {}


class VehicleState:
    def __init__(self):
        self.speeds = []  # List of speeds
        self.number_plate = None  # License plate text
        self.max_speed = 0  # Maximum recorded speed
        self.image = None  # Cropped vehicle image
        self.number_plate_confidence = 0  # Confidence score for the number plate


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
        self.m = cv2.getPerspectiveTransform(
            source.astype(np.float32), target.astype(np.float32)
        )

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
    video_path = r"C:\Users\samar\Desktop\capstone\anpr4.1\anprtest4\capstone_data\Main_Gate_Entry-_New_TIET_Gates_TIET_Gates_20241202092633_20241202094048_280254.mp4"
    args = parse_arguments()  # Parse command-line arguments

    # Load video information (e.g., resolution, frame rate)
    video_info = sv.VideoInfo.from_video_path(video_path)

    # Load the YOLOv8 model using the ultralytics library
    model = YOLO("yolo11m.pt")  # or replace with your model path if needed

    # Initialize ByteTrack for object tracking
    byte_track = sv.ByteTrack(
        frame_rate=video_info.fps,
        track_activation_threshold=0.35,
        minimum_matching_threshold=0.8,
        minimum_consecutive_frames=3,
    )

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
    frame_generator = sv.get_video_frames_generator(video_path)

    # Define a polygon zone to restrict detections to a specific area
    # polygone_zone = sv.PolygonZone(SOURCE, frame_resolution_wh=video_info.resolution_wh)
    polygon_mask = np.zeros(
        (video_info.resolution_wh[1], video_info.resolution_wh[0]), dtype=np.uint8
    )
    cv2.fillPoly(polygon_mask, [MASK], 255)

    # Initialize the view transformer with the source and target points
    view_transformer = ViewTransformer(SOURCE, TARGET)

    # Dictionary to store object coordinates with a rolling window of max length = video FPS
    coordinates = defaultdict(lambda: deque(maxlen=video_info.fps))

    # Process each frame in the video
    for frame_idx, frame in enumerate(frame_generator):
        print(f"Processing frame {frame_idx}")

        masked_frame = cv2.bitwise_and(frame, frame, mask=polygon_mask)
        # Perform inference on the current frame using the YOLO model from ultralytics
        results = model.predict(
            masked_frame, classes=[2, 3, 5, 7], verbose=False, conf=0.25
        )  # Inference for each frame

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
        # detections_sv = detections_sv[polygone_zone.trigger(detections_sv)]

        # Update the tracker with the filtered detections
        detections_sv = byte_track.update_with_detections(detections=detections_sv)
        # print(detections_sv)
        # Get anchor points (e.g., bottom-center) of detections
        points = detections_sv.get_anchors_coordinates(anchor=sv.Position.BOTTOM_CENTER)

        # Transform the anchor points to the target view
        points = view_transformer.transform_points(points=points)
        if points is not None:
            plates = anpr_pipeline.detect_number_plate(masked_frame)
            number_plate_text = ""
            final_plate_list = []
            if plates:
                tracked_plates = anpr_pipeline.track_numer_plates_vehical_data(
                    detections_sv, plates
                )
                number_plates = anpr_pipeline.get_plate_text(
                    masked_frame, tracked_plates
                )

                for number_plate in number_plates:
                    # print(number_plate)
                    print(number_plate)
                    number_plate_text, number_plate_confidence = (
                        number_plate_predictor.update_history(
                            number_plate[0], number_plate[1]
                        )
                    )
                    final_plate_list.append(
                        (number_plate[0], number_plate_text, number_plate_confidence)
                    )

            points = points.astype(int)
            # Update tracked object coordinates and calculate speeds
            labels = []
            for tracker_id, [_, y], (x1, y1, x2, y2) in zip(
                detections_sv.tracker_id, points, detections_sv.xyxy
            ):

                # Ensure a state exists for the current tracker ID
                if tracker_id not in vehicle_states:
                    vehicle_states[tracker_id] = VehicleState()

                current_vehicle_state = vehicle_states[tracker_id]
                coordinates[tracker_id].append(y)

                # Calculate speed if sufficient data points are available
                if len(coordinates[tracker_id]) >= video_info.fps / 2:
                    coordinates_start = coordinates[tracker_id][-1]
                    coordinates_end = coordinates[tracker_id][0]
                    distance = abs(coordinates_start - coordinates_end)
                    time = len(coordinates[tracker_id]) / video_info.fps
                    speed = distance / time * 3.6  # Convert m/s to km/h
                    number_plate_text = vehicle_states.get(tracker_id, "").number_plate
                    labels.append(
                        f"# {number_plate_text if number_plate_text else ""} {int(speed)} km/h"
                    )
                    # Update speed and max speed
                    current_vehicle_state.speeds.append(speed)
                    current_vehicle_state.max_speed = max(
                        current_vehicle_state.max_speed, speed
                    )
                else:
                    labels.append(
                        f"# {tracker_id}"
                    )  # Display ID until speed is calculated

                # Extract and store vehicle image
                if current_vehicle_state.image is None and (
                    number_plate_text or len(current_vehicle_state.speeds) > 10
                ):
                    current_vehicle_state.image = frame[
                        int(y1) : int(y2), int(x1) : int(x2)
                    ]

                if final_plate_list:
                    for plate_id, plate_text, plate_confidence in final_plate_list:
                        if plate_id == tracker_id:
                            if (
                                current_vehicle_state.number_plate is None
                                or plate_confidence
                                > current_vehicle_state.number_plate_confidence
                            ):
                                current_vehicle_state.number_plate = plate_text
                                current_vehicle_state.number_plate_confidence = (
                                    plate_confidence
                                )

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

            if number_plate_text:
                cv2.putText(
                    annotated_frame,
                    number_plate_text,
                    (200, 200),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    4,
                    (0, 255, 0),
                    4,
                )
            frame = annotated_frame

        frame = cv2.resize(frame, (1280, 720))
        # Resize the window dynamically to match the frame size
        cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
        cv2.imshow("Frame", masked_frame)
        # cv2.resizeWindow("Frame", frame.shape[1], frame.shape[0])
        # Exit loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release resources and close the display window
    cv2.destroyAllWindows()
