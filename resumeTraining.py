from ultralytics import YOLO
import os
# PATH_LAST_MODEL =os.path.join(os.curdir,"runs","detect","train","weights""last.pt")

# print(PATH_LAST_MODEL)
if __name__ == "__main__":
    # LOAD MODEL
    model = YOLO(".\\runs\\detect\\train5\\weights\\last.pt")


    # TRAIN THE MODEL
    results = model.train(epochs =500,resume = True)