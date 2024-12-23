import time as t
import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
from collections import defaultdict, deque
from utils.ANPRPipelineWithTracking import ANPRPipelineWithTracking
from utils.NumberPlatePredictor import NumberPlatePredictor
import requests


class SpeedDetectionSystem:
    def __init__(
        self,
        video_path,
        plate_model_path,
        char_model_path,
        yolo_model_path,
        api_url,
        mask=True,
    ):
        self.video_path = video_path
        self.plate_model_path = plate_model_path
        self.char_model_path = char_model_path
        self.yolo_model_path = yolo_model_path
        self.api_url = api_url

        self.anpr_pipeline = ANPRPipelineWithTracking(
            plate_model_path, char_model_path, self_track=False
        )
        self.number_plate_predictor = NumberPlatePredictor()

        self.vehicle_states = {}
        self.coordinates = defaultdict(lambda: deque(maxlen=30))

        # Initialize YOLO model
        self.model = YOLO(yolo_model_path)

        # Load video info
        self.video_info = sv.VideoInfo.from_video_path(video_path)

        # Initialize ByteTrack for tracking
        self.byte_track = sv.ByteTrack(
            frame_rate=self.video_info.fps,
            track_activation_threshold=0.35,
            minimum_matching_threshold=0.8,
            minimum_consecutive_frames=3,
        )

        # Define polygon mask
        self.polygon_mask = np.zeros(
            (self.video_info.resolution_wh[1], self.video_info.resolution_wh[0]),
            dtype=np.uint8,
        )
        self.SOURCE = np.array([[576, 555], [1054, 512], [3080, 1155], [1017, 1493]])
        self.TARGET = np.array(
            [[0, 0], [2, 0], [2, 38], [0, 38]]
        )  # Adjust as per calibration
        self.MASK = np.array([(567, 520), (1224, 1921), (3080, 1155), (1300, 200)])
        cv2.fillPoly(self.polygon_mask, [self.MASK], 255)
        self.mask = mask
        # Perspective transformation
        self.view_transformer = ViewTransformer(self.SOURCE, self.TARGET)

        # Annotators
        self.thickness = sv.calculate_optimal_line_thickness(
            self.video_info.resolution_wh
        )
        self.text_scale = sv.calculate_optimal_text_scale(self.video_info.resolution_wh)
        self.bounding_box_annotator = sv.BoxAnnotator(
            thickness=self.thickness, color_lookup=sv.ColorLookup.TRACK
        )
        self.label_annotator = sv.LabelAnnotator(
            text_scale=self.text_scale,
            text_thickness=self.thickness,
            text_position=sv.Position.BOTTOM_CENTER,
            color_lookup=sv.ColorLookup.TRACK,
        )
        self.trace_annotator = sv.TraceAnnotator(
            thickness=self.thickness,
            trace_length=self.video_info.fps * 2,
            position=sv.Position.BOTTOM_CENTER,
            color_lookup=sv.ColorLookup.TRACK,
        )

        # Request scheduler
        self.request_schuler = set()

    class VehicleState:
        def __init__(self):
            self.speeds = []
            self.number_plate = None
            self.max_speed = 0
            self.image = None
            self.number_plate_confidence = 0
            self.last_request_time_numberplate = 0
            self.last_request_time_overspeeding = 0
            self.last_update = 0

    def process_frame(self, frame):
        if self.mask:
            masked_frame = cv2.bitwise_and(frame, frame, mask=self.polygon_mask)
        else:
            masked_frame = frame.copy()

        results = self.model.predict(
            masked_frame, classes=[2, 3, 5, 7, 67], verbose=False, conf=0.25
        )
        detections = results[0].boxes

        xywh = detections.xyxy.cpu().numpy()
        confidence = detections.conf.cpu().numpy()
        class_id = detections.cls.cpu().numpy()

        detections_sv = sv.Detections(
            xyxy=xywh, confidence=confidence, class_id=class_id
        )
        detections_sv = self.byte_track.update_with_detections(detections=detections_sv)

        points = detections_sv.get_anchors_coordinates(anchor=sv.Position.BOTTOM_CENTER)
        points = self.view_transformer.transform_points(points)

        final_plate_list = []
        labels = []  # Annotations to display
        if points is not None:
            plates = self.anpr_pipeline.detect_number_plate(masked_frame)
            if plates:
                tracked_plates = self.anpr_pipeline.track_numer_plates_vehical_data(
                    detections_sv, plates
                )
                number_plates = self.anpr_pipeline.get_plate_text(
                    masked_frame, tracked_plates
                )
                for number_plate in number_plates:
                    number_plate_text, confidence = (
                        self.number_plate_predictor.update_history(
                            number_plate[0], number_plate[1]
                        )
                    )
                    final_plate_list.append(
                        (number_plate[0], number_plate_text, confidence)
                    )

            for tracker_id, [_, y], (x1, y1, x2, y2) in zip(
                detections_sv.tracker_id, points, detections_sv.xyxy
            ):
                if tracker_id not in self.vehicle_states:
                    self.vehicle_states[tracker_id] = self.VehicleState()

                current_vehicle_state = self.vehicle_states[tracker_id]
                self.coordinates[tracker_id].append(y)
                current_vehicle_state.last_update = t.time()
                if len(self.coordinates[tracker_id]) >= self.video_info.fps / 2:
                    coordinates_start = self.coordinates[tracker_id][-1]
                    coordinates_end = self.coordinates[tracker_id][0]
                    distance = abs(coordinates_start - coordinates_end)
                    time = len(self.coordinates[tracker_id]) / self.video_info.fps
                    speed = distance / time * 3.6

                    current_vehicle_state.speeds.append(speed)
                    current_vehicle_state.max_speed = max(
                        current_vehicle_state.max_speed, speed
                    )

                    if speed > 30:  # Example threshold
                        self.send_alert(
                            tracker_id, speed, current_vehicle_state.number_plate
                        )

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
                                self.send_alert(tracker_id, speed, plate_text)

                # Create labels for the annotations
                label = f"# {tracker_id} | Speed: {int(current_vehicle_state.max_speed)} km/h"
                if current_vehicle_state.number_plate:
                    label += f" | Plate: {current_vehicle_state.number_plate}"
                labels.append(label)

        # Annotate frame
        annotated_frame = frame.copy()
        annotated_frame = self.trace_annotator.annotate(
            scene=annotated_frame, detections=detections_sv
        )
        annotated_frame = self.bounding_box_annotator.annotate(
            scene=annotated_frame, detections=detections_sv
        )
        annotated_frame = self.label_annotator.annotate(
            scene=annotated_frame, detections=detections_sv, labels=labels
        )
        return annotated_frame, self.vehicle_states

    def send_alert(self, tracker_id, speed, number_plate):
        current_time = t.time()
        vehicle_state = self.vehicle_states.get(tracker_id)

        if vehicle_state:
            # Check for number plate alert
            last_request_time_numberplate = vehicle_state.last_request_time_numberplate
            if number_plate and current_time - last_request_time_numberplate >= 30:
                self.vehicle_states[tracker_id].last_request_time_numberplate = (
                    current_time
                )
                print(f"Number plate alert for tracker ID {tracker_id}: {number_plate}")
                # payload = {
                #     "tracker_id": tracker_id,
                #     "speed": speed,
                #     "number_plate": number_plate,
                # }
                # try:
                #     response = requests.post(self.api_url, json=payload)
                #     if response.status_code == 200:
                #         print(f"Number plate alert sent successfully for tracker ID {tracker_id}")
                #     else:
                #         print(f"Failed to send number plate alert for tracker ID {tracker_id}: {response.text}")
                # except requests.RequestException as e:
                #     print(f"Error sending number plate alert: {e}")

            # Check for overspeeding alert
            last_request_time_overspeeding = (
                vehicle_state.last_request_time_overspeeding
            )

            if speed > 30 and current_time - last_request_time_overspeeding >= 30:
                if self.vehicle_states[tracker_id].number_plate or (
                    number_plate and vehicle_state.number_plate_confidence > 0.95
                ):
                    self.vehicle_states[tracker_id].last_request_time_overspeeding = (
                        current_time
                    )
                    print(
                        f"Overspeeding alert for tracker ID {tracker_id}: {speed} km/h | {number_plate or self.vehicle_states[tracker_id].number_plate }"
                    )
                    if tracker_id in self.request_schuler:
                        self.request_schuler.remove(tracker_id)
                # payload = {
                #     "tracker_id": tracker_id,
                #     "speed": speed,
                #     "number_plate": number_plate if number_plate else "",
                # }
                # try:
                #     response = requests.post(self.api_url, json=payload)
                #     if response.status_code == 200:
                #         print(f"Overspeeding alert sent successfully for tracker ID {tracker_id}")
                #     else:
                #         print(f"Failed to send overspeeding alert for tracker ID {tracker_id}: {response.text}")
                # except requests.RequestException as e:
                #     print(f"Error sending overspeeding alert: {e}")
                else:
                    self.request_schuler.add(tracker_id)
                    print(f"Scheduled update for tracker ID {tracker_id}")

            for i in list(self.request_schuler):
                num = self.vehicle_states[i].number_plate
                if (
                    num
                    or (
                        current_time - vehicle_state.last_update >= 4
                        or self.vehicle_states[i].number_plate_confidence > 0.95
                    )
                    and i in self.request_schuler
                ):
                    self.send_alert(i, self.vehicle_states[i].max_speed, num)
                    # self.request_schuler.remove(i)
                else:
                    print(
                        f"Tracker ID {i} not updated as {current_time - vehicle_state.last_update} or {num} with {self.vehicle_states[i].number_plate_confidence}"
                    )

    def run(self):
        frame_generator = sv.get_video_frames_generator(self.video_path)
        for frame_idx, frame in enumerate(frame_generator):
            processed_frame, _ = self.process_frame(frame)
            frame = cv2.resize(processed_frame, (1280, 720))
            cv2.imshow("Frame", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cv2.destroyAllWindows()


class ViewTransformer:
    def __init__(self, source: np.ndarray, target: np.ndarray):
        self.m = cv2.getPerspectiveTransform(
            source.astype(np.float32), target.astype(np.float32)
        )

    def transform_points(self, points: np.ndarray) -> np.ndarray:
        if points is None or len(points) == 0:
            return None
        reshaped_points = np.array([points], dtype=np.float32)
        transformed_points = cv2.perspectiveTransform(reshaped_points, self.m)
        return transformed_points[0] if transformed_points is not None else None


# Usage example
if __name__ == "__main__":
    video_path = "path_to_video.mp4"
    plate_model_path = "best_l.pt"
    char_model_path = "best_char_200.pt"
    yolo_model_path = "yolo11m.pt"
    api_url = "http://example.com/api/alerts"

    system = SpeedDetectionSystem(
        video_path, plate_model_path, char_model_path, yolo_model_path, api_url
    )
    system.run()
