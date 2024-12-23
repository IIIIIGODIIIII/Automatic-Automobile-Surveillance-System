from utils.SpeedDetectionSystem import SpeedDetectionSystem
import cv2
import supervision as sv

# CONSTANTS
# video_path = r"E:\Tech\Python\Projects\Automobile Automobile Surveillance System\Capstone Data\Main_Gate_Entry-_New_TIET_Gates_TIET_Gates_20241202092633_20241202094048_280254.mp4"
video_path = r"C:\Users\samar\Desktop\capstone\anpr4.1\anprtest4\capstone_data\Main_Gate_Entry-_New_TIET_Gates_TIET_Gates_20241202092633_20241202094048_280254.mp4"
plate_model_path = "best_l.pt"
char_model_path = "best_char_200.pt"
yolo_model_path = "yolo11n.pt"
api_url = "http://example.com/api/alerts"


# Create the system
system = SpeedDetectionSystem(
    video_path, plate_model_path, char_model_path, yolo_model_path, api_url
)


# vehicle States

frame_generator = sv.get_video_frames_generator(video_path)
for frame_idx, frame in enumerate(frame_generator):
    processed_frame, vehicle_states = system.process_frame(frame)
    frame = cv2.resize(processed_frame, (1280, 720))
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cv2.destroyAllWindows()
