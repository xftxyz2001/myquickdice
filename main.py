import random
import re
import socket
import sys
import threading

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class DiceChatApp(QWidget):

    # 结果面板（总数 结果）
    def _header(self):
        # 点击复制
        def copyOnClicked(le):
            le.selectAll()
            le.copy()
            self.status.showMessage("结果已复制到剪切板。", 1000)

        l_sum = QLabel("总数")
        self.le_sum = QLineEdit()
        self.le_sum.setReadOnly(True)
        self.le_sum.mousePressEvent = lambda _: copyOnClicked(self.le_sum)

        l_result = QLabel("结果")
        self.le_result = QLineEdit()
        self.le_result.setReadOnly(True)
        self.le_result.mousePressEvent = lambda _: copyOnClicked(self.le_result)

        w = QWidget(self)
        hbox = QHBoxLayout(w)
        hbox.addWidget(l_sum, 1)
        hbox.addWidget(self.le_sum, 1)
        hbox.addWidget(l_result, 1)
        hbox.addWidget(self.le_result, 6)
        w.setLayout(hbox)
        return w

    def _dice(self):
        l_expression = QLabel("表达式")
        le_expression = QLineEdit()
        w_expression = QWidget(self)
        hbox0 = QHBoxLayout(w_expression)
        hbox0.addWidget(l_expression)
        hbox0.addWidget(le_expression, 5)
        w_expression.setLayout(hbox0)

        l_number = QLabel("个数")
        sb_number = QSpinBox()
        sb_number.setMinimum(1)
        l_range = QLabel("上界")
        sb_range = QSpinBox()
        sb_range.setMinimum(2)
        w_numberandrange = QWidget(self)
        hbox1 = QHBoxLayout(w_numberandrange)
        hbox1.addWidget(l_number)
        hbox1.addWidget(sb_number, 1)
        hbox1.addWidget(l_range)
        hbox1.addWidget(sb_range, 1)
        w_numberandrange.setLayout(hbox1)

        tab = QTabWidget(self)
        tab.addTab(w_expression, "表达式")
        tab.addTab(w_numberandrange, "个数与上界")
        # tab.setTabPosition(QTabWidget.TabPosition.West)

        btn_execute = QPushButton("执行")

        def execute():
            if tab.currentIndex() == 1:
                expression = f"{sb_number.value()}d{sb_range.value()}"
            else:
                expression = le_expression.text()
            # 去除表达式中d0123456789+以外的字符
            expression = "".join(filter(lambda x: x in "0123456789+d", expression))
            # 校验表达式合法性
            pattern = (
                r"^(?:(\d+)d(\d+)|d(\d+)|(\d+))(?:\+(?:(\d+)d(\d+)|d(\d+)|(\d+)))*$"
            )
            match = re.match(pattern, expression)
            if not match:
                return

            result = []
            for item in expression.split("+"):
                indexOfd = item.find("d")
                if indexOfd == -1:
                    result.append(int(item))
                    continue
                if indexOfd == 0:
                    n = 1
                    r = int(item[1:])
                else:
                    sa = item.split("d")
                    n, r = int(sa[0]), int(sa[1])
                for i in range(n):
                    result.append(random.randint(1, r))

            s = str(sum(result))
            res = " ".join(map(str, result))
            self.lst_history.insertItem(0, f"{s}[{res}] <{expression}>")
            self.le_sum.setText(s)
            self.le_result.setText(res)

        btn_execute.clicked.connect(lambda: execute())

        w = QWidget(self)
        hbox = QHBoxLayout(w)
        hbox.addWidget(tab)
        hbox.addWidget(btn_execute)
        w.setLayout(hbox)
        return w

    def _left(self):
        self.lst_chat = QListWidget(self)
        le_chat = QLineEdit()
        btn_send = QPushButton("发送")

        w0 = QWidget(self)
        hbox = QHBoxLayout(w0)
        hbox.addWidget(le_chat, 6)
        hbox.addWidget(btn_send, 1)
        w0.setLayout(hbox)

        w = QWidget(self)
        vbox = QVBoxLayout(w)
        vbox.addWidget(self._dice(), 1)
        vbox.addWidget(self.lst_chat, 4)
        vbox.addWidget(w0, 1)
        w.setLayout(vbox)
        return w

    # def create_room(self):
    #     self.is_host = True
    #     self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.server_socket.bind(("0.0.0.0", 12345))
    #     self.server_socket.listen(10)
    #     self.lst_chat.addItem("房间创建成功，等待其他成员加入...")

    #     self.btn_room_operate.setText("离开房间")
    #     threading.Thread(target=self.accept_connections, daemon=True).start()

    # def accept_connections(self):
    #     while True:
    #         client_socket, addr = self.server_socket.accept()
    #         self.lst_chat.addItem(f"新成员加入：{addr}")
    #         self.lst_member.addItem(str(addr))
    #         threading.Thread(
    #             target=self.handle_client, args=(client_socket,), daemon=True
    #         ).start()

    # def handle_client(self, client_socket):
    #     while True:
    #         try:
    #             message = client_socket.recv(1024).decode("utf-8")
    #             if message:
    #                 self.lst_chat.addItem(message)
    #                 self.broadcast_message(message, client_socket)
    #         except ConnectionResetError:
    #             break

    # def broadcast_message(self, message, sender_socket):
    #     for i in range(self.lst_member.count()):
    #         item = self.lst_member.item(i)
    #         addr = eval(item.text())  # 将字符串解析为元组地址
    #         if sender_socket.getpeername() != addr:
    #             try:
    #                 sender_socket.sendto(message.encode("utf-8"), addr)
    #             except Exception as e:
    #                 print(f"消息发送失败: {e}")

    # def join_room(self, code):
    #     self.is_host = False
    #     self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.client_socket.connect(("127.0.0.1", 12345))

    #     self.lst_chat.addItem("成功加入房间")

    #     self.btn_room_operate.setText("离开房间")
    #     threading.Thread(target=self.receive_messages, daemon=True).start()

    # def receive_messages(self):
    #     while True:
    #         try:
    #             message = self.client_socket.recv(1024).decode("utf-8")
    #             if message:
    #                 self.lst_chat.addItem(message)
    #         except ConnectionResetError:
    #             break

    # def leave_room(self):
    #     if self.is_host:
    #         if self.server_socket:
    #             self.server_socket.close()
    #     if self.client_socket:
    #         self.client_socket.close()

    #     self.lst_history.addItem("你已离开房间")
    #     self.btn_room_operate.setText("创建/加入房间")

    def room_operate(self):
        if self.btn_room_operate.text() == "创建/加入房间":
            dialog = QInputDialog()
            dialog.setOkButtonText("创建/加入房间")
            dialog.setCancelButtonText("取消")
            dialog.setWindowTitle("创建/加入房间")
            dialog.setLabelText("请输入房间代码（留空则创建房间）")
            if dialog.exec():
                code = dialog.textValue()
                if code == "":
                    self.create_room()
                else:
                    self.join_room(code)
        elif self.btn_room_operate.text() == "离开房间":
            self.leave_room()

    def _right(self):
        l_history = QLabel("历史记录")
        self.lst_history = QListWidget(self)

        l_room = QLabel("房间成员")
        self.lst_member = QListWidget(self)

        self.btn_room_operate = QPushButton("创建/加入房间")
        self.btn_room_operate.clicked.connect(lambda: self.room_operate())

        w = QWidget(self)
        vbox = QVBoxLayout(w)
        vbox.addWidget(l_history, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(self.lst_history)
        vbox.addWidget(l_room, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(self.lst_member)
        vbox.addWidget(self.btn_room_operate)
        w.setLayout(vbox)
        return w

    def _main(self):
        w = QWidget(self)
        hbox = QHBoxLayout(w)
        hbox.addWidget(self._left(), 3)
        hbox.addWidget(self._right(), 1)
        w.setLayout(hbox)
        return w

    # 窗口居中
    def center(self):
        primaryScreenAvailableSize = QGuiApplication.primaryScreen().availableSize()
        newLeft = (primaryScreenAvailableSize.width() - self.width()) / 2
        newTop = (primaryScreenAvailableSize.height() - self.height()) / 2
        self.move((int)(newLeft), (int)(newTop))

    def __init__(self):
        super().__init__()

        self.status = QStatusBar(self)
        self.status.setSizeGripEnabled(False)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self._header())
        vbox.addWidget(self._main())
        vbox.addWidget(self.status)
        self.setLayout(vbox)

        self.setWindowTitle("My Quick Dice")
        # self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint) # 窗口置顶
        self.show()

        self.center()


app = QApplication(sys.argv)
ex = DiceChatApp()
sys.exit(app.exec())
