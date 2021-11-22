from PyQt5 import QtCore, QtGui, QtWidgets
import mysql.connector as mc
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QTableWidgetItem

import OperForm


class Ui_AdminFom(object):

    def openOperForm(self):
        self.window = QtWidgets.QMainWindow()
        self.ui = OperForm.Ui_OperatorForm()
        self.ui.setupUi(self.window)
        self.window.show()

    def showTableForUsersClick(self):
        choosenTable = self.choosenTableForUsers.currentText()
        query = "SELECT * FROM "
        if choosenTable == "Пользователи":
            query += "users;"
            self.tableWidgetUsers.setColumnCount(4)
            self.tableWidgetUsers.setHorizontalHeaderLabels(["Номер", "Логин", "Пароль", "Роль"])
        elif choosenTable == "Роли":
            query += "userroles;"
            self.tableWidgetUsers.setColumnCount(2)
            self.tableWidgetUsers.setHorizontalHeaderLabels(["Номер", "Роль"])
        try:
            usersDB = mc.connect(
                host="localhost",
                user="root",
                password="root",
                database="mydb"
            )
            result = ""
            mycursor = usersDB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            self.tableWidgetUsers.setRowCount(0)

            for row_number, row_data in enumerate(result):
                self.tableWidgetUsers.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.tableWidgetUsers.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()



    def showTableForFactoryClick(self):
        choosenTable = self.choosenTableForFactory.currentText()

    def insertDataIntoUsers(self):
        try:
            query = "INSERT INTO users (Login, Password, Roles_idRoles) values (%s, %s, %s)"
            login = self.LoginCreate.text()
            password = self.PasswordCreate.text()
            if self.UserRoleCreate.currentText() == "Оператор":
                role = 2
            elif self.UserRoleCreate.currentText() == "Администратор":
                role = 1
            elif self.UserRoleCreate.currentText() == "Разработчик модели":
                role = 3
            value = (login, password, role)
            usersDB = mc.connect(
                host="localhost",
                user="root",
                password="root",
                database="mydb"
            )
            mycursor = usersDB.cursor()
            mycursor.execute(query, value)
            usersDB.commit()                # Обязательно для записи
            msg = QMessageBox()
            msg.setWindowTitle("Успех")
            msg.setText("Выполнено")
            msg.setInformativeText("Учетная запись создана успешно")
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()

    def setupUi(self, AdminFom):
        AdminFom.setObjectName("AdminFom")
        AdminFom.resize(896, 620)
        self.centralwidget = QtWidgets.QWidget(AdminFom)
        self.centralwidget.setObjectName("centralwidget")
        self.Factory = QtWidgets.QTabWidget(self.centralwidget)
        self.Factory.setGeometry(QtCore.QRect(0, 0, 891, 541))
        self.Factory.setAutoFillBackground(False)
        self.Factory.setObjectName("Factory")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.tableWidgetFactory = QtWidgets.QTableWidget(self.tab_3)
        self.tableWidgetFactory.setGeometry(QtCore.QRect(10, 60, 531, 441))
        self.tableWidgetFactory.setObjectName("tableWidgetFactory")
        self.tableWidgetFactory.setColumnCount(0)
        self.tableWidgetFactory.setRowCount(0)
        self.groupBox = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox.setGeometry(QtCore.QRect(550, 50, 321, 451))
        self.groupBox.setObjectName("groupBox")
        self.saveData = QtWidgets.QPushButton(self.groupBox)
        self.saveData.setGeometry(QtCore.QRect(240, 420, 71, 21))
        self.saveData.setObjectName("saveData")
        self.choosenTableForFactory = QtWidgets.QComboBox(self.tab_3)
        self.choosenTableForFactory.setGeometry(QtCore.QRect(10, 30, 131, 21))
        self.choosenTableForFactory.setObjectName("choosenTableForFactory")
        self.tabelLabel_3 = QtWidgets.QLabel(self.tab_3)
        self.tabelLabel_3.setGeometry(QtCore.QRect(10, 10, 131, 18))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.tabelLabel_3.setFont(font)
        self.tabelLabel_3.setObjectName("tabelLabel_3")
        self.showTableForFactory = QtWidgets.QPushButton(self.tab_3)
        self.showTableForFactory.setGeometry(QtCore.QRect(150, 30, 75, 23))
        self.showTableForFactory.setObjectName("showTableForFactory")
        self.showTableForFactory.clicked.connect(self.showTableForFactoryClick)
        self.Factory.addTab(self.tab_3, "")
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_4)
        self.groupBox_2.setGeometry(QtCore.QRect(540, 60, 231, 141))
        self.groupBox_2.setObjectName("groupBox_2")
        self.AddUserButton = QtWidgets.QPushButton(self.groupBox_2)
        self.AddUserButton.setGeometry(QtCore.QRect(140, 110, 75, 23))
        self.AddUserButton.setObjectName("AddUserButton")
        self.AddUserButton.clicked.connect(self.insertDataIntoUsers)
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setGeometry(QtCore.QRect(20, 33, 47, 13))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setGeometry(QtCore.QRect(20, 57, 61, 16))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setGeometry(QtCore.QRect(20, 87, 61, 16))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.layoutWidget = QtWidgets.QWidget(self.groupBox_2)
        self.layoutWidget.setGeometry(QtCore.QRect(80, 30, 137, 76))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.LoginCreate = QtWidgets.QLineEdit(self.layoutWidget)
        self.LoginCreate.setObjectName("LoginCreate")
        self.verticalLayout.addWidget(self.LoginCreate)
        self.PasswordCreate = QtWidgets.QLineEdit(self.layoutWidget)
        self.PasswordCreate.setObjectName("PasswordCreate")
        self.verticalLayout.addWidget(self.PasswordCreate)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.UserRoleCreate = QtWidgets.QComboBox(self.layoutWidget)
        self.UserRoleCreate.setObjectName("UserRoleCreate")
        self.UserRoleCreate.addItem("")
        self.UserRoleCreate.addItem("")
        self.UserRoleCreate.addItem("")
        self.verticalLayout_2.addWidget(self.UserRoleCreate)
        self.tableWidgetUsers = QtWidgets.QTableWidget(self.tab_4)
        self.tableWidgetUsers.setGeometry(QtCore.QRect(10, 60, 521, 441))
        self.tableWidgetUsers.setObjectName("tableWidgetUsers")
        self.tableWidgetUsers.setColumnCount(0)
        self.tableWidgetUsers.setRowCount(0)
        self.choosenTableForUsers = QtWidgets.QComboBox(self.tab_4)
        self.choosenTableForUsers.setGeometry(QtCore.QRect(10, 30, 131, 21))
        self.choosenTableForUsers.setObjectName("choosenTableForUsers")
        self.choosenTableForUsers.addItem("")
        self.choosenTableForUsers.addItem("")
        self.tabelLabel_4 = QtWidgets.QLabel(self.tab_4)
        self.tabelLabel_4.setGeometry(QtCore.QRect(10, 10, 131, 18))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.tabelLabel_4.setFont(font)
        self.tabelLabel_4.setObjectName("tabelLabel_4")
        self.showTableForUsers = QtWidgets.QPushButton(self.tab_4)
        self.showTableForUsers.setGeometry(QtCore.QRect(150, 30, 75, 23))
        self.showTableForUsers.setObjectName("showTableForUsers")
        self.showTableForUsers.clicked.connect(self.showTableForUsersClick)
        self.Factory.addTab(self.tab_4, "")
        self.openOperatorForm_2 = QtWidgets.QPushButton(self.centralwidget)
        self.openOperatorForm_2.setGeometry(QtCore.QRect(10, 540, 181, 31))
        self.openOperatorForm_2.setObjectName("openOperatorForm_2")
        self.openOperatorForm_2.clicked.connect(self.openOperForm)
        self.openReserchForm_2 = QtWidgets.QPushButton(self.centralwidget)
        self.openReserchForm_2.setGeometry(QtCore.QRect(200, 540, 181, 31))
        self.openReserchForm_2.setObjectName("openReserchForm_2")
        AdminFom.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(AdminFom)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 896, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        AdminFom.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(AdminFom)
        self.statusbar.setObjectName("statusbar")
        AdminFom.setStatusBar(self.statusbar)
        self.action = QtWidgets.QAction(AdminFom)
        self.action.setObjectName("action")
        self.action_2 = QtWidgets.QAction(AdminFom)
        self.action_2.setObjectName("action_2")
        self.menu.addAction(self.action)
        self.menu_2.addAction(self.action_2)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.retranslateUi(AdminFom)
        self.Factory.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(AdminFom)

    def retranslateUi(self, AdminFom):
        _translate = QtCore.QCoreApplication.translate
        AdminFom.setWindowTitle(_translate("AdminFom", "MainWindow"))
        self.groupBox.setTitle(_translate("AdminFom", "Промышленные данные"))
        self.saveData.setText(_translate("AdminFom", "Сохранить"))
        self.tabelLabel_3.setText(_translate("AdminFom", "Таблица:"))
        self.showTableForFactory.setText(_translate("AdminFom", "Показать"))
        self.Factory.setTabText(self.Factory.indexOf(self.tab_3), _translate("AdminFom", "Промышленные данные"))
        self.groupBox_2.setTitle(_translate("AdminFom", "Добавление учетных записей"))
        self.AddUserButton.setText(_translate("AdminFom", "Добавить"))
        self.label.setText(_translate("AdminFom", "Логин:"))
        self.label_2.setText(_translate("AdminFom", "Пароль:"))
        self.label_3.setText(_translate("AdminFom", "Роль:"))
        self.UserRoleCreate.setCurrentText(_translate("AdminFom", "Оператор"))
        self.UserRoleCreate.setItemText(0, _translate("AdminFom", "Оператор"))
        self.UserRoleCreate.setItemText(1, _translate("AdminFom", "Администратор"))
        self.UserRoleCreate.setItemText(2, _translate("AdminFom", "Разработчик модели"))
        self.choosenTableForUsers.setCurrentText(_translate("AdminFom", "Пользователи"))
        self.choosenTableForUsers.setItemText(0, _translate("AdminFom", "Пользователи"))
        self.choosenTableForUsers.setItemText(1, _translate("AdminFom", "Роли"))
        self.tabelLabel_4.setText(_translate("AdminFom", "Таблица:"))
        self.showTableForUsers.setText(_translate("AdminFom", "Показать"))
        self.Factory.setTabText(self.Factory.indexOf(self.tab_4), _translate("AdminFom", "Пользователи"))
        self.openOperatorForm_2.setText(_translate("AdminFom", "Перейти в режим оператора"))
        self.openReserchForm_2.setText(_translate("AdminFom", "Перейти в режим исследователя"))
        self.menu.setTitle(_translate("AdminFom", "Файл"))
        self.menu_2.setTitle(_translate("AdminFom", "Справка"))
        self.action.setText(_translate("AdminFom", "Выход"))
        self.action_2.setText(_translate("AdminFom", "О программе"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    AdminFom = QtWidgets.QMainWindow()
    ui = Ui_AdminFom()
    ui.setupUi(AdminFom)
    AdminFom.show()
    sys.exit(app.exec_())
