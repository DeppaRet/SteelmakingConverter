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

import app_theme
from theme_settings import manager, get_theme
from view_toggles import ViewTogglesBar
from locale_settings import manager as locale_manager
from i18n import tr

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
        if choosenTable == tr("AdminFom", "Пользователи"):
            query += "users;"
            self.tableWidgetUsers.setColumnCount(4)
            self.tableWidgetUsers.setHorizontalHeaderLabels(["Номер", "Логин", "Пароль", "Роль"])
        elif choosenTable == tr("AdminFom", "Роли"):
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
            # if choosenTable == tr("AdminFom", "Пользователи"):
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
            if (chTable == tr("AdminFom", "Режимы")):
                query += "v_combined_data;"
                self.tableWidgetFactory.setColumnCount(22) #5
                self.tableWidgetFactory.setHorizontalHeaderLabels(
                    ["Название", "Сталь", "C", "S", "P", "Si", "Mn", "Температура чугуна", "Масса чугуна", "C", "S", "P", "Si", "Mn", "Масса лома", "C", "S", "P", "Si", "Mn", "Высота", "Диаметр"]) #["Номер", "Название", "Сталь", "Лом", "Чугун"])
            elif (chTable == tr("AdminFom", "Сталь")):
                query = "select steelname, scomp.SteelCarbon, scomp.SteelSerum, scomp.SteelPhosphor, scomp.SteelSilicon from steeldata as sdata left join steelcomposition as scomp on SteelComposition_idSteelComposition = idSteelComposition;"
                self.tableWidgetFactory.setColumnCount(5)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Марка", "Углерод", "Сера", "Фосфор", "Кремний"])
            elif (chTable == tr("AdminFom", "Состав стали")):
                query = "select steelname, scomp.SteelCarbon, scomp.SteelSerum, scomp.SteelPhosphor, scomp.SteelSilicon from steeldata as sdata left join steelcomposition as scomp on SteelComposition_idSteelComposition = idSteelComposition;"
                self.tableWidgetFactory.setColumnCount(5)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Марка", "Углерод", "Сера", "Фосфор", "Кремний"])
            elif (chTable == tr("AdminFom", "Чугун")):
                query = "select cdata.idCastSteelData, cdata.CastSteelWeight, cdata.CastSteelTemperature, ccomp.CastSteelCarbon, ccomp.CastSteelSerum, ccomp.CastSteelPhosphor, ccomp.CastSteelSilicon, ccomp.CastSteelManganese from caststeeldata as cdata left join caststeelcomposition as ccomp on CastSteelComposition_idCastSteelComposition = idCastSteelComposition;"
                self.tableWidgetFactory.setColumnCount(8)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Масса", "Температура", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == tr("AdminFom", "Состав чугуна")):
                query = "select ccomp.idCastSteelComposition, ccomp.CastSteelCarbon, ccomp.CastSteelSerum, ccomp.CastSteelPhosphor, ccomp.CastSteelSilicon, ccomp.CastSteelManganese from caststeeldata as cdata left join caststeelcomposition as ccomp on CastSteelComposition_idCastSteelComposition = idCastSteelComposition;"
                self.tableWidgetFactory.setColumnCount(6)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер",  "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == tr("AdminFom", "Лом")):
                query = "select sdata.idScrapData, sdata.ScrapWeight, scomp.ScrapCarbon, scomp.ScrapSerum, scomp.ScrapPhosphor, scomp.ScrapSilicon, scomp.ScrapManganese from scrapdata as sdata left join scrapcomposition as scomp on ScrapComposition_idScrapComposition = idScrapComposition;"
                self.tableWidgetFactory.setColumnCount(7)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Масса", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == tr("AdminFom", "Состав лома")):
                query = "select scomp.idScrapComposition, scomp.ScrapCarbon, scomp.ScrapSerum, scomp.ScrapPhosphor, scomp.ScrapSilicon, scomp.ScrapManganese from scrapdata as sdata left join scrapcomposition as scomp on ScrapComposition_idScrapComposition = idScrapComposition;"
                self.tableWidgetFactory.setColumnCount(6)
                self.tableWidgetFactory.setHorizontalHeaderLabels(["Номер", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == tr("AdminFom", "Флюсы")):
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
            if self.UserRoleCreate.currentText() == tr("AdminFom", "Оператор"):
                role = 2
            elif self.UserRoleCreate.currentText() == tr("AdminFom", "Администратор"):
                role = 1
            elif self.UserRoleCreate.currentText() == tr("AdminFom", "Разработчик модели"):
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
            if self.UserRoleUpdate.currentText() == tr("AdminFom", "Оператор"):
                role = 2
            elif self.UserRoleUpdate.currentText() == tr("AdminFom", "Администратор"):
                role = 1
            elif self.UserRoleUpdate.currentText() == tr("AdminFom", "Разработчик модели"):
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
        msg.setWindowTitle(tr("Message", title))
        msg.setText(tr("Message", text))
        msg.setInformativeText(tr("Message", info_text))
        msg.exec_()

    def refresh_language(self, AdminFom):
        self.retranslateUi(AdminFom)
        if hasattr(self, 'view_toggles'):
            self.view_toggles.language_toggle.sync_from_settings()

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

    def refresh_theme(self):
        theme = get_theme()
        pal = app_theme.palette(theme)
        content_style = app_theme.admin_central_style(theme)
        root = getattr(self, "_admin_form", None)

        if root is not None:
            root.setPalette(pal)
            root.setStyleSheet(app_theme.operator_main_style(theme))

        shells = []
        if hasattr(self, "centralwidget"):
            shells.append(self.centralwidget)
        if hasattr(self, "Factory"):
            shells.append(self.Factory)
            for i in range(self.Factory.count()):
                tab = self.Factory.widget(i)
                if tab is not None:
                    shells.append(tab)

        for widget in shells:
            widget.setAttribute(Qt.WA_StyledBackground, True)
            widget.setAutoFillBackground(True)
            widget.setPalette(pal)
            widget.setStyleSheet(content_style)

        if root is not None:
            app_theme.apply_admin_content_styles(root, theme)
            root.style().unpolish(root)
            root.style().polish(root)
            root.update()

        if hasattr(self, "view_toggles"):
            self.view_toggles.theme_toggle.sync_from_settings()

    def setupUi(self, AdminFom):
        self._admin_form = AdminFom
        AdminFom.setObjectName("AdminFom")
        AdminFom.resize(1150, 750)
        AdminFom.setMinimumSize(900, 600)
        winIcon = QtGui.QIcon()
        winIcon.addPixmap(QtGui.QPixmap("Pictures/steel_ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        AdminFom.setWindowIcon(winIcon)

        self.centralwidget = QtWidgets.QWidget(AdminFom)
        self.centralwidget.setObjectName("centralwidget")

        central_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        central_layout.setContentsMargins(0, 0, 0, 0)

        self.Factory = QtWidgets.QTabWidget()
        self.Factory.setObjectName("Factory")
        central_layout.addWidget(self.Factory)

        # ── TAB 1: Промышленные данные ────────────────────────────────────────
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        tab3_root = QtWidgets.QHBoxLayout(self.tab_3)
        tab3_root.setContentsMargins(8, 8, 8, 8)
        tab3_root.setSpacing(8)

        # --- Left panel: table viewer + mode/flux controls ---
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # table header row
        table_hdr = QtWidgets.QHBoxLayout()
        self.tabelLabel_3 = QtWidgets.QLabel()
        self.tabelLabel_3.setObjectName("tabelLabel_3")
        _f = QtGui.QFont("Times New Roman", 12)
        self.tabelLabel_3.setFont(_f)
        table_hdr.addWidget(self.tabelLabel_3)

        self.choosenTableForFactory = QtWidgets.QComboBox()
        self.choosenTableForFactory.setObjectName("choosenTableForFactory")
        for _ in range(8):
            self.choosenTableForFactory.addItem("")
        self.choosenTableForFactory.setMinimumWidth(150)
        table_hdr.addWidget(self.choosenTableForFactory)

        self.showTableForFactory = QtWidgets.QPushButton()
        self.showTableForFactory.setObjectName("showTableForFactory")
        self.showTableForFactory.clicked.connect(self.showTableForFactoryClick)
        table_hdr.addWidget(self.showTableForFactory)

        self.exportButton = QtWidgets.QPushButton()
        self.exportButton.setObjectName("exportButton")
        self.exportButton.clicked.connect(self.exportData)
        table_hdr.addWidget(self.exportButton)
        table_hdr.addStretch()
        left_layout.addLayout(table_hdr)

        self.tableWidgetFactory = QtWidgets.QTableWidget()
        self.tableWidgetFactory.setObjectName("tableWidgetFactory")
        self.tableWidgetFactory.setColumnCount(0)
        self.tableWidgetFactory.setRowCount(0)
        self.tableWidgetFactory.setAlternatingRowColors(True)
        self.tableWidgetFactory.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.tableWidgetFactory, stretch=1)

        # mode + flux-in-mode side by side
        mid_row = QtWidgets.QHBoxLayout()
        mid_row.setSpacing(6)

        self.groupBox_10 = QtWidgets.QGroupBox()
        self.groupBox_10.setObjectName("groupBox_10")
        mode_grid = QtWidgets.QGridLayout(self.groupBox_10)
        mode_grid.setSpacing(6)
        mode_grid.setColumnStretch(1, 1)

        self.label_28 = QtWidgets.QLabel()
        self.label_28.setObjectName("label_28")
        self.modeName = QtWidgets.QLineEdit()
        self.modeName.setObjectName("modeName")
        mode_grid.addWidget(self.label_28, 0, 0)
        mode_grid.addWidget(self.modeName, 0, 1)

        self.label_23 = QtWidgets.QLabel()
        self.label_23.setObjectName("label_23")
        self.modeSteelName = QtWidgets.QComboBox()
        self.modeSteelName.setObjectName("modeSteelName")
        mode_grid.addWidget(self.label_23, 1, 0)
        mode_grid.addWidget(self.modeSteelName, 1, 1)

        self.label_26 = QtWidgets.QLabel()
        self.label_26.setObjectName("label_26")
        self.modeCastSteel = QtWidgets.QComboBox()
        self.modeCastSteel.setObjectName("modeCastSteel")
        mode_grid.addWidget(self.label_26, 2, 0)
        mode_grid.addWidget(self.modeCastSteel, 2, 1)

        self.label_27 = QtWidgets.QLabel()
        self.label_27.setObjectName("label_27")
        self.modeScrap = QtWidgets.QComboBox()
        self.modeScrap.setObjectName("modeScrap")
        mode_grid.addWidget(self.label_27, 3, 0)
        mode_grid.addWidget(self.modeScrap, 3, 1)

        self.addModeButton = QtWidgets.QPushButton()
        self.addModeButton.setObjectName("addModeButton")
        self.addModeButton.clicked.connect(self.addMode)
        mode_grid.addWidget(self.addModeButton, 4, 0, 1, 2)

        mid_row.addWidget(self.groupBox_10, stretch=1)

        self.groupBox_11 = QtWidgets.QGroupBox()
        self.groupBox_11.setObjectName("groupBox_11")
        fluxmode_vbox = QtWidgets.QVBoxLayout(self.groupBox_11)
        fluxmode_vbox.setSpacing(4)

        self.tip_flyusa_label = QtWidgets.QLabel()
        self.tip_flyusa_label.setObjectName("tip_flyusa_label")
        fluxmode_vbox.addWidget(self.tip_flyusa_label)

        self.FluxeType = QtWidgets.QComboBox()
        self.FluxeType.setEditable(False)
        self.FluxeType.setObjectName("FluxeType")
        fluxmode_vbox.addWidget(self.FluxeType)

        flux_tbl_row = QtWidgets.QHBoxLayout()
        self.FluxeTable = QtWidgets.QTableWidget()
        self.FluxeTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.FluxeTable.setObjectName("FluxeTable")
        self.FluxeTable.setColumnCount(1)
        self.FluxeTable.setRowCount(0)
        _hitem = QtWidgets.QTableWidgetItem()
        self.FluxeTable.setHorizontalHeaderItem(0, _hitem)
        self.FluxeTable.horizontalHeader().setStretchLastSection(True)
        flux_tbl_row.addWidget(self.FluxeTable)

        flux_btn_col = QtWidgets.QVBoxLayout()
        self.AddFluxeButton = QtWidgets.QPushButton()
        self.AddFluxeButton.setText("")
        _icon_add = QtGui.QIcon()
        _icon_add.addPixmap(QtGui.QPixmap("GUI\\../Pictures/add.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.AddFluxeButton.setIcon(_icon_add)
        self.AddFluxeButton.setObjectName("AddFluxeButton")
        self.AddFluxeButton.clicked.connect(self.AddFluxeButtonClicked)
        flux_btn_col.addWidget(self.AddFluxeButton)

        self.RemoveFluxeButton = QtWidgets.QPushButton()
        self.RemoveFluxeButton.setText("")
        self.RemoveFluxeButton.clicked.connect(self.removeFluxeButtonClicked)
        _icon_rm = QtGui.QIcon()
        _icon_rm.addPixmap(QtGui.QPixmap("GUI\\../Pictures/remove.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RemoveFluxeButton.setIcon(_icon_rm)
        self.RemoveFluxeButton.setObjectName("RemoveFluxeButton")
        flux_btn_col.addWidget(self.RemoveFluxeButton)
        flux_btn_col.addStretch()

        flux_tbl_row.addLayout(flux_btn_col)
        fluxmode_vbox.addLayout(flux_tbl_row)

        mid_row.addWidget(self.groupBox_11, stretch=1)
        left_layout.addLayout(mid_row)

        # flux composition entry
        self.groupBox_9 = QtWidgets.QGroupBox()
        self.groupBox_9.setObjectName("groupBox_9")
        flux_grid = QtWidgets.QGridLayout(self.groupBox_9)
        flux_grid.setSpacing(6)
        flux_grid.setColumnStretch(1, 1)
        flux_grid.setColumnStretch(3, 1)

        self.label_30 = QtWidgets.QLabel()
        self.label_30.setObjectName("label_30")
        self.fluxeName = QtWidgets.QLineEdit()
        self.fluxeName.setObjectName("fluxeName")
        self.addFluxeDataButton = QtWidgets.QPushButton()
        self.addFluxeDataButton.setObjectName("addFluxeDataButton")
        self.addFluxeDataButton.clicked.connect(self.addFluxeDataButtonClicked)
        flux_grid.addWidget(self.label_30, 0, 0)
        flux_grid.addWidget(self.fluxeName, 0, 1, 1, 2)
        flux_grid.addWidget(self.addFluxeDataButton, 0, 3)

        self.label_8 = QtWidgets.QLabel()
        self.label_8.setObjectName("label_8")
        self.fluxeCaO = QtWidgets.QLineEdit()
        self.fluxeCaO.setObjectName("fluxeCaO")
        self.label_9 = QtWidgets.QLabel()
        self.label_9.setObjectName("label_9")
        self.fluxeSiO2 = QtWidgets.QLineEdit()
        self.fluxeSiO2.setObjectName("fluxeSiO2")
        flux_grid.addWidget(self.label_8, 1, 0)
        flux_grid.addWidget(self.fluxeCaO, 1, 1)
        flux_grid.addWidget(self.label_9, 1, 2)
        flux_grid.addWidget(self.fluxeSiO2, 1, 3)

        self.label_22 = QtWidgets.QLabel()
        self.label_22.setObjectName("label_22")
        self.fluxeMgO = QtWidgets.QLineEdit()
        self.fluxeMgO.setObjectName("fluxeMgO")
        self.fluxeFe2O3label = QtWidgets.QLabel()
        self.fluxeFe2O3label.setObjectName("fluxeFe2O3label")
        self.fluxeFe2O3 = QtWidgets.QLineEdit()
        self.fluxeFe2O3.setObjectName("fluxeFe2O3")
        flux_grid.addWidget(self.label_22, 2, 0)
        flux_grid.addWidget(self.fluxeMgO, 2, 1)
        flux_grid.addWidget(self.fluxeFe2O3label, 2, 2)
        flux_grid.addWidget(self.fluxeFe2O3, 2, 3)

        self.label_31 = QtWidgets.QLabel()
        self.label_31.setObjectName("label_31")
        self.fluxeFeO = QtWidgets.QLineEdit()
        self.fluxeFeO.setObjectName("fluxeFeO")
        self.label_32 = QtWidgets.QLabel()
        self.label_32.setObjectName("label_32")
        self.fluxeMnO = QtWidgets.QLineEdit()
        self.fluxeMnO.setObjectName("fluxeMnO")
        flux_grid.addWidget(self.label_31, 3, 0)
        flux_grid.addWidget(self.fluxeFeO, 3, 1)
        flux_grid.addWidget(self.label_32, 3, 2)
        flux_grid.addWidget(self.fluxeMnO, 3, 3)

        self.label_33 = QtWidgets.QLabel()
        self.label_33.setObjectName("label_33")
        self.fluxeAl2O3 = QtWidgets.QLineEdit()
        self.fluxeAl2O3.setObjectName("fluxeAl2O3")
        self.label_34 = QtWidgets.QLabel()
        self.label_34.setObjectName("label_34")
        self.fluxeCaCO3 = QtWidgets.QLineEdit()
        self.fluxeCaCO3.setObjectName("fluxeCaCO3")
        flux_grid.addWidget(self.label_33, 4, 0)
        flux_grid.addWidget(self.fluxeAl2O3, 4, 1)
        flux_grid.addWidget(self.label_34, 4, 2)
        flux_grid.addWidget(self.fluxeCaCO3, 4, 3)

        self.label_35 = QtWidgets.QLabel()
        self.label_35.setObjectName("label_35")
        self.fluxeMgCO3 = QtWidgets.QLineEdit()
        self.fluxeMgCO3.setObjectName("fluxeMgCO3")
        flux_grid.addWidget(self.label_35, 5, 0)
        flux_grid.addWidget(self.fluxeMgCO3, 5, 1)

        left_layout.addWidget(self.groupBox_9)

        tab3_root.addWidget(left_panel, stretch=1)

        # --- Right panel: data-entry forms in a scroll area ---
        right_scroll = QtWidgets.QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        right_scroll.setMinimumWidth(440)
        right_scroll.viewport().setAutoFillBackground(False)

        right_container = QtWidgets.QWidget()
        right_container.setAttribute(Qt.WA_TranslucentBackground)
        right_vbox = QtWidgets.QVBoxLayout(right_container)
        right_vbox.setContentsMargins(0, 0, 4, 0)
        right_vbox.setSpacing(8)

        self.groupBox = QtWidgets.QGroupBox()
        self.groupBox.setObjectName("groupBox")
        gb_vbox = QtWidgets.QVBoxLayout(self.groupBox)
        gb_vbox.setSpacing(8)

        # steel
        self.groupBox_5 = QtWidgets.QGroupBox()
        self.groupBox_5.setObjectName("groupBox_5")
        steel_vbox = QtWidgets.QVBoxLayout(self.groupBox_5)
        steel_top = QtWidgets.QHBoxLayout()
        self.label_21 = QtWidgets.QLabel()
        self.label_21.setObjectName("label_21")
        self.steelName = QtWidgets.QLineEdit()
        self.steelName.setObjectName("steelName")
        self.addSteelDataButton = QtWidgets.QPushButton()
        self.addSteelDataButton.setObjectName("addSteelDataButton")
        self.addSteelDataButton.clicked.connect(self.addSteelData)
        steel_top.addWidget(self.label_21)
        steel_top.addWidget(self.steelName, stretch=1)
        steel_top.addWidget(self.addSteelDataButton)
        steel_vbox.addLayout(steel_top)

        self.groupBox_8 = QtWidgets.QGroupBox()
        self.groupBox_8.setObjectName("groupBox_8")
        steel_comp = QtWidgets.QGridLayout(self.groupBox_8)
        steel_comp.setSpacing(6)
        steel_comp.setColumnStretch(1, 1)
        steel_comp.setColumnStretch(3, 1)
        self.label_4 = QtWidgets.QLabel(); self.label_4.setObjectName("label_4")
        self.steelCarbon = QtWidgets.QLineEdit(); self.steelCarbon.setObjectName("steelCarbon")
        self.label_6 = QtWidgets.QLabel(); self.label_6.setObjectName("label_6")
        self.steelSerum = QtWidgets.QLineEdit(); self.steelSerum.setObjectName("steelSerum")
        steel_comp.addWidget(self.label_4, 0, 0)
        steel_comp.addWidget(self.steelCarbon, 0, 1)
        steel_comp.addWidget(self.label_6, 0, 2)
        steel_comp.addWidget(self.steelSerum, 0, 3)
        self.label_5 = QtWidgets.QLabel(); self.label_5.setObjectName("label_5")
        self.steelSilicon = QtWidgets.QLineEdit(); self.steelSilicon.setObjectName("steelSilicon")
        self.label_7 = QtWidgets.QLabel(); self.label_7.setObjectName("label_7")
        self.steelPhosphor = QtWidgets.QLineEdit(); self.steelPhosphor.setObjectName("steelPhosphor")
        steel_comp.addWidget(self.label_5, 1, 0)
        steel_comp.addWidget(self.steelSilicon, 1, 1)
        steel_comp.addWidget(self.label_7, 1, 2)
        steel_comp.addWidget(self.steelPhosphor, 1, 3)
        steel_vbox.addWidget(self.groupBox_8)
        gb_vbox.addWidget(self.groupBox_5)

        # scrap
        self.groupBox_3 = QtWidgets.QGroupBox()
        self.groupBox_3.setObjectName("groupBox_3")
        scrap_vbox = QtWidgets.QVBoxLayout(self.groupBox_3)
        scrap_top = QtWidgets.QHBoxLayout()
        self.label_11 = QtWidgets.QLabel(); self.label_11.setObjectName("label_11")
        self.scrapWeight = QtWidgets.QLineEdit(); self.scrapWeight.setObjectName("scrapWeight")
        self.addScrapDataButton = QtWidgets.QPushButton()
        self.addScrapDataButton.setObjectName("addScrapDataButton")
        self.addScrapDataButton.clicked.connect(self.addScrap)
        scrap_top.addWidget(self.label_11)
        scrap_top.addWidget(self.scrapWeight, stretch=1)
        scrap_top.addWidget(self.addScrapDataButton)
        scrap_vbox.addLayout(scrap_top)

        self.groupBox_7 = QtWidgets.QGroupBox()
        self.groupBox_7.setObjectName("groupBox_7")
        scrap_comp = QtWidgets.QGridLayout(self.groupBox_7)
        scrap_comp.setSpacing(6)
        scrap_comp.setColumnStretch(1, 1)
        scrap_comp.setColumnStretch(3, 1)
        self.label_12 = QtWidgets.QLabel(); self.label_12.setObjectName("label_12")
        self.scrapCarbon = QtWidgets.QLineEdit(); self.scrapCarbon.setObjectName("scrapCarbon")
        self.label_13 = QtWidgets.QLabel(); self.label_13.setObjectName("label_13")
        self.scrapSilicon = QtWidgets.QLineEdit(); self.scrapSilicon.setObjectName("scrapSilicon")
        scrap_comp.addWidget(self.label_12, 0, 0)
        scrap_comp.addWidget(self.scrapCarbon, 0, 1)
        scrap_comp.addWidget(self.label_13, 0, 2)
        scrap_comp.addWidget(self.scrapSilicon, 0, 3)
        self.label_14 = QtWidgets.QLabel(); self.label_14.setObjectName("label_14")
        self.scrapSerum = QtWidgets.QLineEdit(); self.scrapSerum.setObjectName("scrapSerum")
        self.label_15 = QtWidgets.QLabel(); self.label_15.setObjectName("label_15")
        self.scrapPhosphor = QtWidgets.QLineEdit(); self.scrapPhosphor.setObjectName("scrapPhosphor")
        scrap_comp.addWidget(self.label_14, 1, 0)
        scrap_comp.addWidget(self.scrapSerum, 1, 1)
        scrap_comp.addWidget(self.label_15, 1, 2)
        scrap_comp.addWidget(self.scrapPhosphor, 1, 3)
        self.label_25 = QtWidgets.QLabel(); self.label_25.setObjectName("label_25")
        self.scrapManganese = QtWidgets.QLineEdit(); self.scrapManganese.setObjectName("scrapManganese")
        scrap_comp.addWidget(self.label_25, 2, 0)
        scrap_comp.addWidget(self.scrapManganese, 2, 1)
        scrap_vbox.addWidget(self.groupBox_7)
        gb_vbox.addWidget(self.groupBox_3)

        # cast iron
        self.groupBox_4 = QtWidgets.QGroupBox()
        self.groupBox_4.setObjectName("groupBox_4")
        cast_vbox = QtWidgets.QVBoxLayout(self.groupBox_4)
        cast_top = QtWidgets.QHBoxLayout()
        self.label_10 = QtWidgets.QLabel(); self.label_10.setObjectName("label_10")
        self.castTemperature = QtWidgets.QLineEdit(); self.castTemperature.setObjectName("castTemperature")
        self.label_16 = QtWidgets.QLabel(); self.label_16.setObjectName("label_16")
        self.castWeight = QtWidgets.QLineEdit(); self.castWeight.setObjectName("castWeight")
        self.addCastButton = QtWidgets.QPushButton()
        self.addCastButton.setObjectName("addCastButton")
        self.addCastButton.clicked.connect(self.addCastData)
        cast_top.addWidget(self.label_10)
        cast_top.addWidget(self.castTemperature, stretch=1)
        cast_top.addWidget(self.label_16)
        cast_top.addWidget(self.castWeight, stretch=1)
        cast_top.addWidget(self.addCastButton)
        cast_vbox.addLayout(cast_top)

        self.groupBox_6 = QtWidgets.QGroupBox()
        self.groupBox_6.setObjectName("groupBox_6")
        cast_comp = QtWidgets.QGridLayout(self.groupBox_6)
        cast_comp.setSpacing(6)
        cast_comp.setColumnStretch(1, 1)
        cast_comp.setColumnStretch(3, 1)
        self.label_17 = QtWidgets.QLabel(); self.label_17.setObjectName("label_17")
        self.castCarbon = QtWidgets.QLineEdit(); self.castCarbon.setObjectName("castCarbon")
        self.label_18 = QtWidgets.QLabel(); self.label_18.setObjectName("label_18")
        self.castSilicon = QtWidgets.QLineEdit(); self.castSilicon.setObjectName("castSilicon")
        cast_comp.addWidget(self.label_17, 0, 0)
        cast_comp.addWidget(self.castCarbon, 0, 1)
        cast_comp.addWidget(self.label_18, 0, 2)
        cast_comp.addWidget(self.castSilicon, 0, 3)
        self.label_19 = QtWidgets.QLabel(); self.label_19.setObjectName("label_19")
        self.castSerum = QtWidgets.QLineEdit(); self.castSerum.setObjectName("castSerum")
        self.label_20 = QtWidgets.QLabel(); self.label_20.setObjectName("label_20")
        self.castPhosphor = QtWidgets.QLineEdit(); self.castPhosphor.setObjectName("castPhosphor")
        cast_comp.addWidget(self.label_19, 1, 0)
        cast_comp.addWidget(self.castSerum, 1, 1)
        cast_comp.addWidget(self.label_20, 1, 2)
        cast_comp.addWidget(self.castPhosphor, 1, 3)
        self.label_24 = QtWidgets.QLabel(); self.label_24.setObjectName("label_24")
        self.castManganese = QtWidgets.QLineEdit(); self.castManganese.setObjectName("castManganese")
        cast_comp.addWidget(self.label_24, 2, 0)
        cast_comp.addWidget(self.castManganese, 2, 1)
        cast_vbox.addWidget(self.groupBox_6)
        gb_vbox.addWidget(self.groupBox_4)

        right_vbox.addWidget(self.groupBox)
        right_vbox.addStretch()
        right_scroll.setWidget(right_container)
        tab3_root.addWidget(right_scroll, stretch=1)

        self.Factory.addTab(self.tab_3, "")

        # ── TAB 2: Сценарии ───────────────────────────────────────────────────
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        tab2_vbox = QtWidgets.QVBoxLayout(self.tab)
        tab2_vbox.setContentsMargins(8, 8, 8, 8)
        tab2_vbox.setSpacing(8)

        scen_hdr = QtWidgets.QHBoxLayout()
        self.tabelLabel_5 = QtWidgets.QLabel()
        self.tabelLabel_5.setObjectName("tabelLabel_5")
        self.tabelLabel_5.setFont(QtGui.QFont("Times New Roman", 14))
        scen_hdr.addWidget(self.tabelLabel_5)
        scen_hdr.addStretch()

        self.showTableForScenario = QtWidgets.QPushButton()
        self.showTableForScenario.setObjectName("showTableForScenario")
        self.showTableForScenario.clicked.connect(self.showScenario)
        scen_hdr.addWidget(self.showTableForScenario)

        self.exportScenario = QtWidgets.QPushButton()
        self.exportScenario.setObjectName("exportScenario")
        self.exportScenario.clicked.connect(self.exportScenarioFunc)
        scen_hdr.addWidget(self.exportScenario)
        tab2_vbox.addLayout(scen_hdr)

        self.tableWidgetFactory_2 = QtWidgets.QTableWidget()
        self.tableWidgetFactory_2.setObjectName("tableWidgetFactory_2")
        self.tableWidgetFactory_2.setColumnCount(0)
        self.tableWidgetFactory_2.setRowCount(0)
        self.tableWidgetFactory_2.setAlternatingRowColors(True)
        self.tableWidgetFactory_2.horizontalHeader().setStretchLastSection(True)
        self.tableWidgetFactory_2.cellClicked.connect(self.onCellClicked)
        tab2_vbox.addWidget(self.tableWidgetFactory_2, stretch=1)

        self.groupBox_13 = QtWidgets.QGroupBox()
        self.groupBox_13.setObjectName("groupBox_13")
        scen_form_hbox = QtWidgets.QHBoxLayout(self.groupBox_13)
        scen_form_hbox.setSpacing(8)

        scen_left_w = QtWidgets.QWidget()
        scen_left_vbox = QtWidgets.QVBoxLayout(scen_left_w)
        scen_left_vbox.setContentsMargins(0, 0, 0, 0)
        scen_left_vbox.setSpacing(6)

        scen_name_row = QtWidgets.QHBoxLayout()
        self.label_41 = QtWidgets.QLabel(); self.label_41.setObjectName("label_41")
        self.scenarioName = QtWidgets.QLineEdit(); self.scenarioName.setObjectName("scenarioName")
        scen_name_row.addWidget(self.label_41)
        scen_name_row.addWidget(self.scenarioName, stretch=1)
        scen_left_vbox.addLayout(scen_name_row)

        self.label_42 = QtWidgets.QLabel(); self.label_42.setObjectName("label_42")
        scen_left_vbox.addWidget(self.label_42)

        self.scenarioTask = QtWidgets.QPlainTextEdit()
        self.scenarioTask.setObjectName("scenarioTask")
        scen_left_vbox.addWidget(self.scenarioTask, stretch=1)

        scen_form_hbox.addWidget(scen_left_w, stretch=1)

        self.groupBox_15 = QtWidgets.QGroupBox()
        self.groupBox_15.setObjectName("groupBox_15")
        self.groupBox_15.setMinimumWidth(300)
        limits_grid = QtWidgets.QGridLayout(self.groupBox_15)
        limits_grid.setSpacing(8)
        limits_grid.setColumnStretch(1, 1)

        self.label_44 = QtWidgets.QLabel(); self.label_44.setWordWrap(True); self.label_44.setObjectName("label_44")
        self.MinSteelTempLimit = QtWidgets.QLineEdit(); self.MinSteelTempLimit.setObjectName("MinSteelTempLimit")
        limits_grid.addWidget(self.label_44, 0, 0)
        limits_grid.addWidget(self.MinSteelTempLimit, 0, 1)

        self.label_45 = QtWidgets.QLabel(); self.label_45.setWordWrap(True); self.label_45.setObjectName("label_45")
        self.SteelPhosphorLimit = QtWidgets.QLineEdit(); self.SteelPhosphorLimit.setObjectName("SteelPhosphorLimit")
        limits_grid.addWidget(self.label_45, 1, 0)
        limits_grid.addWidget(self.SteelPhosphorLimit, 1, 1)

        self.label_46 = QtWidgets.QLabel(); self.label_46.setWordWrap(True); self.label_46.setObjectName("label_46")
        self.SteelCarbonLimit = QtWidgets.QLineEdit(); self.SteelCarbonLimit.setObjectName("SteelCarbonLimit")
        limits_grid.addWidget(self.label_46, 2, 0)
        limits_grid.addWidget(self.SteelCarbonLimit, 2, 1)

        self.label_43 = QtWidgets.QLabel(); self.label_43.setObjectName("label_43")
        self.modeNameBox = QtWidgets.QComboBox(); self.modeNameBox.setObjectName("modeNameBox")
        limits_grid.addWidget(self.label_43, 3, 0)
        limits_grid.addWidget(self.modeNameBox, 3, 1)

        self.addScenarioButton_2 = QtWidgets.QPushButton()
        self.addScenarioButton_2.setObjectName("addScenarioButton_2")
        self.addScenarioButton_2.clicked.connect(self.addScenario)
        limits_grid.addWidget(self.addScenarioButton_2, 4, 0, 1, 2)

        scen_form_hbox.addWidget(self.groupBox_15)
        tab2_vbox.addWidget(self.groupBox_13)

        self.Factory.addTab(self.tab, "")

        # ── TAB 3: Пользователи ───────────────────────────────────────────────
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        tab4_hbox = QtWidgets.QHBoxLayout(self.tab_4)
        tab4_hbox.setContentsMargins(8, 8, 8, 8)
        tab4_hbox.setSpacing(8)

        # left: table viewer
        users_left_w = QtWidgets.QWidget()
        users_left_vbox = QtWidgets.QVBoxLayout(users_left_w)
        users_left_vbox.setContentsMargins(0, 0, 0, 0)
        users_left_vbox.setSpacing(6)

        users_hdr = QtWidgets.QHBoxLayout()
        self.tabelLabel_4 = QtWidgets.QLabel()
        self.tabelLabel_4.setObjectName("tabelLabel_4")
        self.tabelLabel_4.setFont(QtGui.QFont("Times New Roman", 14))
        users_hdr.addWidget(self.tabelLabel_4)

        self.choosenTableForUsers = QtWidgets.QComboBox()
        self.choosenTableForUsers.setObjectName("choosenTableForUsers")
        self.choosenTableForUsers.addItem("")
        self.choosenTableForUsers.addItem("")
        users_hdr.addWidget(self.choosenTableForUsers)

        self.showTableForUsers = QtWidgets.QPushButton()
        self.showTableForUsers.setObjectName("showTableForUsers")
        self.showTableForUsers.clicked.connect(self.showTableForUsersClick)
        users_hdr.addWidget(self.showTableForUsers)
        users_hdr.addStretch()
        users_left_vbox.addLayout(users_hdr)

        self.tableWidgetUsers = QtWidgets.QTableWidget()
        self.tableWidgetUsers.setObjectName("tableWidgetUsers")
        self.tableWidgetUsers.setColumnCount(0)
        self.tableWidgetUsers.setRowCount(0)
        self.tableWidgetUsers.setAlternatingRowColors(True)
        self.tableWidgetUsers.horizontalHeader().setStretchLastSection(True)
        users_left_vbox.addWidget(self.tableWidgetUsers, stretch=1)

        tab4_hbox.addWidget(users_left_w, stretch=1)

        # right: user management forms
        users_right_w = QtWidgets.QWidget()
        users_right_w.setMinimumWidth(280)
        users_right_vbox = QtWidgets.QVBoxLayout(users_right_w)
        users_right_vbox.setContentsMargins(0, 0, 0, 0)
        users_right_vbox.setSpacing(8)

        self.groupBox_2 = QtWidgets.QGroupBox()
        self.groupBox_2.setObjectName("groupBox_2")
        add_user_grid = QtWidgets.QGridLayout(self.groupBox_2)
        add_user_grid.setSpacing(8)
        add_user_grid.setColumnStretch(1, 1)

        _ufont = QtGui.QFont("Times New Roman", 12)
        self.label = QtWidgets.QLabel(); self.label.setFont(_ufont); self.label.setObjectName("label")
        self.LoginCreate = QtWidgets.QLineEdit(); self.LoginCreate.setObjectName("LoginCreate")
        add_user_grid.addWidget(self.label, 0, 0)
        add_user_grid.addWidget(self.LoginCreate, 0, 1)

        self.label_2 = QtWidgets.QLabel(); self.label_2.setFont(_ufont); self.label_2.setObjectName("label_2")
        self.PasswordCreate = QtWidgets.QLineEdit(); self.PasswordCreate.setObjectName("PasswordCreate")
        self.PasswordCreate.setEchoMode(QtWidgets.QLineEdit.Password)
        add_user_grid.addWidget(self.label_2, 1, 0)
        add_user_grid.addWidget(self.PasswordCreate, 1, 1)

        self.label_3 = QtWidgets.QLabel(); self.label_3.setFont(_ufont); self.label_3.setObjectName("label_3")
        self.UserRoleCreate = QtWidgets.QComboBox(); self.UserRoleCreate.setObjectName("UserRoleCreate")
        self.UserRoleCreate.addItem("")
        self.UserRoleCreate.addItem("")
        self.UserRoleCreate.addItem("")
        add_user_grid.addWidget(self.label_3, 2, 0)
        add_user_grid.addWidget(self.UserRoleCreate, 2, 1)

        self.AddUserButton = QtWidgets.QPushButton()
        self.AddUserButton.setObjectName("AddUserButton")
        self.AddUserButton.clicked.connect(self.insertDataIntoUsers)
        add_user_grid.addWidget(self.AddUserButton, 3, 0, 1, 2)

        users_right_vbox.addWidget(self.groupBox_2)

        self.groupBox_12 = QtWidgets.QGroupBox()
        self.groupBox_12.setObjectName("groupBox_12")
        upd_user_grid = QtWidgets.QGridLayout(self.groupBox_12)
        upd_user_grid.setSpacing(8)
        upd_user_grid.setColumnStretch(1, 1)

        self.label_29 = QtWidgets.QLabel(); self.label_29.setFont(_ufont); self.label_29.setObjectName("label_29")
        self.UserIdUpdate = QtWidgets.QComboBox(); self.UserIdUpdate.setObjectName("UserIdUpdate")
        upd_user_grid.addWidget(self.label_29, 0, 0)
        upd_user_grid.addWidget(self.UserIdUpdate, 0, 1)

        self.label_36 = QtWidgets.QLabel(); self.label_36.setFont(_ufont); self.label_36.setObjectName("label_36")
        self.LoginUpdate = QtWidgets.QLineEdit(); self.LoginUpdate.setObjectName("LoginUpdate")
        upd_user_grid.addWidget(self.label_36, 1, 0)
        upd_user_grid.addWidget(self.LoginUpdate, 1, 1)

        self.label_37 = QtWidgets.QLabel(); self.label_37.setFont(_ufont); self.label_37.setObjectName("label_37")
        self.UserRoleUpdate = QtWidgets.QComboBox(); self.UserRoleUpdate.setObjectName("UserRoleUpdate")
        self.UserRoleUpdate.addItem("")
        self.UserRoleUpdate.addItem("")
        self.UserRoleUpdate.addItem("")
        upd_user_grid.addWidget(self.label_37, 2, 0)
        upd_user_grid.addWidget(self.UserRoleUpdate, 2, 1)

        self.UpdateUserButton = QtWidgets.QPushButton()
        self.UpdateUserButton.setObjectName("UpdateUserButton")
        self.UpdateUserButton.clicked.connect(self.UpdateUser)
        upd_user_grid.addWidget(self.UpdateUserButton, 3, 0, 1, 2)

        users_right_vbox.addWidget(self.groupBox_12)

        sql_row = QtWidgets.QHBoxLayout()
        self.SQLQuery = QtWidgets.QLineEdit()
        self.SQLQuery.setObjectName("SQLQuery")
        sql_row.addWidget(self.SQLQuery, stretch=1)
        self.executeSqlbutton = QtWidgets.QPushButton()
        self.executeSqlbutton.setObjectName("executeSqlbutton")
        self.executeSqlbutton.clicked.connect(self.executeSqlQuery)
        sql_row.addWidget(self.executeSqlbutton)
        users_right_vbox.addLayout(sql_row)
        users_right_vbox.addStretch()

        tab4_hbox.addWidget(users_right_w)

        self.Factory.addTab(self.tab_4, "")

        # ── Menu & status bar ─────────────────────────────────────────────────
        AdminFom.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(AdminFom)
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
        self.menu_view = QtWidgets.QMenu(self.menubar)
        self.view_toggles = ViewTogglesBar()
        self.view_toggles.theme_toggle.theme_changed.connect(lambda _t: self.refresh_theme())
        self.view_toggles.language_toggle.language_changed.connect(
            lambda _l: self.refresh_language(AdminFom)
        )
        toggle_action = QtWidgets.QWidgetAction(AdminFom)
        toggle_action.setDefaultWidget(self.view_toggles)
        self.menu_view.addAction(toggle_action)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.menubar.addAction(self.menu_view.menuAction())

        manager().theme_changed.connect(lambda _t: self.refresh_theme())
        locale_manager().language_changed.connect(
            lambda _l: self.refresh_language(AdminFom)
        )

        self.retranslateUi(AdminFom)
        self.Factory.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(AdminFom)

        def _on_show(event):
            QtWidgets.QMainWindow.showEvent(AdminFom, event)
            self.refresh_theme()

        AdminFom.showEvent = _on_show
        self.refresh_theme()
        QtCore.QTimer.singleShot(0, self.refresh_theme)

    def retranslateUi(self, AdminFom):
        from i18n import tr as _translate
        AdminFom.setWindowTitle(_translate("AdminFom", "Добро пожаловать, администратор"))

        # Tab 1 — Промышленные данные
        self.tabelLabel_3.setText(_translate("AdminFom", "Таблица:"))
        self.showTableForFactory.setText(_translate("AdminFom", "Отобразить"))
        self.exportButton.setText(_translate("AdminFom", "Экспорт"))
        self.choosenTableForFactory.setItemText(0, _translate("AdminFom", "Режимы"))
        self.choosenTableForFactory.setItemText(1, _translate("AdminFom", "Сталь"))
        self.choosenTableForFactory.setItemText(2, _translate("AdminFom", "Состав стали"))
        self.choosenTableForFactory.setItemText(3, _translate("AdminFom", "Чугун"))
        self.choosenTableForFactory.setItemText(4, _translate("AdminFom", "Состав чугуна"))
        self.choosenTableForFactory.setItemText(5, _translate("AdminFom", "Лом"))
        self.choosenTableForFactory.setItemText(6, _translate("AdminFom", "Состав лома"))
        self.choosenTableForFactory.setItemText(7, _translate("AdminFom", "Флюсы"))

        self.groupBox_10.setTitle(_translate("AdminFom", "Добавление режима"))
        self.label_28.setText(_translate("AdminFom", "Название:"))
        self.label_23.setText(_translate("AdminFom", "Сталь:"))
        self.label_26.setText(_translate("AdminFom", "Чугун:"))
        self.label_27.setText(_translate("AdminFom", "Лом:"))
        self.addModeButton.setText(_translate("AdminFom", "Добавить"))

        self.groupBox_11.setTitle(_translate("AdminFom", "Флюсы в режиме"))
        self.tip_flyusa_label.setText(_translate("AdminFom", "Тип флюса:"))
        _hitem = self.FluxeTable.horizontalHeaderItem(0)
        _hitem.setText(_translate("AdminFom", "Тип флюса"))

        self.groupBox_9.setTitle(_translate("AdminFom", "Добавление флюса"))
        self.label_30.setText(_translate("AdminFom", "Название:"))
        self.addFluxeDataButton.setText(_translate("AdminFom", "Добавить"))
        self.label_8.setText(_translate("AdminFom", "CaO:"))
        self.label_9.setText(_translate("AdminFom", "SiO2:"))
        self.label_22.setText(_translate("AdminFom", "MgO:"))
        self.fluxeFe2O3label.setText(_translate("AdminFom", "Fe2O3:"))
        self.label_31.setText(_translate("AdminFom", "FeO:"))
        self.label_32.setText(_translate("AdminFom", "MnO:"))
        self.label_33.setText(_translate("AdminFom", "Al2O3:"))
        self.label_34.setText(_translate("AdminFom", "CaCO3:"))
        self.label_35.setText(_translate("AdminFom", "MgCO3:"))

        self.groupBox.setTitle(_translate("AdminFom", "Промышленные данные"))
        self.groupBox_5.setTitle(_translate("AdminFom", "Добавление данных о стали"))
        self.label_21.setText(_translate("AdminFom", "Название:"))
        self.addSteelDataButton.setText(_translate("AdminFom", "Добавить"))
        self.groupBox_8.setTitle(_translate("AdminFom", "Химический состав"))
        self.label_4.setText(_translate("AdminFom", "Углерод (C):"))
        self.label_6.setText(_translate("AdminFom", "Сера (S):"))
        self.label_5.setText(_translate("AdminFom", "Кремний (Si):"))
        self.label_7.setText(_translate("AdminFom", "Фосфор (P):"))

        self.groupBox_3.setTitle(_translate("AdminFom", "Добавление данных о ломе"))
        self.label_11.setText(_translate("AdminFom", "Масса (Т):"))
        self.addScrapDataButton.setText(_translate("AdminFom", "Добавить"))
        self.groupBox_7.setTitle(_translate("AdminFom", "Химический состав"))
        self.label_12.setText(_translate("AdminFom", "Углерод (C):"))
        self.label_13.setText(_translate("AdminFom", "Кремний (Si):"))
        self.label_14.setText(_translate("AdminFom", "Сера (S):"))
        self.label_15.setText(_translate("AdminFom", "Фосфор (P):"))
        self.label_25.setText(_translate("AdminFom", "Марганец (Mn):"))

        self.groupBox_4.setTitle(_translate("AdminFom", "Добавление данных о чугуне"))
        self.label_10.setText(_translate("AdminFom", "Температура (℃):"))
        self.label_16.setText(_translate("AdminFom", "Масса (Т):"))
        self.addCastButton.setText(_translate("AdminFom", "Добавить"))
        self.groupBox_6.setTitle(_translate("AdminFom", "Химический состав"))
        self.label_17.setText(_translate("AdminFom", "Углерод (C):"))
        self.label_18.setText(_translate("AdminFom", "Кремний (Si):"))
        self.label_19.setText(_translate("AdminFom", "Сера (S):"))
        self.label_20.setText(_translate("AdminFom", "Фосфор (P):"))
        self.label_24.setText(_translate("AdminFom", "Марганец (Mn):"))

        self.Factory.setTabText(self.Factory.indexOf(self.tab_3), _translate("AdminFom", "Промышленные данные"))

        # Tab 2 — Сценарии
        self.tabelLabel_5.setText(_translate("AdminFom", "Сценарии"))
        self.showTableForScenario.setText(_translate("AdminFom", "Обновить"))
        self.exportScenario.setText(_translate("AdminFom", "Экспорт"))
        self.groupBox_13.setTitle(_translate("AdminFom", "Добавление сценария"))
        self.label_41.setText(_translate("AdminFom", "Наименование:"))
        self.label_42.setText(_translate("AdminFom", "Задача:"))
        self.groupBox_15.setTitle(_translate("AdminFom", "Ограничения"))
        self.label_44.setText(_translate("AdminFom", "Минимальная температура стали [℃]:"))
        self.label_45.setText(_translate("AdminFom", "Содержание фосфора в стали [%масс]:"))
        self.label_46.setText(_translate("AdminFom", "Содержание углерода в стали [%масс]:"))
        self.label_43.setText(_translate("AdminFom", "Режим:"))
        self.addScenarioButton_2.setText(_translate("AdminFom", "Добавить"))
        self.Factory.setTabText(self.Factory.indexOf(self.tab), _translate("AdminFom", "Сценарии"))

        # Tab 3 — Пользователи
        self.tabelLabel_4.setText(_translate("AdminFom", "Таблица:"))
        self.choosenTableForUsers.setItemText(0, _translate("AdminFom", "Пользователи"))
        self.choosenTableForUsers.setItemText(1, _translate("AdminFom", "Роли"))
        self.showTableForUsers.setText(_translate("AdminFom", "Отобразить"))

        self.groupBox_2.setTitle(_translate("AdminFom", "Добавление учётной записи"))
        self.label.setText(_translate("AdminFom", "Логин:"))
        self.label_2.setText(_translate("AdminFom", "Пароль:"))
        self.label_3.setText(_translate("AdminFom", "Роль:"))
        self.UserRoleCreate.setCurrentText(_translate("AdminFom", "Оператор"))
        self.UserRoleCreate.setItemText(0, _translate("AdminFom", "Оператор"))
        self.UserRoleCreate.setItemText(1, _translate("AdminFom", "Администратор"))
        self.UserRoleCreate.setItemText(2, _translate("AdminFom", "Разработчик модели"))
        self.AddUserButton.setText(_translate("AdminFom", "Добавить"))

        self.groupBox_12.setTitle(_translate("AdminFom", "Изменение учётной записи"))
        self.label_29.setText(_translate("AdminFom", "Логин:"))
        self.label_36.setText(_translate("AdminFom", "Новый логин:"))
        self.label_37.setText(_translate("AdminFom", "Роль:"))
        self.UserRoleUpdate.setCurrentText(_translate("AdminFom", "Оператор"))
        self.UserRoleUpdate.setItemText(0, _translate("AdminFom", "Оператор"))
        self.UserRoleUpdate.setItemText(1, _translate("AdminFom", "Администратор"))
        self.UserRoleUpdate.setItemText(2, _translate("AdminFom", "Разработчик модели"))
        self.UpdateUserButton.setText(_translate("AdminFom", "Изменить"))

        self.SQLQuery.setPlaceholderText(_translate("AdminFom", "SQL запрос…"))
        self.executeSqlbutton.setText(_translate("AdminFom", "Выполнить"))
        self.Factory.setTabText(self.Factory.indexOf(self.tab_4), _translate("AdminFom", "Пользователи"))

        # Menu
        self.menu.setTitle(_translate("AdminFom", "Файл"))
        self.menu_2.setTitle(_translate("AdminFom", "Справка"))
        self.menu_view.setTitle(_translate("AdminFom", "Вид"))
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
    from theme_settings import get_theme

    app = QtWidgets.QApplication(sys.argv)
    app_theme.apply_to_application(app, get_theme())
    AdminFom = QtWidgets.QMainWindow()
    ui = Ui_AdminFom()
    ui.setupUi(AdminFom)
    AdminFom.show()
    sys.exit(app.exec_())
