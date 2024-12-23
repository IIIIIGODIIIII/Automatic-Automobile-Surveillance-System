import argparse
import cv2
import numpy as np
from inference.models.utils import get_roboflow_model  # Import function to load the YOLO model
import supervision as sv  # Supervision library for tracking, annotations, and detection

# Define the polygon area for zone-based detection
SOURCE = np.array([[1252, 787], [2298, 803], [5039, 2159], [-550, 2159]])

# Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Speed Detection")
    return parser.parse_args()

# Main program execution
if __name__ == "__main__":
    args = parse_arguments()  # Parse command-line arguments

    # Load video information (e.g., resolution, frame rate)
    video_info = sv.VideoInfo.from_video_path("Projects\\Automobile Automobile Surveillance System\\Speed Detection\\vehicles.mp4")

    # Load the YOLOv8 model using Roboflow's utility
    model = get_roboflow_model("yolov8x-640")

    # Initialize ByteTrack for object tracking
    byte_track = sv.ByteTrack(frame_rate=video_info.fps)

    # Calculate optimal thickness for bounding boxes and text based on video resolution
    thickness = sv.calculate_optimal_line_thickness(resolution_wh=video_info.resolution_wh)
    text_scale = sv.calculate_optimal_text_scale(resolution_wh=video_info.resolution_wh)

    # Create annotators for bounding boxes and labels
    bounding_box_annotator = sv.BoxAnnotator(thickness=thickness)
    label_annotator = sv.LabelAnnotator(text_scale=text_scale, text_thickness=thickness)

    # Generator to fetch frames from the video
    frame_generator = sv.get_video_frames_generator("Projects\\Automobile Automobile Surveillance System\\Speed Detection\\vehicles.mp4")

    # Define a polygon zone to restrict detections to a specific area
    polygone_zone = sv.PolygonZone(SOURCE, frame_resolution_wh=video_info.resolution_wh)

    # Process each frame in the video
    for frame in frame_generator:
        # Perform inference on the current frame using the YOLO model
        result = model.infer(frame)[0]
        
        # Convert YOLO model's output into a Detections object
        detections = sv.Detections.from_inference(result)
        
        # Filter detections to include only those inside the polygon zone
        detections = detections[polygone_zone.trigger(detections)]
        
        # Update the tracker with the filtered detections
        detections = byte_track.update_with_detections(detections=detections)

        # Generate labels for the tracked objects using their tracker IDs
        labels = [
            f"#{tracker_id}"
            for tracker_id in detections.tracker_id
        ]

        # Create a copy of the frame for annotations
        annotated_frame = frame.copy()
        
        # Annotate the frame with bounding boxes
        annotated_frame = bounding_box_annotator.annotate(scene=annotated_frame, detections=detections)
        
        # Draw the polygon zone on the frame
        annotated_frame = sv.draw_polygon(annotated_frame, polygon=SOURCE, color=sv.Color.RED)
        
        # Annotate the frame with labels (tracker IDs)
        annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

        # Resize the window dynamically to match the frame size
        cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
        cv2.imshow("Frame", annotated_frame)
        cv2.resizeWindow("Frame", annotated_frame.shape[1], annotated_frame.shape[0])
        
        # Exit loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources and close the display window
    cv2.destroyAllWindows()
