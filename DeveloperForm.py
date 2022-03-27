from PyQt5 import QtCore, QtGui, QtWidgets
import mysql.connector as mc
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QTableWidgetItem

class Ui_Form(object):

    def showChoosenTable(self):
        try:
            chTable = self.choosenTable.currentText()
            query = "SELECT * FROM "
            if(chTable == "Режимы"):
                query += "Mode;"
                self.tableWidget.setColumnCount(6)
                self.tableWidget.setHorizontalHeaderLabels(["Номер", "Название", "Номер стали", "Номер лома", "Номер чугуна", "Мат параметры"])
            elif(chTable == "Сталь"):
                query += "SteelData;"
                self.tableWidget.setColumnCount(3)
                self.tableWidget.setHorizontalHeaderLabels(["Номер", "Марка", "Номер состава"])
            elif (chTable == "Состав стали"):
                query += "SteelComposition;"
                self.tableWidget.setColumnCount(5)
                self.tableWidget.setHorizontalHeaderLabels(["Номер", "Углерод", "Сера", "Фосфор", "Кремний"])
            elif (chTable == "Чугун"):
                query += "CastSteelData;"
                self.tableWidget.setColumnCount(4)
                self.tableWidget.setHorizontalHeaderLabels(["Номер", "Масса", "Температура", "Номер состава"])
            elif (chTable == "Состав чугуна"):
                query += "CastSteelComposition;"
                self.tableWidget.setColumnCount(6)
                self.tableWidget.setHorizontalHeaderLabels(["Номер", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == "Лом"):
                query += "ScrapData;"
                self.tableWidget.setColumnCount(3)
                self.tableWidget.setHorizontalHeaderLabels(["Номер", "Масса", "Номер состава"])
            elif (chTable == "Состав лома"):
                query += "ScrapComposition;"
                self.tableWidget.setColumnCount(6)
                self.tableWidget.setHorizontalHeaderLabels(["Номер", "Углерод", "Сера", "Фосфор", "Кремний", "Марганец"])
            elif (chTable == "Флюсы"):
                query += "FluxeData;"
                self.tableWidget.setColumnCount(3)
                self.tableWidget.setHorizontalHeaderLabels(["Номер", "Название", "Номер состава"])
                # self.tableWidget.setHorizontalHeaderLabels(["Номер", "CaO", "SiO2", "MgO", "Fe2O3", "FeO", "MnO", "Al2O3", "CaCO3", "MgCO3"])

            DB = mc.connect(
                host="localhost",
                user="root",
                password="root",
                database="regimdata"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            self.tableWidget.setRowCount(0)

            for row_number, row_data in enumerate(result):
                self.tableWidget.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(data)))

        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные!")
            #msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def getAllSteel(self):
        try:
            query = "select steelname from steeldata;"
            DB = mc.connect(
                host="localhost",
                user="root",
                password="root",
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
                host="localhost",
                user="root",
                password="root",
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
                host="localhost",
                user="root",
                password="root",
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
                host="localhost",
                user="root",
                password="root",
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
                host="localhost",
                user="root",
                password="root",
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
            msg = QMessageBox()
            self.getAllCast()
            msg.setWindowTitle("Успех")
            msg.setText("Выполнено")
            msg.setInformativeText("Запись успешно добавлена!")
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
                host="localhost",
                user="root",
                password="root",
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
            msg.setWindowTitle("Успех")
            msg.setText("Выполнено")
            msg.setInformativeText("Запись успешно добавлена!")
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
                host="localhost",
                user="root",
                password="root",
                database="regimdata"
            )
            query = "select idsteeldata from steeldata where steelname = '" + self.modeSteelName.currentText() + "'"
            mycursor = DB.cursor()
            mycursor.execute(query)
            idSteel = mycursor.fetchone()[0]
            mycursor.close()

            query = "insert into mode (ModeName, SteelData_idSteelData, ScrapData_idScrapData, CastSteelData_idCastSteelData, MathSettings_idMathSettings) values(%s, %s, %s, %s, 1)"

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

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(902, 540)
        Form.setMinimumSize(QtCore.QSize(872, 540))
        Form.setMaximumSize(QtCore.QSize(1208, 540))
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.tableWidget.setGeometry(QtCore.QRect(10, 60, 391, 461))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.choosenTable = QtWidgets.QComboBox(Form)
        self.choosenTable.setGeometry(QtCore.QRect(10, 30, 141, 22))
        self.choosenTable.setObjectName("choosenTable")
        self.choosenTable.addItem("")
        self.choosenTable.addItem("")
        self.choosenTable.addItem("")
        self.choosenTable.addItem("")
        self.choosenTable.addItem("")
        self.choosenTable.addItem("")
        self.choosenTable.addItem("")
        self.choosenTable.addItem("")
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(10, 10, 91, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.groupBox = QtWidgets.QGroupBox(Form)
        self.groupBox.setGeometry(QtCore.QRect(410, 50, 481, 111))
        self.groupBox.setObjectName("groupBox")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(270, 20, 51, 20))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.modeSteelName = QtWidgets.QComboBox(self.groupBox)
        self.modeSteelName.setGeometry(QtCore.QRect(330, 20, 131, 22))
        self.modeSteelName.setObjectName("modeSteelName")
        self.addModeButton = QtWidgets.QPushButton(self.groupBox)
        self.addModeButton.setGeometry(QtCore.QRect(380, 80, 81, 23))
        self.addModeButton.setObjectName("addModeButton")
        self.addModeButton.clicked.connect(self.addMode)
        self.modeCastSteel = QtWidgets.QComboBox(self.groupBox)
        self.modeCastSteel.setGeometry(QtCore.QRect(90, 50, 131, 22))
        self.modeCastSteel.setObjectName("modeCastSteel")
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(10, 50, 51, 20))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.modeScrap = QtWidgets.QComboBox(self.groupBox)
        self.modeScrap.setGeometry(QtCore.QRect(330, 50, 131, 22))
        self.modeScrap.setObjectName("modeScrap")
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setGeometry(QtCore.QRect(270, 50, 51, 20))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.widget = QtWidgets.QWidget(self.groupBox)
        self.widget.setGeometry(QtCore.QRect(10, 20, 209, 22))
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.widget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.modeName = QtWidgets.QLineEdit(self.widget)
        self.modeName.setObjectName("modeName")
        self.horizontalLayout.addWidget(self.modeName)
        self.displayTableButton = QtWidgets.QPushButton(Form)
        self.displayTableButton.setGeometry(QtCore.QRect(160, 30, 81, 23))
        self.displayTableButton.setObjectName("displayTableButton")
        self.displayTableButton.clicked.connect(self.showChoosenTable)
        self.groupBox_2 = QtWidgets.QGroupBox(Form)
        self.groupBox_2.setGeometry(QtCore.QRect(410, 170, 301, 161))
        self.groupBox_2.setObjectName("groupBox_2")
        self.addScrapDataButton = QtWidgets.QPushButton(self.groupBox_2)
        self.addScrapDataButton.setGeometry(QtCore.QRect(210, 20, 81, 23))
        self.addScrapDataButton.setObjectName("addScrapDataButton")
        self.addScrapDataButton.clicked.connect(self.addScrap)
        self.label_11 = QtWidgets.QLabel(self.groupBox_2)
        self.label_11.setGeometry(QtCore.QRect(10, 20, 101, 16))
        self.label_11.setObjectName("label_11")
        self.scrapWeight = QtWidgets.QLineEdit(self.groupBox_2)
        self.scrapWeight.setGeometry(QtCore.QRect(70, 20, 81, 20))
        self.scrapWeight.setText("")
        self.scrapWeight.setObjectName("scrapWeight")
        self.groupBox_7 = QtWidgets.QGroupBox(self.groupBox_2)
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
        self.groupBox_3 = QtWidgets.QGroupBox(Form)
        self.groupBox_3.setGeometry(QtCore.QRect(410, 330, 301, 191))
        self.groupBox_3.setObjectName("groupBox_3")
        self.castTemperature = QtWidgets.QLineEdit(self.groupBox_3)
        self.castTemperature.setGeometry(QtCore.QRect(110, 20, 81, 20))
        self.castTemperature.setText("")
        self.castTemperature.setObjectName("castTemperature")
        self.label_10 = QtWidgets.QLabel(self.groupBox_3)
        self.label_10.setGeometry(QtCore.QRect(10, 20, 101, 16))
        self.label_10.setObjectName("label_10")
        self.label_16 = QtWidgets.QLabel(self.groupBox_3)
        self.label_16.setGeometry(QtCore.QRect(10, 50, 101, 16))
        self.label_16.setObjectName("label_16")
        self.castWeight = QtWidgets.QLineEdit(self.groupBox_3)
        self.castWeight.setGeometry(QtCore.QRect(110, 50, 81, 20))
        self.castWeight.setText("")
        self.castWeight.setObjectName("castWeight")
        self.groupBox_6 = QtWidgets.QGroupBox(self.groupBox_3)
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
        self.addCastButton = QtWidgets.QPushButton(self.groupBox_3)
        self.addCastButton.setGeometry(QtCore.QRect(200, 30, 81, 23))
        self.addCastButton.setObjectName("addCastButton")
        self.addCastButton.clicked.connect(self.addCastData)
        self.groupBox_10 = QtWidgets.QGroupBox(Form)
        self.groupBox_10.setGeometry(QtCore.QRect(720, 170, 171, 261))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_10.setFont(font)
        self.groupBox_10.setFlat(False)
        self.groupBox_10.setCheckable(False)
        self.groupBox_10.setObjectName("groupBox_10")
        self.FluxeTable = QtWidgets.QTableWidget(self.groupBox_10)
        self.FluxeTable.setGeometry(QtCore.QRect(10, 70, 151, 151))
        self.FluxeTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.FluxeTable.setObjectName("FluxeTable")
        self.FluxeTable.setColumnCount(1)
        self.FluxeTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.FluxeTable.setHorizontalHeaderItem(0, item)
        self.AddFluxeButton = QtWidgets.QPushButton(self.groupBox_10)
        self.AddFluxeButton.setGeometry(QtCore.QRect(100, 230, 31, 21))
        self.AddFluxeButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/add.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.AddFluxeButton.setIcon(icon)
        self.AddFluxeButton.setObjectName("AddFluxeButton")
        self.AddFluxeButton.clicked.connect(self.AddFluxeButtonClicked)
        self.FluxeType = QtWidgets.QComboBox(self.groupBox_10)
        self.FluxeType.setGeometry(QtCore.QRect(10, 40, 141, 22))
        self.FluxeType.setEditable(False)
        self.FluxeType.setObjectName("FluxeType")
        self.RemoveFluxeButton = QtWidgets.QPushButton(self.groupBox_10)
        self.RemoveFluxeButton.setGeometry(QtCore.QRect(130, 230, 31, 21))
        self.RemoveFluxeButton.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/remove.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RemoveFluxeButton.setIcon(icon1)
        self.RemoveFluxeButton.setObjectName("RemoveFluxeButton")
        self.RemoveFluxeButton.clicked.connect(self.removeFluxeButtonClicked)
        self.tip_flyusa_label = QtWidgets.QLabel(self.groupBox_10)
        self.tip_flyusa_label.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.tip_flyusa_label.setObjectName("tip_flyusa_label")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Добро пожаловать, разработчик модели"))
        self.choosenTable.setItemText(0, _translate("Form", "Режимы"))
        self.choosenTable.setItemText(1, _translate("Form", "Сталь"))
        self.choosenTable.setItemText(2, _translate("Form", "Состав стали"))
        self.choosenTable.setItemText(3, _translate("Form", "Чугун"))
        self.choosenTable.setItemText(4, _translate("Form", "Состав чугуна"))
        self.choosenTable.setItemText(5, _translate("Form", "Лом"))
        self.choosenTable.setItemText(6, _translate("Form", "Состав лома"))
        self.choosenTable.setItemText(7, _translate("Form", "Флюсы"))
        self.label.setText(_translate("Form", "Таблица:"))
        self.groupBox.setTitle(_translate("Form", "Добавление режима"))
        self.label_3.setText(_translate("Form", "Сталь:"))
        self.addModeButton.setText(_translate("Form", "Добавить"))
        self.label_4.setText(_translate("Form", "Чугун:"))
        self.label_5.setText(_translate("Form", "Лом:"))
        self.label_2.setText(_translate("Form", "Название:"))
        self.displayTableButton.setText(_translate("Form", "Отобразить"))
        self.groupBox_2.setTitle(_translate("Form", "Добавление данных о ломе"))
        self.addScrapDataButton.setText(_translate("Form", "Добавить"))
        self.label_11.setText(_translate("Form", "Масса (Т):"))
        self.groupBox_7.setTitle(_translate("Form", "Химический состав"))
        self.label_12.setText(_translate("Form", "Углерод (C):"))
        self.label_13.setText(_translate("Form", "Кремний (Si):"))
        self.label_14.setText(_translate("Form", "Сера (S):"))
        self.label_15.setText(_translate("Form", "Фосфор (P):"))
        self.label_25.setText(_translate("Form", "Марганец (Mn):"))
        self.groupBox_3.setTitle(_translate("Form", "Добавление данных о чугуне"))
        self.label_10.setText(_translate("Form", "Температура (℃):"))
        self.label_16.setText(_translate("Form", "Масса (Т):"))
        self.groupBox_6.setTitle(_translate("Form", "Химический состав"))
        self.label_17.setText(_translate("Form", "Углерод (C):"))
        self.label_18.setText(_translate("Form", "Кремний (Si):"))
        self.label_19.setText(_translate("Form", "Сера (S):"))
        self.label_20.setText(_translate("Form", "Фосфор (P):"))
        self.label_24.setText(_translate("Form", "Марганец (Mn):"))
        self.addCastButton.setText(_translate("Form", "Добавить"))
        self.groupBox_10.setTitle(_translate("Form", "Флюсы в режиме"))
        item = self.FluxeTable.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Тип флюса"))
        self.tip_flyusa_label.setText(_translate("Form", "Тип флюса:"))
        self.getFluxes()
        self.getAllScrap()
        self.getAllSteel()
        self.getAllCast()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
