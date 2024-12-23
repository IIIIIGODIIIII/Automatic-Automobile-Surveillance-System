import cv2
import numpy as np

# List to store points
points = []

# Mouse callback function to capture points
def get_points(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Adjust the coordinates to consider the top-left corner of the video frame as (0, 0)
        adjusted_x = x - param['padding']
        adjusted_y = y - param['padding']
        points.append((adjusted_x, adjusted_y))
        print(f"Point marked: {(adjusted_x, adjusted_y)}")

# Function to draw a ruler on the whiteboard
def draw_ruler(whiteboard, padding, frame_height, frame_width):
    height, width, _ = whiteboard.shape
    for i in range(padding, height - padding, 50):
        cv2.line(whiteboard, (padding, i), (width - padding, i), (0, 0, 0), 1)
        cv2.putText(whiteboard, f"{i - padding}", (10, i), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    for i in range(padding, width - padding, 50):
        cv2.line(whiteboard, (i, padding), (i, height - padding), (0, 0, 0), 1)
        cv2.putText(whiteboard, f"{i - padding}", (i, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

# Function to mark points on a single video frame
def mark_points_on_video(video_path, padding=100):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame from video.")
        return

    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Frame", get_points, {'padding': padding})

    # Create a whiteboard with padding
    whiteboard_height = frame.shape[0] + 2 * padding
    whiteboard_width = frame.shape[1] + 2 * padding
    whiteboard = np.ones((whiteboard_height, whiteboard_width, 3), dtype=np.uint8) * 255

    # Place the frame in the center of the whiteboard
    whiteboard[padding:padding + frame.shape[0], padding:padding + frame.shape[1]] = frame

    # Draw the ruler on the whiteboard
    draw_ruler(whiteboard, padding, frame.shape[0], frame.shape[1])

    while True:
        # Draw points on the whiteboard
        for point in points:
            # Adjust the points back to the whiteboard coordinate system for drawing
            cv2.circle(whiteboard, (point[0] + padding, point[1] + padding), 5, (0, 255, 0), -1)

        cv2.imshow("Frame", whiteboard)
        cv2.resizeWindow("Frame", whiteboard.shape[1], whiteboard.shape[0])

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Path to your video file
video_path = "Capstone Data\\2.mp4"
mark_points_on_video(video_path)