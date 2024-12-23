from ultralytics import YOLO

if __name__ == "__main__":
    # LOAD MODEL
    model = YOLO('./runs//detect//train5//weights//best.pt')

    # TRAIN THE MODEL
    results = model.train(data = 'config.yaml',imgsz=640,epochs =40)