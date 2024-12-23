- yolo need data in specific format
- class centerx centery height_BB width_BB
- [cvat.ai](https://www.cvat.ai/) for annotating images 
- imgs shd be in data / images and data /lables
- data / images / train or test             
---
# TO download Dataset
- configure api key in .env file
- run 
```bash
python downloadDataset.py
```

# YOLO config.yml file
- prefer absolute path for path keyword 

# Running training 
[issue-gpu-1](https://github.com/ultralytics/ultralytics/issues/348)
sol: add if __name__ == "__main__":
[issue-gpu-2](https://github.com/ultralytics/ultralytics/issues/664)
