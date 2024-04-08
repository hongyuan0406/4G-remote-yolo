from PyQt5.QtWidgets import QMainWindow,QApplication
from PyQt5.QtCore import *
import imshow
from PyQt5.QtGui import *#QImage
import cv2 as cv
import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import socket
import sys,os
from multiprocessing import Process,Queue,Pipe,freeze_support
from datetime import datetime
import subprocess
import torch
import time
pipe=Pipe()

folder_path=r'.\folder'
yoloTimeInterval = 400   /1000
minScore=0.35
def find_and_kill_process():
    port=2222
    try:
        # 使用netstat查找监听指定端口的程序
        result = subprocess.run(['netstat', '-ano', '|', 'findstr', f':{port}'], capture_output=True, text=True)

        # 提取进程ID
        lines = result.stdout.splitlines()
        if lines:
            process_id = lines[0].split()[-1]
            process_id = int(process_id)

            # 使用taskkill终止进程
            subprocess.run(['taskkill', '/F', '/PID', str(process_id)], shell=True)
            print(f"进程 {process_id} 已终止.")
        else:
            print(f"未找到监听端口 {port} 的程序.")
    except Exception as e:
        print(f"发生错误: {e}")

def check_and_create_folder(folder_path):
    # 检测路径是否存在
    if not os.path.exists(folder_path):
        # 如果不存在，则创建文件夹
        os.makedirs(folder_path)
        print(f"文件夹 {folder_path} 不存在，已创建。")
    else:
        # print(f"文件夹 {folder_path} 已存在。")
        pass
class PyQtMainEntry(QMainWindow, imshow.Ui_Form):
    def __init__(self, pipe):
        super().__init__()
        self.setupUi(self)
        self.pipe = pipe

        self.pushButton.clicked.connect(self.opencam)
        self.pushButton_2.clicked.connect(self.open_folder_in_file_explorer)
        self.frame = cv.imread('295021.jpg')
        img_rows, img_cols, channels = self.frame.shape
        bytesPerLine = channels * img_cols
        QImg = QImage(self.frame.data, img_cols, img_rows, bytesPerLine, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(QImg).scaled(self.label.width(), self.label.height()))
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.queryFrame)
        self._timer.setInterval(30)  # ms
        self._timer.start()
        self.cam = False
        self.noPerson()
        self.model = torch.hub.load("ultralytics/yolov5", "yolov5s")
        self.lastyoloTime=time.time()-0.5
        self.yoloImg=None
    def opencam(self):
        self.cam=True
    def noPerson(self):
        self.label_3.setStyleSheet('background-color: green;')
        self.label_3.setText('无人入侵')
    def havePerson(self):
        self.label_3.setStyleSheet('background-color: red;')
        self.label_3.setText('有人入侵')
    def open_folder_in_file_explorer(self):

        subprocess.run(['explorer', folder_path], shell=True)
    def queryFrame(self):
        # global longitude, latitude, yaw, velocity, status, numofuse, status
        # suc, self.frame = self.camera.read()

        # self.frame.reszie(320,240)
        # print('in')
        if self.cam:
            self.frame = self.pipe.recv()
            # print('over')
            # cv2.imshow("imgr", self.frame)
            self.frame2 = cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)
            img_rows, img_cols, channels = self.frame.shape
            bytesPerLine = channels * img_cols
            QImg = QImage(self.frame2.data, img_cols, img_rows, bytesPerLine, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(QImg)
            self.label.setPixmap(QPixmap.fromImage(QImg).scaled(self.label.width(), self.label.height()))
            if(time.time()-self.lastyoloTime>yoloTimeInterval):
                # print(1)
                self.lastyoloTime=time.time()
                results=self.model(self.frame)
                predictions = results.pred[0].to("cpu")
                boxes = predictions[:, :4]  # x1, y1, x2, y2
                scores = predictions[:, 4]
                categories = predictions[:, 5]
                idx = torch.where(categories == 0)[0]
                # print(idx)
                save=False
                for i in idx.tolist():
                    start_point = (int(boxes[i][0]), int(boxes[i][1]))
                    end_point = (int(boxes[i][2]), int(boxes[i][3]))

                    # 定义矩形的颜色和厚度
                    color = (0, 255, 0)  # BGR格式，这里是绿色
                    thickness = 2

                    # 使用cv2.rectangle绘制矩形
                    if (scores[i]>minScore):
                        cv2.rectangle(self.frame, start_point, end_point, color, thickness)
                        save=True
                        self.havePerson()

                if save:
                    # self.yoloImg=self.frame
                    frame = cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)
                    img_rows, img_cols, channels = frame.shape
                    bytesPerLine = channels * img_cols
                    QImg = QImage(frame.data, img_cols, img_rows, bytesPerLine, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(QImg)
                    self.label_2.setPixmap(QPixmap.fromImage(QImg).scaled(self.label_2.width(), self.label_2.height()))
                    current_time = datetime.now()
                    formatted_time = current_time.strftime("%Y-%m-%d-%H-%M-%S")
                    suc=cv2.imwrite(folder_path+'\\'+formatted_time+'-'+str(time.time())+'.png', self.frame)
                    # suc=cv2.imwrite(str(time.time())+'tmp.png', self.frame)
                    print(suc)
                    print(folder_path+'\\'+'_'+str(time.time())+'.png')

                else:
                    self.noPerson()
            else:
                # print(2)
                pass



def window_start(pipe1):

    app = QtWidgets.QApplication(sys.argv)
    window = PyQtMainEntry(pipe1)

    window.show()
    sys.exit(app.exec_())
def udp_receive(pipe0):
    BUFSIZE = 10000
    # ip_port = ('', 1390)
    ip_port = ('', 2222)
    MTU = 1399
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(ip_port)
    # cv2.namedWindow('imgr')
    data_total = [[], [], [], [], []]
    cnt = [0, 0, 0, 0, 0]  # because the seequence will not in order cnt will incerement
    lastIndex = [0, 0, 0, 0, 0]
    loss_cnt = 0
    length = [0, 0, 0, 0, 0]
    # loss=0
    while True:
        data, client_addr = server.recvfrom(BUFSIZE)
        if data:
            l = int.from_bytes(data[0:2], byteorder='big')
            k = int.from_bytes(data[2:4], byteorder='big')
            j = int.from_bytes(data[4:6], byteorder='big')
            i = int.from_bytes(data[6:8], byteorder='big')
            buffer_index = l % 5
            if l != lastIndex[buffer_index]:
                cnt[buffer_index] = 0
                length[buffer_index] = 0
            cnt[buffer_index] += 1
            # print(i, j, k, l, cnt[buffer_index])
            if i == j - 1:
                data_total[buffer_index][i * MTU:] = list(data[8:])
                length[buffer_index] += len(list(data[8:]))
            else:
                data_total[buffer_index][i * MTU:(i + 1) * MTU] = list(data[8:])
                length[buffer_index] += len(list(data[8:]))
            if cnt[buffer_index] == j:
                b = bytes(data_total[buffer_index])
                stringdata = np.frombuffer(b, dtype='uint8')
                length2 = len(stringdata)
                if k == length[buffer_index] % 100 and k == length2 % 100:
                    if length2 != length[buffer_index]:
                        print(length2, length[buffer_index], k)
                    img = cv2.imdecode(stringdata, 1)
                    current_time = datetime.now()
                    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_size = 0.7
                    font_thickness = 2
                    font_color = (0, 255, 0)
                    cv2.putText(img, formatted_time, (10, 30), font, font_size, font_color, font_thickness)
                    pipe0.send(img)
                    try:
                        pass
                    except:
                        print("show error")
            lastIndex[buffer_index] = l
if __name__ == '__main__':
    find_and_kill_process()
    check_and_create_folder(folder_path)
    freeze_support()
    # os.system('taskkill /f /im test2.exe')
    p1=Process(target=window_start,args=(pipe[1],))
    p2=Process(target=udp_receive,args=(pipe[0],))
    p1.start()
    p2.start()