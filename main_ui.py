# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainapp.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets # Thêm thư viện PyQt5
import cv2 # Thêm thư viện OpenCV
from PyQt5.QtCore import QThread, pyqtSignal # Thêm thư viện QThread
from PyQt5.QtCore import pyqtSignal, Qt, QThread # Thêm thư viện QThread
import numpy as np # Thêm thư viện numpy
from PyQt5.QtGui import QPixmap # Thêm thư viện QPixmap
from PyQt5.QtWidgets import QFileDialog, QMessageBox # Thêm thư viện QMessageBox
import datetime # Thêm thư viện datetime
from PyQt5 import QtCore, QtGui, QtWidgets # Thêm thư viện PyQt5
import base64 # Thêm thư viện base64
import os # Thêm thư viện os
from time import sleep # Thêm thư viện sleep
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import time
import json

api_host = 'http://0.0.0.0:8001/'
type_rq_image = 'img_object_detection_to_img'
type_rq_json = 'img_object_detection_to_json'
type_rq_learn = 'learn_face'
type_rq_save = 'save_face'
type_rq_delete = 'delete_face'

def reload_host():
    global api_host
    # get file host.txt
    f = open("host.txt", "r")
    api_host = f.read()
    print("host: ", api_host)

reload_host()


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    recognized_info_signal = pyqtSignal(str, str, str)

    def __init__(self): # Hàm khởi tạo
        super().__init__()
        self._run_flag = True 
        self.startLearnNewFace = False
        self.saveNewFace = False
        self.name = ""
        self.id = ""
        self.age = ""
    
    def start_learn_new_face(self):
        self.startLearnNewFace = True
        self.saveNewFace = False
        
    
    def save_new_face(self, name, id, age):
        self.saveNewFace = True
        self.startLearnNewFace = False
        self.name = name
        self.id = id
        self.age = age

    def run(self):
        cap = cv2.VideoCapture(0)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        oldtime_update_info = time.time()
        time_out_update_info = 5

        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                try:
                    if self.startLearnNewFace:
                        frame = self.learn_face(frame)
                        print("start learn new face")
                    elif self.saveNewFace:
                        self.save_face(self.name, self.id, self.age)
                        print("save new face")
                        self.saveNewFace = False
                    else:
                        frame, info = self.recognize_face_to_image(frame)
                        if len(info) > 3:
                            oldtime_update_info = time.time()
                            print("info: ", info)
                            info = json.loads(info)
                            self.recognized_info_signal.emit(info["name"], str(info["id"]), str(info["ages"]))
                    self.change_pixmap_signal.emit(frame)
                except Exception as e:
                    print(e)
                    # put string to frame
                    # print("URL ERROR")
                    cv2.putText(frame, "URL ERROR", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    self.change_pixmap_signal.emit(frame)
                    pass

            if (time.time() - oldtime_update_info) > time_out_update_info:
                self.recognized_info_signal.emit("", "", "")
                oldtime_update_info = time.time()
                
        cap.release()

    def delete_face(self, id):
        response = requests.post(api_host + type_rq_delete, data={"id": id})
        return response

    def save_face(self, name, id, age):
        response = requests.post(api_host + type_rq_save, data={"name": name, "id": id, "ages": age})
        return response

    def learn_face(self, frame):
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes = img_encoded.tobytes()
        files = {'file': ('image.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(api_host + type_rq_learn, files=files)
        img = Image.open(BytesIO(response.content))
        img = np.array(img)[:, :, ::-1].copy()
        
        return img
    
    def set_schedule(self, data):
        # use post send data to server
        response = requests.post(api_host + "schedules", json=data)
        return response.json()
    
    def get_schedule(self):
        response = requests.get(api_host + "schedules")
        # print
        _json_data = response.json()
        # print(_json_data["title"])
        # print(_json_data["name"])
        return _json_data

    def recognize_face_to_image(self, frame):
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes = img_encoded.tobytes()
        files = {'file': ('image.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(api_host + type_rq_image, files=files)
        # print("response.headers: ", response.headers["info"])
        info = response.headers["info"]
        img = Image.open(BytesIO(response.content))
        img = np.array(img)[:, :, ::-1].copy()
        return img, info
    
    def stop(self): 
        self._run_flag = False 
        self.wait() 

class Ui_Form(object):

    thread = VideoThread()


    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(640, 482)
        self.tabWidget = QtWidgets.QTabWidget(Form)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 640, 480))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.groupBox = QtWidgets.QGroupBox(self.tab)
        self.groupBox.setGeometry(QtCore.QRect(0, 0, 391, 421))
        self.groupBox.setObjectName("groupBox")
        self.cameraLabel = QtWidgets.QLabel(self.groupBox)
        self.cameraLabel.setGeometry(QtCore.QRect(0, 20, 391, 401))
        self.cameraLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.cameraLabel.setObjectName("cameraLabel")
        self.cameraLabel.setScaledContents(True)
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_2.setGeometry(QtCore.QRect(400, 0, 231, 121))
        self.groupBox_2.setObjectName("groupBox_2")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setGeometry(QtCore.QRect(20, 30, 71, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setGeometry(QtCore.QRect(20, 60, 71, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setGeometry(QtCore.QRect(20, 90, 71, 16))
        self.label_3.setObjectName("label_3")
        self.statusLabel = QtWidgets.QLabel(self.groupBox_2)
        self.statusLabel.setGeometry(QtCore.QRect(100, 90, 120, 16))
        self.statusLabel.setObjectName("statusLabel")
        self.idLabel = QtWidgets.QLabel(self.groupBox_2)
        self.idLabel.setGeometry(QtCore.QRect(100, 60, 120, 16))
        self.idLabel.setObjectName("idLabel")
        self.nameLabel = QtWidgets.QLabel(self.groupBox_2)
        self.nameLabel.setGeometry(QtCore.QRect(100, 30, 120, 16))
        self.nameLabel.setObjectName("nameLabel")
        self.groupBox_3 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_3.setGeometry(QtCore.QRect(400, 120, 231, 51))
        self.groupBox_3.setObjectName("groupBox_3")
        self.startWorkPushButton = QtWidgets.QPushButton(self.groupBox_3)
        self.startWorkPushButton.setGeometry(QtCore.QRect(0, 20, 113, 32))
        self.startWorkPushButton.setObjectName("startWorkPushButton")
        self.stopWorkPushButton = QtWidgets.QPushButton(self.groupBox_3)
        self.stopWorkPushButton.setGeometry(QtCore.QRect(120, 20, 113, 32))
        self.stopWorkPushButton.setObjectName("stopWorkPushButton")
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_4.setGeometry(QtCore.QRect(400, 170, 231, 151))
        self.groupBox_4.setObjectName("groupBox_4")
        self.label_8 = QtWidgets.QLabel(self.groupBox_4)
        self.label_8.setGeometry(QtCore.QRect(10, 30, 41, 21))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(self.groupBox_4)
        self.label_9.setGeometry(QtCore.QRect(10, 60, 41, 21))
        self.label_9.setObjectName("label_9")
        self.startlearnPushButton = QtWidgets.QPushButton(self.groupBox_4)
        self.startlearnPushButton.setGeometry(QtCore.QRect(0, 120, 113, 32))
        self.startlearnPushButton.setObjectName("startlearnPushButton")
        self.savePushButton = QtWidgets.QPushButton(self.groupBox_4)
        self.savePushButton.setGeometry(QtCore.QRect(120, 120, 113, 32))
        self.savePushButton.setObjectName("savePushButton")
        self.nameLineEdit = QtWidgets.QLineEdit(self.groupBox_4)
        self.nameLineEdit.setGeometry(QtCore.QRect(60, 30, 161, 21))
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.idLineEdit = QtWidgets.QLineEdit(self.groupBox_4)
        self.idLineEdit.setGeometry(QtCore.QRect(60, 60, 161, 21))
        self.idLineEdit.setObjectName("idLineEdit")
        self.label_12 = QtWidgets.QLabel(self.groupBox_4)
        self.label_12.setGeometry(QtCore.QRect(10, 90, 41, 21))
        self.label_12.setObjectName("label_12")
        self.agesLineEdit = QtWidgets.QLineEdit(self.groupBox_4)
        self.agesLineEdit.setGeometry(QtCore.QRect(60, 90, 161, 21))
        self.agesLineEdit.setObjectName("agesLineEdit")
        self.groupBox_5 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_5.setGeometry(QtCore.QRect(400, 320, 231, 101))
        self.groupBox_5.setObjectName("groupBox_5")
        self.label_10 = QtWidgets.QLabel(self.groupBox_5)
        self.label_10.setGeometry(QtCore.QRect(10, 30, 41, 21))
        self.label_10.setObjectName("label_10")
        self.idDeletelineEdit = QtWidgets.QLineEdit(self.groupBox_5)
        self.idDeletelineEdit.setGeometry(QtCore.QRect(60, 30, 151, 21))
        self.idDeletelineEdit.setObjectName("idDeletelineEdit")
        self.deletePushButton = QtWidgets.QPushButton(self.groupBox_5)
        self.deletePushButton.setGeometry(QtCore.QRect(50, 60, 131, 32))
        self.deletePushButton.setObjectName("deletePushButton")
        self.exitPushButton = QtWidgets.QPushButton(self.tab)
        self.exitPushButton.setGeometry(QtCore.QRect(260, 422, 113, 32))
        self.exitPushButton.setObjectName("exitPushButton")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.groupBox_6 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_6.setGeometry(QtCore.QRect(0, 0, 611, 421))
        self.groupBox_6.setObjectName("groupBox_6")
        self.tableWidget = QtWidgets.QTableWidget(self.groupBox_6)
        self.tableWidget.setGeometry(QtCore.QRect(10, 31, 591, 381))
        self.tableWidget.setMaximumSize(QtCore.QSize(591, 16777215))
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(5)

        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)

        self.tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setCascadingSectionResizes(False)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.groupBox_7 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_7.setGeometry(QtCore.QRect(140, 100, 331, 171))
        self.groupBox_7.setObjectName("groupBox_7")
        self.label_11 = QtWidgets.QLabel(self.groupBox_7)
        self.label_11.setGeometry(QtCore.QRect(10, 50, 71, 21))
        self.label_11.setObjectName("label_11")
        self.domainServerLineEdit = QtWidgets.QLineEdit(self.groupBox_7)
        self.domainServerLineEdit.setGeometry(QtCore.QRect(90, 50, 211, 21))
        self.domainServerLineEdit.setObjectName("domainServerLineEdit")
        self.setServerIpPushButton = QtWidgets.QPushButton(self.groupBox_7)
        self.setServerIpPushButton.setGeometry(QtCore.QRect(80, 110, 181, 32))
        self.setServerIpPushButton.setObjectName("setServerIpPushButton")
        self.tabWidget.addTab(self.tab_3, "")

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)


        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.recognized_info_signal.connect(self.recognized_info_signal)
        self.thread.start() 

        self.exitPushButton.clicked.connect(self.exit)
        self.setServerIpPushButton.clicked.connect(self.set_server_ip)

        self.startlearnPushButton.clicked.connect(self.start_learn_new_face)
        self.savePushButton.clicked.connect(self.save_new_face)

        self.deletePushButton.clicked.connect(self.delete_face)

        self.startWorkPushButton.clicked.connect(self.start_work)
        self.stopWorkPushButton.clicked.connect(self.stop_work)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_table)
        self.timer.start(1000)
    
    def update_table(self):
        _json_arr = self.thread.get_schedule()
        # _json_arr = json.loads(_json_arr_str)
        self.tableWidget.setRowCount(len(_json_arr))
        for i in range(len(_json_arr)):

            # set id to table
            item = QtWidgets.QTableWidgetItem()
            self.tableWidget.setItem(i, 0, item)
            item.setText(str(_json_arr[i]["id"]))
            item.setTextAlignment(Qt.AlignVCenter)

            # set name to table
            item = QtWidgets.QTableWidgetItem()
            self.tableWidget.setItem(i, 1, item)
            item.setText(str(_json_arr[i]["name"]))
            item.setTextAlignment(Qt.AlignVCenter)

            # set time to table
            item = QtWidgets.QTableWidgetItem()
            self.tableWidget.setItem(i, 2, item)
            item.setText(str(_json_arr[i]["time"]))
            item.setTextAlignment(Qt.AlignVCenter)

            # set date to table
            item = QtWidgets.QTableWidgetItem()
            self.tableWidget.setItem(i, 3, item)
            item.setText(str(_json_arr[i]["date"]))
            item.setTextAlignment(Qt.AlignVCenter)

            # set state to table
            item = QtWidgets.QTableWidgetItem()
            self.tableWidget.setItem(i, 4, item)
            item.setText(str(_json_arr[i]["state"]))
            item.setTextAlignment(Qt.AlignVCenter)
            
        
    
    def start_work(self):
        print("start work")
        # get id, name from label
        id = self.idLabel.text()
        name = self.nameLabel.text()
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        time = datetime.datetime.now().strftime("%H:%M:%S")

        if id == "" or name == "":
            msg = QMessageBox()
            msg.setWindowTitle("ERROR")
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Chưa có kết quả nhận diện")
            # msg.setInformativeText("Vui lòng nhập ID")
            msg.exec_()
            return
        

        data = {
            "id": id,
            "name": name,
            "date": date,
            "state": "Vào làm",
            "time": time
        }
        self.thread.set_schedule(data)
    
    def stop_work(self):
        print("stop work")
        
        # get id, name from label
        id = self.idLabel.text()
        name = self.nameLabel.text()
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        time = datetime.datetime.now().strftime("%H:%M:%S")
        
        if id == "" or name == "":
            msg = QMessageBox()
            msg.setWindowTitle("ERROR")
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Chưa có kết quả nhận diện")
            # msg.setInformativeText("Vui lòng nhập ID")
            msg.exec_()
            return
        
        data = {
            "id": id,
            "name": name,
            "date": date,
            "state": "Tan ca",
            "time": time
        }
        self.thread.set_schedule(data)

    def recognized_info_signal(self, name, id, ages):
        self.nameLabel.setText(name)
        self.idLabel.setText(id)
        self.statusLabel.setText(ages)
        # self.agesLineEdit.setText(ages)

    def delete_face(self):
        id = self.idDeletelineEdit.text()
        self.thread.delete_face(id)

    def start_learn_new_face(self):
        self.thread.start_learn_new_face()

    def save_new_face(self):
        name = self.nameLineEdit.text()
        id = self.idLineEdit.text()
        age = self.agesLineEdit.text()
        self.thread.save_new_face(name, id, age)



    def set_server_ip(self):
        global api_host
        _api_host = self.domainServerLineEdit.text()
        # check url
        if _api_host == "":
            msg = QMessageBox()
            msg.setWindowTitle("ERROR")
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Địa chỉ URL không được để trống")
            msg.setInformativeText("Định dạng URL: http://0.0.0.0:8001/")
            msg.setDetailedText("Trên command prompt gõ: ipconfig để lấy địa chỉ IP của máy tính")
            msg.exec_()
            return
        try:
            requests.get(_api_host, timeout=3)
        except:
            msg = QMessageBox()
            msg.setWindowTitle("ERROR")
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Địa chỉ URL không hợp lệ hoặc không thể kết nối tới server")
            msg.setInformativeText("Định dạng URL: http://0.0.0.0:8001/")
            msg.setDetailedText("Nếu chắc rằng ip và port đã đúng thì kiểm tra lại server đã bật chưa")
            msg.exec_()
            return
        
        api_host = _api_host
        
        # save file host.txt
        f = open("host.txt", "w")
        f.write(api_host)
        print("host: ", api_host)
        msg = QMessageBox()
        msg.setWindowTitle("Success")
        msg.setIcon(QMessageBox.Information)
        msg.setText("Cài đặt địa chỉ URL thành công")
        msg.setInformativeText("domain: " + api_host)
        msg.exec_()

    def exit(self):
        self.thread.stop()
        Form.close()
    
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img) # chuyển đổi kiểu dữ liệu
        self.cameraLabel.setPixmap(qt_img) # hiển thị thông tin
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB) # chuyển đổi kiểu dữ liệu
        h, w, ch = rgb_image.shape  # lấy thông tin kích thước
        bytes_per_line = ch * w # tính toán thông tin
        disply_width = 640 # chiều rộng
        display_height = 480 # chiều cao
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888) # chuyển đổi kiểu dữ liệu
        p = convert_to_Qt_format.scaled(
            disply_width, display_height, Qt.KeepAspectRatio) # chuyển đổi kiểu dữ liệu
        return QPixmap.fromImage(p) # trả về kết quả

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox.setTitle(_translate("Form", "CAMERA NHẬN DIỆN"))
        self.cameraLabel.setText(_translate("Form", "Camera"))
        self.groupBox_2.setTitle(_translate("Form", "Thông tin nhận diện"))
        self.label.setText(_translate("Form", "Tên:"))
        self.label_2.setText(_translate("Form", "ID:"))
        self.label_3.setText(_translate("Form", "Trạng thái:"))
        self.statusLabel.setText(_translate("Form", "Bắt đầu vào làm"))
        self.idLabel.setText(_translate("Form", "2"))
        self.nameLabel.setText(_translate("Form", "Nguyễn Văn A"))
        self.groupBox_3.setTitle(_translate("Form", "Điểm danh"))
        self.startWorkPushButton.setText(_translate("Form", "Vào làm"))
        self.stopWorkPushButton.setText(_translate("Form", "Tan ca"))
        self.groupBox_4.setTitle(_translate("Form", "Thêm khuôn mặt mới"))
        self.label_8.setText(_translate("Form", "Tên:"))
        self.label_9.setText(_translate("Form", "ID:"))
        self.startlearnPushButton.setText(_translate("Form", "Bắt đầu học"))
        self.savePushButton.setText(_translate("Form", "Lưu"))
        self.label_12.setText(_translate("Form", "Tuổi:"))
        self.groupBox_5.setTitle(_translate("Form", "Xoá"))
        self.label_10.setText(_translate("Form", "ID:"))
        self.deletePushButton.setText(_translate("Form", "Xoá "))
        self.exitPushButton.setText(_translate("Form", "Thoát"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Form", "Nhận diện điểm danh"))
        self.groupBox_6.setTitle(_translate("Form", "Danh sách vào ra được ghi nhận"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "ID"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Tên"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Giờ ghi nhận"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Ngày ghi nhận"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("Form", "Trạng thái"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Form", "Danh sách chấm công"))
        self.groupBox_7.setTitle(_translate("Form", "Cài đặt thông tin server"))
        self.label_11.setText(_translate("Form", "Server IP:"))
        self.domainServerLineEdit.setPlaceholderText(_translate("Form", "http://192.168.1.2:8001/"))
        self.setServerIpPushButton.setText(_translate("Form", "Cài đặt server IP"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("Form", "Cài đặt"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())