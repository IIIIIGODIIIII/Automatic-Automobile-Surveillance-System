import cv2
import urllib.request
import numpy as np
import concurrent.futures
from cvlib.object_detection import detect_common_objects, draw_bbox

url = 'http://192.168.200.100/176x144.mjpeg'

def run1():
    cv2.namedWindow("live transmission", cv2.WINDOW_AUTOSIZE)
    stream = urllib.request.urlopen(url)
    buffer = bytes()

    while True:
        try:
            buffer += stream.read(1024)
            a = buffer.find(b'\xff\xd8')
            b = buffer.find(b'\xff\xd9')

            if a != -1 and b != -1:
                jpg = buffer[a:b+2]
                buffer = buffer[b+2:]

                im = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if im is not None:
                    cv2.imshow('live transmission', im)
                    key = cv2.waitKey(5)
                    if key == ord('q'):
                        break
        except Exception as e:
            print(f"Error decoding image: {e}")
            break

    cv2.destroyAllWindows()

def run2():
    cv2.namedWindow("detection", cv2.WINDOW_AUTOSIZE)
    stream = urllib.request.urlopen(url)
    buffer = bytes()

    while True:
        try:
            buffer += stream.read(1024)
            a = buffer.find(b'\xff\xd8')
            b = buffer.find(b'\xff\xd9')

            if a != -1 and b != -1:
                jpg = buffer[a:b+2]
                buffer = buffer[b+2:]

                im = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if im is not None:
                    bbox, label, conf = detect_common_objects(im)
                    im = draw_bbox(im, bbox, label, conf)
                    cv2.imshow('detection', im)
                    key = cv2.waitKey(5)
                    if key == ord('q'):
                        break
        except Exception as e:
            print(f"Error decoding image: {e}")
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    print("Started")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(run1)
        future2 = executor.submit(run2)
        
        # Wait for both threads to complete
        future1.result()
        future2.result()
