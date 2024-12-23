# feed.py

import cv2
import base64
import asyncio
import websockets
import json
import sys
import os

import supervision

# import sys
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.SpeedDetectionSystem import SpeedDetectionSystem
import supervision as sv

# Define the paths to the YOLO model weights
plate_model_path = r"../best_l.pt"
char_model_path = r"../best_char_200.pt"
yolo_model_path = r"../yolo11m.pt"
api_url = "http://example.com/api/alerts"


# video_path = r"C:\Users\samar\Desktop\capstone\anprtest4\videos\192.168.1.108_IP Camera_main_20241115162510.mp4"
# video_path = "rtsp://admin:123456@192.168.1.14/stream"
# video_path = r"C:\Users\samar\Desktop\capstone\anprtest4\capstone_data\Main_Gate_Entry-_New_TIET_Gates_TIET_Gates_20241202084658_20241202092633_202008.mp4"
# video_path = r"C:\Users\samar\Desktop\capstone\anpr4.1\anprtest4\videos\192.168.1.108_IP Camera_main_20241115162510.mp4"
video_path = r"E:\Tech\Python\Projects\Automobile Automobile Surveillance System\Capstone Data\Main_Gate_Entry-_New_TIET_Gates_TIET_Gates_20241202092633_20241202094048_280254.mp4"
# video_path = 0
# Initialize the ANPR pipeline with tracking
# anpr_pipeline = ANPRPipelineWithTracking(plate_model_path, char_model_path)
# number_plate_predictor = NumberPlatePredictor()
# Create the system
if video_path == 0:
    mask = False
else:
    mask = True
system = SpeedDetectionSystem(
    video_path, plate_model_path, char_model_path, yolo_model_path, api_url, mask
)
print(mask)

async def send_video(websocket, path, feedId):
    if path != f"/{feedId}":
        await websocket.close()
        print(f"Unsupported path: {path}", file=sys.stderr)
        return

    print(f"Accepted connection on path: {path} with feedId: {feedId}")
    # camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Modify as needed for different feeds
    # camera = cv2.VideoCapture(0)  # Modify as needed for different feed

    camera = cv2.VideoCapture(video_path)  # Modify as needed for different feeds
    if not camera.isOpened():
        print("Failed to open camera", file=sys.stderr)
        await websocket.close()
        return

    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                print("Failed to read frame from camera", file=sys.stderr)
                break

            processed_frame, vehicle_states = system.process_frame(frame)
            frame = cv2.resize(processed_frame, (1280, 720))

            # Encode the frame to JPEG
            _, buffer = cv2.imencode(".jpg", frame)
            frame_data = base64.b64encode(buffer).decode("utf-8")

            # Create the message with feedId and frame data
            message = {
                "type": "videoFrame",
                "data": {"feedId": feedId, "frame": frame_data},
            }

            await websocket.send(json.dumps(message))

            # Control frame rate (~30 fps)
            # await asyncio.sleep(0.033)
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed", file=sys.stderr)
    finally:
        camera.release()
        print("Camera released")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python feed_model.py <feedId>", file=sys.stderr)
        sys.exit(1)

    feedId = sys.argv[1]
    port = 3000  # Base port; will increment based on feedId

    # Map feedId to port
    try:
        feed_number = int(feedId.replace("feed", ""))
        port = 3000 + feed_number  # e.g., feed16 -> 3016
    except ValueError:
        print("Invalid feedId format. Use 'feed<number>'", file=sys.stderr)
        sys.exit(1)

    start_server = websockets.serve(
        lambda ws, path: send_video(ws, path, feedId), "0.0.0.0", port
    )
    asyncio.get_event_loop().run_until_complete(start_server)
    print(
        f"Python WebSocket server for {feedId} started on ws://0.0.0.0:{port}/{feedId}"
    )
    asyncio.get_event_loop().run_forever()
