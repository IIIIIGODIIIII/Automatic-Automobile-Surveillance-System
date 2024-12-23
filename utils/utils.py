import numpy as np
import cv2
import matplotlib.pyplot as plt
from skimage import morphology


def find_contours(dimensions, img, contour_img):
    cntrs, hierarchy = cv2.findContours(
        img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    lower_width, upper_width, lower_height, upper_height = dimensions
    cntrs = sorted(cntrs, key=cv2.contourArea, reverse=True)[
        :25
    ]  # Increased number of contours to check

    x_cntr_list = []
    img_res = []
    for cntr in cntrs:
        intX, intY, intWidth, intHeight = cv2.boundingRect(cntr)
        aspect_ratio = float(intWidth) / intHeight
        if (
            lower_width < intWidth < upper_width
            and lower_height < intHeight < upper_height
            and 0.2 < aspect_ratio < 1.0
        ):
            hull = cv2.convexHull(cntr)
            hull_area = cv2.contourArea(hull)
            if hull_area > 0:
                solidity = float(cv2.contourArea(cntr)) / hull_area
                if solidity > 0.5:
                    x_cntr_list.append(intX)
                    char_copy = np.zeros((44, 24))
                    char = img[intY : intY + intHeight, intX : intX + intWidth]
                    char = cv2.resize(char, (20, 40))
                    cv2.rectangle(
                        contour_img,
                        (intX, intY),
                        (intX + intWidth, intY + intHeight),
                        (50, 21, 200),
                        2,
                    )
                    char = cv2.subtract(255, char)
                    char_copy[2:42, 2:22] = char
                    char_copy[0:2, :] = 0
                    char_copy[:, 0:2] = 0
                    char_copy[42:44, :] = 0
                    char_copy[:, 22:24] = 0
                    img_res.append(char_copy)

    indices = sorted(range(len(x_cntr_list)), key=lambda k: x_cntr_list[k])
    img_res = np.array([img_res[idx] for idx in indices])

    return img_res, contour_img


def segment_characters(image):
    img_lp = cv2.resize(image, (333, 75))
    img_gray_lp = cv2.cvtColor(img_lp, cv2.COLOR_BGR2GRAY)
    img_gray_lp = cv2.GaussianBlur(img_gray_lp, (5, 5), 0)

    # Adaptive thresholding
    img_binary_lp = cv2.adaptiveThreshold(
        img_gray_lp, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
    )

    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img_binary_lp = cv2.morphologyEx(img_binary_lp, cv2.MORPH_CLOSE, kernel)
    img_binary_lp = cv2.erode(img_binary_lp, np.ones((2, 2), np.uint8))
    img_binary_lp = cv2.dilate(img_binary_lp, np.ones((2, 2), np.uint8))

    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img_binary_lp = cv2.filter2D(img_binary_lp, -1, kernel)

    LP_WIDTH = img_binary_lp.shape[0]
    LP_HEIGHT = img_binary_lp.shape[1]

    img_binary_lp[0:3, :] = 255
    img_binary_lp[:, 0:3] = 255
    img_binary_lp[72:75, :] = 255
    img_binary_lp[:, 330:333] = 255

    dimensions = [LP_WIDTH / 10, LP_WIDTH / 1.5, LP_HEIGHT / 12, LP_HEIGHT / 1.5]
    char_list, contour_img = find_contours(dimensions, img_binary_lp, img_lp.copy())

    return char_list, contour_img


def find_contours_2(dimensions, img, contour_img):
    cntrs, hierarchy = cv2.findContours(
        img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    lower_width, upper_width, lower_height, upper_height = dimensions

    x_cntr_list = []
    img_res = []
    for cntr in cntrs:
        intX, intY, intWidth, intHeight = cv2.boundingRect(cntr)
        aspect_ratio = float(intWidth) / intHeight
        hull = cv2.convexHull(cntr)
        hull_area = cv2.contourArea(hull)
        area = cv2.contourArea(cntr)
        extent = float(area) / (intWidth * intHeight)

        # Filters: width, height, aspect ratio, solidity, extent
        if (
            lower_width < intWidth < upper_width
            and lower_height < intHeight < upper_height
            and 0.2 < aspect_ratio < 1.0
            and hull_area > 0
            and float(area) / hull_area > 0.5
            and extent > 0.3
        ):

            x_cntr_list.append(intX)
            char_copy = np.zeros((44, 24))
            char = img[intY : intY + intHeight, intX : intX + intWidth]
            char = cv2.resize(char, (20, 40))
            cv2.rectangle(
                contour_img,
                (intX, intY),
                (intX + intWidth, intY + intHeight),
                (50, 21, 200),
                2,
            )
            char = cv2.subtract(255, char)
            char_copy[2:42, 2:22] = char
            char_copy[0:2, :] = 0
            char_copy[:, 0:2] = 0
            char_copy[42:44, :] = 0
            char_copy[:, 22:24] = 0
            img_res.append(char_copy)

    # Sort characters based on X position
    indices = sorted(range(len(x_cntr_list)), key=lambda k: x_cntr_list[k])
    img_res = np.array([img_res[idx] for idx in indices])

    return img_res, contour_img


def segment_characters_2(image):
    # Resize image for consistency
    img_lp = cv2.resize(image, (400, 100))

    # Convert to grayscale
    img_gray_lp = cv2.cvtColor(img_lp, cv2.COLOR_BGR2GRAY)

    # Apply adaptive histogram equalization for contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_gray_lp = clahe.apply(img_gray_lp)

    # Bilateral filtering to reduce noise while keeping edges sharp
    img_gray_lp = cv2.bilateralFilter(img_gray_lp, 11, 75, 75)

    # Adaptive thresholding for better binarization under varying lighting conditions
    img_binary_lp = cv2.adaptiveThreshold(
        img_gray_lp, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 10
    )

    # Morphological operations to clean noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img_binary_lp = cv2.morphologyEx(
        img_binary_lp, cv2.MORPH_CLOSE, kernel, iterations=2
    )
    img_binary_lp = cv2.erode(img_binary_lp, np.ones((2, 2), np.uint8), iterations=2)
    img_binary_lp = cv2.dilate(img_binary_lp, np.ones((2, 2), np.uint8), iterations=2)

    # Edge detection
    edges = cv2.Canny(img_binary_lp, 50, 150)

    # Remove horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    remove_horizontal = cv2.morphologyEx(
        edges, cv2.MORPH_OPEN, horizontal_kernel, iterations=2
    )
    cnts = cv2.findContours(
        remove_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )[0]
    for c in cnts:
        cv2.drawContours(edges, [c], -1, (0, 0, 0), 5)

    # Remove vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
    remove_vertical = cv2.morphologyEx(
        edges, cv2.MORPH_OPEN, vertical_kernel, iterations=2
    )
    cnts = cv2.findContours(
        remove_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )[0]
    for c in cnts:
        cv2.drawContours(edges, [c], -1, (0, 0, 0), 5)

    # Blob removal
    br_img = morphology.remove_small_objects(
        edges.astype(bool), min_size=30, connectivity=2
    ).astype(int)
    mask_x, mask_y = np.where(br_img == 0)
    edges[mask_x, mask_y] = 0

    # Find contours and segment characters
    dimensions = [
        img_lp.shape[0] / 10,
        img_lp.shape[0] / 1.5,
        img_lp.shape[1] / 12,
        img_lp.shape[1] / 1.5,
    ]
    char_list, contour_img = find_contours_2(dimensions, edges, img_lp.copy())

    return char_list, contour_img


def fix_dimension(img):
    new_img = np.zeros((32, 32, 3))
    for i in range(3):
        new_img[:, :, i] = img
    return new_img


def show_results(model1, img, char):
    dic = {}
    characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i, c in enumerate(characters):
        dic[i] = c

    output = []
    for i, ch in enumerate(char):  # iterating over the characters
        img_ = cv2.resize(ch, (32, 32))
        img = fix_dimension(img_)
        img = img.reshape(1, 32, 32, 3)  # preparing image for the model

        # Predicting the class
        y_ = model1.predict(img)[
            0
        ]  # Assuming model1.predict returns a single prediction
        y_index = np.argmax(y_)  # Get the index of the highest probability

        character = dic[y_index]  # Map index to the character
        output.append(character)  # Storing the result in a list

    plate_number = "".join(output)

    return plate_number


import cv2
import numpy as np
import re


def preprocess_for_ocr(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to remove noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply edge detection
    edges = cv2.Canny(blur, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours by area and keep the largest one (likely the number plate)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    # Loop through contours to find the best possible rectangle
    number_plate_contour = None
    for contour in contours:
        epsilon = 0.018 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) == 4:  # Number plates are usually rectangular
            number_plate_contour = approx
            break

    if number_plate_contour is None:
        return None

    # Perspective transformation to correct the orientation
    pts = number_plate_contour.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    # Top-left point will have the smallest sum, bottom-right will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Top-right will have the smallest difference, bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # Determine the width and height of the new image
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # Create a top-down view of the image (bird's eye view)
    dst = np.array(
        [[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))

    # Convert to grayscale and threshold for better OCR performance
    gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    _, number_plate_img = cv2.threshold(gray_warped, 150, 255, cv2.THRESH_BINARY)
    return number_plate_img


def concat_number_plate(result):
    # Concatenate all detected text parts
    concatenated_text = "".join([item[-2] for item in result])

    # Remove non-alphanumeric characters at the start and end of the concatenated text
    cleaned_text = re.sub(r"^\W+|\W+$", "", concatenated_text)

    return cleaned_text
