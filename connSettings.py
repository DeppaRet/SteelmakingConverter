import mysql.connector as mc
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QGraphicsDropShadowEffect
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from configparser import ConfigParser

import app_theme
from theme_settings import manager, get_theme, THEME_DARK, THEME_LIGHT
from theme_toggle import ThemeToggle

parser = ConfigParser()


def _read_db_option(cfg: ConfigParser, key: str, default: str = "") -> str:
    if not cfg.has_section("DBsettings"):
        return default
    for k in (key, key.lower(), key.upper()):
        if cfg.has_option("DBsettings", k):
            return str(cfg.get("DBsettings", k))
    return default


class Ui_ConnectionSettings(object):

    def getData(self):
        cfg = ConfigParser()
        cfg.read("dev.ini", encoding="utf-8")
        self.DBIpLine.setText(_read_db_option(cfg, "DBhost", "localhost"))
        self.DBLoginLine.setText(_read_db_option(cfg, "login", "root"))
        self.DBPasswordLine.setText(_read_db_option(cfg, "password", ""))
        if hasattr(self, "theme_toggle"):
            self.theme_toggle.sync_from_settings()

    def save(self):
        cfg = ConfigParser()
        cfg.read("dev.ini", encoding="utf-8")
        if not cfg.has_section("DBsettings"):
            cfg.add_section("DBsettings")
        cfg.set("DBsettings", "DBhost", self.DBIpLine.text())
        cfg.set("DBsettings", "login", self.DBLoginLine.text())
        cfg.set("DBsettings", "password", self.DBPasswordLine.text())
        theme = THEME_LIGHT if self.theme_toggle.is_light() else THEME_DARK
        if not cfg.has_section("AppSettings"):
            cfg.add_section("AppSettings")
        cfg.set("AppSettings", "theme", theme)

        with open("dev.ini", "w", encoding="utf-8") as configfile:
            cfg.write(configfile)
        manager().set_theme(theme, persist=False)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Успех")
        msg.setText("Внимание")
        msg.setInformativeText("Изменения внесены!")
        msg.exec_()

    def connect_to_db(self):
        try:
            connection = mc.connect(
                host=self.DBIpLine.text(),
                database="users_db",
                user=self.DBLoginLine.text(),
                password=self.DBPasswordLine.text(),
            )
            if connection.is_connected():
                db_info = connection.get_server_info()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Внимание")
                msg.setText("Выполнено подключение к MySQL Server версии " + db_info)
                msg.setInformativeText("Подключение к БД установлено!")
                msg.exec_()
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("При подключении возникла ошибка: \n" + str(e))
            msg.exec_()

    def refresh_theme(self, ConnectionSettings):
        theme = get_theme()
        styles = app_theme.connection_styles(theme)
        ConnectionSettings.setPalette(app_theme.palette(theme))
        self.centralwidget.setStyleSheet(styles["central"])
        self.titleLabel.setStyleSheet(styles["title"])
        self.formContainer.setStyleSheet(styles["form_panel"])
        for lbl in getattr(self, "_field_labels", []):
            lbl.setStyleSheet(styles["label"])
        for line in self.lines:
            line.setStyleSheet(styles["line_edit"])
        self.testButton.setStyleSheet(styles["test_btn"])
        self.saveButton.setStyleSheet(styles["save_btn"])
        if hasattr(self, "theme_toggle"):
            self.theme_toggle.sync_from_settings()

    def setupUi(self, ConnectionSettings):
        ConnectionSettings.setObjectName("ConnectionSettings")
        ConnectionSettings.setWindowModality(Qt.WindowModal)
        ConnectionSettings.setFixedSize(400, 380)
        self._dialog = ConnectionSettings

        theme = get_theme()
        styles = app_theme.connection_styles(theme)
        ConnectionSettings.setPalette(app_theme.palette(theme))

        root_layout = QtWidgets.QVBoxLayout(ConnectionSettings)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.centralwidget = QtWidgets.QWidget(ConnectionSettings)
        self.centralwidget.setFixedSize(400, 380)
        root_layout.addWidget(self.centralwidget)

        self.titleLabel = QtWidgets.QLabel(self.centralwidget)
        self.titleLabel.setGeometry(0, 10, 400, 30)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.titleLabel.setStyleSheet(styles["title"])

        self.formContainer = QtWidgets.QWidget(self.centralwidget)
        self.formContainer.setGeometry(25, 50, 350, 250)
        self.formContainer.setStyleSheet(styles["form_panel"])

        rowY = [25, 70, 115, 160, 205]
        labels = ["Хост", "Порт", "Логин", "Пароль", "Тема"]
        self.lines = []
        self._field_labels = []

        for y, label in zip(rowY, labels):
            lbl = QtWidgets.QLabel(self.formContainer)
            lbl.setGeometry(20, y, 70, 25)
            lbl.setText(label)
            lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            lbl.setStyleSheet(styles["label"])
            self._field_labels.append(lbl)

            if label == "Тема":
                self.theme_toggle = ThemeToggle(self.formContainer, persist=False)
                self.theme_toggle.setGeometry(95, y - 1, 76, 28)
                self.theme_toggle.sync_from_settings()
                continue

            line = QtWidgets.QLineEdit(self.formContainer)
            line.setGeometry(95, y - 5, 235, 32)
            line.setFont(QFont("Segoe UI", 11))
            line.setStyleSheet(styles["line_edit"])
            self.lines.append(line)

        self.DBIpLine = self.lines[0]
        self.DBPortLine = self.lines[1]
        self.DBLoginLine = self.lines[2]
        self.DBPasswordLine = self.lines[3]
        self.DBPortLine.setPlaceholderText("3306 (опционально)")

        self.buttonContainer = QtWidgets.QWidget(self.centralwidget)
        self.buttonContainer.setGeometry(25, 315, 350, 45)
        self.buttonContainer.setStyleSheet("background: transparent;")

        self.testButton = QtWidgets.QPushButton(self.buttonContainer)
        self.testButton.setGeometry(0, 5, 140, 35)
        self.testButton.setText("Тест соединения")
        self.testButton.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.testButton.setCursor(Qt.PointingHandCursor)
        self.testButton.setStyleSheet(styles["test_btn"])
        self.testButton.clicked.connect(self.connect_to_db)

        self.saveButton = QtWidgets.QPushButton(self.buttonContainer)
        self.saveButton.setGeometry(210, 5, 140, 35)
        self.saveButton.setText("Сохранить")
        self.saveButton.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.saveButton.setCursor(Qt.PointingHandCursor)
        self.saveButton.setStyleSheet(styles["save_btn"])
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QtGui.QColor(0, 120, 168, 60))
        shadow.setOffset(0, 3)
        self.saveButton.setGraphicsEffect(shadow)
        self.saveButton.clicked.connect(self.save)

        self.retranslateUi(ConnectionSettings)
        QtCore.QMetaObject.connectSlotsByName(ConnectionSettings)
        manager().theme_changed.connect(
            lambda _t: self.refresh_theme(ConnectionSettings)
        )

    def retranslateUi(self, ConnectionSettings):
        _translate = QtCore.QCoreApplication.translate
        ConnectionSettings.setWindowTitle(
            _translate("ConnectionSettings", "Настройка подключения"))
        self.titleLabel.setText(
            _translate("ConnectionSettings", "Настройка подключения к БД"))
        self.getData()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dlg = QtWidgets.QDialog()
    ui = Ui_ConnectionSettings()
    ui.setupUi(dlg)
    dlg.show()
    sys.exit(app.exec_())
