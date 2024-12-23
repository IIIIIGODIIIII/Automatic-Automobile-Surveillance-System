# feed.py

import cv2
import base64
import asyncio
import websockets
import json
import sys
import os

import supervision as sv

# import sys
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.SpeedDetectionSystem import SpeedDetectionSystem

# Define the paths to the YOLO model weights
plate_model_path = r"../best_l.pt"
char_model_path = r"../best_char_200.pt"
yolo_model_path = r"../yolo11n.pt"
api_url = "http://example.com/api/alerts"


# video_path = r"C:\Users\samar\Desktop\capstone\anprtest4\videos\192.168.1.108_IP Camera_main_20241115162510.mp4"
# video_path = "rtsp://admin:123456@192.168.1.14/stream"
# video_path = r"C:\Users\samar\Desktop\capstone\anprtest4\capstone_data\Main_Gate_Entry-_New_TIET_Gates_TIET_Gates_20241202084658_20241202092633_202008.mp4"
# video_path = r"C:\Users\samar\Desktop\capstone\anpr4.1\anprtest4\videos\192.168.1.108_IP Camera_main_20241115162510.mp4"
# video_path = r"E:\Tech\Python\Projects\Automobile Automobile Surveillance System\Capstone Data\Main_Gate_Entry-_New_TIET_Gates_TIET_Gates_20241202092633_20241202094048_280254.mp4"
# video_path = r"E:\Tech\Python\Projects\Automobile Automobile Surveillance System\Capstone Data\mardomujhe.mp4"
# video_path = 0


video_path = r"C:\Users\samar\Desktop\capstone\anpr4.1\anprtest4\capstone_data\Main_Gate_Entry-_New_TIET_Gates_TIET_Gates_20241202092633_20241202094048_280254.mp4"
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

    video_generator = sv.get_video_frames_generator(video_path)

    async def async_video_generator(syncGen):
        for frame in syncGen:
            yield frame

    try:
        async for frame in async_video_generator(video_generator):
            processed_frame, vehicle_states = system.process_frame(frame)
            overspeeding_data = [
                {
                    "vehicle_id": int(state),
                    "number_plate": vehicle_states[state].number_plate,
                    "max_speed": int(vehicle_states[state].max_speed),
                }
                for state in vehicle_states
                if vehicle_states[state].max_speed > 30
            ]
            frame = cv2.resize(processed_frame, (1280, 720))
            # print(overspeeding_data)
            # Encode the frame to JPEG
            _, buffer = cv2.imencode(".jpg", frame)
            frame_data = base64.b64encode(buffer).decode("utf-8")

            # Create the message with feedId and frame data
            message = {
                "type": "videoFrame",
                "data": {
                    "feedId": feedId,
                    "frame": frame_data,
                    "overspeeding_data": overspeeding_data,
                },
            }
            try:
                a = json.dumps(message)
                # print(message["data"]["overspeeding_data"])
                # print('c')
            except:
                # print('p')
                # print(message["data"]["overspeeding_data"])
                a = {
                    "type": "videoFrame",
                    "data": {
                        "feedId": feedId,
                        "frame": frame_data,
                        "overspeeding_data": [],
                    },
                }
                a = json.dumps(a)
            # print(a)
            await websocket.send(a)

            # Control frame rate (~30 fps)
            # await asyncio.sleep(1/60)
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed", file=sys.stderr)
    finally:
        video_generator.close()
        print("Video generator closed")


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
