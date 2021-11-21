from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QLineEdit
import AdminForm
import OperForm
import mysql.connector as mc


class Ui_LoginForm(object):
    def LoginButtonClick(self):
        self.loginFunc()

    def loginFunc(self):
        try:
            msg = QMessageBox()
            login = self.LoginLine.text()
            password = self.PasswordLine.text()

            usersDB = mc.connect(
                host="localhost",
                user="root",
                password="root",
                database="mydb"
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
                msg.setInformativeText('Логин в качестве разработчика модели')
                msg.setWindowTitle("Успех")
                msg.exec_()
                # self.window = QtWidgets.QMainWindow()
                # self.window.setWindowModality(QtCore.Qt.WindowModal)
                # self.ui = OperForm.Ui_OperatorForm()
                # self.ui.administrate.isEnabled(True)
                # self.ui.setupUi(self.window)
                # self.window.show()

        except Exception as err:  # mc.Error
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    # ---------------------------- Interface ----------------------------
    def setupUi(self, LoginForm):
        LoginForm.setObjectName("LoginForm")
        LoginForm.setFixedSize(462, 180)
        LoginForm.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        LoginForm.setDocumentMode(False)
        LoginForm.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.centralwidget = QtWidgets.QWidget(LoginForm)
        self.centralwidget.setObjectName("centralwidget")
        self.loginButton = QtWidgets.QPushButton(self.centralwidget)

        self.loginButton.clicked.connect(self.LoginButtonClick)  # КЛИК КНОПКИ ----------------------------------------

        self.loginButton.setGeometry(QtCore.QRect(340, 130, 111, 41))
        self.loginButton.setObjectName("loginButton")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 30, 111, 121))
        self.label.setMaximumSize(QtCore.QSize(291, 151))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(
            "../../../Рабочий стол/ВУЗ/6 сем/Методы оптимизации/Курсовой проект МО/Курсовой проект методы оптимизации Левинский/OptimizationCourseProject/OptimizationMethods/WindowsFormsApp1/sources/emergency-exit.png"))
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
        LoginForm.setCentralWidget(self.centralwidget)

        self.retranslateUi(LoginForm)
        QtCore.QMetaObject.connectSlotsByName(LoginForm)

    def retranslateUi(self, LoginForm):
        _translate = QtCore.QCoreApplication.translate
        LoginForm.setWindowTitle(_translate("LoginForm", "Авторизация"))
        self.loginButton.setText(_translate("LoginForm", "Войти"))
        self.loginLabel.setText(_translate("LoginForm", "Логин:"))
        self.passwordLabel.setText(_translate("LoginForm", "Пароль:"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    LoginForm = QtWidgets.QMainWindow()
    ui = Ui_LoginForm()
    ui.setupUi(LoginForm)
    LoginForm.show()
    sys.exit(app.exec_())

# https://ru.stackoverflow.com/questions/771907/pyqt5-%D0%9E%D1%82%D0%BA%D1%80%D1%8B%D1%82%D1%8C-%D1%84%D0%BE%D1%80%D0%BC%D1%83-%D0%B2-%D0%B4%D1%80%D1%83%D0%B3%D0%BE%D0%B9-%D1%84%D0%BE%D1%80%D0%BC%D0%B5-%D0%BA%D0%BE%D1%82%D0%BE%D1%80%D1%8B%D0%B5-%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D1%8B%D0%B5-%D0%B2-qt-design
