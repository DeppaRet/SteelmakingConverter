from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QAction, QTableWidgetItem
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt
import mysql.connector as mc
import OperForm
import AboutForm
import hashAuth
from configparser import ConfigParser
import pandas as pd

DBhost = "localhost"
DBlogin = "root"
DBpass = "root"
parser = ConfigParser()
parser.read('dev.ini')

class Ui_AdminFom(object):

    # def updateValue(self):
    #

    def exportData(self):
        try:
            columnHeader = []

            for j in range(self.tableWidgetFactory.model().columnCount()):
                columnHeader.append(self.tableWidgetFactory.horizontalHeaderItem(j).text())

            df = pd.DataFrame(columns = columnHeader)

            for row in range(self.tableWidgetFactory.rowCount()):
                for col in range(self.tableWidgetFactory.columnCount()):
                    df.at[row, columnHeader[col]] = self.tableWidgetFactory.item(row,col).text()

            df.to_excel('Data from programm.xlsx', index = False)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Внмание")
            msg.setText("Экспорт успешно завершен")
            msg.setInformativeText("Файл можно найти в папке с программой")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Экспорт не был завершен!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()


    def exportScenarioFunc(self):
        try:
            columnHeader = []

            for j in range(self.tableWidgetFactory_2.model().columnCount()):
                columnHeader.append(self.tableWidgetFactory_2.horizontalHeaderItem(j).text())

            df = pd.DataFrame(columns = columnHeader)

            for row in range(self.tableWidgetFactory_2.rowCount()):
                for col in range(self.tableWidgetFactory_2.columnCount()):
                    df.at[row, columnHeader[col]] = self.tableWidgetFactory_2.item(row,col).text()

            df.to_excel('Scenario.xlsx', index = False)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Внмание")
            msg.setText("Экспорт успешно завершен")
            msg.setInformativeText("Файл можно найти в папке с программой")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Экспорт не был завершен!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()



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
                query += "v_combined_data;"
                self.tableWidgetFactory.setColumnCount(22) #5
                self.tableWidgetFactory.setHorizontalHeaderLabels(
                    ["Название", "Сталь", "C", "S", "P", "Si", "Mn", "Температура чугуна", "Масса чугуна", "C", "S", "P", "Si", "Mn", "Масса лома", "C", "S", "P", "Si", "Mn", "Высота", "Диаметр"]) #["Номер", "Название", "Сталь", "Лом", "Чугун"])
            elif (chTable == "Сталь"):
                query = "select steelname, scomp.SteelCarbon, scomp.SteelSerum, scomp.SteelPhosphor, scomp.SteelSilicon from steeldata as sdata left join steelcomposition as scomp on SteelComposition_idSteelComposition = idSteelComposition;"
                self.tableWidgetFactory.setColumnCount(5)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Марка", "Углерод", "Сера", "Фосфор", "Кремний"])
            elif (chTable == "Состав стали"):
                query = "select steelname, scomp.SteelCarbon, scomp.SteelSerum, scomp.SteelPhosphor, scomp.SteelSilicon from steeldata as sdata left join steelcomposition as scomp on SteelComposition_idSteelComposition = idSteelComposition;"
                self.tableWidgetFactory.setColumnCount(5)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Марка", "Углерод", "Сера", "Фосфор", "Кремний"])
            elif (chTable == "Чугун"):
                query = "select cdata.idCastSteelData, cdata.CastSteelWeight, cdata.CastSteelTemperature, ccomp.CastSteelCarbon, ccomp.CastSteelSerum, ccomp.CastSteelPhosphor, ccomp.CastSteelSilicon, ccomp.CastSteelManganese from caststeeldata as cdata left join caststeelcomposition as ccomp on CastSteelComposition_idCastSteelComposition = idCastSteelComposition;"
                self.tableWidgetFactory.setColumnCount(8)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Масса", "Температура", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == "Состав чугуна"):
                query = "select ccomp.idCastSteelComposition, ccomp.CastSteelCarbon, ccomp.CastSteelSerum, ccomp.CastSteelPhosphor, ccomp.CastSteelSilicon, ccomp.CastSteelManganese from caststeeldata as cdata left join caststeelcomposition as ccomp on CastSteelComposition_idCastSteelComposition = idCastSteelComposition;"
                self.tableWidgetFactory.setColumnCount(6)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер",  "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == "Лом"):
                query = "select sdata.idScrapData, sdata.ScrapWeight, scomp.ScrapCarbon, scomp.ScrapSerum, scomp.ScrapPhosphor, scomp.ScrapSilicon, scomp.ScrapManganese from scrapdata as sdata left join scrapcomposition as scomp on ScrapComposition_idScrapComposition = idScrapComposition;"
                self.tableWidgetFactory.setColumnCount(7)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Масса", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == "Состав лома"):
                query = "select scomp.idScrapComposition, scomp.ScrapCarbon, scomp.ScrapSerum, scomp.ScrapPhosphor, scomp.ScrapSilicon, scomp.ScrapManganese from scrapdata as sdata left join scrapcomposition as scomp on ScrapComposition_idScrapComposition = idScrapComposition;"
                self.tableWidgetFactory.setColumnCount(6)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == "Флюсы"):
                query = "select fdata.FluxeName, fcomp.CaO, fcomp.SiO2, fcomp.MgO, fcomp.Fe2O3, fcomp.FeO, fcomp.MnO, fcomp.Al2O3, fcomp.CaCO3, fcomp.MgCO3 from fluxedata as fdata left join fluxecomposition as fcomp on FluxeComposition_idFluxeComposition = idFluxeComposition;"
                self.tableWidgetFactory.setColumnCount(10)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Название", "CaO", "SiO2", "MgO", "Fe2O3", "FeO", "MnO", "Al2O3", "CaCO3", "MgCO3"])

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
                host=DBhost,
                user=DBlogin,
                password=DBpass,
                database="users_db"
            )
            mycursor = usersDB.cursor()
            mycursor.execute("SELECT * FROM users WHERE Login = %s", (login,))
            if mycursor.fetchone() is not None:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Внимание")
                msg.setText("Пользователь с таким логином уже существует!")
                msg.exec_()
            else:
                query = "INSERT INTO users (Login, Password, Roles_idRoles) values (%s, %s, %s)"
                mycursor.execute(query, value)
                usersDB.commit()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Успех")
                msg.setText("Внимание")
                msg.setInformativeText("Учетная запись успешно добавлена!")
                msg.exec_()
        except Exception as err:
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

    def addSteelData(self):
        try:
            query = "INSERT INTO steelcomposition (SteelCarbon, SteelSerum, SteelPhosphor, SteelSilicon) values (%s, %s, %s, %s)"
            steelCarbon = self.steelCarbon.text()
            steelSerum = self.steelSerum.text()
            steelPhosphor = self.steelPhosphor.text()
            steelSilicon = self.steelSilicon.text()
            value = (steelCarbon, steelSerum, steelPhosphor, steelSilicon)

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

            tmp = "SteelCarbon = " + steelCarbon + " AND SteelSerum = " + steelSerum + " AND SteelPhosphor = " + steelPhosphor + " AND SteelSilicon = " + steelSilicon
            query = "select idSteelComposition from steelcomposition where (" + tmp + ") ORDER BY SteelCarbon ASC LIMIT 1;"
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchone()[0]
            mycursor.close()


            query = "insert into steeldata (SteelComposition_idSteelComposition, SteelName) values (%s, %s);"
            value = (result, self.steelName.text())
            mycursor = DB.cursor()
            mycursor.execute(query, value)
            DB.commit()
            self.getAllSteel()
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


    def showScenario(self):
        try:
            self.tableWidgetFactory_2.setRowCount(0)
            query = "select ScanrioName, ScenarioTask, SteelCarbonLimit, SteelTempLimit, SteelPhosphorLimit, ModeName from scenario join mode on Mode_idMode = idMode;"
            self.tableWidgetFactory_2.setColumnCount(6)
            self.tableWidgetFactory_2.setHorizontalHeaderLabels(["Наименование", "Задача", "Лимит C", "Лимит T", "Лимит P", "Наименование режима"])

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
                self.tableWidgetFactory_2.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.tableWidgetFactory_2.setItem(row_number, column_number, QTableWidgetItem(str(data)))

            self.tableWidgetFactory_2.horizontalHeader().setDefaultSectionSize(100)
            self.tableWidgetFactory_2.verticalHeader().setDefaultSectionSize(200)
            self.tableWidgetFactory_2.setColumnWidth(1, 250)
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()


    def onCellClicked(self, row, column):
        try:
        # Получение данных из выбранной строки
            data1 = self.tableWidgetFactory_2.item(row, 0).text() if self.tableWidgetFactory_2.item(row, 0) else ''
            data2 = self.tableWidgetFactory_2.item(row, 1).text() if self.tableWidgetFactory_2.item(row, 1) else ''
            data3 = self.tableWidgetFactory_2.item(row, 2).text() if self.tableWidgetFactory_2.item(row, 2) else ''
            data4 = self.tableWidgetFactory_2.item(row, 3).text() if self.tableWidgetFactory_2.item(row, 3) else ''
            data5 = self.tableWidgetFactory_2.item(row, 4).text() if self.tableWidgetFactory_2.item(row, 4) else ''

            # Заполнение текстовых полей
            self.scenarioName.setText(data1)
            self.scenarioTask.setPlainText(data2)
            self.SteelCarbonLimit.setText(data3)
            self.MinSteelTempLimit.setText(data4)
            self.SteelPhosphorLimit.setText(data5)
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def getModes(self):
        try:
            query = "select ModeName from mode;"
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
                    self.modeNameBox.addItem((str(data)))
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


    # def addScenario (self):
    #     try:
    #         DB = mc.connect(
    #             host=DBhost,  # host="192.168.51.179" user="root", password="root",
    #             user=DBlogin,
    #             password=DBpass,
    #             database="regimdata"
    #         )
    #         query = "select idMode from mode where ModeName = '" + self.modeNameBox.currentText() + "'"
    #         mycursor = DB.cursor()
    #         mycursor.execute(query)
    #         idMode = mycursor.fetchone()[0]
    #         mycursor.close()
    #
    #         query = "insert into scenario (ScanrioName, ScenarioTask, Mode_idMode, SteelCarbonLimit, SteelTempLimit, SteelPhosphorLimit) values(%s, %s, %s, %s, %s, %s)"
    #
    #         values = (self.scenarioName.text(), self.scenarioTask.toPlainText(), idMode, self.SteelCarbonLimit.text(), self.MinSteelTempLimit.text(), self.SteelPhosphorLimit.text())
    #
    #         mycursor = DB.cursor()
    #         mycursor.execute(query, values)
    #         DB.commit()  # Обязательно для записи
    #         mycursor.close()
    #         DB.close()
    #         self.showScenario()
    #         msg = QMessageBox()
    #         msg.setIcon(QMessageBox.Information)
    #         msg.setWindowTitle("Успех")
    #         msg.setText("Внимание")
    #         msg.setInformativeText("Сценарий успешно добавлен!")
    #         msg.exec_()
    #
    #     except Exception as err:
    #         msg = QMessageBox()
    #         msg.setIcon(QMessageBox.Critical)
    #         msg.setWindowTitle("Ошибка")
    #         msg.setText("Внимание")
    #         msg.setInformativeText("Проверьте введенные данные!")
    #         msg.exec_()
    #     finally:
    #         mycursor.close()
    #         DB.close()

    def addScenario(self):
        try:
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )

            # Проверка наличия записи с такими же данными
            check_query = "SELECT COUNT(*) FROM scenario WHERE ScanrioName = %s AND ScenarioTask = %s AND Mode_idMode = %s"
            check_values = (
                self.scenarioName.text(),
                self.scenarioTask.toPlainText(),
                self.getModeId(DB)  # Функция для получения idMode
            )
            mycursor = DB.cursor()
            mycursor.execute(check_query, check_values)
            record_count = mycursor.fetchone()[0]
            mycursor.close()

            if record_count > 0:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Предупреждение")
                msg.setText("Внимание")
                msg.setInformativeText("Запись с такими данными уже существует!")
                msg.exec_()
                return

            # Вставка новой записи
            query = "INSERT INTO scenario (ScanrioName, ScenarioTask, Mode_idMode, SteelCarbonLimit, SteelTempLimit, SteelPhosphorLimit) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (
                self.scenarioName.text(),
                self.scenarioTask.toPlainText(),
                check_values[2],  # idMode
                self.SteelCarbonLimit.text(),
                self.MinSteelTempLimit.text(),
                self.SteelPhosphorLimit.text()
            )

            mycursor = DB.cursor()
            mycursor.execute(query, values)
            DB.commit()  # Обязательно для записи
            mycursor.close()
            DB.close()
            self.showScenario()

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Успех")
            msg.setText("Внимание")
            msg.setInformativeText("Сценарий успешно добавлен!")
            msg.exec_()

        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()
        finally:
            try:
                mycursor.close()
                DB.close()
            except:
                pass

    def getModeId(self, DB):
        query = "SELECT idMode FROM mode WHERE ModeName = %s"
        mycursor = DB.cursor()
        mycursor.execute(query, (self.modeNameBox.currentText(),))
        idMode = mycursor.fetchone()[0]
        mycursor.close()
        return idMode



    def getAllUsersId(self):
        query = "select Login from users;"
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
            old_login = str(self.UserIdUpdate.currentText())
            usersDB = mc.connect(
                host=DBhost,
                user=DBlogin,
                password=DBpass,
                database="users_db"
            )
            mycursor = usersDB.cursor()
            mycursor.execute("SELECT * FROM users WHERE Login = %s", (old_login,))
            if mycursor.fetchone() is None:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Внимание")
                msg.setText("Пользователь с таким логином не существует!")
                msg.exec_()
            else:
                mycursor.execute("SELECT * FROM users WHERE Login = %s", (login,))
                if mycursor.fetchone() is not None:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Внимание")
                    msg.setText("Пользователь с таким логином уже существует!")
                    msg.exec_()
                else:
                    query = "update users set login = '" + login + "', Roles_idRoles = " + str(
                        role) + " where login = '" + old_login + "';"
                    mycursor.execute(query)
                    usersDB.commit()
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("Успех")
                    msg.setText("Внимание")
                    msg.setInformativeText("Запись изменена")
                    msg.exec_()
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            msg.exec_()

    def create_message(self, icon, title, text, info_text):
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setInformativeText(info_text)
        msg.exec_()

    def executeSqlQuery(self):
        try:
            query = self.SQLQuery.text()
            lowQuery = query.lower()
            forbidden_words = ["drop", "delete"]
            for word in forbidden_words:
                if word in lowQuery:
                    self.create_message(QMessageBox.Critical, "В доступе отказано", "Внимание",
                                        f"Вы не можете использовать команду {word}.")
                    return
            with mc.connect(
                    host=DBhost,
                    user=DBlogin,
                    password=DBpass,
                    database="regimdata"
            ) as DB:
                mycursor = DB.cursor()
                mycursor.execute(query)
                DB.commit()
                self.create_message(QMessageBox.Information, "Успех", "Внимание", "Запрос выполнен.")
        except Exception as err:
            self.create_message(QMessageBox.Critical, "Ошибка", "Внимание", "Проверьте введенные данные!")

    def openAbout(self):
        self.window = QtWidgets.QDialog()
        self.ui = AboutForm.Ui_Dialog()
        self.ui.setupUi(self.window)
        self.window.show()

    def setupUi(self, AdminFom):
        AdminFom.setObjectName("AdminFom")
        AdminFom.resize(1050, 700)
        winIcon = QtGui.QIcon()
        winIcon.addPixmap(QtGui.QPixmap("Pictures/steel_ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        AdminFom.setWindowIcon(winIcon)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(25, 25, 35))
        palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
        palette.setColor(QPalette.Base, QColor(35, 35, 50))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 60))
        palette.setColor(QPalette.ToolTipBase, QColor(0, 212, 255))
        palette.setColor(QPalette.ToolTipText, QColor(25, 25, 35))
        palette.setColor(QPalette.Text, QColor(224, 224, 224))
        palette.setColor(QPalette.Button, QColor(45, 45, 60))
        palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
        palette.setColor(QPalette.Highlight, QColor(0, 212, 255))
        palette.setColor(QPalette.HighlightedText, QColor(25, 25, 35))
        AdminFom.setPalette(palette)

        self.centralwidget = QtWidgets.QWidget(AdminFom)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet("""
            QWidget#centralwidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e);
            }
            QLabel { color: #e0e0e0; }
            QGroupBox {
                color: #00d4ff;
                font-weight: bold;
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                margin-top: 10px;
                padding: 5px;
                background: rgba(0, 0, 0, 0.2);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QPlainTextEdit {
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 4px;
                padding: 3px 6px;
                color: #ffffff;
            }
            QLineEdit:focus, QPlainTextEdit:focus {
                border: 2px solid #00d4ff;
            }
            QComboBox {
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                padding: 5px;
                color: #ffffff;
            }
            QComboBox:hover { border: 1px solid #00d4ff; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1a1a2e;
                color: #ffffff;
                selection-background-color: #00d4ff;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d4ff, stop:1 #0099cc);
                color: #1a1a2e;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e5ff, stop:1 #00b8d9);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0099cc, stop:1 #0077aa);
            }
            QTableWidget {
                background: rgba(0, 0, 0, 0.3);
                alternate-background-color: rgba(255, 255, 255, 0.05);
                gridline-color: rgba(0, 212, 255, 0.2);
                color: #e0e0e0;
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 8px;
            }
            QTableWidget::item { padding: 5px; color: #e0e0e0; }
            QTableWidget::item:selected { background: rgba(0, 212, 255, 0.3); color: #ffffff; }
            QHeaderView { background: rgba(0, 0, 0, 0.4); }
            QHeaderView::section {
                background: rgba(0, 212, 255, 0.25);
                color: #ffffff;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget QTableCornerButton::section { background: rgba(0, 212, 255, 0.25); border: none; }
            QTabWidget::pane {
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                background: rgba(0, 0, 0, 0.2);
            }
            QTabBar::tab {
                background: rgba(0, 0, 0, 0.3);
                color: #e0e0e0;
                padding: 4px 10px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-size: 10px;
                min-width: 130px;
            }
            QTabBar::tab:selected { background: rgba(0, 212, 255, 0.3); color: #00d4ff; font-weight: bold; }
            QTabBar::tab:hover { background: rgba(0, 212, 255, 0.15); }
            QScrollBar:vertical { background: rgba(0, 0, 0, 0.3); width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background: rgba(0, 212, 255, 0.5); border-radius: 5px; }
            QScrollBar:horizontal { background: rgba(0, 0, 0, 0.3); height: 12px; border-radius: 6px; }
            QScrollBar::handle:horizontal { background: rgba(0, 212, 255, 0.5); border-radius: 5px; }
            QMenuBar { background: rgba(0, 0, 0, 0.5); color: #e0e0e0; }
            QMenuBar::item:selected { background: rgba(0, 212, 255, 0.3); }
            QMenu { background: #1a1a2e; color: #e0e0e0; border: 1px solid rgba(0, 212, 255, 0.3); }
            QMenu::item:selected { background: rgba(0, 212, 255, 0.3); }
            QStatusBar { background: rgba(0, 0, 0, 0.5); color: #e0e0e0; }
        """)

        self.Factory = QtWidgets.QTabWidget(self.centralwidget)
        self.Factory.setGeometry(QtCore.QRect(0, 0, 1041, 661))
        self.Factory.setAutoFillBackground(False)
        self.Factory.setObjectName("Factory")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.groupBox = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox.setGeometry(QtCore.QRect(480, 10, 550, 640))
        self.groupBox.setObjectName("groupBox")
        self.groupBox_3 = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 195, 530, 180))
        self.groupBox_3.setObjectName("groupBox_3")
        self.addScrapDataButton = QtWidgets.QPushButton(self.groupBox_3)
        self.addScrapDataButton.setGeometry(QtCore.QRect(400, 20, 120, 23))
        self.addScrapDataButton.setObjectName("addScrapDataButton")
        self.addScrapDataButton.clicked.connect(self.addScrap)
        self.label_11 = QtWidgets.QLabel(self.groupBox_3)
        self.label_11.setGeometry(QtCore.QRect(10, 20, 101, 16))
        self.label_11.setObjectName("label_11")
        self.scrapWeight = QtWidgets.QLineEdit(self.groupBox_3)
        self.scrapWeight.setGeometry(QtCore.QRect(110, 20, 100, 20))
        self.scrapWeight.setText("")
        self.scrapWeight.setObjectName("scrapWeight")
        self.groupBox_7 = QtWidgets.QGroupBox(self.groupBox_3)
        self.groupBox_7.setGeometry(QtCore.QRect(10, 50, 510, 120))
        self.groupBox_7.setObjectName("groupBox_7")
        self.label_12 = QtWidgets.QLabel(self.groupBox_7)
        self.label_12.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_12.setObjectName("label_12")
        self.label_13 = QtWidgets.QLabel(self.groupBox_7)
        self.label_13.setGeometry(QtCore.QRect(140, 20, 71, 16))
        self.label_13.setObjectName("label_13")
        self.label_14 = QtWidgets.QLabel(self.groupBox_7)
        self.label_14.setGeometry(QtCore.QRect(270, 20, 51, 16))
        self.label_14.setObjectName("label_14")
        self.label_15 = QtWidgets.QLabel(self.groupBox_7)
        self.label_15.setGeometry(QtCore.QRect(400, 20, 61, 16))
        self.label_15.setObjectName("label_15")
        self.scrapCarbon = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapCarbon.setGeometry(QtCore.QRect(10, 35, 120, 20))
        self.scrapCarbon.setObjectName("scrapCarbon")
        self.scrapSilicon = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapSilicon.setGeometry(QtCore.QRect(140, 35, 120, 20))
        self.scrapSilicon.setObjectName("scrapSilicon")
        self.scrapSerum = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapSerum.setGeometry(QtCore.QRect(270, 35, 120, 20))
        self.scrapSerum.setObjectName("scrapSerum")
        self.scrapPhosphor = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapPhosphor.setGeometry(QtCore.QRect(400, 35, 100, 20))
        self.scrapPhosphor.setObjectName("scrapPhosphor")
        self.scrapManganese = QtWidgets.QLineEdit(self.groupBox_7)
        self.scrapManganese.setEnabled(True)
        self.scrapManganese.setGeometry(QtCore.QRect(10, 75, 120, 20))
        self.scrapManganese.setText("")
        self.scrapManganese.setObjectName("scrapManganese")
        self.label_25 = QtWidgets.QLabel(self.groupBox_7)
        self.label_25.setGeometry(QtCore.QRect(10, 55, 81, 16))
        self.label_25.setObjectName("label_25")
        self.groupBox_4 = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_4.setGeometry(QtCore.QRect(10, 380, 530, 230))
        self.groupBox_4.setObjectName("groupBox_4")
        self.label_10 = QtWidgets.QLabel(self.groupBox_4)
        self.label_10.setGeometry(QtCore.QRect(10, 20, 120, 16))
        self.label_10.setObjectName("label_10")
        self.castTemperature = QtWidgets.QLineEdit(self.groupBox_4)
        self.castTemperature.setGeometry(QtCore.QRect(130, 20, 100, 20))
        self.castTemperature.setText("")
        self.castTemperature.setObjectName("castTemperature")
        self.label_16 = QtWidgets.QLabel(self.groupBox_4)
        self.label_16.setGeometry(QtCore.QRect(10, 50, 170, 16))
        self.label_16.setObjectName("label_16")
        self.castWeight = QtWidgets.QLineEdit(self.groupBox_4)
        self.castWeight.setGeometry(QtCore.QRect(130, 50, 100, 20))
        self.castWeight.setText("")
        self.castWeight.setObjectName("castWeight")
        self.groupBox_6 = QtWidgets.QGroupBox(self.groupBox_4)
        self.groupBox_6.setGeometry(QtCore.QRect(10, 75, 510, 120))
        self.groupBox_6.setObjectName("groupBox_6")
        self.label_17 = QtWidgets.QLabel(self.groupBox_6)
        self.label_17.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_17.setObjectName("label_17")
        self.label_18 = QtWidgets.QLabel(self.groupBox_6)
        self.label_18.setGeometry(QtCore.QRect(140, 20, 71, 16))
        self.label_18.setObjectName("label_18")
        self.label_19 = QtWidgets.QLabel(self.groupBox_6)
        self.label_19.setGeometry(QtCore.QRect(270, 20, 51, 16))
        self.label_19.setObjectName("label_19")
        self.label_20 = QtWidgets.QLabel(self.groupBox_6)
        self.label_20.setGeometry(QtCore.QRect(400, 20, 61, 16))
        self.label_20.setObjectName("label_20")
        self.castCarbon = QtWidgets.QLineEdit(self.groupBox_6)
        self.castCarbon.setGeometry(QtCore.QRect(10, 35, 120, 20))
        self.castCarbon.setObjectName("castCarbon")
        self.castSilicon = QtWidgets.QLineEdit(self.groupBox_6)
        self.castSilicon.setGeometry(QtCore.QRect(140, 35, 120, 20))
        self.castSilicon.setObjectName("castSilicon")
        self.castSerum = QtWidgets.QLineEdit(self.groupBox_6)
        self.castSerum.setGeometry(QtCore.QRect(270, 35, 120, 20))
        self.castSerum.setObjectName("castSerum")
        self.castPhosphor = QtWidgets.QLineEdit(self.groupBox_6)
        self.castPhosphor.setGeometry(QtCore.QRect(400, 35, 100, 20))
        self.castPhosphor.setObjectName("castPhosphor")
        self.castManganese = QtWidgets.QLineEdit(self.groupBox_6)
        self.castManganese.setEnabled(True)
        self.castManganese.setGeometry(QtCore.QRect(10, 75, 120, 20))
        self.castManganese.setText("")
        self.castManganese.setObjectName("castManganese")
        self.label_24 = QtWidgets.QLabel(self.groupBox_6)
        self.label_24.setGeometry(QtCore.QRect(10, 70, 81, 16))
        self.label_24.setObjectName("label_24")
        self.addCastButton = QtWidgets.QPushButton(self.groupBox_4)
        self.addCastButton.setGeometry(QtCore.QRect(400, 20, 120, 23))
        self.addCastButton.setObjectName("addCastButton")
        self.addCastButton.clicked.connect(self.addCastData)
        self.groupBox_5 = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_5.setGeometry(QtCore.QRect(10, 20, 530, 170))
        self.groupBox_5.setObjectName("groupBox_5")
        self.groupBox_8 = QtWidgets.QGroupBox(self.groupBox_5)
        self.groupBox_8.setGeometry(QtCore.QRect(10, 60, 510, 100))
        self.groupBox_8.setObjectName("groupBox_8")
        self.label_4 = QtWidgets.QLabel(self.groupBox_8)
        self.label_4.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.groupBox_8)
        self.label_5.setGeometry(QtCore.QRect(10, 50, 71, 16))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.groupBox_8)
        self.label_6.setGeometry(QtCore.QRect(180, 20, 51, 16))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.groupBox_8)
        self.label_7.setGeometry(QtCore.QRect(180, 50, 61, 16))
        self.label_7.setObjectName("label_7")
        self.steelCarbon = QtWidgets.QLineEdit(self.groupBox_8)
        self.steelCarbon.setGeometry(QtCore.QRect(80, 20, 80, 20))
        self.steelCarbon.setObjectName("steelCarbon")
        self.steelSilicon = QtWidgets.QLineEdit(self.groupBox_8)
        self.steelSilicon.setGeometry(QtCore.QRect(80, 50, 80, 20))
        self.steelSilicon.setObjectName("steelSilicon")
        self.steelSerum = QtWidgets.QLineEdit(self.groupBox_8)
        self.steelSerum.setGeometry(QtCore.QRect(250, 20, 80, 20))
        self.steelSerum.setObjectName("steelSerum")
        self.steelPhosphor = QtWidgets.QLineEdit(self.groupBox_8)
        self.steelPhosphor.setGeometry(QtCore.QRect(250, 50, 80, 20))
        self.steelPhosphor.setObjectName("steelPhosphor")
        self.steelName = QtWidgets.QLineEdit(self.groupBox_5)
        self.steelName.setGeometry(QtCore.QRect(70, 30, 150, 20))
        self.steelName.setText("")
        self.steelName.setObjectName("steelName")
        self.label_21 = QtWidgets.QLabel(self.groupBox_5)
        self.label_21.setGeometry(QtCore.QRect(10, 30, 60, 16))
        self.label_21.setObjectName("label_21")
        self.addSteelDataButton = QtWidgets.QPushButton(self.groupBox_5)
        self.addSteelDataButton.setGeometry(QtCore.QRect(400, 30, 120, 23))
        self.addSteelDataButton.setObjectName("addSteelDataButton")
        self.addSteelDataButton.clicked.connect(self.addSteelData)
        self.tabelLabel_3 = QtWidgets.QLabel(self.tab_3)
        self.tabelLabel_3.setGeometry(QtCore.QRect(10, 10, 180, 18))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.tabelLabel_3.setFont(font)
        self.tabelLabel_3.setObjectName("tabelLabel_3")
        self.showTableForFactory = QtWidgets.QPushButton(self.tab_3)
        self.showTableForFactory.setGeometry(QtCore.QRect(200, 30, 110, 25))
        self.showTableForFactory.setObjectName("showTableForFactory")
        self.showTableForFactory.clicked.connect(self.showTableForFactoryClick)
        self.tableWidgetFactory = QtWidgets.QTableWidget(self.tab_3)
        self.tableWidgetFactory.setGeometry(QtCore.QRect(10, 60, 460, 200))
        self.tableWidgetFactory.setObjectName("tableWidgetFactory")
        self.tableWidgetFactory.setColumnCount(0)
        self.tableWidgetFactory.setRowCount(0)
        # self.tableWidgetFactory.itemChanged.connect(self.updateValue)
        self.choosenTableForFactory = QtWidgets.QComboBox(self.tab_3)
        self.choosenTableForFactory.setGeometry(QtCore.QRect(10, 30, 180, 25))
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
        self.groupBox_9.setGeometry(QtCore.QRect(10, 500, 460, 140))
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
        self.fluxeName = QtWidgets.QLineEdit(self.groupBox_9)
        self.fluxeName.setGeometry(QtCore.QRect(80, 20, 111, 20))
        self.fluxeName.setObjectName("fluxeName")
        self.label_30 = QtWidgets.QLabel(self.groupBox_9)
        self.label_30.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_30.setObjectName("label_30")
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
        self.addFluxeDataButton.setGeometry(QtCore.QRect(200, 20, 120, 23))
        self.addFluxeDataButton.setObjectName("addFluxeDataButton")
        self.addFluxeDataButton.clicked.connect(self.addFluxeDataButtonClicked)
        self.groupBox_10 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_10.setGeometry(QtCore.QRect(10, 270, 261, 141))
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
        self.addModeButton.setGeometry(QtCore.QRect(140, 100, 120, 23))
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
        self.groupBox_11.setGeometry(QtCore.QRect(280, 270, 161, 141))
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
        icon.addPixmap(QtGui.QPixmap("GUI\\../Pictures/add.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
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
        icon1.addPixmap(QtGui.QPixmap("GUI\\../Pictures/remove.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RemoveFluxeButton.setIcon(icon1)
        self.RemoveFluxeButton.setObjectName("RemoveFluxeButton")
        self.tip_flyusa_label = QtWidgets.QLabel(self.groupBox_11)
        self.tip_flyusa_label.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.tip_flyusa_label.setObjectName("tip_flyusa_label")
        self.exportButton = QtWidgets.QPushButton(self.tab_3)
        self.exportButton.setGeometry(QtCore.QRect(320, 30, 100, 25))
        self.exportButton.setObjectName("exportButton")
        self.exportButton.clicked.connect(self.exportData)
        self.Factory.addTab(self.tab_3, "")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tabelLabel_5 = QtWidgets.QLabel(self.tab)
        self.tabelLabel_5.setGeometry(QtCore.QRect(10, 10, 131, 18))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(14)
        self.tabelLabel_5.setFont(font)
        self.tabelLabel_5.setObjectName("tabelLabel_5")
        self.exportScenario = QtWidgets.QPushButton(self.tab)
        self.exportScenario.setGeometry(QtCore.QRect(690, 10, 75, 23))
        self.exportScenario.setObjectName("exportScenario")
        self.exportScenario.clicked.connect(self.exportScenarioFunc)
        self.showTableForScenario = QtWidgets.QPushButton(self.tab)
        self.showTableForScenario.setGeometry(QtCore.QRect(610, 10, 75, 23))
        self.showTableForScenario.setObjectName("showTableForScenario")
        self.showTableForScenario.clicked.connect(self.showScenario)
        self.tableWidgetFactory_2 = QtWidgets.QTableWidget(self.tab)
        self.tableWidgetFactory_2.setGeometry(QtCore.QRect(10, 40, 761, 280))
        self.tableWidgetFactory_2.setObjectName("tableWidgetFactory_2")
        self.tableWidgetFactory_2.setColumnCount(0)
        self.tableWidgetFactory_2.setRowCount(0)
        self.tableWidgetFactory_2.cellClicked.connect(self.onCellClicked)
        self.groupBox_13 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_13.setGeometry(QtCore.QRect(10, 330, 761, 300))
        self.groupBox_13.setObjectName("groupBox_13")
        self.addScenarioButton_2 = QtWidgets.QPushButton(self.groupBox_13)
        self.addScenarioButton_2.setGeometry(QtCore.QRect(680, 20, 71, 23))
        self.addScenarioButton_2.setObjectName("addScenarioButton_2")
        self.addScenarioButton_2.clicked.connect(self.addScenario)
        self.scenarioName = QtWidgets.QLineEdit(self.groupBox_13)
        self.scenarioName.setGeometry(QtCore.QRect(100, 20, 201, 20))
        self.scenarioName.setObjectName("scenarioName")
        self.label_41 = QtWidgets.QLabel(self.groupBox_13)
        self.label_41.setGeometry(QtCore.QRect(10, 20, 81, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_41.setFont(font)
        self.label_41.setObjectName("label_41")
        self.label_42 = QtWidgets.QLabel(self.groupBox_13)
        self.label_42.setGeometry(QtCore.QRect(10, 50, 81, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_42.setFont(font)
        self.label_42.setObjectName("label_42")
        self.scenarioTask = QtWidgets.QPlainTextEdit(self.groupBox_13)
        self.scenarioTask.setEnabled(True)
        self.scenarioTask.setGeometry(QtCore.QRect(10, 70, 421, 210))
        self.scenarioTask.setObjectName("scenarioTask")
        self.groupBox_15 = QtWidgets.QGroupBox(self.groupBox_13)
        self.groupBox_15.setGeometry(QtCore.QRect(450, 70, 301, 210))
        self.groupBox_15.setObjectName("groupBox_15")
        self.MinSteelTempLimit = QtWidgets.QLineEdit(self.groupBox_15)
        self.MinSteelTempLimit.setGeometry(QtCore.QRect(160, 30, 131, 20))
        self.MinSteelTempLimit.setText("")
        self.MinSteelTempLimit.setReadOnly(False)
        self.MinSteelTempLimit.setObjectName("MinSteelTempLimit")
        self.label_44 = QtWidgets.QLabel(self.groupBox_15)
        self.label_44.setGeometry(QtCore.QRect(10, 20, 141, 31))
        self.label_44.setWordWrap(True)
        self.label_44.setObjectName("label_44")
        self.label_45 = QtWidgets.QLabel(self.groupBox_15)
        self.label_45.setGeometry(QtCore.QRect(10, 60, 141, 31))
        self.label_45.setWordWrap(True)
        self.label_45.setObjectName("label_45")
        self.SteelPhosphorLimit = QtWidgets.QLineEdit(self.groupBox_15)
        self.SteelPhosphorLimit.setGeometry(QtCore.QRect(160, 70, 131, 20))
        self.SteelPhosphorLimit.setText("")
        self.SteelPhosphorLimit.setReadOnly(False)
        self.SteelPhosphorLimit.setObjectName("SteelPhosphorLimit")
        self.SteelCarbonLimit = QtWidgets.QLineEdit(self.groupBox_15)
        self.SteelCarbonLimit.setGeometry(QtCore.QRect(160, 110, 131, 20))
        self.SteelCarbonLimit.setText("")
        self.SteelCarbonLimit.setReadOnly(False)
        self.SteelCarbonLimit.setObjectName("SteelCarbonLimit")
        self.label_46 = QtWidgets.QLabel(self.groupBox_15)
        self.label_46.setGeometry(QtCore.QRect(10, 100, 141, 31))
        self.label_46.setWordWrap(True)
        self.label_46.setObjectName("label_46")
        self.modeNameBox = QtWidgets.QComboBox(self.groupBox_15)
        self.modeNameBox.setGeometry(QtCore.QRect(160, 150, 131, 21))
        self.modeNameBox.setObjectName("modeNameBox")
        self.label_43 = QtWidgets.QLabel(self.groupBox_15)
        self.label_43.setGeometry(QtCore.QRect(10, 150, 51, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_43.setFont(font)
        self.label_43.setObjectName("label_43")
        self.Factory.addTab(self.tab, "")
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
        self.tableWidgetUsers.setGeometry(QtCore.QRect(10, 60, 521, 591))
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
        self.SQLQuery.setGeometry(QtCore.QRect(540, 580, 161, 21))
        self.SQLQuery.setObjectName("SQLQuery")
        self.executeSqlbutton = QtWidgets.QPushButton(self.tab_4)
        self.executeSqlbutton.setGeometry(QtCore.QRect(710, 580, 71, 23))
        self.executeSqlbutton.setObjectName("executeSqlbutton")
        self.executeSqlbutton.clicked.connect(self.executeSqlQuery)
        self.Factory.addTab(self.tab_4, "")
        AdminFom.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(AdminFom)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1050, 21))
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
        self.exportButton.setText(_translate("AdminFom", "Экспорт"))
        self.label_26.setText(_translate("AdminFom", "Чугун:"))
        self.label_27.setText(_translate("AdminFom", "Лом:"))
        self.label_28.setText(_translate("AdminFom", "Название:"))
        self.groupBox_11.setTitle(_translate("AdminFom", "Флюсы в режиме"))
        item = self.FluxeTable.horizontalHeaderItem(0)
        item.setText(_translate("AdminFom", "Тип флюса"))
        self.tip_flyusa_label.setText(_translate("AdminFom", "Тип флюса:"))
        self.exportButton.setText(_translate("AdminFom", "Экспорт"))
        self.Factory.setTabText(self.Factory.indexOf(self.tab_3), _translate("AdminFom", "Промышленные данные"))
        self.tabelLabel_5.setText(_translate("AdminFom", "Сценарии"))
        self.exportScenario.setText(_translate("AdminFom", "Экспорт"))
        self.showTableForScenario.setText(_translate("AdminFom", "Обновить"))
        self.groupBox_13.setTitle(_translate("AdminFom", "Добавление сценария"))
        self.addScenarioButton_2.setText(_translate("AdminFom", "Добавить"))
        self.label_41.setText(_translate("AdminFom", "Наименование:"))
        self.label_42.setText(_translate("AdminFom", "Задача:"))
        self.groupBox_15.setTitle(_translate("AdminFom", "Ограничения"))
        self.label_44.setText(_translate("AdminFom", "Минимальная температура стали [℃]:"))
        self.label_45.setText(_translate("AdminFom", "Содержание фосфора в стали [%масс]:"))
        self.label_46.setText(_translate("AdminFom", "Содержание углерода в стали [%масс]:"))
        self.label_43.setText(_translate("AdminFom", "Режим:"))
        self.Factory.setTabText(self.Factory.indexOf(self.tab), _translate("AdminFom", "Сценарии"))
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
        self.getModes()
        self.getAllUsersId()
        self.showScenario()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    AdminFom = QtWidgets.QMainWindow()
    ui = Ui_AdminFom()
    ui.setupUi(AdminFom)
    AdminFom.show()
    sys.exit(app.exec_())
