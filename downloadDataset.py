import os
from dotenv import load_dotenv
from roboflow import Roboflow
import shutil
load_dotenv()

# put your api key in a .env file
rf = Roboflow(api_key=os.getenv('ROBOFLOW_API_KEY'))
project = rf.workspace("roboflow-universe-projects").project("license-plate-recognition-rxg4e")
version = project.version(4)
dataset = version.download("yolov8")


current_dir = os.curdir

source_train = os.path.join(os.curdir,'License-Plate-Recognition-4','train')
source_test = os.path.join(os.curdir,'License-Plate-Recognition-4','test')
source_valid = os.path.join(os.curdir,'License-Plate-Recognition-4','valid')
destination_train = os.path.join(os.curdir,'datasets','train')
destination_test = os.path.join(os.curdir,'datasets','test')
destination_valid = os.path.join(os.curdir,'datasets','valid')
shutil.move(source_train, destination_train)
shutil.move(source_test, destination_test)
shutil.move(source_valid, destination_valid)