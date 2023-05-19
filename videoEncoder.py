from datetime import timedelta
import cv2
import numpy as np
import os
from PIL import Image
import io

rate = 0
INPUT_FILENAME = 'Neko arc trả lại tâm trí.mp4';
OUTPUT_FILENAME = 'Death_Korps.Mjpeg';
video = cv2.VideoCapture(INPUT_FILENAME);
rate = video.get(cv2.CAP_PROP_FPS);
outputFile=open(OUTPUT_FILENAME, 'wb');

lengthEncode = bytearray(5)

while 1:
    isRead, frame = video.read();
    if not isRead:
        break
    imgByte = io.BytesIO();
    encodeParam = [int(cv2.IMWRITE_JPEG_QUALITY), 70];
    isSuccess, buf = cv2.imencode('.jpg', frame, encodeParam);
    imgByte = io.BytesIO(buf);
    imglen = len(imgByte.getvalue());
    print(imglen);
    print((imglen // 10000)+48);
    lengthEncode[0] = (imglen // 10000) + 48;
    imglen = imglen - (imglen // 10000) * 10000;
    lengthEncode[1] = (imglen // 1000) + 48;
    imglen = imglen - (imglen // 1000) * 1000;
    lengthEncode[2] = (imglen // 100) + 48;
    imglen = imglen - (imglen // 100) * 100;
    lengthEncode[3] = (imglen // 10) + 48;
    imglen = imglen - (imglen // 10) * 10;
    lengthEncode[4] = (imglen // 1) + 48;
    outputFile.write(lengthEncode);
    outputFile.write(imgByte.getvalue());