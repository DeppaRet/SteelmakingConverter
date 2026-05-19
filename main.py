import os
import sys

from converter3d.qt_bootstrap import bootstrap_qt

bootstrap_qt()

from PyQt5 import QtCore, QtGui, QtWidgets

# Required before QtWebEngine import AND before QApplication.
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)

from PyQt5.QtWidgets import QMessageBox, QLineEdit, QGraphicsDropShadowEffect
from PyQt5.QtGui import QLinearGradient, QPalette, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QRect, QPoint

import AdminForm
import OperForm
import DeveloperForm
import mysql.connector as mc
import hashAuth, connSettings
from configparser import ConfigParser
import config
import app_theme
from theme_settings import manager, get_theme
from theme_toggle import ThemeToggle

DBhost = "localhost"
DBlogin = "root"
DBpass = "root"
parser = ConfigParser()


#кафедральный ip 192.168.51.179


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
    def refresh_theme(self):
        theme = get_theme()
        styles = app_theme.login_styles(theme)
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app_theme.apply_to_application(app, theme)
        if hasattr(self, '_login_form') and self._login_form:
            self._login_form.setPalette(app_theme.palette(theme))
        self.centralwidget.setStyleSheet(styles["central"])
        self.titleLabel.setStyleSheet(styles["title"])
        self.iconLabel.setStyleSheet(styles["icon"])
        self.formContainer.setStyleSheet(styles["form_panel"])
        self.loginLabel.setStyleSheet(styles["label"])
        self.passwordLabel.setStyleSheet(styles["label"])
        self.LoginLine.setStyleSheet(styles["line_edit"])
        self.PasswordLine.setStyleSheet(styles["line_edit"])
        self.loginButton.setStyleSheet(styles["primary_btn"])
        self.SettingsButton.setStyleSheet(styles["settings_btn"])
        if hasattr(self, "theme_toggle"):
            self.theme_toggle.sync_from_settings()

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
                host=DBhost,                                        #192.168.51.179
                user=DBlogin,                                       #user="root",
                password=DBpass,                                    #password="root",
                database="users_db"
            )
            result = ""
            config.UserLogin = login
            mycursor = usersDB.cursor()
            query = "SELECT Roles_idRoles FROM users where Login like '" + login + "' AND Password Like '" + password + "';"
            mycursor.execute(query)
            result = mycursor.fetchone()[0]
            if result == None:
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Внимание")
                msg.setInformativeText('Неверный логин или пароль')
                msg.setWindowTitle("Ошибка")
                app_theme.style_message_box(msg)
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
            msg.setInformativeText("Проверьте введенные данные или настройки подключения!")
            # msg.setInformativeText("Error: {0}".format(err))
            app_theme.style_message_box(msg)
            msg.exec_()

    def openSettings(self):
        parent = getattr(self, "_login_form", None)
        dlg = QtWidgets.QDialog(parent)
        dlg.setWindowModality(Qt.WindowModal)
        ui = connSettings.Ui_ConnectionSettings()
        ui.setupUi(dlg)
        dlg.exec_()
        self.refresh_theme()

    # ---------------------------- Interface ----------------------------
    def setupUi(self, LoginForm):
        LoginForm.setObjectName("LoginForm")
        LoginForm.setFixedSize(420, 340)
        self._login_form = LoginForm

        winIcon = QtGui.QIcon()
        winIcon.addPixmap(QtGui.QPixmap("Pictures/steel_ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        LoginForm.setWindowIcon(winIcon)

        self.centralwidget = QtWidgets.QWidget(LoginForm)
        self.centralwidget.setObjectName("centralwidget")

        self.titleLabel = QtWidgets.QLabel(self.centralwidget)
        self.titleLabel.setGeometry(0, 15, 420, 30)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        titleFont = QFont("Segoe UI", 14, QFont.Bold)
        self.titleLabel.setFont(titleFont)

        self.iconLabel = QtWidgets.QLabel(self.centralwidget)
        self.iconLabel.setGeometry(155, 50, 110, 80)
        self.iconLabel.setAlignment(Qt.AlignCenter)
        self.iconLabel.setPixmap(QtGui.QPixmap("Pictures/steel_ico.png").scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.formContainer = QtWidgets.QWidget(self.centralwidget)
        self.formContainer.setObjectName("loginFormPanel")
        self.formContainer.setGeometry(40, 145, 340, 140)

        self.loginLabel = QtWidgets.QLabel(self.formContainer)
        self.loginLabel.setGeometry(25, 20, 70, 25)
        loginLabelFont = QFont("Segoe UI", 11, QFont.Bold)
        self.loginLabel.setFont(loginLabelFont)

        self.LoginLine = QtWidgets.QLineEdit(self.formContainer)
        self.LoginLine.setGeometry(100, 15, 215, 35)
        self.LoginLine.setFont(QFont("Segoe UI", 11))
        self.LoginLine.setPlaceholderText("Введите логин")

        self.passwordLabel = QtWidgets.QLabel(self.formContainer)
        self.passwordLabel.setGeometry(25, 60, 70, 25)
        self.passwordLabel.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.PasswordLine = QtWidgets.QLineEdit(self.formContainer)
        self.PasswordLine.setGeometry(100, 55, 215, 35)
        self.PasswordLine.setFont(QFont("Segoe UI", 11))
        self.PasswordLine.setEchoMode(QLineEdit.Password)
        self.PasswordLine.setPlaceholderText("Введите пароль")

        self.loginButton = QtWidgets.QPushButton(self.formContainer)
        self.loginButton.setGeometry(100, 100, 140, 32)
        self.loginButton.setCursor(Qt.PointingHandCursor)
        self.loginButton.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.loginButton.setText("Войти")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 212, 255, 80))
        shadow.setOffset(0, 4)
        self.loginButton.setGraphicsEffect(shadow)
        self.loginButton.clicked.connect(self.LoginButtonClick)

        self.SettingsButton = QtWidgets.QPushButton(self.centralwidget)
        self.SettingsButton.setGeometry(268, 295, 30, 24)
        self.SettingsButton.setText("")
        self.SettingsButton.setCursor(Qt.PointingHandCursor)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Pictures/png-transparent-settings-gear-icon-gear-configuration-set-up-thumbnail.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SettingsButton.setIcon(icon)
        self.SettingsButton.clicked.connect(self.openSettings)

        self.theme_toggle = ThemeToggle(self.centralwidget)
        self.theme_toggle.setGeometry(300, 293, 76, 28)
        self.theme_toggle.theme_changed.connect(lambda _t: self.refresh_theme())

        LoginForm.setCentralWidget(self.centralwidget)

        self.retranslateUi(LoginForm)
        QtCore.QMetaObject.connectSlotsByName(LoginForm)
        self.refresh_theme()
        manager().theme_changed.connect(lambda _t: self.refresh_theme())

    def retranslateUi(self, LoginForm):
        _translate = QtCore.QCoreApplication.translate
        LoginForm.setWindowTitle(_translate("LoginForm", "Авторизация"))
        self.titleLabel.setText(_translate("LoginForm", "Steelmaking Converter"))
        self.loginLabel.setText(_translate("LoginForm", "Логин"))
        self.passwordLabel.setText(_translate("LoginForm", "Пароль"))
        self.getSettings()



if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    theme = get_theme()
    app_theme.apply_to_application(app, theme)
    manager().theme_changed.connect(
        lambda t: app_theme.apply_to_application(app, t)
    )
    try:
        from converter3d.visual_style import set_ui_theme
        set_ui_theme(theme)
    except ImportError:
        pass
    LoginForm = QtWidgets.QMainWindow()
    ui = Ui_LoginForm()
    ui.setupUi(LoginForm)
    LoginForm.show()
    sys.exit(app.exec_())

# https://ru.stackoverflow.com/questions/771907/pyqt5-%D0%9E%D1%82%D0%BA%D1%80%D1%8B%D1%82%D1%8C-%D1%84%D0%BE%D1%80%D0%BC%D1%83-%D0%B2-%D0%B4%D1%80%D1%83%D0%B3%D0%BE%D0%B9-%D1%84%D0%BE%D1%80%D0%BC%D0%B5-%D0%BA%D0%BE%D1%82%D0%BE%D1%80%D1%8B%D0%B5-%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D1%8B%D0%B5-%D0%B2-qt-design
def getLogin():
    login = Ui_LoginForm.LoginLine.text()
    return login