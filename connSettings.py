from PyQt5 import QtCore, QtGui, QtWidgets
from configparser import ConfigParser

from PyQt5.QtWidgets import QMessageBox

parser = ConfigParser()


class Ui_ConnectionSettings(object):

    def getData(self):
        parser.read('dev.ini')
        tmp = str(parser.get('DBsettings', 'DBhost'))
        self.DBIpLine.setText(str(parser.get('DBsettings', 'DBhost')))
        self.DBLoginLine.setText(str(parser.get('DBsettings', 'login')))
        self.DBPasswordLine.setText(str(parser.get('DBsettings', 'password')))

    def save(self):
        parser = ConfigParser()
        parser.read('dev.ini')
        parser.set('DBsettings', 'DBhost', self.DBIpLine.text())
        parser.set('DBsettings', 'login', self.DBLoginLine.text())
        parser.set('DBsettings', 'password', self.DBPasswordLine.text())

        # Writing our configuration file to 'example.ini'
        with open('dev.ini', 'w') as configfile:
            parser.write(configfile)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Успех")
        msg.setText("Внимание")
        msg.setInformativeText("Изменения внесены!")
        msg.exec_()

    def setupUi(self, ConnectionSettings):
        ConnectionSettings.setObjectName("ConnectionSettings")
        ConnectionSettings.setWindowModality(QtCore.Qt.WindowModal)
        ConnectionSettings.resize(355, 181)
        self.saveButton = QtWidgets.QPushButton(ConnectionSettings)
        self.saveButton.setGeometry(QtCore.QRect(270, 150, 75, 23))
        self.saveButton.setObjectName("saveButton")
        self.saveButton.clicked.connect(self.save)
        self.label = QtWidgets.QLabel(ConnectionSettings)
        self.label.setGeometry(QtCore.QRect(10, 30, 71, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.DBIpLine = QtWidgets.QLineEdit(ConnectionSettings)
        self.DBIpLine.setGeometry(QtCore.QRect(102, 30, 241, 20))
        self.DBIpLine.setObjectName("DBIpLine")
        self.label_2 = QtWidgets.QLabel(ConnectionSettings)
        self.label_2.setGeometry(QtCore.QRect(90, 0, 221, 16))
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.DBPortLine = QtWidgets.QLineEdit(ConnectionSettings)
        self.DBPortLine.setGeometry(QtCore.QRect(102, 60, 241, 20))
        self.DBPortLine.setObjectName("DBPortLine")
        self.label_3 = QtWidgets.QLabel(ConnectionSettings)
        self.label_3.setGeometry(QtCore.QRect(10, 60, 71, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.DBLoginLine = QtWidgets.QLineEdit(ConnectionSettings)
        self.DBLoginLine.setGeometry(QtCore.QRect(100, 90, 241, 20))
        self.DBLoginLine.setObjectName("DBLoginLine")
        self.label_4 = QtWidgets.QLabel(ConnectionSettings)
        self.label_4.setGeometry(QtCore.QRect(10, 90, 71, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.DBPasswordLine = QtWidgets.QLineEdit(ConnectionSettings)
        self.DBPasswordLine.setGeometry(QtCore.QRect(100, 120, 241, 20))
        self.DBPasswordLine.setObjectName("DBPasswordLine")
        self.label_5 = QtWidgets.QLabel(ConnectionSettings)
        self.label_5.setGeometry(QtCore.QRect(10, 120, 71, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")

        self.retranslateUi(ConnectionSettings)
        QtCore.QMetaObject.connectSlotsByName(ConnectionSettings)

    def retranslateUi(self, ConnectionSettings):
        _translate = QtCore.QCoreApplication.translate
        ConnectionSettings.setWindowTitle(_translate("ConnectionSettings", "Настройка подключения к базе MySQL"))
        self.saveButton.setText(_translate("ConnectionSettings", "Принять"))
        self.label.setText(_translate("ConnectionSettings", "Ip-адресс"))
        self.DBPortLine.setPlaceholderText(_translate("ConnectionSettings", "если порт отустствует оставьте поле пустым"))
        self.label_3.setText(_translate("ConnectionSettings", "Порт"))
        self.label_4.setText(_translate("ConnectionSettings", "Логин"))
        self.label_5.setText(_translate("ConnectionSettings", "Пароль"))
        self.getData()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ConnectionSettings = QtWidgets.QDialog()
    ui = Ui_ConnectionSettings()
    ui.setupUi(ConnectionSettings)
    ConnectionSettings.show()
    sys.exit(app.exec_())
