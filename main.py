from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QLineEdit
import AdminForm
import OperForm
import DeveloperForm
import mysql.connector as mc
from SteelmakingConverter import hashAuth, connSettings
from configparser import ConfigParser

DBhost = "localhost"
DBlogin = "root"
DBpass = "root"
parser = ConfigParser()

# config = ConfigParser()
#
# config['DBsettings'] = {
#     'DBhost': 'localhost',
#     'login': 'root',
#     'password': 'root'
# }
# with open('./dev.ini', 'w') as f:
#     config.write(f)

class Ui_LoginForm(object):

    def getSettings(self):
        parser.read('dev.ini')
        global DBhost
        DBhost = (str(parser.get('DBsettings', 'DBhost')))
        global DBlogin
        DBlogin = (str(parser.get('DBsettings', 'login')))
        global DBpass
        DBpass = (str(parser.get('DBsettings', 'password')))

    def LoginButtonClick(self):
        self.loginFunc()

    def loginFunc(self):
        try:
            self.getSettings()
            msg = QMessageBox()
            login = self.LoginLine.text()
            password = self.PasswordLine.text()
            password = hashAuth.Hash.getHash(password)
            usersDB = mc.connect(
                host= DBhost, #192.168.51.179
                user= DBlogin, #user="root",
                password= DBpass, #password="root",
                database="users_db"
            )
            result = ""
            mycursor = usersDB.cursor()
            query = "SELECT Roles_idRoles FROM users where Login like '" + login + "' AND Password Like '" + password + "';"
            mycursor.execute(query)
            result = mycursor.fetchone()[0]
            if result == None:
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Внимание")
                msg.setInformativeText('Неверный логин или пароль')
                msg.setWindowTitle("Ошибка")
                msg.exec_()

            elif result == 1:
                self.window = QtWidgets.QMainWindow()
                # self.window.setWindowModality(QtCore.Qt.WindowModal)
                self.ui = AdminForm.Ui_AdminFom()
                # self.ui.administrate.isEnabled(True)
                self.ui.setupUi(self.window)
                self.window.show()
            elif result == 2:
                # msg.setInformativeText('Логин в качестве оператора')
                # msg.setWindowTitle("Успех")
                # msg.exec_()
                self.window = QtWidgets.QMainWindow()
                # self.window.setWindowModality(QtCore.Qt.WindowModal)
                self.ui = OperForm.Ui_OperatorForm()
                self.ui.setupUi(self.window)
                self.window.show()
            elif result == 3:
                # msg.setInformativeText('Логин в качестве разработчика модели')
                # msg.setWindowTitle("Успех")
                # msg.exec_()
                self.window = QtWidgets.QMainWindow()
                # self.window.setWindowModality(QtCore.Qt.WindowModal)
                self.ui = DeveloperForm.Ui_Form()
                self.ui.setupUi(self.window)
                self.window.show()

        except Exception as err:  # mc.Error
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def openSettings(self):
        self.window = QtWidgets.QDialog()
        # self.window.setWindowModality(QtCore.Qt.WindowModal)
        self.ui = connSettings.Ui_ConnectionSettings()
        self.ui.setupUi(self.window)
        self.window.exec_()

    # ---------------------------- Interface ----------------------------
    def setupUi(self, LoginForm):
        LoginForm.setObjectName("LoginForm")
        LoginForm.setFixedSize(462, 180)
        LoginForm.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        LoginForm.setDocumentMode(False)
        LoginForm.setTabShape(QtWidgets.QTabWidget.Triangular)
        winIcon = QtGui.QIcon()
        winIcon.addPixmap(QtGui.QPixmap("SteelmakingConverter/Pictures/steel_ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        LoginForm.setWindowIcon(winIcon)
        self.centralwidget = QtWidgets.QWidget(LoginForm)
        self.centralwidget.setObjectName("centralwidget")
        self.loginButton = QtWidgets.QPushButton(self.centralwidget)

        self.loginButton.clicked.connect(self.LoginButtonClick)

        self.loginButton.setGeometry(QtCore.QRect(340, 130, 111, 41))
        self.loginButton.setObjectName("loginButton")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 30, 111, 121))
        self.label.setMaximumSize(QtCore.QSize(291, 151))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap("SteelmakingConverter/Pictures/emergency-exit.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(150, 50, 304, 66))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.loginLabel = QtWidgets.QLabel(self.widget)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.loginLabel.setFont(font)
        self.loginLabel.setObjectName("loginLabel")
        self.horizontalLayout.addWidget(self.loginLabel)
        self.LoginLine = QtWidgets.QLineEdit(self.widget)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.LoginLine.setFont(font)
        self.LoginLine.setPlaceholderText("")
        self.LoginLine.setObjectName("LoginLine")
        self.horizontalLayout.addWidget(self.LoginLine)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.passwordLabel = QtWidgets.QLabel(self.widget)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.passwordLabel.setFont(font)
        self.passwordLabel.setObjectName("passwordLabel")
        self.horizontalLayout_2.addWidget(self.passwordLabel)
        self.PasswordLine = QtWidgets.QLineEdit(self.widget)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.PasswordLine.setFont(font)
        self.PasswordLine.setPlaceholderText("")
        self.PasswordLine.setObjectName("PasswordLine")
        self.PasswordLine.setEchoMode(QLineEdit.Password)
        self.horizontalLayout_2.addWidget(self.PasswordLine)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.SettingsButton = QtWidgets.QPushButton(self.centralwidget)
        self.SettingsButton.setGeometry(QtCore.QRect(430, 10, 21, 20))
        self.SettingsButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("SteelmakingConverter/Pictures/png-transparent-settings-gear-icon-gear-configuration-set-up-thumbnail.png"))
        self.SettingsButton.setIcon(icon)
        self.SettingsButton.setObjectName("SettingsButton")
        self.SettingsButton.clicked.connect(self.openSettings)
        LoginForm.setCentralWidget(self.centralwidget)

        self.retranslateUi(LoginForm)
        QtCore.QMetaObject.connectSlotsByName(LoginForm)

    def retranslateUi(self, LoginForm):
        _translate = QtCore.QCoreApplication.translate
        LoginForm.setWindowTitle(_translate("LoginForm", "Авторизация"))
        self.loginButton.setText(_translate("LoginForm", "Войти"))
        self.loginLabel.setText(_translate("LoginForm", "Логин:"))
        self.passwordLabel.setText(_translate("LoginForm", "Пароль:"))
        self.getSettings()



if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    LoginForm = QtWidgets.QMainWindow()
    ui = Ui_LoginForm()
    ui.setupUi(LoginForm)
    LoginForm.show()
    sys.exit(app.exec_())

# https://ru.stackoverflow.com/questions/771907/pyqt5-%D0%9E%D1%82%D0%BA%D1%80%D1%8B%D1%82%D1%8C-%D1%84%D0%BE%D1%80%D0%BC%D1%83-%D0%B2-%D0%B4%D1%80%D1%83%D0%B3%D0%BE%D0%B9-%D1%84%D0%BE%D1%80%D0%BC%D0%B5-%D0%BA%D0%BE%D1%82%D0%BE%D1%80%D1%8B%D0%B5-%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D1%8B%D0%B5-%D0%B2-qt-design
