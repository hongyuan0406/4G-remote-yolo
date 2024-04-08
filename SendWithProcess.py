import socket
import cv2
import numpy as np
import datetime
import time
from multiprocessing import Process, Queue, Pipe, freeze_support

BUFSIZE = 60000

IMAGE_SIZE_X = 480 * 1
IMAGE_SIZE_Y = 320 * 1
pipe = Pipe()
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

cnt = 0
hostname='6876.top'
ip_address = socket.gethostbyname(hostname)
ip_port = (ip_address, 50101)
def img_send(stringData):
    client.sendto(stringData, ip_port)


def img_encode(img, i=1, j=1):
    global cnt
    cnt += 1
    if cnt > 200:
        cnt = 0
    MTU = 1399
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
    img_encode = cv2.imencode('.jpg', img, encode_param)[1]
    data = np.array(img_encode)
    stringData = data.tostring()
    length = len(stringData)
    length_num = length // MTU + 1  # for mtu
    # print(length,length_num)
    CheckSum = length - (length // 100) * 100  # 取length的后两位作为校验和

    for index in range(length_num):

        # j = length_num
        if index != length_num :
            img_send(index.to_bytes(2, byteorder='big') + length_num.to_bytes(2, byteorder='big') + CheckSum.to_bytes(2,
                                                                                                                      byteorder='big') + cnt.to_bytes(
                2, byteorder='big') + stringData[index * MTU:length])
        else:
            img_send(index.to_bytes(2, byteorder='big') + length_num.to_bytes(2, byteorder='big') + CheckSum.to_bytes(2,
                                                                                                                      byteorder='big') + cnt.to_bytes(
                2, byteorder='big') + stringData[index * MTU:(index + 1) * MTU])
        


def img_split(img):
    # for i in range(IMAGE_ROW):
    #     # print(160 * (i + 1))
    #     for j in range(IMAGE_COLUMN):
    #         cv2.imshow('test'+str(i)+' '+str(j),img[j*IMAGE_BASE_SIZE_Y:(j+1)*IMAGE_BASE_SIZE_Y,i*IMAGE_BASE_SIZE_X:(i+1)*IMAGE_BASE_SIZE_X])
    #         img_encode(img[j*IMAGE_BASE_SIZE_Y:(j+1)*IMAGE_BASE_SIZE_Y,i*IMAGE_BASE_SIZE_X:(i+1)*IMAGE_BASE_SIZE_X],i,j)
    #         pass
    img_encode(img, 1, 1)


def img_cap_process(pipe):
    cap = cv2.VideoCapture(0)
    cap.set(3, IMAGE_SIZE_X)
    cap.set(4, IMAGE_SIZE_Y)
    # cap.set(cv2.CAP_PROP_FPS,10)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))
    cv2.namedWindow("imgt", 0)
    cv2.resizeWindow("imgt", IMAGE_SIZE_X, IMAGE_SIZE_Y)
    while True:

        # a=datetime.datetime.now()
        suc, img = cap.read()
        img = cv2.resize(img, (IMAGE_SIZE_X, IMAGE_SIZE_Y))
        pipe.send(img)
        cv2.imshow("imgt", img)
        if cv2.waitKey(1) & 0xff == ord("1"):
            break


def img_cap_process_debug(pipe):
    # cap = cv2.VideoCapture(0)
    # cap.set(3, IMAGE_SIZE_X)
    # cap.set(4, IMAGE_SIZE_Y)
    # # cap.set(cv2.CAP_PROP_FPS,10)
    # fps = cap.get(cv2.CAP_PROP_FPS)
    mp4_file_path = r'C:\Users\afc\Videos\test (2).mp4'

    # Create a VideoCapture object
    cap = cv2.VideoCapture(mp4_file_path)
    # print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))
    cv2.namedWindow("imgt", 0)
    cv2.resizeWindow("imgt", IMAGE_SIZE_X, IMAGE_SIZE_Y)
    while True:

        # a=datetime.datetime.now()
        suc, img = cap.read()
        img = cv2.resize(img, (IMAGE_SIZE_X, IMAGE_SIZE_Y))
        time.sleep(0.03)
        # print(suc)
        pipe.send(img)
        cv2.imshow("imgt", img)
        if cv2.waitKey(1) & 0xff == ord("1"):
            break


def img_encode_process(pipe):
    while True:
        img = pipe.recv()
        img_encode(img)


if __name__ == '__main__':
    Process(target=img_encode_process, args=(pipe[1],)).start()
    # Process(target=img_cap_process,args=(pipe[0],)).start()
    Process(target=img_cap_process, args=(pipe[0],)).start()

    client.close()
