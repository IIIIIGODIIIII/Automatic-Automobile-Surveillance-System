# Vehicle Speed Detection and Tracking

This project implements a robust vehicle speed detection system using a combination of optical flow and perspective transformation. It leverages advanced computer vision techniques like YOLO for object detection, polygon zone transformation for accuracy in tracking, and calculates vehicle speeds in real-time.

---

## Key Features
- **Real-Time Speed Detection:** Tracks vehicles and estimates their speeds dynamically from video streams.
- **Advanced Object Detection:** Utilizes YOLO (You Only Look Once) for accurate vehicle detection.
- **Polygon Zone Transformation:** Improves tracking accuracy using perspective transformation.
- **Efficient Processing:** Designed to handle high-speed vehicles across multiple lanes.

---

### Methodology

#### 1. **Object Detection**
   - YOLO is used for detecting vehicles in video streams.
   - Only specific classes like `Car`, `Truck`, and `Bus` are targeted for processing.

#### 2. **Tracking with Optical Flow**
   - The bottom-center of the bounding box is tracked frame by frame using the Lucas-Kanade method.
   - Ensures accurate trajectory tracking, even in occlusions.

#### 3. **Polygon Zone Transformation**
   - Perspective transformation is applied to map points from the video frame to a real-world plane.
   - Provides better accuracy for distance and speed calculations.

#### 4. **Speed Estimation**
   - Speed is calculated based on transformed distances and frame processing rates.
   - Outputs the speed in km/h directly on the video feed.

---

### Results and Evaluation

#### **Accuracy Metrics**
- Mean Absolute Error (MAE): 2.5 km/h
- Root Mean Square Error (RMSE): 3.2 km/h

#### **Efficiency**
- Processing Speed: 
  - **With GPU (CUDA):** ~15 FPS
  - **Without GPU:** ~0.5 FPS
- **CPU Usage:** 95%
- **GPU Usage (with CUDA):** 70%

#### **Robustness**
- Tested under varying lighting conditions.
- Performs well across speeds ranging from 0 to 60 km/h.

---

### Installation

#### Prerequisites
- Python 3.8+
- OpenCV
- YOLO model files (`yolov8n.pt`)
- Supervision Library for advanced annotations.

#### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/IIIIIGODIIIII/Automatic-Automobile-Surveillance-System.git
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt requirement.txt

### Input Requirements
- Video Format: MP4 or similar.
- Resolution: Minimum of 480x640 recommended.
- FPS: Ensure consistent frame rates for accuracy.
  
### Future Scope
- Integration with LiDAR sensors: Enhance accuracy of distance measurements.
- High-Speed Vehicle Detection: Extend the capability to handle speeds >100 km/h.
- Edge Deployment: Optimize for deployment on edge devices like NVIDIA Jetson.
  
### Acknowledgments
- YOLOv8: Advanced object detection.
- Supervision Library: Robust tracking and annotation.
- OpenCV: Essential for image processing tasks.
