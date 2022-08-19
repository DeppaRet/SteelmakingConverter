from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView, QFileDialog
import mysql.connector as mc
from PyQt5.QtWidgets import QMessageBox
import AboutForm
from tkinter import *
from tkinter import filedialog
from configparser import ConfigParser
# import numpy as np
# import tensorflow as tf
# from keras import models
# from keras.applications.densenet import layers
# from tensorflow import keras
# import matplotlib.pyplot as plt
# import sklearn as sk
# from sklearn import preprocessing

metalChargeCalcked = False
tableCalcked = False
slagCalcked = False
blastCalcked = False
materialBalanceCalcked = False
heatBalanceCalcked = False
DBhost = "localhost"
DBlogin = "root"
DBpass = "root"
parser = ConfigParser()


class FluxeComposition(object):
    name = "Флюс"
    fluxeCaO = 0.0
    fluxeSiO2 = 0.0
    fluxeMgO = 0.0
    fluxeFe2O3 = 0.0
    fluxeFeO = 0.0
    fluxeAl2O3 = 0.0
    fluxeCaCO3 = 0.0
    fluxeMgCO3 = 0.0
    fluxeWeight = 0.0

listOfNamesForClass = ['fluxe1', 'fluxe2', 'fluxe3', 'fluxe4', 'fluxe5', 'fluxe6', 'fluxe7', 'fluxe8',
                               'fluxe9', 'fluxe10','fluxe11','fluxe12','fluxe13','fluxe14','fluxe15', 'fluxe16']
class Ui_OperatorForm(object):

    def getSettings(self):
        parser.read('dev.ini')
        global DBhost
        DBhost = (str(parser.get('DBsettings', 'DBhost')))
        global DBlogin
        DBlogin = (str(parser.get('DBsettings', 'login')))
        global DBpass
        DBpass = (str(parser.get('DBsettings', 'password')))

    def getModes(self):
        try:
            query = "select ModeName from mode;"
            DB = mc.connect(
                host = DBhost, # host="192.168.51.179" user="root", password="root",
                user = DBlogin,
                password = DBpass,
                database="regimdata"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            for row_number, row_data in enumerate(result):
                for column_number, data in enumerate(row_data):
                    self.ModeComboBox.addItem((str(data)))

            query = "select Name from ferroalloy;"
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="FerroalloyDB"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            for row_number, row_data in enumerate(result):
                for column_number, data in enumerate(row_data):
                    self.FeroType.addItem((str(data)))

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


    def chooseMods(self):
        try:

            currentMode = self.ModeComboBox.currentText()
            query = "select SteelData_idSteelData from mode where ModeName = '" + currentMode + "';"
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            steelId = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            steelId = mycursor.fetchone()[0]
            mycursor.close()

            query = "select ScrapData_idScrapData from mode where ModeName = '" + currentMode + "';"
            scrapId = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            scrapId = mycursor.fetchone()[0]
            mycursor.close()

            query = "select CastSteelData_idCastSteelData from mode where ModeName = '" + currentMode + "';"
            castId = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            castId = mycursor.fetchone()[0]
            mycursor.close()

            query = "select idMode from mode where ModeName = '" + currentMode + "';"
            modeId = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            modeId = mycursor.fetchone()[0]
            mycursor.close()

            query = "select * from steelcomposition where idSteelComposition = (select SteelComposition_idSteelComposition from steeldata where idSteelData = " + str(steelId) + ");"
            mycursor = DB.cursor()
            mycursor.execute(query)
            steelComposition = mycursor.fetchall()
            self.steelCarbon.setText(str(steelComposition[0][1]))
            self.steelSerum.setText(str(steelComposition[0][2]))
            self.steelPhosphor.setText(str(steelComposition[0][3]))
            self.steelSilicon.setText(str(steelComposition[0][4]))
            self.steelManganese.setText(str(steelComposition[0][5]))
            mycursor.close()

            query = "select * from caststeelcomposition where idCastSteelComposition = (select CastSteelComposition_idCastSteelComposition from caststeeldata where idCastSteelData = "+ str(castId) + ");"
            mycursor = DB.cursor()
            mycursor.execute(query)
            castComposition = mycursor.fetchall()
            self.castCarbon.setText(str(castComposition[0][1]))
            self.castSerum.setText(str(castComposition[0][2]))
            self.castPhosphor.setText(str(castComposition[0][3]))
            self.castSilicon.setText(str(castComposition[0][4]))
            self.castManganese.setText(str(castComposition[0][5]))

            query = "select CastSteelWeight, CastSteelTemperature from caststeeldata where idCastSteelData = " + str(castId) + ";"
            mycursor.execute(query)
            castData = mycursor.fetchall()
            self.castWeight.setText(str(castData[0][0]))
            self.castTemperature.setText(str(castData[0][1]))

            query = "select * from scrapcomposition where idScrapComposition = (select ScrapComposition_idScrapComposition from scrapdata where idScrapData = "+ str(scrapId) +");"
            mycursor.execute(query)
            scrapData = mycursor.fetchall()
            self.scrapCarbon.setText(str(scrapData[0][1]))
            self.scrapSerum.setText(str(scrapData[0][2]))
            self.scrapPhosphor.setText(str(scrapData[0][3]))
            self.scrapSilicon.setText(str(scrapData[0][4]))
            self.scrapManganese.setText(str(scrapData[0][5]))

            query = "select ScrapWeight from scrapdata where idScrapData = " + str(scrapId) +";"
            mycursor.execute(query)
            scrapWeight = mycursor.fetchall()
            self.scrapWeight.setText(str(scrapWeight[0][0]))
            mycursor.close()
            DB.close()
            self.getFluxeInMode(modeId)

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

    def getFluxeInMode(self, modeId):
        self.FluxeTable.setRowCount(0)
        DB = mc.connect(
            host=DBhost,  # host="192.168.51.179" user="root", password="root",
            user=DBlogin,
            password=DBpass,
            database="regimdata"
        )
        query = "select FluxeData_idFluxeData from fluxedata_has_mode where Mode_idMode = " + str(modeId) + ";"
        mycursor = DB.cursor()
        mycursor.execute(query)
        fluxes = mycursor.fetchall()
        if len(fluxes) != 0:
            for i in range(len(fluxes)):
                query = "select FluxeName from fluxedata where idFluxeData = " + str(fluxes[i][0]) +";"
                mycursor.execute(query)
                currentFluxe = mycursor.fetchone()
                rows = self.FluxeTable.rowCount()
                text = currentFluxe[0]
                self.FluxeTable.insertRow(rows)
                self.FluxeTable.setItem(rows, 0, QTableWidgetItem(text))
                query = "select fluxeweight from fluxedata_has_mode where FluxeData_idFluxeData = " + str(fluxes[i][0]) + " AND Mode_idMode = " + str(modeId) + ";"
                mycursor.execute(query)
                weights = mycursor.fetchone()
                isempty = not all(weights)
                if isempty:
                    continue

                text = str(weights[0])
                self.FluxeTable.setItem(rows, 1, QTableWidgetItem(text))
                k = 0
        DB.close()

    def calcMetalChargeClicked(self):
        try:
            castSteelWeightValue = float(self.castWeight.text())
            castSteelTemperatureValue = float(self.castTemperature.text())
            castSteelCarbonValue = float(self.castCarbon.text())
            castSteelSerumValue = float(self.castSerum.text())
            castSteelSiliconValue = float(self.castSilicon.text())
            castSteelPhosphorValue = float(self.castPhosphor.text())
            castSteelManganeseValue = float(self.castManganese.text())

            scrapCarbonValue = float(self.scrapCarbon.text())
            scrapSerumValue = float(self.scrapSerum.text())
            scrapSiliconValue = float(self.scrapSilicon.text())
            scrapPhosphorValue = float(self.scrapPhosphor.text())
            scrapWeightValue = float(self.scrapWeight.text())
            scrapManganeseValue = float(self.scrapManganese.text())

            totalWeightValue = castSteelWeightValue + scrapWeightValue

            carbonChem = (castSteelCarbonValue * castSteelWeightValue + scrapCarbonValue * scrapWeightValue)/totalWeightValue
            chemSerum = (castSteelSerumValue * castSteelWeightValue + scrapSerumValue * scrapWeightValue)/totalWeightValue
            chemPhosphor = (castSteelPhosphorValue * castSteelWeightValue + scrapPhosphorValue * scrapWeightValue)/totalWeightValue
            chemSilicon = (castSteelSiliconValue * castSteelWeightValue + scrapSiliconValue * scrapWeightValue)/totalWeightValue
            chemManganese = (castSteelManganeseValue * castSteelWeightValue + scrapManganeseValue * scrapWeightValue)/totalWeightValue

            # carbonChem = (castSteelCarbonValue * castSteelWeightValue + scrapCarbonValue * scrapWeightValue) / totalWeightValue
            # chemSerum = (castSteelSerumValue * castSteelWeightValue + scrapSerumValue * scrapWeightValue) / totalWeightValue
            # chemPhosphor = (castSteelPhosphorValue * castSteelWeightValue + scrapPhosphorValue * scrapWeightValue) / totalWeightValue
            # chemSilicon = (castSteelSiliconValue * castSteelWeightValue + scrapSiliconValue * scrapWeightValue) / totalWeightValue
            # chemManganese = (castSteelManganeseValue * castSteelWeightValue + scrapManganeseValue * scrapWeightValue) / totalWeightValue

            self.MetalCharge.setText(str(round(totalWeightValue, 3)))
            self.ChemCarbon.setText(str(round(carbonChem, 3)))
            self.ChemSerum.setText(str(round(chemSerum,3)))
            self.ChemPhosphor.setText(str(round(chemPhosphor,3)))
            self.ChemManganese.setText(str(round(chemManganese,3)))
            self.ChemSilicon.setText(str(round(chemSilicon,3)))
            global metalChargeCalcked
            metalChargeCalcked = True

        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        return

    def calcTableClick(self):
        try:
            global metalChargeCalcked
            if (metalChargeCalcked == False):
                self.calcMetalChargeClicked()
                metalChargeCalcked = True
            chemCarbonValue = float(self.ChemCarbon.text())
            chemSerumValue = float(self.ChemSerum.text())
            chemPhosphorValue = float(self.ChemPhosphor.text())
            chemManganesevalue = float(self.ChemManganese.text())
            chemSiliconValue = float(self.ChemSilicon.text())

            self.OxidationTable.setItem(0, 0, QTableWidgetItem(str(round(chemCarbonValue, 3))))
            self.OxidationTable.setItem(0, 1, QTableWidgetItem("-"))
            self.OxidationTable.setItem(0, 2, QTableWidgetItem("-"))
            self.OxidationTable.setItem(0, 3, QTableWidgetItem(str(round(chemSiliconValue, 3)))) # silicon value
            self.OxidationTable.setItem(0, 4, QTableWidgetItem(str(round(chemManganesevalue, 3)))) # manganese
            self.OxidationTable.setItem(0, 5, QTableWidgetItem(str(round(chemPhosphorValue, 3)))) # Phosphor
            self.OxidationTable.setItem(0, 6, QTableWidgetItem(str(round(chemSerumValue, 3)))) # serum
            self.OxidationTable.setItem(0, 7, QTableWidgetItem("-"))  # serum

            steelCarbonValue = float(self.steelCarbon.text())
            steelSerumValue = float(self.steelSerum.text())
            steelSiliconValue = float(self.steelSilicon.text())
            steelPhosphorValue = float(self.steelPhosphor.text())
            steelManganeseValue = float(self.steelManganese.text()) # добавить поле ввода для марганца float(self.steel.text())

            if(steelCarbonValue <= 0.1):
                Mn = 85.0
                P = 93.0
                S = 37.0
            elif((steelCarbonValue > 0.1) and (steelCarbonValue <= 0.25)):
                Mn = 77.0
                P = 87.0
                S = 43.0
            elif(steelCarbonValue > 0.25):
                Mn = 73.0
                P = 83.0
                S = 47.0

            manganeseAfter = chemManganesevalue * (100.0 - Mn) * 0.01
            phosphorAfter = chemPhosphorValue * (100.0 - P) * 0.01
            serumAfter = chemSerumValue * (100.0 - S) * 0.01
            siliconAfter = 0 #Кремний при выплавке стали в конвертере с основной футеровкой окисляется практически полностью, поэтому

            self.OxidationTable.setItem(1, 0, QTableWidgetItem(str(round(steelCarbonValue, 3))))
            self.OxidationTable.setItem(1, 1, QTableWidgetItem("-"))
            self.OxidationTable.setItem(1, 2, QTableWidgetItem("-"))
            self.OxidationTable.setItem(1, 3, QTableWidgetItem(str(round(siliconAfter, 3))))  # silicon value
            self.OxidationTable.setItem(1, 4, QTableWidgetItem(str(round(manganeseAfter, 3))))  # manganese
            self.OxidationTable.setItem(1, 5, QTableWidgetItem(str(round(phosphorAfter, 3))))  # Phosphor
            self.OxidationTable.setItem(1, 6, QTableWidgetItem(str(round(serumAfter, 3))))  # serum
            self.OxidationTable.setItem(1, 7, QTableWidgetItem("-"))  # serum

            carbonRemove = chemCarbonValue - steelCarbonValue
            carbonToCO = carbonRemove * 0.9
            carbonToCO2 = carbonRemove * 0.1
            siliconRemove = chemSiliconValue - siliconAfter
            manganeseRemove = chemManganesevalue - manganeseAfter
            phosphorRemove = chemPhosphorValue - phosphorAfter
            serumRemove = (chemSerumValue - serumAfter)
            summRemove = carbonToCO + carbonToCO2 + siliconRemove +manganeseRemove + phosphorRemove + serumRemove

            self.OxidationTable.setItem(2, 0, QTableWidgetItem(str(round(carbonRemove, 3))))
            self.OxidationTable.setItem(2, 1, QTableWidgetItem(str(round(carbonToCO, 3))))
            self.OxidationTable.setItem(2, 2, QTableWidgetItem(str(round(carbonToCO2, 3))))
            self.OxidationTable.setItem(2, 3, QTableWidgetItem(str(round(siliconRemove, 3))))  # silicon value
            self.OxidationTable.setItem(2, 4, QTableWidgetItem(str(round(manganeseRemove, 3))))  # manganese
            self.OxidationTable.setItem(2, 5, QTableWidgetItem(str(round(phosphorRemove, 3))))  # Phosphor
            self.OxidationTable.setItem(2, 6, QTableWidgetItem(str(round(serumRemove, 3))))  # serum
            self.OxidationTable.setItem(2, 7, QTableWidgetItem(str(round(summRemove, 3))))  # summ

            carbonToCOOxygen = carbonToCO * 16/12
            carbonToCO2Oxygen = carbonToCO2 * 32/12
            siliconOxygen = siliconRemove * 32/28
            manganesOxygen = manganeseRemove * 16/55
            phosphorOxygen = phosphorRemove * 5 * 16 / 2 / 31
            summOxygen = carbonToCOOxygen + carbonToCO2Oxygen + siliconOxygen + manganesOxygen +phosphorOxygen

            self.OxidationTable.setItem(3, 0, QTableWidgetItem("-"))
            self.OxidationTable.setItem(3, 1, QTableWidgetItem(str(round(carbonToCOOxygen, 3))))
            self.OxidationTable.setItem(3, 2, QTableWidgetItem(str(round(carbonToCO2Oxygen, 3))))
            self.OxidationTable.setItem(3, 3, QTableWidgetItem(str(round(siliconOxygen, 3))))  # silicon value
            self.OxidationTable.setItem(3, 4, QTableWidgetItem(str(round(manganesOxygen, 3))))  # manganese
            self.OxidationTable.setItem(3, 5, QTableWidgetItem(str(round(phosphorOxygen, 3))))  # Phosphor
            self.OxidationTable.setItem(3, 6, QTableWidgetItem("-"))  # serum
            self.OxidationTable.setItem(3, 7, QTableWidgetItem(str(round(summOxygen, 3))))  # summ

            carbonToCOOxygenM3 = carbonToCOOxygen * 22.4 / 32
            carbonToCO2OxygenM3 = carbonToCO2Oxygen * 22.4 / 32
            siliconOxygenM3 = siliconOxygen * 22.4 / 32
            manganesOxygenM3 = manganesOxygen * 22.4 / 32
            phosphorOxygenM3 = phosphorOxygen * 22.4 / 32
            summOxygenM3 = carbonToCOOxygenM3 + carbonToCO2OxygenM3 + siliconOxygenM3 + manganesOxygenM3 + phosphorOxygenM3

            self.OxidationTable.setItem(4, 0, QTableWidgetItem("-"))
            self.OxidationTable.setItem(4, 1, QTableWidgetItem(str(round(carbonToCOOxygenM3, 3))))
            self.OxidationTable.setItem(4, 2, QTableWidgetItem(str(round(carbonToCO2OxygenM3, 3))))
            self.OxidationTable.setItem(4, 3, QTableWidgetItem(str(round(siliconOxygenM3, 3))))  # silicon value
            self.OxidationTable.setItem(4, 4, QTableWidgetItem(str(round(manganesOxygenM3, 3))))  # manganese
            self.OxidationTable.setItem(4, 5, QTableWidgetItem(str(round(phosphorOxygenM3, 3))))  # Phosphor
            self.OxidationTable.setItem(4, 6, QTableWidgetItem("-"))  # serum
            self.OxidationTable.setItem(4, 7, QTableWidgetItem(str(round(summOxygenM3, 3))))  # summ

            oxidesToCO = carbonToCO + carbonToCOOxygen
            oxidesToCO2 = carbonToCO2 + carbonToCO2Oxygen
            oxidesSilicon = siliconRemove + siliconOxygen
            oxidesManganes = manganeseRemove + manganesOxygen
            oxidesPhosphor = phosphorRemove + phosphorOxygen
            oxidesSerum = serumRemove
            oxidesSumm = oxidesToCO + oxidesToCO2 + oxidesSilicon + oxidesManganes + oxidesPhosphor

            self.OxidationTable.setItem(5, 0, QTableWidgetItem("-"))
            self.OxidationTable.setItem(5, 1, QTableWidgetItem(str(round(oxidesToCO, 3))))
            self.OxidationTable.setItem(5, 2, QTableWidgetItem(str(round(oxidesToCO2, 3))))
            self.OxidationTable.setItem(5, 3, QTableWidgetItem(str(round(oxidesSilicon, 3))))  # silicon value
            self.OxidationTable.setItem(5, 4, QTableWidgetItem(str(round(oxidesManganes, 3))))  # manganese
            self.OxidationTable.setItem(5, 5, QTableWidgetItem(str(round(oxidesPhosphor, 3))))  # Phosphor
            self.OxidationTable.setItem(5, 6, QTableWidgetItem(str(round(oxidesSerum, 3))))  # serum
            self.OxidationTable.setItem(5, 7, QTableWidgetItem(str(round(oxidesSumm, 3))))  # summ
            global tableCalcked
            tableCalcked = True
        except Exception as err:  # mc.Error
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        return

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

    def AddFeroBtnClicked(self):
        try:
            self.ChemEmission.setRowCount(0)
            rows = self.ChemEmission.rowCount()
            text = self.FeroType.currentText()
            query = "select * from ferroalloy where Name = '"+ text + "';"
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="FerroalloyDB"
            )
            result = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            result = mycursor.fetchall()
            self.ChemEmission.insertRow(rows)
            i = result[0]
            self.ChemEmission.setItem(0, 0, QTableWidgetItem(i[1]))
            self.ChemEmission.setItem(0, 1, QTableWidgetItem(str(i[2])))
            self.ChemEmission.setItem(0, 2, QTableWidgetItem(str(i[3])))
            self.ChemEmission.setItem(0, 3, QTableWidgetItem(str(i[4])))
            self.ChemEmission.setItem(0, 4, QTableWidgetItem(str(i[5])))
            self.ChemEmission.setItem(0, 5, QTableWidgetItem(str(i[6])))
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()
        finally:
            DB.close()
            mycursor.close()

    def removeFeroBtnClicked(self):
        self.ChemEmission.setRowCount(0)

    def slagCalcClicked(self):
        try:
            global tableCalcked
            if (tableCalcked == False):
                self.calcTableClick()
                tableCalcked = True
            oxidesSilicon = float(self.OxidationTable.item(5,3).text())
            oxidesManganes = float(self.OxidationTable.item(5,4).text())
            oxidesPhosphor = float(self.OxidationTable.item(5,5).text())
            oxidesSerum = float(self.OxidationTable.item(5,6).text())
            slagSiO2 = 0
            slagAl2O3 = 0
            slagCaO = 0
            slagFeO = 0
            slagMgO = 0
            slagFe2O3 = 0
            slagOthers = 0
            totalSlagSiO2 = 0
            # listOfNamesForClass = ['fluxe1', 'fluxe2', 'fluxe3', 'fluxe4', 'fluxe5', 'fluxe6', 'fluxe7', 'fluxe8',
            #                        'fluxe9']
            fluxesRowCount = self.FluxeTable.rowCount()
            for row in range(fluxesRowCount):
                listOfNamesForClass[row] = FluxeComposition()
                listOfNamesForClass[row].name = str(self.FluxeTable.item(row, 0).text())
                name = listOfNamesForClass[row].name
                query = "select * from fluxecomposition where idFluxeComposition in (select (FluxeComposition_idFluxeComposition) from fluxedata where FluxeName = '" + name + "');"
                usersDB = mc.connect(
                    host=DBhost,  # host="192.168.51.179" user="root", password="root",
                    user=DBlogin,
                    password=DBpass,
                    database="regimdata"
                )
                result = ""
                mycursor = usersDB.cursor()
                mycursor.execute(query)
                result = mycursor.fetchall()
                listOfNamesForClass[row].fluxeCaO = result[0][1]
                listOfNamesForClass[row].fluxeSiO2 = result[0][2]
                listOfNamesForClass[row].fluxeMgO = result[0][3]
                listOfNamesForClass[row].fluxeFe2O3 = result[0][4]
                listOfNamesForClass[row].fluxeFeO = result[0][5]
                listOfNamesForClass[row].fluxeMnO = result[0][6]
                listOfNamesForClass[row].fluxeAl2O3 = result[0][7]
                listOfNamesForClass[row].fluxeCaCO3 = result[0][8]
                listOfNamesForClass[row].fluxeMgCO3 = result[0][9]
                listOfNamesForClass[row].fluxeWeight = float(self.FluxeTable.item(row, 1).text())

                totalSlagSiO2 += listOfNamesForClass[row].fluxeWeight * listOfNamesForClass[row].fluxeSiO2/100
                slagCaO += listOfNamesForClass[row].fluxeWeight * (listOfNamesForClass[row].fluxeCaO/100 + listOfNamesForClass[row].fluxeCaCO3 / 100 * 52/96)
                slagMgO += listOfNamesForClass[row].fluxeWeight * (listOfNamesForClass[row].fluxeMgO/100 + listOfNamesForClass[row].fluxeMgCO3 / 100 * 40/84)
                slagAl2O3 += listOfNamesForClass[row].fluxeWeight * listOfNamesForClass[row].fluxeAl2O3 / 100

            FeO = 20.0 + 0.218 / float(self.steelCarbon.text()) + 0.031 / float(self.steelPhosphor.text())
            Fe2O3 = 0.0

            steelCarbon = float(self.steelCarbon.text())
            steelPhosphor = float(self.steelPhosphor.text())

            metalChargeWeight = float(self.MetalCharge.text())

            slagSiO2 = oxidesSilicon * metalChargeWeight/100 + totalSlagSiO2
            slagOthers = (oxidesManganes + oxidesPhosphor + oxidesSerum) * metalChargeWeight/100
            slagWeight = ((slagSiO2 + slagCaO + slagMgO + slagAl2O3 + slagOthers) / (100 - FeO - Fe2O3)) * 100
            slagFeO = FeO / 100 * slagWeight
            slagFe2O3 = Fe2O3 / 100 * slagWeight

            self.SlagWeight.setText(str(round(slagWeight, 3)))
            self.SlagSiO2.setText(str(round(slagSiO2, 3)))
            self.SlagSiO2Perc.setText(str(round(slagSiO2/slagWeight * 100, 3)))
            self.SlagAl2O3.setText(str(round(slagAl2O3, 3)))
            self.SlagAl2O3Perc.setText(str(round(slagAl2O3/slagWeight*100, 3)))
            self.SlagCaO.setText(str(round(slagCaO, 3)))
            self.SlagCaOPerc.setText(str(round(slagCaO/slagWeight*100, 3)))
            self.SlagFeO.setText(str(round(slagFeO, 3)))
            self.SlagFeOPerc.setText(str(round(slagFeO/slagWeight*100, 3)))
            self.SlagMgO.setText(str(round(slagMgO, 3)))
            self.SlagMgOPerc.setText(str(round(slagMgO/slagWeight*100, 3)))
            self.SlagFe2O3.setText(str(round(slagFe2O3)))
            self.SlagFe2O3Perc.setText(str(round(slagFe2O3/slagWeight*100)))
            self.SlagOthers.setText(str(round(slagOthers, 3)))
            self.SlagOthersPerc.setText(str(round(slagOthers/slagWeight*100, 3)))
            global slagCalcked
            slagCalcked = True
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def blastCalcClicked(self):
        try:
            global slagCalcked
            if (slagCalcked == False):
                self.slagCalcClicked()
                slagCalcked = True
            metalChargeWeight = float(self.MetalCharge.text())
            tmp = self.OxidationTable.item(3,7).text()
            totalOxygenRequired = float(self.OxidationTable.item(3,7).text())/100 * metalChargeWeight

            FeO = 0.0
            Fe2O3 = 0.0
            fluxesRowCount = self.FluxeTable.rowCount()
            for row in range(fluxesRowCount):
                currentFluxeWeight = listOfNamesForClass[row].fluxeWeight
                FeO += currentFluxeWeight * listOfNamesForClass[row].fluxeFeO / 100
                Fe2O3 += currentFluxeWeight * listOfNamesForClass[row].fluxeFe2O3 / 100

            tmpOxygenRequired = FeO * 16 / 72 + Fe2O3 * 48 / 160.0

            ironOxygenRequired = float(self.SlagFeO.text()) * 16 / 72 + float(self.SlagFe2O3.text()) * 48 / 160
            carbonOxygenRequired = float(self.OxidationTable.item(5,1).text()) / 100 * metalChargeWeight * 0.1 * 16/28
            summaryOxygenRequired = totalOxygenRequired + ironOxygenRequired + carbonOxygenRequired - tmpOxygenRequired
            totalBlastConsumptionKg = (summaryOxygenRequired * 0.01 + summaryOxygenRequired) * 100 / 99.5
            totalBlastConsumptionM3 = totalBlastConsumptionKg * 22.4/32
            excessBlast = totalBlastConsumptionKg * 0.08

            self.TotalOxygenDemandBlast.setText(str(round(summaryOxygenRequired, 3)))
            self.TotalConsumptionOfBlastKg.setText(str(round(totalBlastConsumptionKg, 3)))
            self.TotalConsumptionOfBlastM3.setText(str(round(totalBlastConsumptionM3, 3)))
            self.ExcessBlast.setText(str(round(excessBlast, 3)))
            global blastCalcked
            blastCalcked = True
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def MaterialBalanceCalcClicked(self):
        try:
            global blastCalcked
            if (blastCalcked == False):
                self.blastCalcClicked()
                blastCalcked = True
            totalOxygenRequired = float(self.SlagFeO.text())* 16 / 72 + float(self.SlagFe2O3.text()) * 48 / 160
            totalFeO = 0
            totalFe2O3 = 0
            totalCaCO3 = 0
            totalMgCO3 = 0
            fluxesRowCount = self.FluxeTable.rowCount()
            for row in range(fluxesRowCount):
                currentFluxeWeight = listOfNamesForClass[row].fluxeWeight
                totalFeO += currentFluxeWeight * listOfNamesForClass[row].fluxeFeO / 100
                totalFe2O3 += currentFluxeWeight * listOfNamesForClass[row].fluxeFe2O3 / 100
                totalCaCO3 += currentFluxeWeight * listOfNamesForClass[row].fluxeCaCO3 / 100
                totalMgCO3 += currentFluxeWeight * listOfNamesForClass[row].fluxeMgCO3 / 100

            amountOfReclaimedIron = totalFeO + totalFe2O3 - totalFeO * 16/72 - totalFe2O3 * 48/160
            self.ReclaimedIronWeight.setText(str(round(amountOfReclaimedIron, 3)))

            weightOfOxedizedImpurities = float(self.OxidationTable.item(2,7).text())/100 * float(self.MetalCharge.text())
            self.MassOfOxidizedImpurities.setText(str(round(weightOfOxedizedImpurities, 3)))

            weightOfIronOxides = float(self.SlagFeO.text()) + float(self.SlagFe2O3.text()) - totalOxygenRequired
            self.MassOfOxidesPassingIntoSlag.setText(str(round(weightOfIronOxides, 3)))
            self.LossWithCarryOver.setText(str(round(0.02 * float(self.MetalCharge.text()), 3)))

            oxidesToCO = float(self.OxidationTable.item(5, 1).text())
            oxidesToCO2 = float(self.OxidationTable.item(5, 2).text())
            metalChargeWeight = float(self.MetalCharge.text())
            self.OutputDataTable.setItem(0, 0, QTableWidgetItem(str(round(oxidesToCO * metalChargeWeight / 100, 3))))
            self.OutputDataTable.setItem(0, 1, QTableWidgetItem(str(round(oxidesToCO2 * metalChargeWeight / 100, 3))))
            self.OutputDataTable.setItem(0, 2, QTableWidgetItem(str(round(float(self.OutputDataTable.item(0, 0).text()) + float(self.OutputDataTable.item(0,1).text()), 3))))
            self.OutputDataTable.setItem(1, 0, QTableWidgetItem(str("-")))
            self.OutputDataTable.setItem(1, 1, QTableWidgetItem(str(round(totalCaCO3 * 44/96, 3))))
            self.OutputDataTable.setItem(1, 2, QTableWidgetItem(str(round(totalCaCO3 * 44/96, 3))))
            self.OutputDataTable.setItem(2, 0, QTableWidgetItem(str(round(-0.1 * float(self.OutputDataTable.item(0, 0).text()), 3))))
            self.OutputDataTable.setItem(2, 1, QTableWidgetItem(str(round(0.1 * float(self.OutputDataTable.item(0, 0).text()) * 44 / 28, 3))))
            self.OutputDataTable.setItem(2, 2, QTableWidgetItem(str(round(float(self.OutputDataTable.item(2, 0).text()) + float(self.OutputDataTable.item(2, 1).text()), 3))))
            self.OutputDataTable.setItem(3, 0, QTableWidgetItem(str("-")))
            self.OutputDataTable.setItem(3, 1, QTableWidgetItem(str(round(totalMgCO3 * 44 / 84, 3))))
            self.OutputDataTable.setItem(3, 2, QTableWidgetItem(str(round(totalMgCO3 * 44 / 84, 3))))
            tmp = float(self.OutputDataTable.item(0, 0).text()) + float(self.OutputDataTable.item(2, 0).text());
            self.OutputDataTable.setItem(4, 0, QTableWidgetItem(str(round(tmp, 3))))
            tmp = float(self.OutputDataTable.item(0, 1).text()) + float(self.OutputDataTable.item(1, 1).text()) + float(self.OutputDataTable.item(2, 1).text()) + float(self.OutputDataTable.item(3, 1).text())
            self.OutputDataTable.setItem(4, 1, QTableWidgetItem(str(round(tmp, 3))))
            tmp = float(self.OutputDataTable.item(0, 2).text()) + float(self.OutputDataTable.item(1, 2).text()) + float(self.OutputDataTable.item(2, 2).text()) + float(self.OutputDataTable.item(3, 2).text())
            self.OutputDataTable.setItem(4, 2, QTableWidgetItem(str(round(tmp, 3))))
            self.OutputDataTable.setItem(5, 0, QTableWidgetItem(str(round(float(self.OutputDataTable.item(4, 0).text()) * 22.4 / 28, 3))))
            tmp = float(self.OutputDataTable.item(4, 1).text()) * 22.4 / 44
            self.OutputDataTable.setItem(5, 1, QTableWidgetItem(str(round(tmp, 3))))
            self.OutputDataTable.setItem(5, 2, QTableWidgetItem(str(round(float(self.OutputDataTable.item(5, 0).text()) + float(self.OutputDataTable.item(5, 1).text()), 3))))
            self.OutputDataTable.setItem(6, 0, QTableWidgetItem(str(round(float(self.OutputDataTable.item(4,0).text()) / float(self.OutputDataTable.item(4,2).text()) * 100, 3))))
            self.OutputDataTable.setItem(6, 1, QTableWidgetItem(str(round(float(self.OutputDataTable.item(4,1).text()) / float(self.OutputDataTable.item(4,2).text()) * 100, 3))))
            self.OutputDataTable.setItem(6, 2, QTableWidgetItem(str(100)))

            tmp = 0.00001 * 200 * 70 * float(self.OutputDataTable.item(5,2).text())
            self.DustLoss.setText(str(round(tmp, 3)))

            oxidesPassingIntoSlag = float(self.MassOfOxidesPassingIntoSlag.text())
            oxidizedImpurities = float(self.MassOfOxidizedImpurities.text())
            lossWithCarryOver = float(self.LossWithCarryOver.text())
            dustLoss = float(self.DustLoss.text())
            reclaimedIronWeight = float(self.ReclaimedIronWeight.text())
            liquidIron = metalChargeWeight + reclaimedIronWeight - (oxidizedImpurities + oxidesPassingIntoSlag +
                                                                    lossWithCarryOver + dustLoss)
            self.LiquidIronYield.setText(str(round(liquidIron, 3)))

            incomingDataRowCount = self.IncomingData.rowCount()

            if incomingDataRowCount > 0:
                while incomingDataRowCount > 0:
                    self.IncomingData.removeRow(0)
                    incomingDataRowCount -= 1
            # self.OutputData.setSectionResizeMode(QHeaderView.Stretch)
            # self.OutputData.setStretchLastSection(1)

            self.IncomingData.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
            self.OutputData.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)


            self.IncomingData.insertRow(incomingDataRowCount)
            self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem("Чугун жидкий"))
            self.IncomingData.setItem(incomingDataRowCount, 1, QTableWidgetItem(str(round(float(self.castWeight.text())*1000, 3))))

            incomingDataRowCount += 1
            self.IncomingData.insertRow(incomingDataRowCount)
            self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem("Лом"))
            self.IncomingData.setItem(incomingDataRowCount, 1, QTableWidgetItem(str(round(float(self.scrapWeight.text()) * 1000, 3))))

            incomingDataRowCount += 1
            for row in range(fluxesRowCount):
                self.IncomingData.insertRow(incomingDataRowCount)
                self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem(str(listOfNamesForClass[row].name)))
                self.IncomingData.setItem(incomingDataRowCount, 1,
                                          QTableWidgetItem(str(round(listOfNamesForClass[row].fluxeWeight * 1000, 2))))
                incomingDataRowCount += 1

            self.IncomingData.insertRow(incomingDataRowCount)
            self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem("Дутьё"))
            self.IncomingData.setItem(incomingDataRowCount, 1,
                                      QTableWidgetItem(str(round(float(self.TotalConsumptionOfBlastKg.text()) * 1000, 3))))
            incomingDataRowCount += 1

            summary = 0
            for row in range(incomingDataRowCount - 1):
                summary += float(self.IncomingData.item(row, 1).text())

            self.IncomingData.insertRow(incomingDataRowCount)
            self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem("Итого"))
            self.IncomingData.setItem(incomingDataRowCount, 1, QTableWidgetItem(str(int(summary))))

            outRowCount = self.OutputData.rowCount()
            if outRowCount > 0:
                while outRowCount > 0:
                    self.OutputData.removeRow(0)
                    outRowCount -= 1

            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem("Металл жидкий"))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(liquidIron * 1000, 3))))

            outRowCount+=1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem("Шлак"))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(float(self.SlagWeight.text()) * 1000, 3))))

            outRowCount+=1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem("Газ"))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(float(self.OutputDataTable.item(4,2).text()) * 1000, 3))))

            outRowCount+=1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem("Избыток дутья"))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(float(self.ExcessBlast.text()) * 1000, 3))))

            outRowCount += 1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem("Выносы и выбросы"))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(float(self.LossWithCarryOver.text()) * 1000, 3))))

            outRowCount += 1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem("Потери с пылью"))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(float(self.DustLoss.text()) * 1000, 3))))

            outRowCount += 1
            summary = 0
            for row in range(outRowCount-1):
                summary += float(self.OutputData.item(row, 1).text())

            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem("Итого"))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(summary, 3))))
            self.IncomingData.resizeColumnsToContents()
            self.OutputData.resizeColumnsToContents()
            global materialBalanceCalcked
            materialBalanceCalcked = True

        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def HeatBalanceCalcClicked(self):
        try:
            global materialBalanceCalcked
            if(materialBalanceCalcked == False):
                self.MaterialBalanceCalcClicked()
                materialBalanceCalcked = True
            #Физическое тепло жидкого чугуна
            PhysCastHeat = float(self.castWeight.text()) * 1000.0 * (61.9 + 0.88 * float(self.castTemperature.text()))
            self.CastPhysHeat.setText(str(round(PhysCastHeat, 3)))
            self.IncomingHeatTable.setItem(0, 0, QTableWidgetItem(str(PhysCastHeat)))

            #Тепло от реакции окисления
            TotalRemovedCarbon = float(self.OxidationTable.item(2, 0).text())
            TotalRemovedSilicon = float(self.OxidationTable.item(2, 3).text())
            TotalRemovedMagn = float(self.OxidationTable.item(2, 4).text())
            TotalRemovedPhosph = float(self.OxidationTable.item(2, 5).text())
            HeatReactOfOxidation = (14770.0 * TotalRemovedCarbon + 26970.0 * TotalRemovedSilicon + 7000.0 * TotalRemovedMagn + 21730.0 * TotalRemovedPhosph) * float(self.MetalCharge.text()) * 10.0
            self.ThermalReactEffect.setText(str(round(HeatReactOfOxidation, 3)))
            self.IncomingHeatTable.setItem(1, 0, QTableWidgetItem(str(HeatReactOfOxidation)))

            #Химическое тепло от образования оксидов
            ChemHeatOxidAppear =  3707.0 * float(self.SlagFeO.text()) * 1000.0 + 5278.0 * float(self.SlagFe2O3.text()) * 1000.0
            self.ChemHeatOxyd.setText(str(round(ChemHeatOxidAppear, 3)))
            self.IncomingHeatTable.setItem(2, 0, QTableWidgetItem(str(round(ChemHeatOxidAppear, 3))))

            #Тепловой эффект реакции шлакообразования
            ChemSlagHeat =  628.0 * float(self.SlagCaO.text()) * 1000.0 + 1464.0 * float(self.SlagSiO2.text()) * 1000.0
            self.ChemHeatSlag.setText(str(round(ChemSlagHeat, 2)))
            self.IncomingHeatTable.setItem(3, 0, QTableWidgetItem(str(round(ChemSlagHeat, 3))))
            
            #Тепло от дожигания CO
            BurningCO = float(self.OutputDataTable.item(2, 0).text())
            HeatOfBurningCO = 101.0 * 100.0 * abs(BurningCO) * 1000.0 * 0.2
            self.HeatCO.setText(str(round(HeatOfBurningCO, 2)))
            self.IncomingHeatTable.setItem(4, 0, QTableWidgetItem(str(round(HeatOfBurningCO, 3))))

            #Общий приход тепла
            TotalHeatInc = PhysCastHeat + HeatReactOfOxidation + ChemHeatOxidAppear + ChemSlagHeat + HeatOfBurningCO
            self.TotalHeatInc.setText(str(TotalHeatInc))
            self.IncomingHeatTable.setItem(5, 0, QTableWidgetItem(str(round(TotalHeatInc, 2))))

            #Расходные статьи
            #
            # Физическое тепло отходящих газов
            COKilo = float(self.OutputDataTable.item(4, 0).text()) * 1000
            CO2Kilo = float(self.OutputDataTable.item(4, 1).text()) * 1000
            PhysGasHeat = (1.32 * 2000.0 - 220.0) * (COKilo + CO2Kilo)
            self.PhysHeatOutGas.setText(str(round(PhysGasHeat, 3)))
            self.OutputHeatTable.setItem(3, 0, QTableWidgetItem(str(round(PhysGasHeat, 3))))
            
            #Затраты тепла на разложение оксидов железа
            rows = self.FluxeTable.rowCount()
            totalFeO = 0
            totalFe2O3 = 0
            for row in range(rows):
                currentFluxeWeight = listOfNamesForClass[row].fluxeWeight
                totalFeO += currentFluxeWeight * 1000 * listOfNamesForClass[row].fluxeFeO / 100
                totalFe2O3 += currentFluxeWeight * 1000 * listOfNamesForClass[row].fluxeFe2O3 / 100
            FeOxydesHeatLoses = 3707.0 * totalFeO + 5278.0 * totalFe2O3
            self.HeatConsDecompos.setText(str(round(FeOxydesHeatLoses, 3)))
            self.OutputHeatTable.setItem(2, 0, QTableWidgetItem(str(round(FeOxydesHeatLoses, 3))))

            #Потери тепла с выносами и выбросами
            emissions = float(self.OutputData.item(4, 1).text())
            emissionsHeatLoses =  (54.8 + 0.84 * 1550.0) * emissions
            self.HeatLosesRemove.setText(str(round(emissionsHeatLoses, 3)))
            self.OutputHeatTable.setItem(4, 0, QTableWidgetItem(str(round(FeOxydesHeatLoses, 3))))

            #Затраты тепла на пылеобразование
            dustFeLoses = float(self.OutputData.item(5, 1).text())
            heatDustLoses = (54.8 + 0.84 * 2000.0) * dustFeLoses
            self.HeatDustForm.setText(str(round(heatDustLoses, 3)))
            self.OutputHeatTable.setItem(5, 0, QTableWidgetItem(str(round(heatDustLoses, 3))))

            #Тепло на разложение карбонатов
            totalCaCO3Decom = float(self.OutputDataTable.item(1, 2).text())
            totalMgCO3Decom = float(self.OutputDataTable.item(3, 2).text())
            heatCarbonDecom =  4038.0 * (totalCaCO3Decom * 1000.0 + totalMgCO3Decom * 1000.0)
            self.HeatCarbonDecom.setText(str(round(heatCarbonDecom, 3)))
            self.OutputHeatTable.setItem(6, 0, QTableWidgetItem(str(round(heatCarbonDecom, 3))))

            #Тепловые потери
            heatLoses = TotalHeatInc * 0.03 #можно брать из базы как настраиваемый параметр
            self.HeatLoses.setText(str(round(heatLoses, 3)))
            self.OutputHeatTable.setItem(7, 0, QTableWidgetItem(str(round(heatLoses, 3))))

            #Температура жидкого металла в конце продувки
            SteelTemperature = (TotalHeatInc - PhysGasHeat - FeOxydesHeatLoses - emissionsHeatLoses - heatDustLoses -
                                heatCarbonDecom - heatLoses - 54.8 * float(self.LiquidIronYield.text())*1000.0 +
                                1379 * float(self.SlagWeight.text()) * 1000) / (0.84 * float(self.LiquidIronYield.text()) *
                                1000 + 2.09 * float(self.SlagWeight.text())*1000)

            #Физическое тепло жидкого металла
            PhysSteelHeat = (54.8 + 0.84 * SteelTemperature) * float(self.LiquidIronYield.text()) * 1000
            self.PhysHeatLiquidSteel.setText(str(round(PhysSteelHeat, 3)))
            self.OutputHeatTable.setItem(0, 0, QTableWidgetItem(str(round(PhysSteelHeat, 3))))

            #Физическое тепло шлака
            PhysSlagHeat = (2.09 * SteelTemperature - 1379.0) * float(self.SlagWeight.text()) * 1000
            self.PhysHeatSlag.setText(str(round(PhysSlagHeat, 3)))
            self.OutputHeatTable.setItem(1, 0, QTableWidgetItem(str(round(PhysSteelHeat, 3))))

            #Общий расход тепла
            TotalHeatOut = PhysSteelHeat + PhysSlagHeat + PhysGasHeat + FeOxydesHeatLoses + heatLoses + heatCarbonDecom + heatDustLoses + emissionsHeatLoses
            self.TotalHeatCons.setText(str(round(TotalHeatOut, 3)))
            self.OutputHeatTable.setItem(8, 0, QTableWidgetItem(str(round(TotalHeatOut, 3))))

            #Температура жидкого металла в конце продувки
            self.LiquidSteelTemp.setText(str(round(SteelTemperature, 3)))

            #Температура перегрева
            # МОЖНО ДОБАВИТЬ ПРОВЕРКУ НА ТО, ЕСЛИ ТЕМПРЕАТУРА ПЕРЕГРЕВА ОТРИЦАТЕЛЬНАЯ ТО БАН
            meltTemperature = 1539.0 - 80.0 * float(self.steelCarbon.text())
            overheatTemperature = SteelTemperature - meltTemperature
            self.OverheatTemp.setText(str(round(overheatTemperature, 3)))

            #Выводим кол-во процентов в таблицы


            global heatBalanceCalcked
            heatBalanceCalcked = True
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def deoxCalc(self):
        try:
            global heatBalanceCalcked
            if(heatBalanceCalcked == False):
                self.HeatBalanceCalcClicked()
                heatBalanceCalcked = True
            if(self.ChemEmission.rowCount() == 0):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Ошибка")
                msg.setText("Внимание")
                msg.setInformativeText("Не выбран феросплав!")
                # msg.setInformativeText("Error: {0}".format(err))
                msg.exec_()
                return

            A = 0.255817 * float(self.LiquidSteelTemp.text()) - 335
            B = 0.066103 * float(self.LiquidSteelTemp.text()) - 85


            # Процентное содержание веществ в шлаке
            slagCaO = float(self.SlagCaOPerc.text())
            slagSiO2 = float(self.SlagSiO2Perc.text())
            slagFeO = float(self.SlagFeOPerc.text())
            slagMgO = float(self.SlagMgOPerc.text())

            # Рассчет растворимости MgO
            limitSolubilityMgO = (A - B * slagCaO/slagSiO2) * 0.075 * slagFeO - 0.875
            limitSolubilityMgO = abs(limitSolubilityMgO)
            #Потери массы футеровки
            liningWeightLoss = 4.11155 * pow(10, -6) * float(self.LiquidSteelTemp.text()) * (limitSolubilityMgO - slagMgO)
            self.LiningWeightLoss.setText(str(round(liningWeightLoss, 3)))

            self.resultSteelTemperature.setText(self.LiquidSteelTemp.text())
            self.SlagWeightRes.setText(self.SlagWeight.text())

            carbonRemaining = float(self.OxidationTable.item(1,0).text())
            umn = 0
            if(carbonRemaining < 0.10):
                umn = 27.5
            elif(carbonRemaining >= 0.10 and carbonRemaining <= 0.25):
                umn = 25.0
            elif(carbonRemaining > 0.25):
                umn = 17.5

            #расход феросплава
            steelManganese = float(self.steelManganese.text())
            tmp1 = float(self.LiquidIronYield.text())
            tmp2 = float(self.OxidationTable.item(1,4).text())
            tmp3 = float(self.ChemEmission.item(0,3).text())

            firstFero = 100 * float(self.LiquidIronYield.text()) * 1000 * (
                    steelManganese - float(self.OxidationTable.item(1,4).text()))/(
                    float(self.ChemEmission.item(0,3).text())*(100-umn))

            firstFero = abs(firstFero)

            self.rashod_pervovo_ferrosplava_line_edit_2.setText(str(round(firstFero, 3)))

            # заместо 0.5 должен быть концентрация марганца но ее нет на интерфейсе поэтому пока так
            #firstFero = 100 * float(self.LiquidIronYield.text()) * 1000 * (
                        #0.5 - float(self.OxidationTable.item(1, 4).text())) / (
                                    #float(self.ChemEmission.item(0, 3).text()) * (100 - umn))
            #self.rashod_pervovo_ferrosplava_line_edit_2.setText(str(round(firstFero, 3)))


            #Выход металла после раскисления
            vyhod_pervovo_metalla_posle_raskisleniya = firstFero + float(self.LiquidIronYield.text())*1000
            self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2.setText(str(round(vyhod_pervovo_metalla_posle_raskisleniya, 3)))

            #Баланс элементов после раскисления стали
            _0_0 = float(self.OxidationTable.item(1,0).text())
            _0_1 = 0
            _0_2 = float(self.OxidationTable.item(1,3).text())
            _0_3 = 0
            _0_4 = float(self.OxidationTable.item(1,4).text())
            _0_5 = 0
            _0_6 = float(self.OxidationTable.item(1,5).text())
            _0_7 = float(self.OxidationTable.item(1,6).text())
            _0_8 = 100.0 - (_0_0 + _0_1 + _0_2 + _0_3 + _0_4 + _0_5 + _0_6 + _0_7)
            _0_9 = 100

            _1_0 = _0_0 * float(self.LiquidIronYield.text()) * 1000.0 / 100.0
            _1_1 = _0_1 * float(self.LiquidIronYield.text()) * 1000.0 / 100.0
            _1_2 = _0_2 * float(self.LiquidIronYield.text()) * 1000.0 / 100.0
            _1_3 = _0_3 * float(self.LiquidIronYield.text()) * 1000.0 / 100.0
            _1_4 = _0_4 * float(self.LiquidIronYield.text()) * 1000.0 / 100.0
            _1_5 = _0_5 * float(self.LiquidIronYield.text()) * 1000.0 / 100.0
            _1_6 = _0_6 * float(self.LiquidIronYield.text()) * 1000.0 / 100.0
            _1_7 = _0_7 * float(self.LiquidIronYield.text()) * 1000.0 / 100.0
            _1_9 = float(self.LiquidIronYield.text()) * 1000
            _1_8 = _1_9 - (_1_0 + _1_1 + _1_2 + _1_3 + _1_4 + _1_5 + _1_6 + _1_7)

            _2_0 = firstFero * float(self.ChemEmission.item(0, 1).text()) / 100.0 / 2.0
            _2_1 = firstFero * float(self.ChemEmission.item(0, 1).text()) / 100.0 / 2.0
            _2_2 = firstFero * float(self.ChemEmission.item(0, 2).text()) / 100.0 / 2.0
            _2_3 = firstFero * float(self.ChemEmission.item(0, 2).text()) / 100.0 / 2.0
            _2_4 = firstFero * float(self.ChemEmission.item(0, 3).text()) / 100.0 / 2.0
            _2_5 = firstFero * float(self.ChemEmission.item(0, 3).text()) / 100.0 / 2.0
            _2_6 = firstFero * float(self.ChemEmission.item(0, 4).text()) / 100.0 / 2.0
            _2_7 = firstFero * float(self.ChemEmission.item(0, 5).text()) / 100.0 / 2.0
            _2_9 = firstFero
            _2_8 = _2_9 - (_2_0 + _2_1 + _2_2 + _2_3 + _2_4 + _2_5 + _2_6 + _2_7)

            _3_0 = _1_0 + _2_0
            _3_1 = 0.0
            _3_2 = _1_2 + _2_2
            _3_3 = 0.0
            _3_4 = _1_4 + _2_4
            _3_5 = 0.0
            _3_6 = _1_6 + _2_6
            _3_7 = _1_7 + _2_7
            _3_8 = _1_8 + _2_8
            _3_9 = _1_9 + _2_9

            _4_0 = 0.0
            _4_1 = _2_1 * 28.0 / 12.0
            _4_2 = 0.0
            _4_3 = _2_3 * 60.0 / 28.0
            _4_4 = 0.0
            _4_5 = _2_5 * 71.0 / 55.0
            _4_6 = 0.0
            _4_7 = 0.0
            _4_8 = 0.0
            _4_9 = 0.0

            _5_0 = _3_0 / _3_9 * 100.0
            _5_1 = 0.0
            _5_2 = _3_2 / _3_9 * 100.0
            _5_3 = 0.0
            _5_4 = _3_4 / _3_9 * 100.0
            _5_5 = 0.0
            _5_6 = _3_6 / _3_9 * 100.0
            _5_7 = _3_7 / _3_9 * 100.0
            _5_8 = _3_8 / _3_9 * 100.0
            _5_9 = 100.0

            self.DeoxidationBalance.setItem(0, 0, QTableWidgetItem(str(round(_0_0, 3))))
            self.DeoxidationBalance.setItem(0, 1, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(0, 2, QTableWidgetItem(str(round(_0_2, 3))))
            self.DeoxidationBalance.setItem(0, 3, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(0, 4, QTableWidgetItem(str(round(_0_4, 3))))
            self.DeoxidationBalance.setItem(0, 5, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(0, 6, QTableWidgetItem(str(round(_0_6, 3))))
            self.DeoxidationBalance.setItem(0, 7, QTableWidgetItem(str(round(_0_7, 3))))
            self.DeoxidationBalance.setItem(0, 8, QTableWidgetItem(str(round(_0_8, 3))))
            self.DeoxidationBalance.setItem(0, 9, QTableWidgetItem(str(round(_0_9, 3))))

            self.DeoxidationBalance.setItem(1, 0, QTableWidgetItem(str(round(_1_0, 3))))
            self.DeoxidationBalance.setItem(1, 1, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(1, 2, QTableWidgetItem(str(round(_1_2, 3))))
            self.DeoxidationBalance.setItem(1, 3, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(1, 4, QTableWidgetItem(str(round(_1_4, 3))))
            self.DeoxidationBalance.setItem(1, 5, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(1, 6, QTableWidgetItem(str(round(_1_6, 3))))
            self.DeoxidationBalance.setItem(1, 7, QTableWidgetItem(str(round(_1_7, 3))))
            self.DeoxidationBalance.setItem(1, 8, QTableWidgetItem(str(round(_1_0, 3))))
            self.DeoxidationBalance.setItem(1, 8, QTableWidgetItem(str(round(_1_9, 3))))

            self.DeoxidationBalance.setItem(2, 0, QTableWidgetItem(str(round(_2_0, 3))))
            self.DeoxidationBalance.setItem(2, 1, QTableWidgetItem(str(round(_2_1, 3))))
            self.DeoxidationBalance.setItem(2, 2, QTableWidgetItem(str(round(_2_2, 3))))
            self.DeoxidationBalance.setItem(2, 3, QTableWidgetItem(str(round(_2_3, 3))))
            self.DeoxidationBalance.setItem(2, 4, QTableWidgetItem(str(round(_2_4, 3))))
            self.DeoxidationBalance.setItem(2, 5, QTableWidgetItem(str(round(_2_5, 3))))
            self.DeoxidationBalance.setItem(2, 6, QTableWidgetItem(str(round(_2_6, 3))))
            self.DeoxidationBalance.setItem(2, 7, QTableWidgetItem(str(round(_2_7, 3))))
            self.DeoxidationBalance.setItem(2, 8, QTableWidgetItem(str(round(_2_8, 3))))
            self.DeoxidationBalance.setItem(2, 9, QTableWidgetItem(str(round(_2_9, 3))))

            self.DeoxidationBalance.setItem(3, 0, QTableWidgetItem(str(round(_3_0, 3))))
            self.DeoxidationBalance.setItem(3, 1, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(3, 2, QTableWidgetItem(str(round(_3_2, 3))))
            self.DeoxidationBalance.setItem(3, 3, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(3, 4, QTableWidgetItem(str(round(_3_4, 3))))
            self.DeoxidationBalance.setItem(3, 5, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(3, 6, QTableWidgetItem(str(round(_3_6, 3))))
            self.DeoxidationBalance.setItem(3, 7, QTableWidgetItem(str(round(_3_7, 3))))
            self.DeoxidationBalance.setItem(3, 8, QTableWidgetItem(str(round(_3_8, 3))))
            self.DeoxidationBalance.setItem(3, 9, QTableWidgetItem(str(round(_3_9, 3))))

            self.DeoxidationBalance.setItem(4, 0, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(4, 1, QTableWidgetItem(str(round(_4_1, 3))))
            self.DeoxidationBalance.setItem(4, 2, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(4, 3, QTableWidgetItem(str(round(_4_3, 3))))
            self.DeoxidationBalance.setItem(4, 4, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(4, 5, QTableWidgetItem(str(round(_4_5, 3))))
            self.DeoxidationBalance.setItem(4, 6, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(4, 7, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(4, 8, QTableWidgetItem("-"))
            self.DeoxidationBalance.setItem(4, 9, QTableWidgetItem("-"))

            self.DeoxidationBalance.setItem(5, 0, QTableWidgetItem(str(round(_5_0, 3))))
            self.DeoxidationBalance.setItem(5, 1, QTableWidgetItem(str(round(_5_1, 3))))
            self.DeoxidationBalance.setItem(5, 2, QTableWidgetItem(str(round(_5_2, 3))))
            self.DeoxidationBalance.setItem(5, 3, QTableWidgetItem(str(round(_5_3, 3))))
            self.DeoxidationBalance.setItem(5, 4, QTableWidgetItem(str(round(_5_4, 3))))
            self.DeoxidationBalance.setItem(5, 5, QTableWidgetItem(str(round(_5_5, 3))))
            self.DeoxidationBalance.setItem(5, 6, QTableWidgetItem(str(round(_5_6, 3))))
            self.DeoxidationBalance.setItem(5, 7, QTableWidgetItem(str(round(_5_7, 3))))
            self.DeoxidationBalance.setItem(5, 8, QTableWidgetItem(str(round(_5_8, 3))))
            self.DeoxidationBalance.setItem(5, 9, QTableWidgetItem(str(round(_5_9, 3))))

            #Состав стали
            self.SteelChemResult.setItem(0, 0, QTableWidgetItem(str(round(_5_0, 3))))
            self.SteelChemResult.setItem(0, 1, QTableWidgetItem(str(round(_5_2, 3))))
            self.SteelChemResult.setItem(0, 2, QTableWidgetItem(str(round(_5_4, 3))))
            self.SteelChemResult.setItem(0, 3, QTableWidgetItem(str(round(_5_7, 3))))
            self.SteelChemResult.setItem(0, 4, QTableWidgetItem(str(round(_5_6, 3))))

            self.SlagChemResult.setItem(0, 0, QTableWidgetItem(str(self.SlagSiO2Perc.text())))
            self.SlagChemResult.setItem(0, 1, QTableWidgetItem(str(self.SlagAl2O3Perc.text())))
            self.SlagChemResult.setItem(0, 2, QTableWidgetItem(str(self.SlagCaOPerc.text())))
            self.SlagChemResult.setItem(0, 3, QTableWidgetItem(str(self.SlagFeOPerc.text())))
            self.SlagChemResult.setItem(0, 4, QTableWidgetItem(str(self.SlagMgOPerc.text())))

            self.CO2ThrowRes.setText(str(self.OutputDataTable.item(4,1).text()))
            self.SteelWeightRes.setText(str(self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2.text()))


        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()

    def openAbout(self):
        self.window = QtWidgets.QDialog()
        self.ui = AboutForm.Ui_Dialog()
        self.ui.setupUi(self.window)
        self.window.show()

    def saveResult(self):
        file = filedialog.asksaveasfile(defaultextension='.txt',
                                        filetypes=[
                                            ("Text file", ".txt"),
                                            ("HTML file", ".html"),
                                            ("All files", ".*"),
                                        ])
        if file is None:
            return
        try:
            tmpFluxes = ""
            fluxesRowCount = self.FluxeTable.rowCount()
            for row in range(fluxesRowCount):
                name = str(self.FluxeTable.item(row, 0).text())
                weight = str(self.FluxeTable.item(row, 1).text())
                tmpFluxes += name + " массой " + weight + " Т., "
            filetext = "Результат плавки для следующего набора данных:\nЧугун: Температура [C]: " + str(self.castTemperature.text()) +\
                       ", Масса [Т] " + str(self.castWeight.text()) + " со следующим содержанием веществ[%масс]:\n" + \
                       "Углерод: " + str(self.castCarbon.text()) + ", Сера:" + str(self.castSerum.text()) + \
                       ", Кремний: " + str(self.castSilicon.text()) + ", Фосфор: " + str(self.castPhosphor.text()) +\
                       ", Марганец: " + str(self.castManganese.text()) +"\nЛом: " +\
                       "Масса [Т] " + str(self.scrapWeight.text()) + " со следующим содержанием веществ[%масс]:\n" + \
                       "Углерод: " + str(self.scrapCarbon.text()) + ", Сера:" + str(self.scrapSerum.text()) + \
                       ", Кремний: " + str(self.scrapSilicon.text()) + ", Фосфор: " + str(self.scrapPhosphor.text()) +\
                       ", Марганец: " + str(self.scrapManganese.text()) + "\nс использованием флюсов: " + tmpFluxes + \
                       "\nБыла получена сталь массой " + self.SteelWeightRes.text() + " кг, Температурой " + self.resultSteelTemperature.text() + \
                       "C, со следующим содержанием веществ [%масс]:\n" + "Углерод: " + str(self.SteelChemResult.item(0,0).text()) + \
                       ", Кремний: " + str(self.SteelChemResult.item(0,1).text()) + ", Марганец: " + str(self.SteelChemResult.item(0,2).text()) + \
                       ", Сера: " + str(self.SteelChemResult.item(0,3).text()) + ", Фосфор: " + str(self.SteelChemResult.item(0,4).text())
            file.write(filetext)
            file.close()
        except Exception as err:
            s = 0

    def setupUi(self, OperatorForm):
        OperatorForm.setObjectName("OperatorForm")
        OperatorForm.resize(993, 670)
        OperatorForm.setMinimumSize(QtCore.QSize(993, 670))
        OperatorForm.setMaximumSize(QtCore.QSize(993, 670))
        winIcon = QtGui.QIcon()
        winIcon.addPixmap(QtGui.QPixmap("SteelmakingConverter/Pictures/steel_ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        OperatorForm.setWindowIcon(winIcon)
        self.centralwidget = QtWidgets.QWidget(OperatorForm)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 991, 731))
        self.tabWidget.setMinimumSize(QtCore.QSize(981, 731))
        self.tabWidget.setMaximumSize(QtCore.QSize(981, 731))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.groupBox = QtWidgets.QGroupBox(self.tab)
        self.groupBox.setGeometry(QtCore.QRect(20, 70, 301, 141))
        self.groupBox.setObjectName("groupBox")
        self.groupBox_4 = QtWidgets.QGroupBox(self.groupBox)
        self.groupBox_4.setGeometry(QtCore.QRect(10, 20, 281, 111))
        self.groupBox_4.setObjectName("groupBox_4")
        self.label = QtWidgets.QLabel(self.groupBox_4)
        self.label.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.groupBox_4)
        self.label_2.setGeometry(QtCore.QRect(10, 50, 71, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox_4)
        self.label_3.setGeometry(QtCore.QRect(150, 20, 51, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.groupBox_4)
        self.label_4.setGeometry(QtCore.QRect(150, 50, 61, 16))
        self.label_4.setObjectName("label_4")
        self.steelCarbon = QtWidgets.QLineEdit(self.groupBox_4)
        self.steelCarbon.setGeometry(QtCore.QRect(80, 20, 51, 20))
        self.steelCarbon.setObjectName("steelCarbon")
        self.steelSilicon = QtWidgets.QLineEdit(self.groupBox_4)
        self.steelSilicon.setGeometry(QtCore.QRect(80, 50, 51, 20))
        self.steelSilicon.setObjectName("steelSilicon")
        self.steelSerum = QtWidgets.QLineEdit(self.groupBox_4)
        self.steelSerum.setGeometry(QtCore.QRect(220, 20, 51, 20))
        self.steelSerum.setObjectName("steelSerum")
        self.steelPhosphor = QtWidgets.QLineEdit(self.groupBox_4)
        self.steelPhosphor.setGeometry(QtCore.QRect(220, 50, 51, 20))
        self.steelPhosphor.setObjectName("steelPhosphor")
        self.label_26 = QtWidgets.QLabel(self.groupBox_4)
        self.label_26.setGeometry(QtCore.QRect(60, 80, 81, 16))
        self.label_26.setObjectName("label_26")
        self.steelManganese = QtWidgets.QLineEdit(self.groupBox_4)
        self.steelManganese.setEnabled(True)
        self.steelManganese.setGeometry(QtCore.QRect(150, 80, 51, 20))
        self.steelManganese.setText("")
        self.steelManganese.setObjectName("steelManganese")
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_2.setGeometry(QtCore.QRect(330, 10, 301, 201))
        self.groupBox_2.setObjectName("groupBox_2")
        self.castTemperature = QtWidgets.QLineEdit(self.groupBox_2)
        self.castTemperature.setGeometry(QtCore.QRect(110, 20, 81, 20))
        self.castTemperature.setText("")
        self.castTemperature.setObjectName("castTemperature")
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setGeometry(QtCore.QRect(10, 20, 101, 16))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.groupBox_2)
        self.label_6.setGeometry(QtCore.QRect(10, 50, 101, 16))
        self.label_6.setObjectName("label_6")
        self.castWeight = QtWidgets.QLineEdit(self.groupBox_2)
        self.castWeight.setGeometry(QtCore.QRect(110, 50, 81, 20))
        self.castWeight.setText("")
        self.castWeight.setObjectName("castWeight")
        self.groupBox_6 = QtWidgets.QGroupBox(self.groupBox_2)
        self.groupBox_6.setGeometry(QtCore.QRect(10, 80, 281, 111))
        self.groupBox_6.setObjectName("groupBox_6")
        self.label_7 = QtWidgets.QLabel(self.groupBox_6)
        self.label_7.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(self.groupBox_6)
        self.label_8.setGeometry(QtCore.QRect(10, 50, 71, 16))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(self.groupBox_6)
        self.label_9.setGeometry(QtCore.QRect(150, 20, 51, 16))
        self.label_9.setObjectName("label_9")
        self.label_10 = QtWidgets.QLabel(self.groupBox_6)
        self.label_10.setGeometry(QtCore.QRect(150, 50, 61, 16))
        self.label_10.setObjectName("label_10")
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
        self.groupBox_5 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_5.setGeometry(QtCore.QRect(20, 220, 171, 80))
        self.groupBox_5.setObjectName("groupBox_5")
        self.MetalCharge = QtWidgets.QLineEdit(self.groupBox_5)
        self.MetalCharge.setEnabled(False)
        self.MetalCharge.setGeometry(QtCore.QRect(10, 40, 51, 20))
        self.MetalCharge.setObjectName("MetalCharge")
        self.label_16 = QtWidgets.QLabel(self.groupBox_5)
        self.label_16.setGeometry(QtCore.QRect(10, 20, 41, 16))
        self.label_16.setObjectName("label_16")
        self.calcMetalCharge = QtWidgets.QPushButton(self.groupBox_5)
        self.calcMetalCharge.setEnabled(True)
        self.calcMetalCharge.setGeometry(QtCore.QRect(110, 10, 51, 61))
        self.calcMetalCharge.setText("")
        self.calcMetalCharge.clicked.connect(self.calcMetalChargeClicked)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/calculate.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.calcMetalCharge.setIcon(icon)
        self.calcMetalCharge.setIconSize(QtCore.QSize(48, 48))
        self.calcMetalCharge.setObjectName("calcMetalCharge")
        self.groupBox_3 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_3.setGeometry(QtCore.QRect(640, 10, 301, 201))
        self.groupBox_3.setObjectName("groupBox_3")
        self.label_11 = QtWidgets.QLabel(self.groupBox_3)
        self.label_11.setGeometry(QtCore.QRect(10, 30, 101, 16))
        self.label_11.setObjectName("label_11")
        self.scrapWeight = QtWidgets.QLineEdit(self.groupBox_3)
        self.scrapWeight.setGeometry(QtCore.QRect(70, 30, 81, 20))
        self.scrapWeight.setText("")
        self.scrapWeight.setObjectName("scrapWeight")
        self.groupBox_7 = QtWidgets.QGroupBox(self.groupBox_3)
        self.groupBox_7.setGeometry(QtCore.QRect(10, 80, 281, 111))
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
        self.groupBox_8 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_8.setGeometry(QtCore.QRect(200, 220, 431, 80))
        self.groupBox_8.setObjectName("groupBox_8")
        self.label_17 = QtWidgets.QLabel(self.groupBox_8)
        self.label_17.setGeometry(QtCore.QRect(10, 20, 71, 16))
        self.label_17.setObjectName("label_17")
        self.ChemCarbon = QtWidgets.QLineEdit(self.groupBox_8)
        self.ChemCarbon.setEnabled(False)
        self.ChemCarbon.setGeometry(QtCore.QRect(80, 20, 51, 20))
        self.ChemCarbon.setObjectName("ChemCarbon")
        self.label_18 = QtWidgets.QLabel(self.groupBox_8)
        self.label_18.setGeometry(QtCore.QRect(10, 50, 51, 16))
        self.label_18.setObjectName("label_18")
        self.ChemSerum = QtWidgets.QLineEdit(self.groupBox_8)
        self.ChemSerum.setEnabled(False)
        self.ChemSerum.setGeometry(QtCore.QRect(80, 50, 51, 20))
        self.ChemSerum.setObjectName("ChemSerum")
        self.ChemSilicon = QtWidgets.QLineEdit(self.groupBox_8)
        self.ChemSilicon.setEnabled(False)
        self.ChemSilicon.setGeometry(QtCore.QRect(210, 20, 51, 20))
        self.ChemSilicon.setObjectName("ChemSilicon")
        self.label_19 = QtWidgets.QLabel(self.groupBox_8)
        self.label_19.setGeometry(QtCore.QRect(140, 20, 71, 16))
        self.label_19.setObjectName("label_19")
        self.ChemPhosphor = QtWidgets.QLineEdit(self.groupBox_8)
        self.ChemPhosphor.setEnabled(False)
        self.ChemPhosphor.setGeometry(QtCore.QRect(210, 50, 51, 20))
        self.ChemPhosphor.setObjectName("ChemPhosphor")
        self.label_20 = QtWidgets.QLabel(self.groupBox_8)
        self.label_20.setGeometry(QtCore.QRect(140, 50, 61, 16))
        self.label_20.setObjectName("label_20")
        self.ChemManganese = QtWidgets.QLineEdit(self.groupBox_8)
        self.ChemManganese.setEnabled(False)
        self.ChemManganese.setGeometry(QtCore.QRect(350, 20, 51, 20))
        self.ChemManganese.setText("")
        self.ChemManganese.setObjectName("ChemManganese")
        self.label_21 = QtWidgets.QLabel(self.groupBox_8)
        self.label_21.setGeometry(QtCore.QRect(270, 20, 91, 16))
        self.label_21.setObjectName("label_21")
        self.groupBox_9 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_9.setGeometry(QtCore.QRect(20, 310, 901, 281))
        self.groupBox_9.setObjectName("groupBox_9")
        # self.MetalCharge_2 = QtWidgets.QLineEdit(self.groupBox_9)
        # self.MetalCharge_2.setEnabled(False)
        # self.MetalCharge_2.setGeometry(QtCore.QRect(70, 30, 71, 20))
        # self.MetalCharge_2.setObjectName("MetalCharge_2")
        # self.label_22 = QtWidgets.QLabel(self.groupBox_9)
        # self.label_22.setGeometry(QtCore.QRect(20, 30, 71, 16))
        # self.label_22.setObjectName("label_22")
        self.OxidationTable = QtWidgets.QTableWidget(self.groupBox_9)
        self.OxidationTable.setEnabled(False)
        self.OxidationTable.setGeometry(QtCore.QRect(10, 60, 811, 211))
        self.OxidationTable.setObjectName("OxidationTable")
        self.OxidationTable.setColumnCount(8)
        self.OxidationTable.setRowCount(6)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.OxidationTable.setItem(0, 0, item)
        self.OxidationTable.horizontalHeader().setDefaultSectionSize(80)
        self.calcTable = QtWidgets.QPushButton(self.groupBox_9)
        self.calcTable.setEnabled(True)
        self.calcTable.setGeometry(QtCore.QRect(830, 60, 51, 61))
        self.calcTable.setText("")
        self.calcTable.setIcon(icon)
        self.calcTable.setIconSize(QtCore.QSize(48, 48))
        self.calcTable.setObjectName("calcTable")
        self.calcTable.clicked.connect(self.calcTableClick)
        self.NextSlag = QtWidgets.QLabel(self.tab)
        self.NextSlag.setEnabled(False)
        self.NextSlag.setGeometry(QtCore.QRect(940, 530, 61, 61))
        self.NextSlag.setText("")
        self.NextSlag.setPixmap(QtGui.QPixmap(":/icons/icons/arrow_right.ico"))
        self.NextSlag.setScaledContents(True)
        self.NextSlag.setObjectName("NextSlag")
        self.groupBox_11 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_11.setGeometry(QtCore.QRect(20, 10, 301, 80))
        self.groupBox_11.setObjectName("groupBox_11")
        self.ModeComboBox = QtWidgets.QComboBox(self.groupBox_11)
        self.ModeComboBox.setGeometry(QtCore.QRect(70, 30, 141, 22))
        self.ModeComboBox.setObjectName("ModeComboBox")
        self.label_23 = QtWidgets.QLabel(self.groupBox_11)
        self.label_23.setGeometry(QtCore.QRect(10, 30, 61, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_23.setFont(font)
        self.label_23.setObjectName("label_23")
        self.AddNewMode = QtWidgets.QPushButton(self.groupBox_11)
        self.AddNewMode.setEnabled(False)
        self.AddNewMode.setGeometry(QtCore.QRect(260, 50, 31, 21))
        self.AddNewMode.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/add.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.AddNewMode.setIcon(icon1)
        self.AddNewMode.setObjectName("AddNewMode")
        self.AddNewMode.clicked.connect(self.chooseMods)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.groupBox_10 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_10.setGeometry(QtCore.QRect(20, 10, 231, 251))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.groupBox_10.setFont(font)
        self.groupBox_10.setFlat(False)
        self.groupBox_10.setCheckable(False)
        self.groupBox_10.setObjectName("groupBox_10")
        self.FluxeTable = QtWidgets.QTableWidget(self.groupBox_10)
        self.FluxeTable.setGeometry(QtCore.QRect(10, 60, 211, 151))
        self.FluxeTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.FluxeTable.setObjectName("FluxeTable")
        self.FluxeTable.setColumnCount(2)
        self.FluxeTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.FluxeTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.FluxeTable.setHorizontalHeaderItem(1, item)
        self.AddFluxeButton = QtWidgets.QPushButton(self.groupBox_10)
        self.AddFluxeButton.setGeometry(QtCore.QRect(160, 220, 31, 21))
        self.AddFluxeButton.setText("")
        self.AddFluxeButton.setIcon(icon1)
        self.AddFluxeButton.setObjectName("AddFluxeButton")
        self.AddFluxeButton.clicked.connect(self.AddFluxeButtonClicked)
        self.tip_flyusa_label = QtWidgets.QLabel(self.groupBox_10)
        self.tip_flyusa_label.setGeometry(QtCore.QRect(10, 30, 71, 16))
        self.tip_flyusa_label.setObjectName("tip_flyusa_label")
        self.FluxeType = QtWidgets.QComboBox(self.groupBox_10)
        self.FluxeType.setGeometry(QtCore.QRect(80, 30, 141, 22))
        self.FluxeType.setEditable(False)
        self.FluxeType.setObjectName("FluxeType")
        self.RemoveFluxeButton = QtWidgets.QPushButton(self.groupBox_10)
        self.RemoveFluxeButton.setGeometry(QtCore.QRect(190, 220, 31, 21))
        self.RemoveFluxeButton.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/remove.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RemoveFluxeButton.setIcon(icon2)
        self.RemoveFluxeButton.setObjectName("RemoveFluxeButton")
        self.RemoveFluxeButton.clicked.connect(self.removeFluxeButtonClicked)
        self.shlak_group_box = QtWidgets.QGroupBox(self.tab_2)
        self.shlak_group_box.setGeometry(QtCore.QRect(260, 20, 651, 241))
        self.shlak_group_box.setObjectName("shlak_group_box")
        self.him_sostav_shlaka_group_box = QtWidgets.QGroupBox(self.shlak_group_box)
        self.him_sostav_shlaka_group_box.setGeometry(QtCore.QRect(10, 70, 311, 161))
        self.him_sostav_shlaka_group_box.setObjectName("him_sostav_shlaka_group_box")
        self.SlagSiO2Label = QtWidgets.QLabel(self.him_sostav_shlaka_group_box)
        self.SlagSiO2Label.setGeometry(QtCore.QRect(10, 30, 46, 13))
        self.SlagSiO2Label.setObjectName("SlagSiO2Label")
        self.SlagCaOLabel = QtWidgets.QLabel(self.him_sostav_shlaka_group_box)
        self.SlagCaOLabel.setGeometry(QtCore.QRect(10, 60, 46, 13))
        self.SlagCaOLabel.setObjectName("SlagCaOLabel")
        self.SlagMgOLabel = QtWidgets.QLabel(self.him_sostav_shlaka_group_box)
        self.SlagMgOLabel.setGeometry(QtCore.QRect(10, 90, 46, 13))
        self.SlagMgOLabel.setObjectName("SlagMgOLabel")
        self.SlagAl2O3Label = QtWidgets.QLabel(self.him_sostav_shlaka_group_box)
        self.SlagAl2O3Label.setGeometry(QtCore.QRect(170, 30, 46, 13))
        self.SlagAl2O3Label.setObjectName("SlagAl2O3Label")
        self.SlagOthersLabel = QtWidgets.QLabel(self.him_sostav_shlaka_group_box)
        self.SlagOthersLabel.setGeometry(QtCore.QRect(10, 120, 46, 13))
        self.SlagOthersLabel.setObjectName("SlagOthersLabel")
        self.SlagSiO2 = QtWidgets.QLineEdit(self.him_sostav_shlaka_group_box)
        self.SlagSiO2.setEnabled(False)
        self.SlagSiO2.setGeometry(QtCore.QRect(60, 30, 91, 20))
        self.SlagSiO2.setInputMask("")
        self.SlagSiO2.setObjectName("SlagSiO2")
        self.SlagCaO = QtWidgets.QLineEdit(self.him_sostav_shlaka_group_box)
        self.SlagCaO.setEnabled(False)
        self.SlagCaO.setGeometry(QtCore.QRect(60, 60, 91, 20))
        self.SlagCaO.setInputMask("")
        self.SlagCaO.setObjectName("SlagCaO")
        self.SlagMgO = QtWidgets.QLineEdit(self.him_sostav_shlaka_group_box)
        self.SlagMgO.setEnabled(False)
        self.SlagMgO.setGeometry(QtCore.QRect(60, 90, 91, 20))
        self.SlagMgO.setInputMask("")
        self.SlagMgO.setObjectName("SlagMgO")
        self.SlagAl2O3 = QtWidgets.QLineEdit(self.him_sostav_shlaka_group_box)
        self.SlagAl2O3.setEnabled(False)
        self.SlagAl2O3.setGeometry(QtCore.QRect(210, 30, 91, 20))
        self.SlagAl2O3.setInputMask("")
        self.SlagAl2O3.setObjectName("SlagAl2O3")
        self.SlagOthers = QtWidgets.QLineEdit(self.him_sostav_shlaka_group_box)
        self.SlagOthers.setEnabled(False)
        self.SlagOthers.setGeometry(QtCore.QRect(60, 120, 91, 20))
        self.SlagOthers.setInputMask("")
        self.SlagOthers.setObjectName("SlagOthers")
        self.SlagFeO = QtWidgets.QLineEdit(self.him_sostav_shlaka_group_box)
        self.SlagFeO.setEnabled(False)
        self.SlagFeO.setGeometry(QtCore.QRect(210, 60, 91, 20))
        self.SlagFeO.setInputMask("")
        self.SlagFeO.setObjectName("SlagFeO")
        self.SlagFeOLabel = QtWidgets.QLabel(self.him_sostav_shlaka_group_box)
        self.SlagFeOLabel.setGeometry(QtCore.QRect(170, 60, 46, 13))
        self.SlagFeOLabel.setObjectName("SlagFeOLabel")
        self.SlagFe2O3 = QtWidgets.QLineEdit(self.him_sostav_shlaka_group_box)
        self.SlagFe2O3.setEnabled(False)
        self.SlagFe2O3.setGeometry(QtCore.QRect(210, 90, 91, 20))
        self.SlagFe2O3.setInputMask("")
        self.SlagFe2O3.setObjectName("SlagFe2O3")
        self.SlagFe2O3Label = QtWidgets.QLabel(self.him_sostav_shlaka_group_box)
        self.SlagFe2O3Label.setGeometry(QtCore.QRect(170, 90, 46, 13))
        self.SlagFe2O3Label.setObjectName("SlagFe2O3Label")
        self.SlagWeightLabel = QtWidgets.QLabel(self.shlak_group_box)
        self.SlagWeightLabel.setGeometry(QtCore.QRect(20, 30, 61, 16))
        self.SlagWeightLabel.setObjectName("SlagWeightLabel")
        self.SlagWeight = QtWidgets.QLineEdit(self.shlak_group_box)
        self.SlagWeight.setEnabled(False)
        self.SlagWeight.setGeometry(QtCore.QRect(80, 30, 121, 20))
        self.SlagWeight.setObjectName("SlagWeight")
        self.SlagCalc = QtWidgets.QPushButton(self.shlak_group_box)
        self.SlagCalc.setEnabled(True)
        self.SlagCalc.setGeometry(QtCore.QRect(590, 10, 51, 61))
        self.SlagCalc.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("SteelmakingConverter/Pictures/calculate.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.SlagCalc.setIcon(icon3)
        self.SlagCalc.setIconSize(QtCore.QSize(48, 48))
        self.SlagCalc.setObjectName("SlagCalc")
        self.SlagCalc.clicked.connect(self.slagCalcClicked)
        self.him_sostav_shlaka_v_procentah_group_box = QtWidgets.QGroupBox(self.shlak_group_box)
        self.him_sostav_shlaka_v_procentah_group_box.setGeometry(QtCore.QRect(330, 70, 311, 161))
        self.him_sostav_shlaka_v_procentah_group_box.setObjectName("him_sostav_shlaka_v_procentah_group_box")
        self.SlagSiO2Perc = QtWidgets.QLineEdit(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagSiO2Perc.setEnabled(False)
        self.SlagSiO2Perc.setGeometry(QtCore.QRect(60, 30, 91, 20))
        self.SlagSiO2Perc.setInputMask("")
        self.SlagSiO2Perc.setObjectName("SlagSiO2Perc")
        self.SlagAl2O3Label_2 = QtWidgets.QLabel(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagAl2O3Label_2.setGeometry(QtCore.QRect(170, 30, 46, 13))
        self.SlagAl2O3Label_2.setObjectName("SlagAl2O3Label_2")
        self.SlagAl2O3Perc = QtWidgets.QLineEdit(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagAl2O3Perc.setEnabled(False)
        self.SlagAl2O3Perc.setGeometry(QtCore.QRect(210, 30, 91, 20))
        self.SlagAl2O3Perc.setInputMask("")
        self.SlagAl2O3Perc.setObjectName("SlagAl2O3Perc")
        self.SlagFeOPerc = QtWidgets.QLineEdit(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagFeOPerc.setEnabled(False)
        self.SlagFeOPerc.setGeometry(QtCore.QRect(210, 60, 91, 20))
        self.SlagFeOPerc.setInputMask("")
        self.SlagFeOPerc.setObjectName("SlagFeOPerc")
        self.SlagFeOLabel_2 = QtWidgets.QLabel(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagFeOLabel_2.setGeometry(QtCore.QRect(170, 60, 46, 13))
        self.SlagFeOLabel_2.setObjectName("SlagFeOLabel_2")
        self.SlagFe2O3Label_2 = QtWidgets.QLabel(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagFe2O3Label_2.setGeometry(QtCore.QRect(170, 90, 46, 13))
        self.SlagFe2O3Label_2.setObjectName("SlagFe2O3Label_2")
        self.SlagSiO2Label_2 = QtWidgets.QLabel(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagSiO2Label_2.setGeometry(QtCore.QRect(10, 30, 46, 13))
        self.SlagSiO2Label_2.setObjectName("SlagSiO2Label_2")
        self.SlagCaOPerc = QtWidgets.QLineEdit(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagCaOPerc.setEnabled(False)
        self.SlagCaOPerc.setGeometry(QtCore.QRect(60, 60, 91, 20))
        self.SlagCaOPerc.setInputMask("")
        self.SlagCaOPerc.setObjectName("SlagCaOPerc")
        self.SlagCaOLabel_2 = QtWidgets.QLabel(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagCaOLabel_2.setGeometry(QtCore.QRect(10, 60, 46, 13))
        self.SlagCaOLabel_2.setObjectName("SlagCaOLabel_2")
        self.SlagOthersPerc = QtWidgets.QLineEdit(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagOthersPerc.setEnabled(False)
        self.SlagOthersPerc.setGeometry(QtCore.QRect(60, 120, 91, 20))
        self.SlagOthersPerc.setInputMask("")
        self.SlagOthersPerc.setObjectName("SlagOthersPerc")
        self.SlagMgOPerc = QtWidgets.QLineEdit(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagMgOPerc.setEnabled(False)
        self.SlagMgOPerc.setGeometry(QtCore.QRect(60, 90, 91, 20))
        self.SlagMgOPerc.setInputMask("")
        self.SlagMgOPerc.setObjectName("SlagMgOPerc")
        self.SlagMgOLabel_2 = QtWidgets.QLabel(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagMgOLabel_2.setGeometry(QtCore.QRect(10, 90, 46, 13))
        self.SlagMgOLabel_2.setObjectName("SlagMgOLabel_2")
        self.SlagFe2O3Perc = QtWidgets.QLineEdit(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagFe2O3Perc.setEnabled(False)
        self.SlagFe2O3Perc.setGeometry(QtCore.QRect(210, 90, 91, 20))
        self.SlagFe2O3Perc.setInputMask("")
        self.SlagFe2O3Perc.setObjectName("SlagFe2O3Perc")
        self.SlagOthersLabel_2 = QtWidgets.QLabel(self.him_sostav_shlaka_v_procentah_group_box)
        self.SlagOthersLabel_2.setGeometry(QtCore.QRect(10, 120, 46, 13))
        self.SlagOthersLabel_2.setObjectName("SlagOthersLabel_2")
        self.raschet_dutya_group_box = QtWidgets.QGroupBox(self.tab_2)
        self.raschet_dutya_group_box.setGeometry(QtCore.QRect(20, 270, 371, 231))
        self.raschet_dutya_group_box.setObjectName("raschet_dutya_group_box")
        self.TotalConsumptionOfBlastKg = QtWidgets.QLineEdit(self.raschet_dutya_group_box)
        self.TotalConsumptionOfBlastKg.setEnabled(False)
        self.TotalConsumptionOfBlastKg.setGeometry(QtCore.QRect(260, 70, 91, 20))
        self.TotalConsumptionOfBlastKg.setObjectName("TotalConsumptionOfBlastKg")
        self.ExcessBlast = QtWidgets.QLineEdit(self.raschet_dutya_group_box)
        self.ExcessBlast.setEnabled(False)
        self.ExcessBlast.setGeometry(QtCore.QRect(260, 130, 91, 20))
        self.ExcessBlast.setObjectName("ExcessBlast")
        self.TotalConsumptionOfBlastM3 = QtWidgets.QLineEdit(self.raschet_dutya_group_box)
        self.TotalConsumptionOfBlastM3.setEnabled(False)
        self.TotalConsumptionOfBlastM3.setGeometry(QtCore.QRect(260, 100, 91, 20))
        self.TotalConsumptionOfBlastM3.setObjectName("TotalConsumptionOfBlastM3")
        self.TotalOxygenDemandBlast = QtWidgets.QLineEdit(self.raschet_dutya_group_box)
        self.TotalOxygenDemandBlast.setEnabled(False)
        self.TotalOxygenDemandBlast.setGeometry(QtCore.QRect(260, 40, 91, 20))
        self.TotalOxygenDemandBlast.setObjectName("TotalOxygenDemandBlast")
        self.TotalOxygenDemandBlastLabel = QtWidgets.QLabel(self.raschet_dutya_group_box)
        self.TotalOxygenDemandBlastLabel.setGeometry(QtCore.QRect(20, 40, 231, 16))
        self.TotalOxygenDemandBlastLabel.setObjectName("TotalOxygenDemandBlastLabel")
        self.TotalConsumptionOfBlastKgLabel = QtWidgets.QLabel(self.raschet_dutya_group_box)
        self.TotalConsumptionOfBlastKgLabel.setGeometry(QtCore.QRect(20, 70, 191, 16))
        self.TotalConsumptionOfBlastKgLabel.setObjectName("TotalConsumptionOfBlastKgLabel")
        self.ExcessBlastLabel = QtWidgets.QLabel(self.raschet_dutya_group_box)
        self.ExcessBlastLabel.setGeometry(QtCore.QRect(20, 130, 201, 16))
        self.ExcessBlastLabel.setObjectName("ExcessBlastLabel")
        self.TotalConsumptionOfBlastM3Label = QtWidgets.QLabel(self.raschet_dutya_group_box)
        self.TotalConsumptionOfBlastM3Label.setGeometry(QtCore.QRect(20, 100, 191, 16))
        self.TotalConsumptionOfBlastM3Label.setObjectName("TotalConsumptionOfBlastM3Label")
        self.BlastCalc = QtWidgets.QPushButton(self.raschet_dutya_group_box)
        self.BlastCalc.setEnabled(True)
        self.BlastCalc.setGeometry(QtCore.QRect(300, 160, 51, 61))
        self.BlastCalc.setText("")
        self.BlastCalc.setIcon(icon)
        self.BlastCalc.setIconSize(QtCore.QSize(48, 48))
        self.BlastCalc.setObjectName("BlastCalc")
        self.BlastCalc.clicked.connect(self.blastCalcClicked)
        self.changeSetings = QtWidgets.QCheckBox(self.raschet_dutya_group_box)
        self.changeSetings.setGeometry(QtCore.QRect(20, 20, 221, 17))
        self.changeSetings.setObjectName("changeSetings")
        self.changeSetings.toggled.connect(self.TotalOxygenDemandBlast.setEnabled)
        self.changeSetings.toggled.connect(self.TotalConsumptionOfBlastKg.setEnabled)
        self.changeSetings.toggled.connect(self.TotalConsumptionOfBlastM3.setEnabled)
        self.changeSetings.toggled.connect(self.ExcessBlast.setEnabled)
        self.NextMat = QtWidgets.QLabel(self.tab_2)
        self.NextMat.setEnabled(False)
        self.NextMat.setGeometry(QtCore.QRect(940, 540, 61, 61))
        self.NextMat.setText("")
        self.NextMat.setPixmap(QtGui.QPixmap(":/icons/icons/arrow_right.ico"))
        self.NextMat.setScaledContents(True)
        self.NextMat.setObjectName("NextMat")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.ReclaimedIronWeightLabel = QtWidgets.QLabel(self.tab_3)
        self.ReclaimedIronWeightLabel.setGeometry(QtCore.QRect(10, 20, 371, 21))
        self.ReclaimedIronWeightLabel.setLineWidth(0)
        self.ReclaimedIronWeightLabel.setObjectName("ReclaimedIronWeightLabel")
        self.ReclaimedIronWeight = QtWidgets.QLineEdit(self.tab_3)
        self.ReclaimedIronWeight.setEnabled(False)
        self.ReclaimedIronWeight.setGeometry(QtCore.QRect(380, 20, 81, 20))
        self.ReclaimedIronWeight.setObjectName("ReclaimedIronWeight")
        self.IncomingData = QtWidgets.QTableWidget(self.tab_3)
        self.IncomingData.setEnabled(False)
        self.IncomingData.setGeometry(QtCore.QRect(10, 90, 211, 361))
        self.IncomingData.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.IncomingData.setObjectName("IncomingData")
        self.IncomingData.setColumnCount(2)
        self.IncomingData.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingData.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingData.setHorizontalHeaderItem(1, item)
        self.OutputData = QtWidgets.QTableWidget(self.tab_3)
        self.OutputData.setEnabled(False)
        self.OutputData.setGeometry(QtCore.QRect(250, 90, 211, 361))
        self.OutputData.setObjectName("OutputData")
        self.OutputData.setColumnCount(2)
        self.OutputData.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.OutputData.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputData.setHorizontalHeaderItem(1, item)
        self.LiquidIronYield = QtWidgets.QLineEdit(self.tab_3)
        self.LiquidIronYield.setEnabled(False)
        self.LiquidIronYield.setGeometry(QtCore.QRect(380, 50, 81, 20))
        self.LiquidIronYield.setObjectName("LiquidIronYield")
        self.vyhod_zhidkovo_metalla_pered_raskisleniem_label = QtWidgets.QLabel(self.tab_3)
        self.vyhod_zhidkovo_metalla_pered_raskisleniem_label.setGeometry(QtCore.QRect(10, 50, 311, 16))
        self.vyhod_zhidkovo_metalla_pered_raskisleniem_label.setObjectName("vyhod_zhidkovo_metalla_pered_raskisleniem_label")
        self.OutputDataGroupBox = QtWidgets.QGroupBox(self.tab_3)
        self.OutputDataGroupBox.setGeometry(QtCore.QRect(470, 80, 471, 371))
        self.OutputDataGroupBox.setObjectName("OutputDataGroupBox")
        self.MassOfOxidizedImpuritiesLabel = QtWidgets.QLabel(self.OutputDataGroupBox)
        self.MassOfOxidizedImpuritiesLabel.setGeometry(QtCore.QRect(20, 30, 181, 16))
        self.MassOfOxidizedImpuritiesLabel.setObjectName("MassOfOxidizedImpuritiesLabel")
        self.MassOfOxidesPassingIntoSlagLabel = QtWidgets.QLabel(self.OutputDataGroupBox)
        self.MassOfOxidesPassingIntoSlagLabel.setGeometry(QtCore.QRect(20, 50, 251, 16))
        self.MassOfOxidesPassingIntoSlagLabel.setObjectName("MassOfOxidesPassingIntoSlagLabel")
        self.LossWithCarryOverLabel = QtWidgets.QLabel(self.OutputDataGroupBox)
        self.LossWithCarryOverLabel.setGeometry(QtCore.QRect(20, 70, 251, 16))
        self.LossWithCarryOverLabel.setObjectName("LossWithCarryOverLabel")
        self.DustLossLabel = QtWidgets.QLabel(self.OutputDataGroupBox)
        self.DustLossLabel.setGeometry(QtCore.QRect(20, 90, 251, 16))
        self.DustLossLabel.setObjectName("DustLossLabel")
        self.MassOfOxidizedImpurities = QtWidgets.QLineEdit(self.OutputDataGroupBox)
        self.MassOfOxidizedImpurities.setEnabled(False)
        self.MassOfOxidizedImpurities.setGeometry(QtCore.QRect(350, 30, 101, 20))
        self.MassOfOxidizedImpurities.setObjectName("MassOfOxidizedImpurities")
        self.MassOfOxidesPassingIntoSlag = QtWidgets.QLineEdit(self.OutputDataGroupBox)
        self.MassOfOxidesPassingIntoSlag.setEnabled(False)
        self.MassOfOxidesPassingIntoSlag.setGeometry(QtCore.QRect(350, 50, 101, 20))
        self.MassOfOxidesPassingIntoSlag.setObjectName("MassOfOxidesPassingIntoSlag")
        self.LossWithCarryOver = QtWidgets.QLineEdit(self.OutputDataGroupBox)
        self.LossWithCarryOver.setEnabled(False)
        self.LossWithCarryOver.setGeometry(QtCore.QRect(350, 70, 101, 20))
        self.LossWithCarryOver.setObjectName("LossWithCarryOver")
        self.DustLoss = QtWidgets.QLineEdit(self.OutputDataGroupBox)
        self.DustLoss.setEnabled(False)
        self.DustLoss.setGeometry(QtCore.QRect(350, 90, 101, 20))
        self.DustLoss.setObjectName("DustLoss")
        self.OutputDataTable = QtWidgets.QTableWidget(self.OutputDataGroupBox)
        self.OutputDataTable.setEnabled(False)
        self.OutputDataTable.setGeometry(QtCore.QRect(20, 120, 441, 241))
        self.OutputDataTable.setObjectName("OutputDataTable")
        self.OutputDataTable.setColumnCount(3)
        self.OutputDataTable.setRowCount(7)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setVerticalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputDataTable.setHorizontalHeaderItem(2, item)
        self.NextTerm = QtWidgets.QLabel(self.tab_3)
        self.NextTerm.setEnabled(False)
        self.NextTerm.setGeometry(QtCore.QRect(950, 540, 61, 61))
        self.NextTerm.setText("")
        self.NextTerm.setPixmap(QtGui.QPixmap(":/icons/icons/arrow_right.ico"))
        self.NextTerm.setScaledContents(True)
        self.NextTerm.setObjectName("NextTerm")
        self.MaterialBalanceCalc = QtWidgets.QPushButton(self.tab_3)
        self.MaterialBalanceCalc.setEnabled(True)
        self.MaterialBalanceCalc.setGeometry(QtCore.QRect(890, 460, 51, 61))
        self.MaterialBalanceCalc.setText("")
        self.MaterialBalanceCalc.setIcon(icon)
        self.MaterialBalanceCalc.setIconSize(QtCore.QSize(48, 48))
        self.MaterialBalanceCalc.setObjectName("MaterialBalanceCalc")
        self.MaterialBalanceCalc.clicked.connect(self.MaterialBalanceCalcClicked)
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.temperatura_zhidkovo_metalla_v_konce_produvki_label_2 = QtWidgets.QLabel(self.tab_4)
        self.temperatura_zhidkovo_metalla_v_konce_produvki_label_2.setGeometry(QtCore.QRect(0, 410, 291, 16))
        self.temperatura_zhidkovo_metalla_v_konce_produvki_label_2.setObjectName("temperatura_zhidkovo_metalla_v_konce_produvki_label_2")
        self.label_49 = QtWidgets.QLabel(self.tab_4)
        self.label_49.setGeometry(QtCore.QRect(290, 540, 201, 16))
        self.label_49.setObjectName("label_49")
        self.rashodnie_statii_group_box_2 = QtWidgets.QGroupBox(self.tab_4)
        self.rashodnie_statii_group_box_2.setGeometry(QtCore.QRect(490, 10, 471, 531))
        self.rashodnie_statii_group_box_2.setObjectName("rashodnie_statii_group_box_2")
        self.HeatDustForm = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.HeatDustForm.setEnabled(False)
        self.HeatDustForm.setGeometry(QtCore.QRect(300, 120, 101, 20))
        self.HeatDustForm.setObjectName("HeatDustForm")
        self.PhysHeatSlag = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.PhysHeatSlag.setEnabled(False)
        self.PhysHeatSlag.setGeometry(QtCore.QRect(300, 40, 101, 20))
        self.PhysHeatSlag.setObjectName("PhysHeatSlag")
        self.phizicheskoe_teplo_zhidkovo_metalla_label_2 = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.phizicheskoe_teplo_zhidkovo_metalla_label_2.setGeometry(QtCore.QRect(20, 20, 221, 16))
        self.phizicheskoe_teplo_zhidkovo_metalla_label_2.setObjectName("phizicheskoe_teplo_zhidkovo_metalla_label_2")
        self.PhysHeatLiquidSteel = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.PhysHeatLiquidSteel.setEnabled(False)
        self.PhysHeatLiquidSteel.setGeometry(QtCore.QRect(300, 20, 101, 20))
        self.PhysHeatLiquidSteel.setObjectName("PhysHeatLiquidSteel")
        self.HeatLosesRemove = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.HeatLosesRemove.setEnabled(False)
        self.HeatLosesRemove.setGeometry(QtCore.QRect(300, 100, 101, 20))
        self.HeatLosesRemove.setObjectName("HeatLosesRemove")
        self.HeatConsDecompos_label = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.HeatConsDecompos_label.setGeometry(QtCore.QRect(20, 80, 281, 16))
        self.HeatConsDecompos_label.setObjectName("HeatConsDecompos_label")
        self.poteri_tepla_s_vynosami_i_vybrosami_label_2 = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.poteri_tepla_s_vynosami_i_vybrosami_label_2.setGeometry(QtCore.QRect(20, 100, 251, 16))
        self.poteri_tepla_s_vynosami_i_vybrosami_label_2.setObjectName("poteri_tepla_s_vynosami_i_vybrosami_label_2")
        self.HeatDustForm_label = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.HeatDustForm_label.setGeometry(QtCore.QRect(20, 120, 251, 16))
        self.HeatDustForm_label.setObjectName("HeatDustForm_label")
        self.phizicheskoe_teplo_othodyashih_gazov_label_2 = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.phizicheskoe_teplo_othodyashih_gazov_label_2.setGeometry(QtCore.QRect(20, 60, 261, 16))
        self.phizicheskoe_teplo_othodyashih_gazov_label_2.setObjectName("phizicheskoe_teplo_othodyashih_gazov_label_2")
        self.PhysHeatOutGas = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.PhysHeatOutGas.setEnabled(False)
        self.PhysHeatOutGas.setGeometry(QtCore.QRect(300, 60, 101, 20))
        self.PhysHeatOutGas.setObjectName("PhysHeatOutGas")
        self.phizicheskoe_teplo_shlaka_label_2 = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.phizicheskoe_teplo_shlaka_label_2.setGeometry(QtCore.QRect(20, 40, 251, 16))
        self.phizicheskoe_teplo_shlaka_label_2.setObjectName("phizicheskoe_teplo_shlaka_label_2")
        self.HeatConsDecompos = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.HeatConsDecompos.setEnabled(False)
        self.HeatConsDecompos.setGeometry(QtCore.QRect(300, 80, 101, 20))
        self.HeatConsDecompos.setObjectName("HeatConsDecompos")
        self.HeatLoses = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.HeatLoses.setEnabled(False)
        self.HeatLoses.setGeometry(QtCore.QRect(300, 160, 101, 20))
        self.HeatLoses.setObjectName("HeatLoses")
        self.teplovie_poteri_label_2 = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.teplovie_poteri_label_2.setGeometry(QtCore.QRect(20, 160, 251, 16))
        self.teplovie_poteri_label_2.setObjectName("teplovie_poteri_label_2")
        self.teplo_na_razlozhenie_karbonatov_label_2 = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.teplo_na_razlozhenie_karbonatov_label_2.setGeometry(QtCore.QRect(20, 140, 281, 16))
        self.teplo_na_razlozhenie_karbonatov_label_2.setObjectName("teplo_na_razlozhenie_karbonatov_label_2")
        self.obshii_rashod_tepla_label_2 = QtWidgets.QLabel(self.rashodnie_statii_group_box_2)
        self.obshii_rashod_tepla_label_2.setGeometry(QtCore.QRect(20, 180, 251, 16))
        self.obshii_rashod_tepla_label_2.setObjectName("obshii_rashod_tepla_label_2")
        self.HeatCarbonDecom = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.HeatCarbonDecom.setEnabled(False)
        self.HeatCarbonDecom.setGeometry(QtCore.QRect(300, 140, 101, 20))
        self.HeatCarbonDecom.setObjectName("HeatCarbonDecom")
        self.TotalHeatCons = QtWidgets.QLineEdit(self.rashodnie_statii_group_box_2)
        self.TotalHeatCons.setEnabled(False)
        self.TotalHeatCons.setGeometry(QtCore.QRect(300, 180, 101, 20))
        self.TotalHeatCons.setObjectName("TotalHeatCons")
        self.OutputHeatTable = QtWidgets.QTableWidget(self.rashodnie_statii_group_box_2)
        self.OutputHeatTable.setEnabled(False)
        self.OutputHeatTable.setGeometry(QtCore.QRect(10, 210, 451, 311))
        self.OutputHeatTable.setObjectName("OutputHeatTable")
        self.OutputHeatTable.setColumnCount(2)
        self.OutputHeatTable.setRowCount(9)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setVerticalHeaderItem(8, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.OutputHeatTable.setHorizontalHeaderItem(1, item)
        self.temperatura_peregreva_label_2 = QtWidgets.QLabel(self.tab_4)
        self.temperatura_peregreva_label_2.setGeometry(QtCore.QRect(0, 430, 251, 16))
        self.temperatura_peregreva_label_2.setObjectName("temperatura_peregreva_label_2")
        self.LiquidSteelTemp = QtWidgets.QLineEdit(self.tab_4)
        self.LiquidSteelTemp.setEnabled(False)
        self.LiquidSteelTemp.setGeometry(QtCore.QRect(300, 410, 101, 20))
        self.LiquidSteelTemp.setObjectName("LiquidSteelTemp")
        self.prihodnie_statii_group_box_2 = QtWidgets.QGroupBox(self.tab_4)
        self.prihodnie_statii_group_box_2.setGeometry(QtCore.QRect(0, 10, 481, 391))
        self.prihodnie_statii_group_box_2.setObjectName("prihodnie_statii_group_box_2")
        self.ChemHeatOxyd = QtWidgets.QLineEdit(self.prihodnie_statii_group_box_2)
        self.ChemHeatOxyd.setEnabled(False)
        self.ChemHeatOxyd.setGeometry(QtCore.QRect(290, 70, 101, 20))
        self.ChemHeatOxyd.setObjectName("ChemHeatOxyd")
        self.ThermalReactEffect = QtWidgets.QLineEdit(self.prihodnie_statii_group_box_2)
        self.ThermalReactEffect.setEnabled(False)
        self.ThermalReactEffect.setGeometry(QtCore.QRect(290, 50, 101, 20))
        self.ThermalReactEffect.setObjectName("ThermalReactEffect")
        self.ChemHeatSlag = QtWidgets.QLineEdit(self.prihodnie_statii_group_box_2)
        self.ChemHeatSlag.setEnabled(False)
        self.ChemHeatSlag.setGeometry(QtCore.QRect(290, 90, 101, 20))
        self.ChemHeatSlag.setObjectName("ChemHeatSlag")
        self.teplovoi_effect_reakcii_shlakoobrazovaniya_label_2 = QtWidgets.QLabel(self.prihodnie_statii_group_box_2)
        self.teplovoi_effect_reakcii_shlakoobrazovaniya_label_2.setGeometry(QtCore.QRect(10, 90, 281, 16))
        self.teplovoi_effect_reakcii_shlakoobrazovaniya_label_2.setObjectName("teplovoi_effect_reakcii_shlakoobrazovaniya_label_2")
        self.teplovoi_effect_reakcii_okisleniya_label_2 = QtWidgets.QLabel(self.prihodnie_statii_group_box_2)
        self.teplovoi_effect_reakcii_okisleniya_label_2.setGeometry(QtCore.QRect(10, 50, 251, 16))
        self.teplovoi_effect_reakcii_okisleniya_label_2.setObjectName("teplovoi_effect_reakcii_okisleniya_label_2")
        self.himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2 = QtWidgets.QLabel(self.prihodnie_statii_group_box_2)
        self.himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2.setGeometry(QtCore.QRect(10, 70, 261, 16))
        self.himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2.setObjectName("himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2")
        self.phizicheskoe_teplo_zhidkovo_chuguna_label_2 = QtWidgets.QLabel(self.prihodnie_statii_group_box_2)
        self.phizicheskoe_teplo_zhidkovo_chuguna_label_2.setGeometry(QtCore.QRect(10, 30, 221, 16))
        self.phizicheskoe_teplo_zhidkovo_chuguna_label_2.setObjectName("phizicheskoe_teplo_zhidkovo_chuguna_label_2")
        self.CastPhysHeat = QtWidgets.QLineEdit(self.prihodnie_statii_group_box_2)
        self.CastPhysHeat.setEnabled(False)
        self.CastPhysHeat.setGeometry(QtCore.QRect(290, 30, 101, 20))
        self.CastPhysHeat.setObjectName("CastPhysHeat")
        self.HeatCO = QtWidgets.QLineEdit(self.prihodnie_statii_group_box_2)
        self.HeatCO.setEnabled(False)
        self.HeatCO.setGeometry(QtCore.QRect(290, 110, 101, 20))
        self.HeatCO.setObjectName("HeatCO")
        self.teplo_ot_dozhiganiya_co_label_2 = QtWidgets.QLabel(self.prihodnie_statii_group_box_2)
        self.teplo_ot_dozhiganiya_co_label_2.setGeometry(QtCore.QRect(10, 110, 251, 16))
        self.teplo_ot_dozhiganiya_co_label_2.setObjectName("teplo_ot_dozhiganiya_co_label_2")
        self.TotalHeatInc = QtWidgets.QLineEdit(self.prihodnie_statii_group_box_2)
        self.TotalHeatInc.setEnabled(False)
        self.TotalHeatInc.setGeometry(QtCore.QRect(290, 130, 101, 20))
        self.TotalHeatInc.setObjectName("TotalHeatInc")
        self.obshii_prihod_tepla_label_2 = QtWidgets.QLabel(self.prihodnie_statii_group_box_2)
        self.obshii_prihod_tepla_label_2.setGeometry(QtCore.QRect(10, 130, 251, 16))
        self.obshii_prihod_tepla_label_2.setObjectName("obshii_prihod_tepla_label_2")
        self.IncomingHeatTable = QtWidgets.QTableWidget(self.prihodnie_statii_group_box_2)
        self.IncomingHeatTable.setEnabled(False)
        self.IncomingHeatTable.setGeometry(QtCore.QRect(0, 160, 471, 221))
        self.IncomingHeatTable.setObjectName("IncomingHeatTable")
        self.IncomingHeatTable.setColumnCount(2)
        self.IncomingHeatTable.setRowCount(6)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingHeatTable.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingHeatTable.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingHeatTable.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingHeatTable.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingHeatTable.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingHeatTable.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingHeatTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.IncomingHeatTable.setHorizontalHeaderItem(1, item)
        self.OverheatTemp = QtWidgets.QLineEdit(self.tab_4)
        self.OverheatTemp.setEnabled(False)
        self.OverheatTemp.setGeometry(QtCore.QRect(300, 430, 101, 20))
        self.OverheatTemp.setObjectName("OverheatTemp")
        self.label_50 = QtWidgets.QLabel(self.tab_4)
        self.label_50.setGeometry(QtCore.QRect(290, 470, 61, 61))
        self.label_50.setText("")
        self.label_50.setPixmap(QtGui.QPixmap(":/icons/icons/arrow_right.ico"))
        self.label_50.setScaledContents(True)
        self.label_50.setObjectName("label_50")
        self.NextSteel = QtWidgets.QLabel(self.tab_4)
        self.NextSteel.setEnabled(False)
        self.NextSteel.setGeometry(QtCore.QRect(940, 540, 61, 61))
        self.NextSteel.setText("")
        self.NextSteel.setPixmap(QtGui.QPixmap(":/icons/icons/arrow_right.ico"))
        self.NextSteel.setScaledContents(True)
        self.NextSteel.setObjectName("NextSteel")
        self.HeatBalanceCalc = QtWidgets.QPushButton(self.tab_4)
        self.HeatBalanceCalc.setEnabled(True)
        self.HeatBalanceCalc.setGeometry(QtCore.QRect(430, 470, 51, 61))
        self.HeatBalanceCalc.setText("")
        self.HeatBalanceCalc.setIcon(icon)
        self.HeatBalanceCalc.setIconSize(QtCore.QSize(48, 48))
        self.HeatBalanceCalc.setObjectName("HeatBalanceCalc")
        self.HeatBalanceCalc.clicked.connect(self.HeatBalanceCalcClicked)
        self.tabWidget.addTab(self.tab_4, "")
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.tip_ferrosplava_label_2 = QtWidgets.QLabel(self.tab_5)
        self.tip_ferrosplava_label_2.setGeometry(QtCore.QRect(10, 10, 101, 16))
        self.tip_ferrosplava_label_2.setObjectName("tip_ferrosplava_label_2")
        self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2 = QtWidgets.QLineEdit(self.tab_5)
        self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2.setEnabled(False)
        self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2.setGeometry(QtCore.QRect(770, 60, 91, 20))
        self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2.setObjectName("vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2")
        self.balans_pri_raskislenii_stali_label_2 = QtWidgets.QLabel(self.tab_5)
        self.balans_pri_raskislenii_stali_label_2.setGeometry(QtCore.QRect(10, 130, 251, 16))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.balans_pri_raskislenii_stali_label_2.setFont(font)
        self.balans_pri_raskislenii_stali_label_2.setObjectName("balans_pri_raskislenii_stali_label_2")
        self.label_51 = QtWidgets.QLabel(self.tab_5)
        self.label_51.setGeometry(QtCore.QRect(770, 40, 211, 16))
        self.label_51.setObjectName("label_51")
        self.FeroType = QtWidgets.QComboBox(self.tab_5)
        self.FeroType.setGeometry(QtCore.QRect(110, 10, 161, 22))
        self.FeroType.setEditable(False)
        self.FeroType.setObjectName("FeroType")
        self.label_52 = QtWidgets.QLabel(self.tab_5)
        self.label_52.setGeometry(QtCore.QRect(630, 40, 141, 16))
        self.label_52.setObjectName("label_52")
        self.ChemEmission = QtWidgets.QTableWidget(self.tab_5)
        self.ChemEmission.setEnabled(True)
        self.ChemEmission.setGeometry(QtCore.QRect(10, 40, 611, 91))
        self.ChemEmission.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ChemEmission.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ChemEmission.setObjectName("ChemEmission")
        self.ChemEmission.setColumnCount(6)
        self.ChemEmission.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.ChemEmission.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.ChemEmission.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.ChemEmission.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.ChemEmission.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.ChemEmission.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.ChemEmission.setHorizontalHeaderItem(5, item)
        self.DeoxidationBalance = QtWidgets.QTableWidget(self.tab_5)
        self.DeoxidationBalance.setEnabled(True)
        self.DeoxidationBalance.setGeometry(QtCore.QRect(10, 150, 931, 221))
        self.DeoxidationBalance.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.DeoxidationBalance.setObjectName("DeoxidationBalance")
        self.DeoxidationBalance.setColumnCount(10)
        self.DeoxidationBalance.setRowCount(6)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(8, item)
        item = QtWidgets.QTableWidgetItem()
        self.DeoxidationBalance.setHorizontalHeaderItem(9, item)
        self.DeoxidationBalance.horizontalHeader().setDefaultSectionSize(70)
        self.rashod_pervovo_ferrosplava_line_edit_2 = QtWidgets.QLineEdit(self.tab_5)
        self.rashod_pervovo_ferrosplava_line_edit_2.setEnabled(False)
        self.rashod_pervovo_ferrosplava_line_edit_2.setGeometry(QtCore.QRect(630, 60, 91, 20))
        self.rashod_pervovo_ferrosplava_line_edit_2.setObjectName("rashod_pervovo_ferrosplava_line_edit_2")
        self.RemoveFero = QtWidgets.QPushButton(self.tab_5)
        self.RemoveFero.setGeometry(QtCore.QRect(320, 10, 31, 21))
        self.RemoveFero.setText("")
        self.RemoveFero.setIcon(icon2)
        self.RemoveFero.setObjectName("RemoveFero")
        self.RemoveFero.clicked.connect(self.removeFeroBtnClicked)
        self.AddFero = QtWidgets.QPushButton(self.tab_5)
        self.AddFero.setGeometry(QtCore.QRect(280, 10, 31, 21))
        self.AddFero.setText("")
        self.AddFero.setIcon(icon1)
        self.AddFero.setObjectName("AddFero")
        self.AddFero.clicked.connect(self.AddFeroBtnClicked)
        self.groupBox_12 = QtWidgets.QGroupBox(self.tab_5)
        self.groupBox_12.setGeometry(QtCore.QRect(10, 380, 931, 201))
        self.groupBox_12.setObjectName("groupBox_12")
        self.SteelChemResult = QtWidgets.QTableWidget(self.groupBox_12)
        self.SteelChemResult.setEnabled(False)
        self.SteelChemResult.setGeometry(QtCore.QRect(310, 30, 511, 61))
        self.SteelChemResult.setObjectName("SteelChemResult")
        self.SteelChemResult.setColumnCount(5)
        self.SteelChemResult.setRowCount(1)
        item = QtWidgets.QTableWidgetItem()
        self.SteelChemResult.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.SteelChemResult.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.SteelChemResult.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.SteelChemResult.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.SteelChemResult.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.SteelChemResult.setHorizontalHeaderItem(4, item)
        self.himicheskii_sostav_poluchennoi_stali_label_2 = QtWidgets.QLabel(self.groupBox_12)
        self.himicheskii_sostav_poluchennoi_stali_label_2.setGeometry(QtCore.QRect(310, 10, 221, 16))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.himicheskii_sostav_poluchennoi_stali_label_2.setFont(font)
        self.himicheskii_sostav_poluchennoi_stali_label_2.setObjectName("himicheskii_sostav_poluchennoi_stali_label_2")
        self.CO2ThrowRes = QtWidgets.QLineEdit(self.groupBox_12)
        self.CO2ThrowRes.setEnabled(True)
        self.CO2ThrowRes.setGeometry(QtCore.QRect(190, 20, 91, 20))
        self.CO2ThrowRes.setObjectName("CO2ThrowRes")
        self.SlagWeightRes = QtWidgets.QLineEdit(self.groupBox_12)
        self.SlagWeightRes.setEnabled(True)
        self.SlagWeightRes.setGeometry(QtCore.QRect(190, 80, 91, 20))
        self.SlagWeightRes.setObjectName("SlagWeightRes")
        self.label_43 = QtWidgets.QLabel(self.groupBox_12)
        self.label_43.setGeometry(QtCore.QRect(10, 20, 181, 16))
        self.label_43.setObjectName("label_43")
        self.label_44 = QtWidgets.QLabel(self.groupBox_12)
        self.label_44.setGeometry(QtCore.QRect(10, 50, 171, 16))
        self.label_44.setObjectName("label_44")
        self.SteelWeightRes = QtWidgets.QLineEdit(self.groupBox_12)
        self.SteelWeightRes.setEnabled(True)
        self.SteelWeightRes.setGeometry(QtCore.QRect(190, 50, 91, 20))
        self.SteelWeightRes.setObjectName("SteelWeightRes")
        self.label_45 = QtWidgets.QLabel(self.groupBox_12)
        self.label_45.setGeometry(QtCore.QRect(10, 80, 171, 16))
        self.label_45.setObjectName("label_45")
        self.label_46 = QtWidgets.QLabel(self.groupBox_12)
        self.label_46.setGeometry(QtCore.QRect(10, 140, 161, 16))
        self.label_46.setObjectName("label_46")
        self.LiningWeightLoss = QtWidgets.QLineEdit(self.groupBox_12)
        self.LiningWeightLoss.setGeometry(QtCore.QRect(190, 140, 91, 20))
        self.LiningWeightLoss.setText("")
        self.LiningWeightLoss.setObjectName("LiningWeightLoss")
        self.label_47 = QtWidgets.QLabel(self.groupBox_12)
        self.label_47.setGeometry(QtCore.QRect(10, 110, 171, 16))
        self.label_47.setObjectName("label_47")
        self.resultSteelTemperature = QtWidgets.QLineEdit(self.groupBox_12)
        self.resultSteelTemperature.setEnabled(True)
        self.resultSteelTemperature.setGeometry(QtCore.QRect(190, 110, 91, 20))
        self.resultSteelTemperature.setObjectName("resultSteelTemperature")
        self.SteelDeoxidationCalc = QtWidgets.QPushButton(self.groupBox_12)
        self.SteelDeoxidationCalc.setEnabled(True)
        self.SteelDeoxidationCalc.setGeometry(QtCore.QRect(870, 40, 51, 61))
        self.SteelDeoxidationCalc.setText("")
        self.SteelDeoxidationCalc.setIcon(icon)
        self.SteelDeoxidationCalc.setIconSize(QtCore.QSize(48, 48))
        self.SteelDeoxidationCalc.setObjectName("SteelDeoxidationCalc")
        self.SteelDeoxidationCalc.clicked.connect(self.deoxCalc)
        self.SlagChemResult = QtWidgets.QTableWidget(self.groupBox_12)
        self.SlagChemResult.setEnabled(False)
        self.SlagChemResult.setGeometry(QtCore.QRect(310, 120, 511, 61))
        self.SlagChemResult.setObjectName("SlagChemResult")
        self.SlagChemResult.setColumnCount(5)
        self.SlagChemResult.setRowCount(1)
        item = QtWidgets.QTableWidgetItem()
        self.SlagChemResult.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.SlagChemResult.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.SlagChemResult.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.SlagChemResult.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.SlagChemResult.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.SlagChemResult.setHorizontalHeaderItem(4, item)
        self.himicheskii_sostav_poluchennoi_stali_label_3 = QtWidgets.QLabel(self.groupBox_12)
        self.himicheskii_sostav_poluchennoi_stali_label_3.setGeometry(QtCore.QRect(310, 100, 221, 16))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.himicheskii_sostav_poluchennoi_stali_label_3.setFont(font)
        self.himicheskii_sostav_poluchennoi_stali_label_3.setObjectName("himicheskii_sostav_poluchennoi_stali_label_3")
        self.tabWidget.addTab(self.tab_5, "")
        OperatorForm.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(OperatorForm)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 993, 21))
        self.menubar.setObjectName("menubar")
        self.Menu = QtWidgets.QMenu(self.menubar)
        self.Menu.setObjectName("Menu")
        self.Help = QtWidgets.QMenu(self.menubar)
        self.Help.setObjectName("Help")
        self.Administrate = QtWidgets.QMenu(self.menubar)
        self.Administrate.setEnabled(False)
        self.Administrate.setObjectName("Administrate")
        OperatorForm.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(OperatorForm)
        self.statusbar.setObjectName("statusbar")
        OperatorForm.setStatusBar(self.statusbar)
        self.about = QtWidgets.QAction(OperatorForm)
        self.about.setObjectName("about")
        self.SaveFile = QtWidgets.QAction(OperatorForm)
        self.SaveFile.setObjectName("SaveFile")
        self.SaveFile.setStatusTip('Save file')
        self.Exit = QtWidgets.QAction(OperatorForm)
        self.Exit.setObjectName("Exit")
        self.addUser = QtWidgets.QAction(OperatorForm)
        self.addUser.setEnabled(False)
        self.addUser.setObjectName("addUser")
        self.AddUser = QtWidgets.QAction(OperatorForm)
        self.AddUser.setEnabled(False)
        self.AddUser.setObjectName("AddUser")
        self.AddDbData = QtWidgets.QAction(OperatorForm)
        self.AddDbData.setEnabled(False)
        self.AddDbData.setObjectName("AddDbData")

        self.Menu.addAction(self.SaveFile)
        self.Menu.addSeparator()
        self.Menu.addAction(self.Exit)
        self.Help.addAction(self.about)
        self.Administrate.addAction(self.AddUser)
        self.Administrate.addAction(self.AddDbData)
        self.menubar.addAction(self.Menu.menuAction())
        self.menubar.addAction(self.Administrate.menuAction())
        self.menubar.addAction(self.Help.menuAction())


        self.Exit.setShortcut('Ctrl+Q')
        self.Exit.triggered.connect(lambda: self.app.Quit)

        self.about.triggered.connect(self.openAbout)
        self.SaveFile.triggered.connect(self.saveResult)

        self.retranslateUi(OperatorForm)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(OperatorForm)

    def retranslateUi(self, OperatorForm):
        _translate = QtCore.QCoreApplication.translate
        OperatorForm.setWindowTitle(_translate("OperatorForm", "Процесс плавки стали"))

        # устанавливаем стандартные значения
        self.steelCarbon.setText("0.085")
        self.steelSerum.setText("0.04")
        self.steelSilicon.setText("0.2")
        self.steelPhosphor.setText("0.035")
        self.steelManganese.setText("0.5")

        self.castTemperature.setText("1400")
        self.castWeight.setText("290")
        self.castCarbon.setText("4")
        self.castSerum.setText("0.025")
        self.castPhosphor.setText("0.15")
        self.castManganese.setText("0.7")
        self.castSilicon.setText("0.6")

        self.scrapWeight.setText("110")
        self.scrapCarbon.setText("0.1")
        self.scrapSerum.setText("0.04")
        self.scrapSilicon.setText("0.2")
        self.scrapManganese.setText("0.05")
        self.scrapPhosphor.setText("0.4")

        self.groupBox.setTitle(_translate("OperatorForm", "Сталь"))
        self.groupBox_4.setTitle(_translate("OperatorForm", "Химический состав, %масс"))
        self.label.setText(_translate("OperatorForm", "Углерод (C):"))
        self.label_2.setText(_translate("OperatorForm", "Кремний (Si):"))
        self.label_3.setText(_translate("OperatorForm", "Сера (S):"))
        self.label_4.setText(_translate("OperatorForm", "Фосфор (P):"))
        self.label_26.setText(_translate("OperatorForm", "Марганец (Mn):"))
        self.groupBox_2.setTitle(_translate("OperatorForm", "Чугун"))
        self.label_5.setText(_translate("OperatorForm", "Температура [℃]:"))
        self.label_6.setText(_translate("OperatorForm", "Масса [т]:"))
        self.groupBox_6.setTitle(_translate("OperatorForm", "Химический состав, %масс"))
        self.label_7.setText(_translate("OperatorForm", "Углерод (C):"))
        self.label_8.setText(_translate("OperatorForm", "Кремний (Si):"))
        self.label_9.setText(_translate("OperatorForm", "Сера (S):"))
        self.label_10.setText(_translate("OperatorForm", "Фосфор (P):"))
        self.label_24.setText(_translate("OperatorForm", "Марганец (Mn):"))
        self.groupBox_5.setTitle(_translate("OperatorForm", "Металлошихта, т"))
        self.label_16.setText(_translate("OperatorForm", "Масса:"))
        self.groupBox_3.setTitle(_translate("OperatorForm", "Лом"))
        self.label_11.setText(_translate("OperatorForm", "Масса [т]:"))
        self.groupBox_7.setTitle(_translate("OperatorForm", "Химический состав, %масс"))
        self.label_12.setText(_translate("OperatorForm", "Углерод (C):"))
        self.label_13.setText(_translate("OperatorForm", "Кремний (Si):"))
        self.label_14.setText(_translate("OperatorForm", "Сера (S):"))
        self.label_15.setText(_translate("OperatorForm", "Фосфор (P):"))
        self.label_25.setText(_translate("OperatorForm", "Марганец (Mn):"))
        self.groupBox_8.setTitle(_translate("OperatorForm", "Химический состав шихты, %масс"))
        self.label_17.setText(_translate("OperatorForm", "Углерод (C):"))
        self.label_18.setText(_translate("OperatorForm", "Сера (S):"))
        self.label_19.setText(_translate("OperatorForm", "Кремний (Si):"))
        self.label_20.setText(_translate("OperatorForm", "Фосфор (P):"))
        self.label_21.setText(_translate("OperatorForm", "Марганец (Mn):"))
        self.groupBox_9.setTitle(_translate("OperatorForm", "Окисление элементов металлошихты (на 100кг металлошихты)"))
        #self.label_22.setText(_translate("OperatorForm", "Масса:"))
        item = self.OxidationTable.verticalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Содержится в шихте"))
        item = self.OxidationTable.verticalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Остаётся после продувки"))
        item = self.OxidationTable.verticalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Удаляется после продувки"))
        item = self.OxidationTable.verticalHeaderItem(3)
        item.setText(_translate("OperatorForm", "Требуется кислорода [кг]"))
        item = self.OxidationTable.verticalHeaderItem(4)
        item.setText(_translate("OperatorForm", "Требуется кислорода [м^3]"))
        item = self.OxidationTable.verticalHeaderItem(5)
        item.setText(_translate("OperatorForm", "Образуется оксидов"))
        item = self.OxidationTable.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Всего C"))
        item = self.OxidationTable.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Ок. C до CO"))
        item = self.OxidationTable.horizontalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Ок. C до CO2"))
        item = self.OxidationTable.horizontalHeaderItem(3)
        item.setText(_translate("OperatorForm", "Si"))
        item = self.OxidationTable.horizontalHeaderItem(4)
        item.setText(_translate("OperatorForm", "Mn"))
        item = self.OxidationTable.horizontalHeaderItem(5)
        item.setText(_translate("OperatorForm", "P"))
        item = self.OxidationTable.horizontalHeaderItem(6)
        item.setText(_translate("OperatorForm", "S"))
        item = self.OxidationTable.horizontalHeaderItem(7)
        item.setText(_translate("OperatorForm", "Всего"))
        __sortingEnabled = self.OxidationTable.isSortingEnabled()
        self.OxidationTable.setSortingEnabled(False)
        self.OxidationTable.setSortingEnabled(__sortingEnabled)
        self.groupBox_11.setTitle(_translate("OperatorForm", "Выбрать режим и параметры из базы данных"))
        self.label_23.setText(_translate("OperatorForm", "Режим:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("OperatorForm", "Металлошихта"))
        self.groupBox_10.setTitle(_translate("OperatorForm", "Флюсы"))
        item = self.FluxeTable.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Тип флюса"))
        item = self.FluxeTable.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Масса [т]"))
        self.tip_flyusa_label.setText(_translate("OperatorForm", "Тип флюса:"))
        self.shlak_group_box.setTitle(_translate("OperatorForm", "Шлак"))
        self.him_sostav_shlaka_group_box.setTitle(_translate("OperatorForm", "Химический состав, т"))
        self.SlagSiO2Label.setText(_translate("OperatorForm", "SiO2:"))
        self.SlagCaOLabel.setText(_translate("OperatorForm", "CaO:"))
        self.SlagMgOLabel.setText(_translate("OperatorForm", "MgO:"))
        self.SlagAl2O3Label.setText(_translate("OperatorForm", "Al2O3:"))
        self.SlagOthersLabel.setText(_translate("OperatorForm", "Прочие:"))
        self.SlagFeOLabel.setText(_translate("OperatorForm", "FeO:"))
        self.SlagFe2O3Label.setText(_translate("OperatorForm", "Fe2O3:"))
        self.SlagWeightLabel.setText(_translate("OperatorForm", "Масса [т]:"))
        self.him_sostav_shlaka_v_procentah_group_box.setTitle(_translate("OperatorForm", "Химический состав, %"))
        self.SlagAl2O3Label_2.setText(_translate("OperatorForm", "Al2O3:"))
        self.SlagFeOLabel_2.setText(_translate("OperatorForm", "FeO:"))
        self.SlagFe2O3Label_2.setText(_translate("OperatorForm", "Fe2O3:"))
        self.SlagSiO2Label_2.setText(_translate("OperatorForm", "SiO2:"))
        self.SlagCaOLabel_2.setText(_translate("OperatorForm", "CaO:"))
        self.SlagMgOLabel_2.setText(_translate("OperatorForm", "MgO:"))
        self.SlagOthersLabel_2.setText(_translate("OperatorForm", "Прочие:"))
        self.raschet_dutya_group_box.setTitle(_translate("OperatorForm", "Параметры дутья"))
        self.TotalOxygenDemandBlastLabel.setText(_translate("OperatorForm", "Общая потребность в кислороде дутья [кг]:"))
        self.TotalConsumptionOfBlastKgLabel.setText(_translate("OperatorForm", "Общий расход дутья [кг]:"))
        self.ExcessBlastLabel.setText(_translate("OperatorForm", "Избыток дутья [кг]:"))
        self.TotalConsumptionOfBlastM3Label.setText(_translate("OperatorForm", "Общий расход дутья [м^3]:"))
        self.changeSetings.setText(_translate("OperatorForm", "Изменить текущие настройки дутья"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("OperatorForm", "Шлак"))
        self.ReclaimedIronWeightLabel.setText(_translate("OperatorForm", "Кол-во железа, восстановленного из неметаллических материалов [т]:"))
        item = self.IncomingData.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Наименование"))
        item = self.IncomingData.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "кг"))
        item = self.OutputData.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Наименование"))
        item = self.OutputData.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "кг"))
        self.vyhod_zhidkovo_metalla_pered_raskisleniem_label.setText(_translate("OperatorForm", "Выход жидкого металла перед раскислением [т]:"))
        self.OutputDataGroupBox.setTitle(_translate("OperatorForm", "Расходная часть"))
        self.MassOfOxidizedImpuritiesLabel.setText(_translate("OperatorForm", "Масса окислившихся примесей [т]:"))
        self.MassOfOxidesPassingIntoSlagLabel.setText(_translate("OperatorForm", "Масса оксидов железа, переходящих в шлак [т]:"))
        self.LossWithCarryOverLabel.setText(_translate("OperatorForm", "Потери металла с выносами и выбросами [т]:"))
        self.DustLossLabel.setText(_translate("OperatorForm", "Потери железа с пылью [т]:"))
        item = self.OutputDataTable.verticalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Окисление углерода"))
        item = self.OutputDataTable.verticalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Разложение CaCO3"))
        item = self.OutputDataTable.verticalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Дожигание части CO"))
        item = self.OutputDataTable.verticalHeaderItem(3)
        item.setText(_translate("OperatorForm", "Разложение MgCO3"))
        item = self.OutputDataTable.verticalHeaderItem(4)
        item.setText(_translate("OperatorForm", "Итого, кг"))
        item = self.OutputDataTable.verticalHeaderItem(5)
        item.setText(_translate("OperatorForm", "Итого, м^3"))
        item = self.OutputDataTable.verticalHeaderItem(6)
        item.setText(_translate("OperatorForm", "Состав газа, %"))
        item = self.OutputDataTable.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "CO"))
        item = self.OutputDataTable.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "CO2"))
        item = self.OutputDataTable.horizontalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Всего"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("OperatorForm", "Материальный баланс"))
        self.temperatura_zhidkovo_metalla_v_konce_produvki_label_2.setText(_translate("OperatorForm", "Температура жидкого металла в конце продувки [°C]:"))
        self.rashodnie_statii_group_box_2.setTitle(_translate("OperatorForm", "Расходные статьи"))
        self.phizicheskoe_teplo_zhidkovo_metalla_label_2.setText(_translate("OperatorForm", "Физическое тепло жидкого металла [кДж]:"))
        self.HeatConsDecompos_label.setText(_translate("OperatorForm", "Затраты тепла на разложение оксидов железа [кДж]:"))
        self.poteri_tepla_s_vynosami_i_vybrosami_label_2.setText(_translate("OperatorForm", "Потери тепла с выносами и выбросами [кДж]:"))
        self.HeatDustForm_label.setText(_translate("OperatorForm", "Затраты тепла на пылеобразование [кДж]:"))
        self.phizicheskoe_teplo_othodyashih_gazov_label_2.setText(_translate("OperatorForm", "Физическое тепло отходящих газов [кДж]:"))
        self.phizicheskoe_teplo_shlaka_label_2.setText(_translate("OperatorForm", "Физическое тепло шлака [кДж]:"))
        self.teplovie_poteri_label_2.setText(_translate("OperatorForm", "Тепловые потери [кДж]:"))
        self.teplo_na_razlozhenie_karbonatov_label_2.setText(_translate("OperatorForm", "Тепло на разложение карбонатов [кДж]:"))
        self.obshii_rashod_tepla_label_2.setText(_translate("OperatorForm", "Общий расход тепла [кДж]:"))
        item = self.OutputHeatTable.verticalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Физ. тепло жидкого металла"))
        item = self.OutputHeatTable.verticalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Физ. тепло шлака"))
        item = self.OutputHeatTable.verticalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Затраты тепла на разл. оксидов железа"))
        item = self.OutputHeatTable.verticalHeaderItem(3)
        item.setText(_translate("OperatorForm", "Физ. тепло отходящих газов"))
        item = self.OutputHeatTable.verticalHeaderItem(4)
        item.setText(_translate("OperatorForm", "Потери тепла с выносами и выбросами"))
        item = self.OutputHeatTable.verticalHeaderItem(5)
        item.setText(_translate("OperatorForm", "Затраты тепла на пылеобразование"))
        item = self.OutputHeatTable.verticalHeaderItem(6)
        item.setText(_translate("OperatorForm", "Тепло на разложение карбонатов"))
        item = self.OutputHeatTable.verticalHeaderItem(7)
        item.setText(_translate("OperatorForm", "Тепловые потери"))
        item = self.OutputHeatTable.verticalHeaderItem(8)
        item.setText(_translate("OperatorForm", "Итого"))
        item = self.OutputHeatTable.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Кол-во, кДж"))
        item = self.OutputHeatTable.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Кол-во, %"))
        self.temperatura_peregreva_label_2.setText(_translate("OperatorForm", "Температура перегрева [°C]:"))
        self.prihodnie_statii_group_box_2.setTitle(_translate("OperatorForm", "Приходные статьи"))
        self.teplovoi_effect_reakcii_shlakoobrazovaniya_label_2.setText(_translate("OperatorForm", "Тепловой эффект реакций шлакообразования [кДж]:"))
        self.teplovoi_effect_reakcii_okisleniya_label_2.setText(_translate("OperatorForm", "Тепловой эффект реакции окисления [кДж]:"))
        self.himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2.setText(_translate("OperatorForm", "Химическое тепло от образования оксидов [кДж]:"))
        self.phizicheskoe_teplo_zhidkovo_chuguna_label_2.setText(_translate("OperatorForm", "Физическое тепло жидкого чугуна [кДж]:"))
        self.teplo_ot_dozhiganiya_co_label_2.setText(_translate("OperatorForm", "Тепло от дожигания CO [кДж]:"))
        self.obshii_prihod_tepla_label_2.setText(_translate("OperatorForm", "Общий приход тепла [кДж]:"))
        item = self.IncomingHeatTable.verticalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Физ. тепло жидкого чугуна"))
        item = self.IncomingHeatTable.verticalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Тепл. эффект реакции оксиления"))
        item = self.IncomingHeatTable.verticalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Хим. тепло обр. оксидов железа шлака"))
        item = self.IncomingHeatTable.verticalHeaderItem(3)
        item.setText(_translate("OperatorForm", "Тепл. эффект реакции шлакообразования"))
        item = self.IncomingHeatTable.verticalHeaderItem(4)
        item.setText(_translate("OperatorForm", "Тепло от дожигания CO"))
        item = self.IncomingHeatTable.verticalHeaderItem(5)
        item.setText(_translate("OperatorForm", "Итого"))
        item = self.IncomingHeatTable.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Кол-во, кДж"))
        item = self.IncomingHeatTable.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Кол-во, %"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _translate("OperatorForm", "Тепловой баланс"))
        self.tip_ferrosplava_label_2.setText(_translate("OperatorForm", "Тип ферросллава:"))
        self.balans_pri_raskislenii_stali_label_2.setText(_translate("OperatorForm", "Баланс элементов при раскислении стали"))
        self.label_51.setText(_translate("OperatorForm", "Выход металла после раскисления [кг]:"))
        self.label_52.setText(_translate("OperatorForm", "Расход ферросплава [кг]:"))
        item = self.ChemEmission.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Тип"))
        item = self.ChemEmission.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "C, %"))
        item = self.ChemEmission.horizontalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Si, %"))
        item = self.ChemEmission.horizontalHeaderItem(3)
        item.setText(_translate("OperatorForm", "Mn, %"))
        item = self.ChemEmission.horizontalHeaderItem(4)
        item.setText(_translate("OperatorForm", "P, %"))
        item = self.ChemEmission.horizontalHeaderItem(5)
        item.setText(_translate("OperatorForm", "S, %"))
        item = self.DeoxidationBalance.verticalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Содержится перед раскислением, %"))
        item = self.DeoxidationBalance.verticalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Содержится перед раскислением, кг"))
        item = self.DeoxidationBalance.verticalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Вносится первым ферросплавом, кг"))
        item = self.DeoxidationBalance.verticalHeaderItem(3)
        item.setText(_translate("OperatorForm", "Содержится после раскисления, кг"))
        item = self.DeoxidationBalance.verticalHeaderItem(4)
        item.setText(_translate("OperatorForm", "Образуется оксида, кг"))
        item = self.DeoxidationBalance.verticalHeaderItem(5)
        item.setText(_translate("OperatorForm", "Состав стали после раскисления, %"))
        item = self.DeoxidationBalance.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "Ост. C"))
        item = self.DeoxidationBalance.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "C до CO"))
        item = self.DeoxidationBalance.horizontalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Ост. Si"))
        item = self.DeoxidationBalance.horizontalHeaderItem(3)
        item.setText(_translate("OperatorForm", "Si до SiO2"))
        item = self.DeoxidationBalance.horizontalHeaderItem(4)
        item.setText(_translate("OperatorForm", "Ост. Mn"))
        item = self.DeoxidationBalance.horizontalHeaderItem(5)
        item.setText(_translate("OperatorForm", "Mn до MnO"))
        item = self.DeoxidationBalance.horizontalHeaderItem(6)
        item.setText(_translate("OperatorForm", "P"))
        item = self.DeoxidationBalance.horizontalHeaderItem(7)
        item.setText(_translate("OperatorForm", "S"))
        item = self.DeoxidationBalance.horizontalHeaderItem(8)
        item.setText(_translate("OperatorForm", "Fe"))
        item = self.DeoxidationBalance.horizontalHeaderItem(9)
        item.setText(_translate("OperatorForm", "Всего"))
        self.groupBox_12.setTitle(_translate("OperatorForm", "Результат плавки"))
        item = self.SteelChemResult.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "C"))
        item = self.SteelChemResult.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Si"))
        item = self.SteelChemResult.horizontalHeaderItem(2)
        item.setText(_translate("OperatorForm", "Mn"))
        item = self.SteelChemResult.horizontalHeaderItem(3)
        item.setText(_translate("OperatorForm", "S"))
        item = self.SteelChemResult.horizontalHeaderItem(4)
        item.setText(_translate("OperatorForm", "P"))
        self.himicheskii_sostav_poluchennoi_stali_label_2.setText(_translate("OperatorForm", "Химический состав полученной стали:"))
        self.label_43.setText(_translate("OperatorForm", "Выбросы CO2 [кг]:"))
        self.label_44.setText(_translate("OperatorForm", "Масса стали [кг]:"))
        self.label_45.setText(_translate("OperatorForm", "Масса шлака [т]:"))
        self.label_46.setText(_translate("OperatorForm", "Потеря массы футеровки [кг]:"))
        self.label_47.setText(_translate("OperatorForm", "Температура выхода стали [°C]:"))
        item = self.SlagChemResult.horizontalHeaderItem(0)
        item.setText(_translate("OperatorForm", "SiO2"))
        item = self.SlagChemResult.horizontalHeaderItem(1)
        item.setText(_translate("OperatorForm", "Al2O3"))
        item = self.SlagChemResult.horizontalHeaderItem(2)
        item.setText(_translate("OperatorForm", "CaO"))
        item = self.SlagChemResult.horizontalHeaderItem(3)
        item.setText(_translate("OperatorForm", "FeO"))
        item = self.SlagChemResult.horizontalHeaderItem(4)
        item.setText(_translate("OperatorForm", "MgO"))
        self.himicheskii_sostav_poluchennoi_stali_label_3.setText(_translate("OperatorForm", "Химический состав шлака:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _translate("OperatorForm", "Раскисление стали"))
        self.Menu.setTitle(_translate("OperatorForm", "Файл"))
        self.Help.setTitle(_translate("OperatorForm", "Справка"))
        self.Administrate.setTitle(_translate("OperatorForm", "Администрирование"))
        self.about.setText(_translate("OperatorForm", "О программе"))
        self.SaveFile.setText(_translate("OperatorForm", "Сохранить результат"))
        self.Exit.setText(_translate("OperatorForm", "Выйти"))
        self.addUser.setText(_translate("OperatorForm", "Добавить пользователя"))
        self.AddUser.setText(_translate("OperatorForm", "Добавить пользователя"))
        self.AddDbData.setText(_translate("OperatorForm", "Добавить данные в бд"))
        self.getSettings()
        self.getFluxes()
        self.getModes()
        self.AddNewMode.setEnabled(1)
        self.tab_4.setEnabled(1)
        self.tab_5.setEnabled(1)





if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    OperatorForm = QtWidgets.QMainWindow()
    ui = Ui_OperatorForm()
    ui.setupUi(OperatorForm)
    OperatorForm.show()
    sys.exit(app.exec_())

