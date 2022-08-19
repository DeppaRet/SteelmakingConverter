from PyQt5 import QtCore, QtGui, QtWidgets
import mysql.connector as mc
from PyQt5.QtWidgets import QMessageBox, QAction
from PyQt5.QtWidgets import QTableWidgetItem
import OperForm
import AboutForm
from SteelmakingConverter import hashAuth
from configparser import ConfigParser

DBhost = "localhost"
DBlogin = "root"
DBpass = "root"
parser = ConfigParser()
parser.read('dev.ini')

class Ui_AdminFom(object):

    def getSettings(self):
        global DBhost
        DBhost = (str(parser.get('DBsettings', 'DBhost')))
        global DBlogin
        DBlogin = (str(parser.get('DBsettings', 'login')))
        global DBpass
        DBpass = (str(parser.get('DBsettings', 'password')))

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
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="users_db"
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

            usersCount = self.tableWidgetUsers.rowCount()
            # if choosenTable == "Пользователи":
            #     for row in range(usersCount):
            #         self.tableWidgetUsers.setItem(row, 2, QTableWidgetItem(str("*********")))
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()


    def showTableForFactoryClick(self):
        try:
            chTable = self.choosenTableForFactory.currentText()
            query = "SELECT * FROM "
            if (chTable == "Режимы"):
                query += "Mode;"
                self.tableWidgetFactory.setColumnCount(5)
                self.tableWidgetFactory.setHorizontalHeaderLabels(
                    ["Номер", "Название", "Номер стали", "Номер лома", "Номер чугуна"])
            elif (chTable == "Сталь"):
                query += "SteelData;"
                self.tableWidgetFactory.setColumnCount(3)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Марка", "Номер состава"])
            elif (chTable == "Состав стали"):
                query += "SteelComposition;"
                self.tableWidgetFactory.setColumnCount(5)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Углерод", "Сера", "Фосфор", "Кремний"])
            elif (chTable == "Чугун"):
                query += "CastSteelData;"
                self.tableWidgetFactory.setColumnCount(4)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Масса", "Температура", "Номер состава"])
            elif (chTable == "Состав чугуна"):
                query += "CastSteelComposition;"
                self.tableWidgetFactory.setColumnCount(6)
                self.tableWidgetFactory.setHorizontalHeaderLabels(
                    ["Номер", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == "Лом"):
                query += "ScrapData;"
                self.tableWidgetFactory.setColumnCount(3)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Масса", "Номер состава"])
            elif (chTable == "Состав лома"):
                query += "ScrapComposition;"
                self.tableWidgetFactory.setColumnCount(6)
                self.tableWidgetFactory.setHorizontalHeaderLabels(
                    ["Номер", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == "Флюсы"):
                query += "FluxeData;"
                self.tableWidgetFactory.setColumnCount(3)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Название", "Номер состава"])
                # self.tableWidget.setHorizontalHeaderLabels(["Номер", "CaO", "SiO2", "MgO", "Fe2O3", "FeO", "MnO", "Al2O3", "CaCO3", "MgCO3"])

            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            self.tableWidgetFactory.setRowCount(0)

            for row_number, row_data in enumerate(result):
                self.tableWidgetFactory.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.tableWidgetFactory.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def insertDataIntoUsers(self):
        try:
            query = "INSERT INTO users (Login, Password, Roles_idRoles) values (%s, %s, %s)"
            login = self.LoginCreate.text()
            password = self.PasswordCreate.text()
            password = hashAuth.Hash.getHash(password)
            if self.UserRoleCreate.currentText() == "Оператор":
                role = 2
            elif self.UserRoleCreate.currentText() == "Администратор":
                role = 1
            elif self.UserRoleCreate.currentText() == "Разработчик модели":
                role = 3
            value = (login, password, role)
            usersDB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="users_db"
            )
            mycursor = usersDB.cursor()
            mycursor.execute(query, value)
            usersDB.commit()                # Обязательно для записи
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Успех")
            msg.setText("Внимание")
            msg.setInformativeText("Учетная запись успешно добавлена!")
            msg.exec_()
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()



    def getAllSteel(self):
        try:
            query = "select steelname from steeldata;"
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            for row_number, row_data in enumerate(result):
                for column_number, data in enumerate(row_data):
                    self.modeSteelName.addItem((str(data)))
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        finally:
            mycursor.close()
            DB.close()

    def getAllScrap(self):
        try:
            query = "select idScrapData from scrapdata;"
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            for row_number, row_data in enumerate(result):
                for column_number, data in enumerate(row_data):
                    self.modeScrap.addItem((str(data)))
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        finally:
            mycursor.close()
            DB.close()

    def getAllCast(self):
        try:
            query = "select idcaststeeldata from caststeeldata;"
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            for row_number, row_data in enumerate(result):
                for column_number, data in enumerate(row_data):
                    self.modeCastSteel.addItem((str(data)))
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        finally:
            mycursor.close()
            DB.close()

    def getFluxes(self):
        try:
            query = "select FluxeName from fluxedata;"
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            for row_number, row_data in enumerate(result):
                for column_number, data in enumerate(row_data):
                    self.FluxeType.addItem((str(data)))
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        finally:
            mycursor.close()
            DB.close()

    def AddFluxeButtonClicked(self):
        try:
            rows = self.FluxeTable.rowCount()
            text = self.FluxeType.currentText()
            self.FluxeTable.insertRow(rows)
            self.FluxeTable.setItem(rows, 0, QTableWidgetItem(text))
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def removeFluxeButtonClicked(self):
        rows = self.FluxeTable.rowCount()
        self.FluxeTable.setRowCount(0)

    def addCastData(self):
        try:
            query = "INSERT INTO CastSteelComposition (CastSteelCarbon, CastSteelSerum, CastSteelPhosphor, CastSteelSilicon, CastSteelManganese) values (%s, %s, %s, %s, %s)"
            castCarbon = self.castCarbon.text()
            castSerum = self.castSerum.text()
            castPhosphor = self.castPhosphor.text()
            castSilicon = self.castSilicon.text()
            castMang = self.castManganese.text()
            value = (castCarbon, castSerum, castPhosphor, castSilicon, castMang)

            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )

            mycursor = DB.cursor()
            mycursor.execute(query, value)
            DB.commit()                # Обязательно для записи
            mycursor.close()

            tmp = "CastSteelCarbon = " + castCarbon + " AND CastSteelSerum = " + castSerum + " AND CastSteelPhosphor = " + castPhosphor + " AND CastSteelSilicon = " + castSilicon + " AND CastSteelManganese = " + castMang
            query = "select idCastSteelComposition from caststeelcomposition where (" + tmp + ") ORDER BY CastSteelCarbon ASC LIMIT 1;"
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchone()[0]
            mycursor.close()


            query = "insert into caststeeldata (CastSteelWeight, CastSteelTemperature, CastSteelComposition_idCastSteelComposition) values (%s, %s, %s);"
            value = (self.castWeight.text(), self.castTemperature.text(), result)
            mycursor = DB.cursor()
            mycursor.execute(query, value)
            DB.commit()
            self.getAllCast()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Успех")
            msg.setText("Внимание")
            msg.setInformativeText("Запись успешно добавлена!")
            msg.exec_()
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()

    def addScrap(self):
        try:
            query = "insert into scrapcomposition (ScrapCarbon, ScrapSerum, ScrapPhosphor, ScrapSilicon, ScrapManganese) values (%s, %s, %s, %s, %s)"
            scrapCarbon = self.scrapCarbon.text()
            scrapSerum = self.scrapSerum.text()
            scrapPhosphor = self.scrapPhosphor.text()
            scrapSilicon = self.scrapSilicon.text()
            scrapMang = self.scrapManganese.text()
            value = (scrapCarbon, scrapSerum, scrapPhosphor, scrapSilicon, scrapMang)
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            mycursor = DB.cursor()
            mycursor.execute(query, value)
            DB.commit()                # Обязательно для записи
            mycursor.close()

            tmp = "ScrapCarbon = " + scrapCarbon + " AND ScrapSerum = " + scrapSerum + " AND ScrapPhosphor = " + scrapPhosphor + " AND ScrapSilicon = " + scrapSilicon + " AND ScrapManganese = " + scrapMang
            query = "select idScrapComposition from scrapcomposition where (" + tmp + ") ORDER BY ScrapCarbon ASC LIMIT 1;"
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchone()[0]
            mycursor.close()

            query = "insert into scrapdata (ScrapWeight, ScrapComposition_idScrapComposition) values(%s, %s)"
            value = (self.scrapWeight.text(), result)
            mycursor = DB.cursor()
            mycursor.execute(query, value)
            DB.commit()
            DB.close()

            self.getAllScrap()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Успех")
            msg.setText("Внимание")
            msg.setInformativeText("Запись успешно добавлена!")
            msg.exec_()
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()

    def addMode(self):
        try:
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            query = "select idsteeldata from steeldata where steelname = '" + self.modeSteelName.currentText() + "'"
            mycursor = DB.cursor()
            mycursor.execute(query)
            idSteel = mycursor.fetchone()[0]
            mycursor.close()

            query = "insert into mode (ModeName, SteelData_idSteelData, ScrapData_idScrapData, CastSteelData_idCastSteelData) values(%s, %s, %s, %s)"

            values = (self.modeName.text(), idSteel, self.modeScrap.currentText(), self.modeCastSteel.currentText())

            mycursor = DB.cursor()
            mycursor.execute(query, values)
            DB.commit()  # Обязательно для записи
            mycursor.close()

            if(self.FluxeTable.rowCount() != 0):
                query = "select idMode from mode where ModeName = '" + self.modeName.text() + "'"
                mycursor = DB.cursor()
                mycursor.execute(query)
                idMode = mycursor.fetchone()[0]
                mycursor.close()
                fluxesRowCount = self.FluxeTable.rowCount()
                for row in range(fluxesRowCount):
                    name = self.FluxeTable.item(row, 0).text()
                    query = "select idFluxeData from FluxeData where FluxeName = '" + name + "'"
                    mycursor = DB.cursor()
                    mycursor.execute(query)
                    idFluxe = mycursor.fetchone()[0]
                    mycursor.close()

                    query = "insert into fluxedata_has_mode (FluxeData_idFluxeData, Mode_idMode) values (%s, %s)"
                    values = (idFluxe, idMode)
                    mycursor = DB.cursor()
                    mycursor.execute(query, values)
                    DB.commit()  # Обязательно для записи
                    mycursor.close()
            DB.close()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Успех")
            msg.setText("Внимание")
            msg.setInformativeText("Режим успешно добавлен!")
            msg.exec_()
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()
        finally:
            mycursor.close()
            DB.close()

    def addFluxeDataButtonClicked(self):
        try:
            query = "insert into fluxecomposition (CaO, SiO2, MgO, Fe2O3, FeO, MnO, Al2O3, CaCO3, MgCO3) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            CaO = float(self.fluxeCaO.text())
            SiO2 = float(self.fluxeSiO2.text())
            MgO = float(self.fluxeMgO.text())
            Fe2O3 = float(self.fluxeFe2O3.text())
            FeO = float(self.fluxeFeO.text())
            MnO = float(self.fluxeMnO.text())
            Al2O3 = float(self.fluxeAl2O3.text())
            CaCO3 = float(self.fluxeCaCO3.text())
            MgCO3 = float(self.fluxeMgCO3.text())
            value = (CaO, SiO2, MgO, Fe2O3, FeO, MnO, Al2O3, CaCO3, MgCO3)
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )

            mycursor = DB.cursor()
            mycursor.execute(query, value)
            DB.commit()  # Обязательно для записи
            mycursor.close()

            tmp = "CaO = " + str(CaO) + " AND SiO2 = " + str(SiO2) + " AND MgO = " + str(MgO) + " AND Fe2O3 = " + str(Fe2O3) + " AND FeO = " + str(FeO) + " AND MnO = " + str(MnO) + " AND Al2O3 = " + str(Al2O3) + " AND CaCO3 = " + str(CaCO3) + " AND MgCO3 = " + str(MgCO3)
            query = "select idFluxeComposition from fluxecomposition where (" + tmp + ") ORDER BY CaO ASC LIMIT 1;"
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchone()[0]
            mycursor.close()

            query = "insert into fluxedata (FluxeName, FluxeComposition_idFluxeComposition) values(%s, %s)"
            value = (self.fluxeName.text(), result)
            mycursor = DB.cursor()
            mycursor.execute(query, value)
            DB.commit()
            DB.close()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Успех")
            msg.setText("Внимание")
            msg.setInformativeText("Запись успешно добавлена!")
            msg.exec_()

        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()
        # finally:
        #     mycursor.close()
        #     DB.close()

    def getAllUsersId(self):
        query = "select idusers from users"
        usersDB = mc.connect(
            host=DBhost,  # host="192.168.51.179" user="root", password="root",
            user=DBlogin,
            password=DBpass,
            database="users_db"
        )
        mycursor = usersDB.cursor()
        mycursor.execute(query)
        users = mycursor.fetchall()
        for row_number, row_data in enumerate(users):
            for column_number, data in enumerate(row_data):
                self.UserIdUpdate.addItem((str(data)))

        o = 0

    def UpdateUser(self):
        try:
            if self.UserRoleUpdate.currentText() == "Оператор":
                role = 2
            elif self.UserRoleUpdate.currentText() == "Администратор":
                role = 1
            elif self.UserRoleUpdate.currentText() == "Разработчик модели":
                role = 3
            login = str(self.LoginUpdate.text())
            query = "update users set login = '" + login + "', Roles_idRoles = " + str(role) + " where idusers = " + str(self.UserIdUpdate.currentText())
            usersDB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="users_db"
            )
            mycursor = usersDB.cursor()
            mycursor.execute(query)
            usersDB.commit()  # Обязательно для записи
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Успех")
            msg.setText("Внимание")
            msg.setInformativeText("Запись изменена")
            msg.exec_()

        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()


    def executeSqlQuery(self):
        try:
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            query = self.SQLQuery.text()
            lowQuery = query.lower()
            if "drop" in lowQuery:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("В доступе отказано")
                msg.setText("Внимание")
                msg.setInformativeText("Вы не можете удалить таблицу.")
                msg.exec_()
                DB.close()
                return
            elif "delete" in lowQuery:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("В доступе отказано")
                msg.setText("Внимание")
                msg.setInformativeText("Вы не можете удалить запись.")
                msg.exec_()
                DB.close()
                return
            else:
                mycursor = DB.cursor()
                mycursor.execute(query)
                DB.commit()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Успех")
                msg.setText("Внимание")
                msg.setInformativeText("Запрос выполнен.")
                msg.exec_()
                DB.close()
                return
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()

    def openAbout(self):
        self.window = QtWidgets.QDialog()
        self.ui = AboutForm.Ui_Dialog()
        self.ui.setupUi(self.window)
        self.window.show()

    def setupUi(self, AdminFom):
        AdminFom.setObjectName("AdminFom")
        AdminFom.resize(798, 620)
        winIcon = QtGui.QIcon()
        winIcon.addPixmap(QtGui.QPixmap("SteelmakingConverter/Pictures/steel_ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        AdminFom.setWindowIcon(winIcon)
        self.centralwidget = QtWidgets.QWidget(AdminFom)
        self.centralwidget.setObjectName("centralwidget")
        self.Factory = QtWidgets.QTabWidget(self.centralwidget)
        self.Factory.setGeometry(QtCore.QRect(0, 0, 791, 581))
        self.Factory.setAutoFillBackground(False)
        self.Factory.setObjectName("Factory")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.groupBox = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox.setGeometry(QtCore.QRect(450, 10, 331, 541))
        self.groupBox.setObjectName("groupBox")
        self.groupBox_3 = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 170, 301, 161))
        self.groupBox_3.setObjectName("groupBox_3")
        self.addScrapDataButton = QtWidgets.QPushButton(self.groupBox_3)
        self.addScrapDataButton.setGeometry(QtCore.QRect(210, 20, 81, 23))
        self.addScrapDataButton.setObjectName("addScrapDataButton")
        self.addScrapDataButton.clicked.connect(self.addScrap)
        self.label_11 = QtWidgets.QLabel(self.groupBox_3)
        self.label_11.setGeometry(QtCore.QRect(10, 20, 101, 16))
        self.label_11.setObjectName("label_11")
        self.scrapWeight = QtWidgets.QLineEdit(self.groupBox_3)
        self.scrapWeight.setGeometry(QtCore.QRect(70, 20, 81, 20))
        self.scrapWeight.setText("")
        self.scrapWeight.setObjectName("scrapWeight")
        self.groupBox_7 = QtWidgets.QGroupBox(self.groupBox_3)
        self.groupBox_7.setGeometry(QtCore.QRect(10, 40, 281, 111))
        self.groupBox_7.setObjectName("groupBox_7")
        self.label_12 = QtWidgets.QLabel(self.groupBox_7)
        self.label_12.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_12.setObjectName("label_12")
        self.label_13 = QtWidgets.QLabel(self.groupBox_7)
        self.label_13.setGeometry(QtCore.QRect(10, 50, 71, 16))
        self.label_13.setObjectName("label_13")
        self.label_14 = QtWidgets.QLabel(self.groupBox_7)
        self.label_14.setGeometry(QtCore.QRect(150, 20, 51, 16))
        self.label_14.setObjectName("label_14")
        self.label_15 = QtWidgets.QLabel(self.groupBox_7)
        self.label_15.setGeometry(QtCore.QRect(150, 50, 61, 16))
        self.label_15.setObjectName("label_15")
        self.scrapCarbon = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapCarbon.setGeometry(QtCore.QRect(80, 20, 51, 20))
        self.scrapCarbon.setObjectName("scrapCarbon")
        self.scrapSilicon = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapSilicon.setGeometry(QtCore.QRect(80, 50, 51, 20))
        self.scrapSilicon.setObjectName("scrapSilicon")
        self.scrapSerum = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapSerum.setGeometry(QtCore.QRect(220, 20, 51, 20))
        self.scrapSerum.setObjectName("scrapSerum")
        self.scrapPhosphor = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapPhosphor.setGeometry(QtCore.QRect(220, 50, 51, 20))
        self.scrapPhosphor.setObjectName("scrapPhosphor")
        self.label_25 = QtWidgets.QLabel(self.groupBox_7)
        self.label_25.setGeometry(QtCore.QRect(130, 80, 81, 16))
        self.label_25.setObjectName("label_25")
        self.scrapManganese = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapManganese.setEnabled(True)
        self.scrapManganese.setGeometry(QtCore.QRect(220, 80, 51, 20))
        self.scrapManganese.setText("")
        self.scrapManganese.setObjectName("scrapManganese")
        self.groupBox_4 = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_4.setGeometry(QtCore.QRect(10, 340, 301, 191))
        self.groupBox_4.setObjectName("groupBox_4")
        self.castTemperature = QtWidgets.QLineEdit(self.groupBox_4)
        self.castTemperature.setGeometry(QtCore.QRect(110, 20, 81, 20))
        self.castTemperature.setText("")
        self.castTemperature.setObjectName("castTemperature")
        self.label_10 = QtWidgets.QLabel(self.groupBox_4)
        self.label_10.setGeometry(QtCore.QRect(10, 20, 101, 16))
        self.label_10.setObjectName("label_10")
        self.label_16 = QtWidgets.QLabel(self.groupBox_4)
        self.label_16.setGeometry(QtCore.QRect(10, 50, 101, 16))
        self.label_16.setObjectName("label_16")
        self.castWeight = QtWidgets.QLineEdit(self.groupBox_4)
        self.castWeight.setGeometry(QtCore.QRect(110, 50, 81, 20))
        self.castWeight.setText("")
        self.castWeight.setObjectName("castWeight")
        self.groupBox_6 = QtWidgets.QGroupBox(self.groupBox_4)
        self.groupBox_6.setGeometry(QtCore.QRect(10, 70, 281, 111))
        self.groupBox_6.setObjectName("groupBox_6")
        self.label_17 = QtWidgets.QLabel(self.groupBox_6)
        self.label_17.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_17.setObjectName("label_17")
        self.label_18 = QtWidgets.QLabel(self.groupBox_6)
        self.label_18.setGeometry(QtCore.QRect(10, 50, 71, 16))
        self.label_18.setObjectName("label_18")
        self.label_19 = QtWidgets.QLabel(self.groupBox_6)
        self.label_19.setGeometry(QtCore.QRect(150, 20, 51, 16))
        self.label_19.setObjectName("label_19")
        self.label_20 = QtWidgets.QLabel(self.groupBox_6)
        self.label_20.setGeometry(QtCore.QRect(150, 50, 61, 16))
        self.label_20.setObjectName("label_20")
        self.castCarbon = QtWidgets.QLineEdit(self.groupBox_6)
        self.castCarbon.setGeometry(QtCore.QRect(80, 20, 51, 20))
        self.castCarbon.setObjectName("castCarbon")
        self.castSilicon = QtWidgets.QLineEdit(self.groupBox_6)
        self.castSilicon.setGeometry(QtCore.QRect(80, 50, 51, 20))
        self.castSilicon.setObjectName("castSilicon")
        self.castSerum = QtWidgets.QLineEdit(self.groupBox_6)
        self.castSerum.setGeometry(QtCore.QRect(220, 20, 51, 20))
        self.castSerum.setObjectName("castSerum")
        self.castPhosphor = QtWidgets.QLineEdit(self.groupBox_6)
        self.castPhosphor.setGeometry(QtCore.QRect(220, 50, 51, 20))
        self.castPhosphor.setObjectName("castPhosphor")
        self.castManganese = QtWidgets.QLineEdit(self.groupBox_6)
        self.castManganese.setEnabled(True)
        self.castManganese.setGeometry(QtCore.QRect(220, 80, 51, 20))
        self.castManganese.setText("")
        self.castManganese.setObjectName("castManganese")
        self.label_24 = QtWidgets.QLabel(self.groupBox_6)
        self.label_24.setGeometry(QtCore.QRect(130, 80, 81, 16))
        self.label_24.setObjectName("label_24")
        self.addCastButton = QtWidgets.QPushButton(self.groupBox_4)
        self.addCastButton.setGeometry(QtCore.QRect(200, 30, 81, 23))
        self.addCastButton.setObjectName("addCastButton")
        self.addCastButton.clicked.connect(self.addCastData)
        self.groupBox_5 = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_5.setGeometry(QtCore.QRect(10, 20, 301, 151))
        self.groupBox_5.setObjectName("groupBox_5")
        self.groupBox_8 = QtWidgets.QGroupBox(self.groupBox_5)
        self.groupBox_8.setGeometry(QtCore.QRect(10, 60, 281, 81))
        self.groupBox_8.setObjectName("groupBox_8")
        self.label_4 = QtWidgets.QLabel(self.groupBox_8)
        self.label_4.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.groupBox_8)
        self.label_5.setGeometry(QtCore.QRect(10, 50, 71, 16))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.groupBox_8)
        self.label_6.setGeometry(QtCore.QRect(150, 20, 51, 16))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.groupBox_8)
        self.label_7.setGeometry(QtCore.QRect(150, 50, 61, 16))
        self.label_7.setObjectName("label_7")
        self.steelCarbon = QtWidgets.QLineEdit(self.groupBox_8)
        self.steelCarbon.setGeometry(QtCore.QRect(80, 20, 51, 20))
        self.steelCarbon.setObjectName("steelCarbon")
        self.steelSilicon = QtWidgets.QLineEdit(self.groupBox_8)
        self.steelSilicon.setGeometry(QtCore.QRect(80, 50, 51, 20))
        self.steelSilicon.setObjectName("steelSilicon")
        self.steelSerum = QtWidgets.QLineEdit(self.groupBox_8)
        self.steelSerum.setGeometry(QtCore.QRect(220, 20, 51, 20))
        self.steelSerum.setObjectName("steelSerum")
        self.steelPhosphor = QtWidgets.QLineEdit(self.groupBox_8)
        self.steelPhosphor.setGeometry(QtCore.QRect(220, 50, 51, 20))
        self.steelPhosphor.setObjectName("steelPhosphor")
        self.label_21 = QtWidgets.QLabel(self.groupBox_5)
        self.label_21.setGeometry(QtCore.QRect(10, 30, 101, 16))
        self.label_21.setObjectName("label_21")
        self.steelName = QtWidgets.QLineEdit(self.groupBox_5)
        self.steelName.setGeometry(QtCore.QRect(70, 30, 81, 20))
        self.steelName.setText("")
        self.steelName.setObjectName("steelName")
        self.addSteelDataButton = QtWidgets.QPushButton(self.groupBox_5)
        self.addSteelDataButton.setGeometry(QtCore.QRect(210, 30, 81, 23))
        self.addSteelDataButton.setObjectName("addSteelDataButton")
        self.tabelLabel_3 = QtWidgets.QLabel(self.tab_3)
        self.tabelLabel_3.setGeometry(QtCore.QRect(10, 10, 131, 18))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.tabelLabel_3.setFont(font)
        self.tabelLabel_3.setObjectName("tabelLabel_3")
        self.showTableForFactory = QtWidgets.QPushButton(self.tab_3)
        self.showTableForFactory.setGeometry(QtCore.QRect(160, 30, 75, 23))
        self.showTableForFactory.setObjectName("showTableForFactory")
        self.showTableForFactory.clicked.connect(self.showTableForFactoryClick)
        self.tableWidgetFactory = QtWidgets.QTableWidget(self.tab_3)
        self.tableWidgetFactory.setGeometry(QtCore.QRect(10, 60, 431, 211))
        self.tableWidgetFactory.setObjectName("tableWidgetFactory")
        self.tableWidgetFactory.setColumnCount(0)
        self.tableWidgetFactory.setRowCount(0)
        self.choosenTableForFactory = QtWidgets.QComboBox(self.tab_3)
        self.choosenTableForFactory.setGeometry(QtCore.QRect(10, 30, 141, 22))
        self.choosenTableForFactory.setObjectName("choosenTableForFactory")
        self.choosenTableForFactory.addItem("")
        self.choosenTableForFactory.addItem("")
        self.choosenTableForFactory.addItem("")
        self.choosenTableForFactory.addItem("")
        self.choosenTableForFactory.addItem("")
        self.choosenTableForFactory.addItem("")
        self.choosenTableForFactory.addItem("")
        self.choosenTableForFactory.addItem("")
        self.groupBox_9 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_9.setGeometry(QtCore.QRect(10, 430, 431, 121))
        self.groupBox_9.setObjectName("groupBox_9")
        self.label_8 = QtWidgets.QLabel(self.groupBox_9)
        self.label_8.setGeometry(QtCore.QRect(20, 50, 31, 16))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(self.groupBox_9)
        self.label_9.setGeometry(QtCore.QRect(20, 70, 71, 16))
        self.label_9.setObjectName("label_9")
        self.label_22 = QtWidgets.QLabel(self.groupBox_9)
        self.label_22.setGeometry(QtCore.QRect(120, 50, 31, 16))
        self.label_22.setObjectName("label_22")
        self.fluxeFe2O3label = QtWidgets.QLabel(self.groupBox_9)
        self.fluxeFe2O3label.setGeometry(QtCore.QRect(120, 70, 61, 16))
        self.fluxeFe2O3label.setObjectName("fluxeFe2O3label")
        self.fluxeCaO = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeCaO.setGeometry(QtCore.QRect(50, 50, 51, 20))
        self.fluxeCaO.setObjectName("fluxeCaO")
        self.fluxeSiO2 = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeSiO2.setGeometry(QtCore.QRect(50, 70, 51, 20))
        self.fluxeSiO2.setObjectName("fluxeSiO2")
        self.fluxeMgO = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeMgO.setGeometry(QtCore.QRect(160, 50, 51, 20))
        self.fluxeMgO.setObjectName("fluxeMgO")
        self.fluxeFe2O3 = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeFe2O3.setGeometry(QtCore.QRect(160, 70, 51, 20))
        self.fluxeFe2O3.setObjectName("fluxeFe2O3")
        self.label_30 = QtWidgets.QLabel(self.groupBox_9)
        self.label_30.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_30.setObjectName("label_30")
        self.fluxeName = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeName.setGeometry(QtCore.QRect(80, 20, 111, 20))
        self.fluxeName.setObjectName("fluxeName")
        self.label_31 = QtWidgets.QLabel(self.groupBox_9)
        self.label_31.setGeometry(QtCore.QRect(230, 50, 31, 16))
        self.label_31.setObjectName("label_31")
        self.fluxeFeO = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeFeO.setGeometry(QtCore.QRect(260, 50, 51, 20))
        self.fluxeFeO.setObjectName("fluxeFeO")
        self.label_32 = QtWidgets.QLabel(self.groupBox_9)
        self.label_32.setGeometry(QtCore.QRect(230, 70, 31, 16))
        self.label_32.setObjectName("label_32")
        self.fluxeMnO = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeMnO.setGeometry(QtCore.QRect(260, 70, 51, 20))
        self.fluxeMnO.setObjectName("fluxeMnO")
        self.label_33 = QtWidgets.QLabel(self.groupBox_9)
        self.label_33.setGeometry(QtCore.QRect(330, 50, 41, 16))
        self.label_33.setObjectName("label_33")
        self.fluxeAl2O3 = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeAl2O3.setGeometry(QtCore.QRect(370, 50, 51, 20))
        self.fluxeAl2O3.setObjectName("fluxeAl2O3")
        self.label_34 = QtWidgets.QLabel(self.groupBox_9)
        self.label_34.setGeometry(QtCore.QRect(330, 70, 41, 16))
        self.label_34.setObjectName("label_34")
        self.fluxeCaCO3 = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeCaCO3.setGeometry(QtCore.QRect(370, 70, 51, 20))
        self.fluxeCaCO3.setObjectName("fluxeCaCO3")
        self.label_35 = QtWidgets.QLabel(self.groupBox_9)
        self.label_35.setGeometry(QtCore.QRect(330, 90, 41, 16))
        self.label_35.setObjectName("label_35")
        self.fluxeMgCO3 = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeMgCO3.setGeometry(QtCore.QRect(370, 90, 51, 20))
        self.fluxeMgCO3.setObjectName("fluxeMgCO3")
        self.addFluxeDataButton = QtWidgets.QPushButton(self.groupBox_9)
        self.addFluxeDataButton.setGeometry(QtCore.QRect(340, 10, 81, 23))
        self.addFluxeDataButton.setObjectName("addFluxeDataButton")
        self.addFluxeDataButton.clicked.connect(self.addFluxeDataButtonClicked)
        self.groupBox_10 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_10.setGeometry(QtCore.QRect(10, 280, 261, 141))
        self.groupBox_10.setObjectName("groupBox_10")
        self.label_23 = QtWidgets.QLabel(self.groupBox_10)
        self.label_23.setGeometry(QtCore.QRect(140, 20, 41, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_23.setFont(font)
        self.label_23.setObjectName("label_23")
        self.modeSteelName = QtWidgets.QComboBox(self.groupBox_10)
        self.modeSteelName.setGeometry(QtCore.QRect(180, 20, 61, 22))
        self.modeSteelName.setObjectName("modeSteelName")
        self.addModeButton = QtWidgets.QPushButton(self.groupBox_10)
        self.addModeButton.setGeometry(QtCore.QRect(170, 110, 71, 23))
        self.addModeButton.setObjectName("addModeButton")
        self.addModeButton.clicked.connect(self.addMode)
        self.modeCastSteel = QtWidgets.QComboBox(self.groupBox_10)
        self.modeCastSteel.setGeometry(QtCore.QRect(70, 50, 61, 22))
        self.modeCastSteel.setObjectName("modeCastSteel")
        self.label_26 = QtWidgets.QLabel(self.groupBox_10)
        self.label_26.setGeometry(QtCore.QRect(10, 50, 51, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_26.setFont(font)
        self.label_26.setObjectName("label_26")
        self.modeScrap = QtWidgets.QComboBox(self.groupBox_10)
        self.modeScrap.setGeometry(QtCore.QRect(180, 50, 61, 22))
        self.modeScrap.setObjectName("modeScrap")
        self.label_27 = QtWidgets.QLabel(self.groupBox_10)
        self.label_27.setGeometry(QtCore.QRect(150, 50, 31, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_27.setFont(font)
        self.label_27.setObjectName("label_27")
        self.modeName = QtWidgets.QLineEdit(self.groupBox_10)
        self.modeName.setGeometry(QtCore.QRect(70, 20, 61, 20))
        self.modeName.setObjectName("modeName")
        self.label_28 = QtWidgets.QLabel(self.groupBox_10)
        self.label_28.setGeometry(QtCore.QRect(10, 20, 52, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_28.setFont(font)
        self.label_28.setObjectName("label_28")
        self.groupBox_11 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_11.setGeometry(QtCore.QRect(280, 280, 161, 141))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_11.setFont(font)
        self.groupBox_11.setFlat(False)
        self.groupBox_11.setCheckable(False)
        self.groupBox_11.setObjectName("groupBox_11")
        self.FluxeTable = QtWidgets.QTableWidget(self.groupBox_11)
        self.FluxeTable.setGeometry(QtCore.QRect(10, 70, 101, 61))
        self.FluxeTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.FluxeTable.setObjectName("FluxeTable")
        self.FluxeTable.setColumnCount(1)
        self.FluxeTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.FluxeTable.setHorizontalHeaderItem(0, item)
        self.AddFluxeButton = QtWidgets.QPushButton(self.groupBox_11)
        self.AddFluxeButton.setGeometry(QtCore.QRect(120, 70, 31, 21))
        self.AddFluxeButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/add.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.AddFluxeButton.setIcon(icon)
        self.AddFluxeButton.setObjectName("AddFluxeButton")
        self.AddFluxeButton.clicked.connect(self.AddFluxeButtonClicked)
        self.FluxeType = QtWidgets.QComboBox(self.groupBox_11)
        self.FluxeType.setGeometry(QtCore.QRect(10, 40, 141, 22))
        self.FluxeType.setEditable(False)
        self.FluxeType.setObjectName("FluxeType")
        self.RemoveFluxeButton = QtWidgets.QPushButton(self.groupBox_11)
        self.RemoveFluxeButton.setGeometry(QtCore.QRect(120, 110, 31, 21))
        self.RemoveFluxeButton.setText("")
        self.RemoveFluxeButton.clicked.connect(self.removeFluxeButtonClicked)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/remove.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RemoveFluxeButton.setIcon(icon1)
        self.RemoveFluxeButton.setObjectName("RemoveFluxeButton")
        self.tip_flyusa_label = QtWidgets.QLabel(self.groupBox_11)
        self.tip_flyusa_label.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.tip_flyusa_label.setObjectName("tip_flyusa_label")
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
        self.tableWidgetUsers = QtWidgets.QTableWidget(self.tab_4)
        self.tableWidgetUsers.setGeometry(QtCore.QRect(10, 60, 521, 481))
        self.tableWidgetUsers.setObjectName("tableWidgetUsers")
        self.tableWidgetUsers.setColumnCount(0)
        self.tableWidgetUsers.setRowCount(0)
        self.groupBox_12 = QtWidgets.QGroupBox(self.tab_4)
        self.groupBox_12.setGeometry(QtCore.QRect(540, 210, 231, 141))
        self.groupBox_12.setObjectName("groupBox_12")
        self.UpdateUserButton = QtWidgets.QPushButton(self.groupBox_12)
        self.UpdateUserButton.setGeometry(QtCore.QRect(140, 110, 75, 23))
        self.UpdateUserButton.setObjectName("UpdateUserButton")
        self.UpdateUserButton.clicked.connect(self.UpdateUser)
        self.label_29 = QtWidgets.QLabel(self.groupBox_12)
        self.label_29.setGeometry(QtCore.QRect(20, 33, 51, 16))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.label_29.setFont(font)
        self.label_29.setObjectName("label_29")
        self.label_36 = QtWidgets.QLabel(self.groupBox_12)
        self.label_36.setGeometry(QtCore.QRect(20, 57, 61, 16))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.label_36.setFont(font)
        self.label_36.setObjectName("label_36")
        self.label_37 = QtWidgets.QLabel(self.groupBox_12)
        self.label_37.setGeometry(QtCore.QRect(20, 87, 61, 20))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.label_37.setFont(font)
        self.label_37.setObjectName("label_37")
        self.layoutWidget_2 = QtWidgets.QWidget(self.groupBox_12)
        self.layoutWidget_2.setGeometry(QtCore.QRect(80, 30, 137, 76))
        self.layoutWidget_2.setObjectName("layoutWidget_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.layoutWidget_2)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.UserIdUpdate = QtWidgets.QComboBox(self.layoutWidget_2)
        self.UserIdUpdate.setCurrentText("")
        self.UserIdUpdate.setObjectName("UserIdUpdate")
        self.verticalLayout_4.addWidget(self.UserIdUpdate)
        self.LoginUpdate = QtWidgets.QLineEdit(self.layoutWidget_2)
        self.LoginUpdate.setObjectName("LoginUpdate")
        self.verticalLayout_4.addWidget(self.LoginUpdate)
        self.verticalLayout_3.addLayout(self.verticalLayout_4)
        self.UserRoleUpdate = QtWidgets.QComboBox(self.layoutWidget_2)
        self.UserRoleUpdate.setObjectName("UserRoleUpdate")
        self.UserRoleUpdate.addItem("")
        self.UserRoleUpdate.addItem("")
        self.UserRoleUpdate.addItem("")
        self.verticalLayout_3.addWidget(self.UserRoleUpdate)
        self.SQLQuery = QtWidgets.QLineEdit(self.tab_4)
        self.SQLQuery.setGeometry(QtCore.QRect(540, 520, 161, 21))
        self.SQLQuery.setObjectName("SQLQuery")
        self.executeSqlbutton = QtWidgets.QPushButton(self.tab_4)
        self.executeSqlbutton.setGeometry(QtCore.QRect(710, 520, 71, 23))
        self.executeSqlbutton.setObjectName("executeSqlbutton")
        self.executeSqlbutton.clicked.connect(self.executeSqlQuery)
        self.Factory.addTab(self.tab_4, "")
        AdminFom.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(AdminFom)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 798, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        AdminFom.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(AdminFom)
        self.statusbar.setObjectName("statusbar")
        AdminFom.setStatusBar(self.statusbar)
        self.exit = QtWidgets.QAction(AdminFom)
        self.exit.setObjectName("exit")
        self.about = QtWidgets.QAction(AdminFom)
        self.about.setObjectName("about")

        self.exit.setShortcut('Ctrl+Q')
        self.exit.triggered.connect(lambda: self.app.Quit)

        self.about.triggered.connect(self.openAbout)

        self.menu.addAction(self.exit)
        self.menu_2.addAction(self.about)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())



        self.retranslateUi(AdminFom)
        self.Factory.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(AdminFom)

    def retranslateUi(self, AdminFom):
        _translate = QtCore.QCoreApplication.translate
        AdminFom.setWindowTitle(_translate("AdminFom", "Добро пожаловать, администратор"))
        self.groupBox.setTitle(_translate("AdminFom", "Промышленные данные"))
        self.groupBox_3.setTitle(_translate("AdminFom", "Добавление данных о ломе"))
        self.addScrapDataButton.setText(_translate("AdminFom", "Добавить"))
        self.label_11.setText(_translate("AdminFom", "Масса (Т):"))
        self.groupBox_7.setTitle(_translate("AdminFom", "Химический состав"))
        self.label_12.setText(_translate("AdminFom", "Углерод (C):"))
        self.label_13.setText(_translate("AdminFom", "Кремний (Si):"))
        self.label_14.setText(_translate("AdminFom", "Сера (S):"))
        self.label_15.setText(_translate("AdminFom", "Фосфор (P):"))
        self.label_25.setText(_translate("AdminFom", "Марганец (Mn):"))
        self.groupBox_4.setTitle(_translate("AdminFom", "Добавление данных о чугуне"))
        self.label_10.setText(_translate("AdminFom", "Температура (℃):"))
        self.label_16.setText(_translate("AdminFom", "Масса (Т):"))
        self.groupBox_6.setTitle(_translate("AdminFom", "Химический состав"))
        self.label_17.setText(_translate("AdminFom", "Углерод (C):"))
        self.label_18.setText(_translate("AdminFom", "Кремний (Si):"))
        self.label_19.setText(_translate("AdminFom", "Сера (S):"))
        self.label_20.setText(_translate("AdminFom", "Фосфор (P):"))
        self.label_24.setText(_translate("AdminFom", "Марганец (Mn):"))
        self.addCastButton.setText(_translate("AdminFom", "Добавить"))
        self.groupBox_5.setTitle(_translate("AdminFom", "Добавление данных о стали"))
        self.groupBox_8.setTitle(_translate("AdminFom", "Химический состав"))
        self.label_4.setText(_translate("AdminFom", "Углерод (C):"))
        self.label_5.setText(_translate("AdminFom", "Кремний (Si):"))
        self.label_6.setText(_translate("AdminFom", "Сера (S):"))
        self.label_7.setText(_translate("AdminFom", "Фосфор (P):"))
        self.label_21.setText(_translate("AdminFom", "Название"))
        self.addSteelDataButton.setText(_translate("AdminFom", "Добавить"))
        self.tabelLabel_3.setText(_translate("AdminFom", "Таблица:"))
        self.showTableForFactory.setText(_translate("AdminFom", "Отобразить"))
        self.choosenTableForFactory.setItemText(0, _translate("AdminFom", "Режимы"))
        self.choosenTableForFactory.setItemText(1, _translate("AdminFom", "Сталь"))
        self.choosenTableForFactory.setItemText(2, _translate("AdminFom", "Состав стали"))
        self.choosenTableForFactory.setItemText(3, _translate("AdminFom", "Чугун"))
        self.choosenTableForFactory.setItemText(4, _translate("AdminFom", "Состав чугуна"))
        self.choosenTableForFactory.setItemText(5, _translate("AdminFom", "Лом"))
        self.choosenTableForFactory.setItemText(6, _translate("AdminFom", "Состав лома"))
        self.choosenTableForFactory.setItemText(7, _translate("AdminFom", "Флюсы"))
        self.groupBox_9.setTitle(_translate("AdminFom", "Добавление флюсов"))
        self.label_8.setText(_translate("AdminFom", "CaO:"))
        self.label_9.setText(_translate("AdminFom", "SiO2:"))
        self.label_22.setText(_translate("AdminFom", "MgO:"))
        self.fluxeFe2O3label.setText(_translate("AdminFom", "Fe2O3:"))
        self.label_30.setText(_translate("AdminFom", "Название:"))
        self.label_31.setText(_translate("AdminFom", "FeO:"))
        self.label_32.setText(_translate("AdminFom", "MnO:"))
        self.label_33.setText(_translate("AdminFom", "Al2O3:"))
        self.label_34.setText(_translate("AdminFom", "CaCO3:"))
        self.label_35.setText(_translate("AdminFom", "MgCO3:"))
        self.addFluxeDataButton.setText(_translate("AdminFom", "Добавить"))
        self.groupBox_10.setTitle(_translate("AdminFom", "Добавление режима"))
        self.label_23.setText(_translate("AdminFom", "Сталь:"))
        self.addModeButton.setText(_translate("AdminFom", "Добавить"))
        self.label_26.setText(_translate("AdminFom", "Чугун:"))
        self.label_27.setText(_translate("AdminFom", "Лом:"))
        self.label_28.setText(_translate("AdminFom", "Название:"))
        self.groupBox_11.setTitle(_translate("AdminFom", "Флюсы в режиме"))
        item = self.FluxeTable.horizontalHeaderItem(0)
        item.setText(_translate("AdminFom", "Тип флюса"))
        self.tip_flyusa_label.setText(_translate("AdminFom", "Тип флюса:"))
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
        self.choosenTableForUsers.setItemText(0, _translate("AdminFom", "Пользователи"))
        self.choosenTableForUsers.setItemText(1, _translate("AdminFom", "Роли"))
        self.tabelLabel_4.setText(_translate("AdminFom", "Таблица:"))
        self.showTableForUsers.setText(_translate("AdminFom", "Отобразить"))
        self.groupBox_12.setTitle(_translate("AdminFom", "Изменение учетных записей"))
        self.UpdateUserButton.setText(_translate("AdminFom", "Изменить"))
        self.label_29.setText(_translate("AdminFom", "Номер"))
        self.label_36.setText(_translate("AdminFom", "Логин"))
        self.label_37.setText(_translate("AdminFom", "Роль:"))
        self.UserRoleUpdate.setCurrentText(_translate("AdminFom", "Оператор"))
        self.UserRoleUpdate.setItemText(0, _translate("AdminFom", "Оператор"))
        self.UserRoleUpdate.setItemText(1, _translate("AdminFom", "Администратор"))
        self.UserRoleUpdate.setItemText(2, _translate("AdminFom", "Разработчик модели"))
        self.SQLQuery.setPlaceholderText(_translate("AdminFom", "Поле для ввода SQL запроса"))
        self.executeSqlbutton.setText(_translate("AdminFom", "Выполнить"))
        self.Factory.setTabText(self.Factory.indexOf(self.tab_4), _translate("AdminFom", "Пользователи"))
        self.menu.setTitle(_translate("AdminFom", "Файл"))
        self.menu_2.setTitle(_translate("AdminFom", "Справка"))
        self.exit.setText(_translate("AdminFom", "Выход"))
        self.about.setText(_translate("AdminFom", "О программе"))
        self.getSettings()
        self.getFluxes()
        self.getAllScrap()
        self.getAllSteel()
        self.getAllCast()
        self.getAllUsersId()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    AdminFom = QtWidgets.QMainWindow()
    ui = Ui_AdminFom()
    ui.setupUi(AdminFom)
    AdminFom.show()
    sys.exit(app.exec_())
