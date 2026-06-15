import os
import sys

from converter3d.qt_bootstrap import bootstrap_qt

bootstrap_qt()

from PyQt5 import QtCore, QtGui, QtWidgets

# Required before QtWebEngine import AND before QApplication.
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)

from PyQt5.QtWidgets import QLineEdit, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

import AdminForm
import OperForm
import DeveloperForm
import mysql.connector as mc
import hashAuth, connSettings
from configparser import ConfigParser
import config
import app_theme
from theme_settings import manager, get_theme
from locale_settings import manager as locale_manager, get_language
from view_toggles import ViewTogglesBar
from i18n import tr, msg_critical

DBhost = "localhost"
DBlogin = "root"
DBpass = "root"
parser = ConfigParser()


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
        if hasattr(self, "view_toggles"):
            self.view_toggles.theme_toggle.sync_from_settings()

    def refresh_language(self, LoginForm):
        self.retranslateUi(LoginForm)
        if hasattr(self, "view_toggles"):
            self.view_toggles.language_toggle.sync_from_settings()

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
            login = self.LoginLine.text()
            password = self.PasswordLine.text()

            password = hashAuth.Hash.getHash(password)
            usersDB = mc.connect(
                host=DBhost,
                user=DBlogin,
                password=DBpass,
                database="users_db"
            )
            result = ""
            config.UserLogin = login
            mycursor = usersDB.cursor()
            query = "SELECT Roles_idRoles FROM users where Login like '" + login + "' AND Password Like '" + password + "';"
            mycursor.execute(query)
            row = mycursor.fetchone()
            if row is None:
                result = None
            else:
                result = row[0]
            if result is None:
                msg_critical(
                    getattr(self, "_login_form", None),
                    "Ошибка",
                    "Внимание",
                    "Неверный логин или пароль",
                )

            elif result == 1:
                self.window = QtWidgets.QMainWindow()
                self.ui = AdminForm.Ui_AdminFom()
                self.ui.setupUi(self.window)
                self.window.show()
            elif result == 2:
                self.window = QtWidgets.QMainWindow()
                self.ui = OperForm.Ui_OperatorForm()
                self.ui.setupUi(self.window)
                self.window.show()
            elif result == 3:
                self.window = QtWidgets.QMainWindow()
                self.ui = DeveloperForm.Ui_Form()
                self.ui.setupUi(self.window)
                self.window.show()

        except Exception as err:
            detail = str(err).strip() or type(err).__name__
            msg_critical(
                getattr(self, "_login_form", None),
                "Ошибка",
                "Внимание",
                "Проверьте введенные данные или настройки подключения!\n\n"
                f"({detail})",
            )

    def openSettings(self):
        parent = getattr(self, "_login_form", None)
        dlg = QtWidgets.QDialog(parent)
        dlg.setWindowModality(Qt.WindowModal)
        ui = connSettings.Ui_ConnectionSettings()
        ui.setupUi(dlg)
        dlg.exec_()
        self.refresh_theme()
        self.refresh_language(parent)

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

        self.passwordLabel = QtWidgets.QLabel(self.formContainer)
        self.passwordLabel.setGeometry(25, 60, 70, 25)
        self.passwordLabel.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.PasswordLine = QtWidgets.QLineEdit(self.formContainer)
        self.PasswordLine.setGeometry(100, 55, 215, 35)
        self.PasswordLine.setFont(QFont("Segoe UI", 11))
        self.PasswordLine.setEchoMode(QLineEdit.Password)

        self.loginButton = QtWidgets.QPushButton(self.formContainer)
        self.loginButton.setGeometry(100, 100, 140, 32)
        self.loginButton.setCursor(Qt.PointingHandCursor)
        self.loginButton.setFont(QFont("Segoe UI", 11, QFont.Bold))
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 212, 255, 80))
        shadow.setOffset(0, 4)
        self.loginButton.setGraphicsEffect(shadow)
        self.loginButton.clicked.connect(self.LoginButtonClick)

        self.SettingsButton = QtWidgets.QPushButton(self.centralwidget)
        self.SettingsButton.setGeometry(384, 295, 30, 24)
        self.SettingsButton.setText("")
        self.SettingsButton.setCursor(Qt.PointingHandCursor)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Pictures/png-transparent-settings-gear-icon-gear-configuration-set-up-thumbnail.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SettingsButton.setIcon(icon)
        self.SettingsButton.clicked.connect(self.openSettings)

        self.view_toggles = ViewTogglesBar(self.centralwidget)
        self.view_toggles.setGeometry(126, 293, 168, 32)
        self.view_toggles.theme_toggle.theme_changed.connect(lambda _t: self.refresh_theme())
        self.view_toggles.language_toggle.language_changed.connect(
            lambda _l: self.refresh_language(LoginForm)
        )

        LoginForm.setCentralWidget(self.centralwidget)

        self.retranslateUi(LoginForm)
        QtCore.QMetaObject.connectSlotsByName(LoginForm)
        self.refresh_theme()
        manager().theme_changed.connect(lambda _t: self.refresh_theme())
        locale_manager().language_changed.connect(
            lambda _l: self.refresh_language(LoginForm)
        )

    def retranslateUi(self, LoginForm):
        from i18n import tr as _t
        LoginForm.setWindowTitle(_t("LoginForm", "Авторизация"))
        self.titleLabel.setText(_t("LoginForm", "Steelmaking Converter"))
        self.loginLabel.setText(_t("LoginForm", "Логин"))
        self.passwordLabel.setText(_t("LoginForm", "Пароль"))
        self.LoginLine.setPlaceholderText(_t("LoginForm", "Введите логин"))
        self.PasswordLine.setPlaceholderText(_t("LoginForm", "Введите пароль"))
        self.loginButton.setText(_t("LoginForm", "Войти"))
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
    ui.refresh_language(LoginForm)
    LoginForm.show()
    sys.exit(app.exec_())


def getLogin():
    login = Ui_LoginForm.LoginLine.text()
    return login
