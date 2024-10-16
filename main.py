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

        def send():
            text = le_chat.text()
            if text:
                self.lst_chat.addItem(f"我: {text}")
                if self.is_client:
                    self.client_socket.send(text.encode("utf-8"))
                le_chat.clear()

        btn_send.clicked.connect(lambda: send())

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

    # 创建房间
    def create_room(self):
        self.is_host = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", 0))
        self.server_socket.listen(10)
        threading.Thread(target=self.accept_connections, daemon=True).start()
        self.client_sockets = []  # 客户端套接字列表

        host, port = self.server_socket.getsockname()
        self.lst_chat.addItem(f"房间 {host}:{port} 创建成功，等待其他成员加入...")
        return port

    def broadcast_update_member_list(self):
        lst_member = []
        for _, display in self.client_sockets:
            lst_member.append(display)
        self.broadcast_message(f"///update{lst_member}")

    # 接受客户端连接
    def accept_connections(self):
        while self.is_host:
            try:
                client_socket, (host, port) = self.server_socket.accept()
                display = f"member{random.randint(1,1000)}({host}:{port})"
                self.client_sockets.append([client_socket, display])
                threading.Thread(
                    target=self.handle_client, args=(client_socket,), daemon=True
                ).start()

                self.broadcast_message(f"{display} 加入了房间.", client_socket)
                self.broadcast_update_member_list()
            except OSError:
                print("Server socket has been closed.")
                break

    # 处理客户端消息
    def handle_client(self, client_socket):
        from_display = "unknown"
        for socket, display in self.client_sockets:
            if client_socket == socket:
                from_display = display

        while self.is_host:
            try:
                message = client_socket.recv(1024).decode("utf-8")
                # 空消息
                if not message:
                    continue
                # 特殊消息
                elif message.startswith("///"):
                    # 更改用户名
                    if message.startswith("///rename"):
                        new_display = message[9:].strip()
                        for i in range(len(self.client_sockets)):
                            if self.client_sockets[i][0] == client_socket:
                                indexOfAddr = self.client_sockets[i][1].index("(")
                                self.client_sockets[i][
                                    1
                                ] = f"{new_display}({self.client_sockets[i][1].substring(indexOfAddr)})"
                        self.broadcast_message(
                            f"{from_display} 更名为 {new_display}.", client_socket
                        )
                        self.broadcast_update_member_list()
                    elif message.startswith("///quit"):
                        self.client_sockets.remove([client_socket, from_display])
                        self.broadcast_message(
                            f"{from_display} 退出了房间.", client_socket
                        )
                        self.broadcast_update_member_list()
                # 普通消息
                else:
                    self.broadcast_message(f"{from_display}: {message}", client_socket)
            except ConnectionResetError:
                break

    # 广播消息
    def broadcast_message(self, message, sender_socket=None):
        for client_socket, _ in self.client_sockets:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode("utf-8"))
                except Exception as e:
                    print(f"消息发送失败: {e}")

    # 加入房间
    def join_room(self, code):
        self.is_client = True
        host, port = code.split(":")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, int(port)))
        threading.Thread(target=self.receive_messages, daemon=True).start()

        self.lst_chat.addItem(f"已加入房间 {host}:{port}")
        self.btn_room_operate.setText("离开房间")

    # 接收消息
    def receive_messages(self):
        while self.is_client:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                # 空消息
                if not message:
                    continue
                elif message.startswith("///"):
                    if message.startswith("///update"):
                        self.lst_member.clear()
                        for member in eval(message[9:]):
                            self.lst_member.addItem(member)
                    elif message.startswith("///quit"):
                        self.lst_chat.addItem("房间已关闭")
                        self.after_leave_room()
                else:
                    self.lst_chat.addItem(message)
            except ConnectionResetError:
                break
            except ConnectionAbortedError:
                break

    # 离开房间
    def leave_room(self):
        if self.is_host:
            if self.server_socket:
                self.broadcast_message("///quit")
                self.server_socket.close()
        elif self.is_client:
            if self.client_socket:
                self.client_socket.send("///quit".encode("utf-8"))
                self.client_socket.close()

        self.after_leave_room()

    def after_leave_room(self):
        if self.is_host:
            self.is_host = False
            self.client_sockets = []
        elif self.is_client:
            self.is_client = False

        self.lst_member.clear()
        self.lst_chat.addItem("已离开房间")
        self.btn_room_operate.setText("创建/加入房间")

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
                    port = self.create_room()
                    self.join_room(f"localhost:{port}")
                else:
                    code = code.strip().replace("：", ":").replace("。", ".")
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
        self.is_host = False
        self.is_client = False

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
