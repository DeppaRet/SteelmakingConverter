import mysql.connector as mc
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt
from configparser import ConfigParser

parser = ConfigParser()

class Ui_ConnectionSettings(object):

    def getData(self):
        parser.read('dev.ini')
        self.DBIpLine.setText(str(parser.get('DBsettings', 'DBhost')))
        self.DBLoginLine.setText(str(parser.get('DBsettings', 'login')))
        self.DBPasswordLine.setText(str(parser.get('DBsettings', 'password')))

    def save(self):
        parser = ConfigParser()
        parser.read('dev.ini')
        parser.set('DBsettings', 'DBhost', self.DBIpLine.text())
        parser.set('DBsettings', 'login', self.DBLoginLine.text())
        parser.set('DBsettings', 'password', self.DBPasswordLine.text())

        with open('dev.ini', 'w') as configfile:
            parser.write(configfile)

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
                database='users_db',
                user=self.DBLoginLine.text(),
                password=self.DBPasswordLine.text()
            )
            if connection.is_connected():
                db_info = connection.get_server_info()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Внимание")
                msg.setText("Выполнено подключение к MySQL Server версии " + db_info)
                print("Connected to MySQL Server version ", db_info)
                cursor = connection.cursor()
                cursor.execute("select database();")
                record = cursor.fetchone()
                print("You're connected to database: ", record)
                msg.setInformativeText("Подключение к БД установлено!")
                msg.exec_()

        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("При подключении возникла ошибка: \n" + str(e))
            msg.exec_()
            print("Error while connecting to MySQL", e)

    def setupUi(self, ConnectionSettings):
        ConnectionSettings.setObjectName("ConnectionSettings")
        ConnectionSettings.setWindowModality(Qt.WindowModal)
        ConnectionSettings.setFixedSize(400, 320)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(25, 25, 35))
        ConnectionSettings.setPalette(palette)

        self.centralwidget = QtWidgets.QWidget(ConnectionSettings)
        self.centralwidget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e);
            }
        """)

        self.titleLabel = QtWidgets.QLabel(self.centralwidget)
        self.titleLabel.setGeometry(0, 10, 400, 30)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        titleFont = QFont("Segoe UI", 14, QFont.Bold)
        self.titleLabel.setFont(titleFont)
        self.titleLabel.setStyleSheet("color: #00d4ff; background: transparent;")

        self.formContainer = QtWidgets.QWidget(self.centralwidget)
        self.formContainer.setGeometry(25, 50, 350, 200)
        self.formContainer.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                border: 1px solid rgba(0, 212, 255, 0.2);
            }
        """)

        lineEditStyle = """
            QLineEdit {
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
                background: rgba(0, 212, 255, 0.1);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """

        rowY = [25, 70, 115, 160]
        labels = ["Хост", "Порт", "Логин", "Пароль"]
        self.lines = []

        for i, (y, label) in enumerate(zip(rowY, labels)):
            lbl = QtWidgets.QLabel(self.formContainer)
            lbl.setGeometry(20, y, 70, 25)
            lbl.setText(label)
            lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            lbl.setStyleSheet("color: #ffffff; background: transparent;")

            line = QtWidgets.QLineEdit(self.formContainer)
            line.setGeometry(95, y - 5, 235, 32)
            line.setFont(QFont("Segoe UI", 11))
            line.setStyleSheet(lineEditStyle)
            self.lines.append(line)

        self.DBIpLine = self.lines[0]
        self.DBPortLine = self.lines[1]
        self.DBLoginLine = self.lines[2]
        self.DBPasswordLine = self.lines[3]
        self.DBPortLine.setPlaceholderText("3306 (опционально)")

        self.buttonContainer = QtWidgets.QWidget(self.centralwidget)
        self.buttonContainer.setGeometry(25, 260, 350, 45)
        self.buttonContainer.setStyleSheet("background: transparent;")

        self.testButton = QtWidgets.QPushButton(self.buttonContainer)
        self.testButton.setGeometry(0, 5, 140, 35)
        self.testButton.setText("Тест соединения")
        self.testButton.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.testButton.setCursor(Qt.PointingHandCursor)
        self.testButton.setStyleSheet("""
            QPushButton {
                background: rgba(0, 212, 255, 0.2);
                color: #00d4ff;
                border: 1px solid #00d4ff;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(0, 212, 255, 0.4);
            }
        """)
        self.testButton.clicked.connect(self.connect_to_db)

        self.saveButton = QtWidgets.QPushButton(self.buttonContainer)
        self.saveButton.setGeometry(210, 5, 140, 35)
        self.saveButton.setText("Сохранить")
        self.saveButton.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.saveButton.setCursor(Qt.PointingHandCursor)
        self.saveButton.setStyleSheet("""
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
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 212, 255, 60))
        shadow.setOffset(0, 3)
        self.saveButton.setGraphicsEffect(shadow)
        self.saveButton.clicked.connect(self.save)

        self.retranslateUi(ConnectionSettings)
        QtCore.QMetaObject.connectSlotsByName(ConnectionSettings)

    def retranslateUi(self, ConnectionSettings):
        _translate = QtCore.QCoreApplication.translate
        ConnectionSettings.setWindowTitle(_translate("ConnectionSettings", "Настройка подключения"))
        self.titleLabel.setText(_translate("ConnectionSettings", "Настройка подключения к БД"))
        self.getData()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ConnectionSettings = QtWidgets.QDialog()
    ui = Ui_ConnectionSettings()
    ui.setupUi(ConnectionSettings)
    ConnectionSettings.show()
    sys.exit(app.exec_())
