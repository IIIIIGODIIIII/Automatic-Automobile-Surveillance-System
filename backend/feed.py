# feed.py

import cv2
import base64
import asyncio
import websockets
import json
import sys


async def send_video(websocket, path, feedId):
    if path != f"/{feedId}":
        await websocket.close()
        print(f"Unsupported path: {path}", file=sys.stderr)
        return

    print(f"Accepted connection on path: {path} with feedId: {feedId}")
    # camera = cv2.VideoCapture(0,cv2.CAP_DSHOW)  # Modify as needed for different feeds
    rtsp_url = 'rtsp://admin:123456@192.168.1.14/stream'
    camera = cv2.VideoCapture(rtsp_url)

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

            # Encode the frame to JPEG
            _, buffer = cv2.imencode(".jpg", frame)
            frame_data = base64.b64encode(buffer).decode("utf-8")

            # Create the message with feedId and frame data
            message = {
                "type": "videoFrame",
                "data": {"feedId": feedId, "frame": frame_data},
            }

            await websocket.send(json.dumps(message))

            # Control frame rate (~60 fps)
            await asyncio.sleep(1/60)
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed", file=sys.stderr)
    finally:
        camera.release()
        print("Camera released")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python feed.py <feedId>", file=sys.stderr)
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
