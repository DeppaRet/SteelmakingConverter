import os, site, sys

# Chromium sandbox can cause hard native crashes on some Windows configs.
# --no-sandbox disables it; must be set before any Qt import.
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox")

# Add user-level Qt5/bin to DLL search path BEFORE any PyQt5 imports so that
# PyQtWebEngine DLLs (installed to user AppData) are found on Windows.
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    _qt_dll_dirs: list[str] = []
    try:
        _qt_dll_dirs.append(site.getusersitepackages())
    except Exception:
        pass
    try:
        _qt_dll_dirs.extend(site.getsitepackages())
    except Exception:
        pass
    for _sp in _qt_dll_dirs:
        _d = os.path.join(_sp, "PyQt5", "Qt5", "bin")
        if os.path.isdir(_d):
            try:
                os.add_dll_directory(_d)
            except OSError:
                pass

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QLineEdit, QGraphicsDropShadowEffect
from PyQt5.QtGui import QLinearGradient, QPalette, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QRect, QPoint

# QtWebEngineWidgets MUST be imported before QCoreApplication is created.
# Do it here (before QApplication in __main__) so OperForm can use it safely.
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView as _  # noqa: F401
    del _
except Exception:
    pass
import AdminForm
import OperForm
import DeveloperForm
import mysql.connector as mc
import hashAuth, connSettings
from configparser import ConfigParser
import config

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
        LoginForm.setFixedSize(420, 340)
        
        winIcon = QtGui.QIcon()
        winIcon.addPixmap(QtGui.QPixmap("Pictures/steel_ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        LoginForm.setWindowIcon(winIcon)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(25, 25, 35))
        LoginForm.setPalette(palette)

        self.centralwidget = QtWidgets.QWidget(LoginForm)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet("""
            QWidget#centralwidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e);
                border-radius: 15px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

        self.titleLabel = QtWidgets.QLabel(self.centralwidget)
        self.titleLabel.setGeometry(0, 15, 420, 30)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        titleFont = QFont("Segoe UI", 14, QFont.Bold)
        self.titleLabel.setFont(titleFont)
        self.titleLabel.setStyleSheet("color: #00d4ff; background: transparent;")

        self.iconLabel = QtWidgets.QLabel(self.centralwidget)
        self.iconLabel.setGeometry(155, 50, 110, 80)
        self.iconLabel.setAlignment(Qt.AlignCenter)
        self.iconLabel.setPixmap(QtGui.QPixmap("Pictures/steel_ico.png").scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.iconLabel.setStyleSheet("background: #e8e8e8; border-radius: 12px; border: 2px solid #00d4ff; padding: 5px;")

        self.formContainer = QtWidgets.QWidget(self.centralwidget)
        self.formContainer.setGeometry(40, 145, 340, 140)
        self.formContainer.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                border: 1px solid rgba(0, 212, 255, 0.2);
            }
        """)

        self.loginLabel = QtWidgets.QLabel(self.formContainer)
        self.loginLabel.setGeometry(25, 20, 70, 25)
        loginLabelFont = QFont("Segoe UI", 11, QFont.Bold)
        self.loginLabel.setFont(loginLabelFont)
        self.loginLabel.setStyleSheet("color: #ffffff; background: transparent;")

        self.LoginLine = QtWidgets.QLineEdit(self.formContainer)
        self.LoginLine.setGeometry(100, 15, 215, 35)
        self.LoginLine.setFont(QFont("Segoe UI", 11))
        self.LoginLine.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                padding: 5px 12px;
                color: #ffffff;
                selection-background-color: #00d4ff;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
                background: rgba(0, 212, 255, 0.1);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        self.LoginLine.setPlaceholderText("Введите логин")

        self.passwordLabel = QtWidgets.QLabel(self.formContainer)
        self.passwordLabel.setGeometry(25, 60, 70, 25)
        self.passwordLabel.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.passwordLabel.setStyleSheet("color: #ffffff; background: transparent;")

        self.PasswordLine = QtWidgets.QLineEdit(self.formContainer)
        self.PasswordLine.setGeometry(100, 55, 215, 35)
        self.PasswordLine.setFont(QFont("Segoe UI", 11))
        self.PasswordLine.setEchoMode(QLineEdit.Password)
        self.PasswordLine.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                padding: 5px 12px;
                color: #ffffff;
                selection-background-color: #00d4ff;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
                background: rgba(0, 212, 255, 0.1);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        self.PasswordLine.setPlaceholderText("Введите пароль")

        self.loginButton = QtWidgets.QPushButton(self.formContainer)
        self.loginButton.setGeometry(100, 100, 140, 32)
        self.loginButton.setCursor(Qt.PointingHandCursor)
        self.loginButton.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.loginButton.setText("Войти")
        self.loginButton.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d4ff, stop:1 #0099cc);
                color: #1a1a2e;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e5ff, stop:1 #00b8d9);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0099cc, stop:1 #0077aa);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 212, 255, 80))
        shadow.setOffset(0, 4)
        self.loginButton.setGraphicsEffect(shadow)
        self.loginButton.clicked.connect(self.LoginButtonClick)

        self.SettingsButton = QtWidgets.QPushButton(self.centralwidget)
        self.SettingsButton.setGeometry(385, 295, 30, 20)
        self.SettingsButton.setText("")
        self.SettingsButton.setCursor(Qt.PointingHandCursor)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Pictures/png-transparent-settings-gear-icon-gear-configuration-set-up-thumbnail.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SettingsButton.setIcon(icon)
        self.SettingsButton.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        self.SettingsButton.clicked.connect(self.openSettings)

        LoginForm.setCentralWidget(self.centralwidget)

        self.retranslateUi(LoginForm)
        QtCore.QMetaObject.connectSlotsByName(LoginForm)

    def retranslateUi(self, LoginForm):
        _translate = QtCore.QCoreApplication.translate
        LoginForm.setWindowTitle(_translate("LoginForm", "Авторизация"))
        self.titleLabel.setText(_translate("LoginForm", "Steelmaking Converter"))
        self.loginLabel.setText(_translate("LoginForm", "Логин"))
        self.passwordLabel.setText(_translate("LoginForm", "Пароль"))
        self.getSettings()



if __name__ == "__main__":
    import sys

    # QtWebEngineWidgets requires this attribute to be set before QApplication
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)
    LoginForm = QtWidgets.QMainWindow()
    ui = Ui_LoginForm()
    ui.setupUi(LoginForm)
    LoginForm.show()
    sys.exit(app.exec_())

# https://ru.stackoverflow.com/questions/771907/pyqt5-%D0%9E%D1%82%D0%BA%D1%80%D1%8B%D1%82%D1%8C-%D1%84%D0%BE%D1%80%D0%BC%D1%83-%D0%B2-%D0%B4%D1%80%D1%83%D0%B3%D0%BE%D0%B9-%D1%84%D0%BE%D1%80%D0%BC%D0%B5-%D0%BA%D0%BE%D1%82%D0%BE%D1%80%D1%8B%D0%B5-%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D0%BD%D1%8B%D0%B5-%D0%B2-qt-design
def getLogin():
    login = Ui_LoginForm.LoginLine.text()
    return login