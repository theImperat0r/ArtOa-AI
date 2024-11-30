import cv2
import numpy as np

img = cv2.imread("generated_images/4b935ec6c34d0ac8711553de6fafe210.png")

denoised_img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

darker_img = cv2.convertScaleAbs(img, alpha=1.0, beta=-25)

cv2.imwrite("output_high_quality.jpg", darker_img)