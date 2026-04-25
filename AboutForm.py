from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt


DARK_STYLE = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e);
    }
    QLabel { color: #e0e0e0; }
"""


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(500, 220)
        Dialog.setMinimumSize(380, 160)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(25, 25, 35))
        palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
        palette.setColor(QPalette.Base, QColor(35, 35, 50))
        Dialog.setPalette(palette)
        Dialog.setStyleSheet(DARK_STYLE)

        outer = QtWidgets.QVBoxLayout(Dialog)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(14)

        title = QtWidgets.QLabel()
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #00d4ff; margin-bottom: 4px;")
        outer.addWidget(title)

        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.HLine)
        divider.setStyleSheet("color: rgba(0, 212, 255, 0.3);")
        outer.addWidget(divider)

        self.label = QtWidgets.QLabel()
        self.label.setObjectName("label")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Segoe UI", 10))
        self.label.setWordWrap(True)
        outer.addWidget(self.label)

        self._title_label = title
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "О программе"))
        self._title_label.setText(_translate("Dialog", "О программе"))
        self.label.setText(_translate("Dialog",
            "Программный комплекс предназначен для обучения\n"
            "операторов-дистрибьюторов управлению сталеплавильным конвертером.\n\n"
            "Разработан в рамках ВКР студентом группы 429м\n"
            "Левинским Ильёй"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
