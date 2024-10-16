import random
import re
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QSpinBox, QStatusBar, QStyle, QTabWidget, QVBoxLayout, QWidget


# 结果（显示自己上次的执行结果）
# 单选（表达式、个数 次数）
# 添加到预设（预设列表：左键执行预设，右键删除）
# 创建房间（解散房间） 加入房间（退出房间）
# 用户名 房间代码（ip+端口 base64）
# 房间成员（列表）（可以@）
# 对话框（执行 发送）
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
            pattern = r"^(?:(\d+)d(\d+)|d(\d+)|(\d+))(?:\+(?:(\d+)d(\d+)|d(\d+)|(\d+)))*$"
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
        vbox.addWidget(self._dice())
        vbox.addWidget(self.lst_chat)
        vbox.addWidget(w0)
        w.setLayout(vbox)
        return w

    def _create_join(self):
        def create():
            print("create")

        def join():
            print("join")

        btn_create = QPushButton("创建房间")
        btn_join = QPushButton("加入房间")

        btn_create.clicked.connect(lambda: create())
        btn_join.clicked.connect(lambda: join())

        w = QWidget(self)
        vbox = QVBoxLayout(w)
        vbox.addWidget(btn_create)
        vbox.addWidget(btn_join)
        w.setLayout(vbox)
        return w

    def _room(self):
        l_room = QLabel("房间列表")
        self.lst_member = QListWidget(self)

        w = QWidget(self)
        vbox = QVBoxLayout(w)
        vbox.addWidget(l_room, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(self.lst_member)
        w.setLayout(vbox)
        return w

    def _right(self):
        l_history = QLabel("历史记录")
        self.lst_history = QListWidget(self)

        w = QWidget(self)
        vbox = QVBoxLayout(w)
        vbox.addWidget(l_history, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(self.lst_history)
        vbox.addWidget(self._create_join())
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
