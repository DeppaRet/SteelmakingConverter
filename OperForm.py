import math

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView, QFileDialog
from PyQt5.QtGui import QPalette, QColor
import mysql.connector as mc
from PyQt5.QtWidgets import QMessageBox
import AboutForm
from tkinter import filedialog
from configparser import ConfigParser

import config
import app_theme
from theme_settings import manager, get_theme
from theme_toggle import ThemeToggle

try:
    from converter3d.widget import create_converter_widget, WEBENGINE_AVAILABLE
except ImportError:
    WEBENGINE_AVAILABLE = False
    create_converter_widget = None

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
Protokol = ""
step = 1

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


class WorkerThread(QThread):
    progress = pyqtSignal(int)
    result_scenario = pyqtSignal(str, str, str, str)
    result_mode = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, scenario, db_host, db_login, db_pass):
        super().__init__()
        self.scenario = scenario
        self.db_host = db_host
        self.db_login = db_login
        self.db_pass = db_pass

    def run(self):
        try:
            self.progress.emit(0)
            query = f"SELECT ScenarioTask, SteelCarbonLimit, SteelPhosphorLimit, SteelTempLimit FROM scenario WHERE ScanrioName = '{self.scenario}';"
            DB = mc.connect(
                host=self.db_host,
                user=self.db_login,
                password=self.db_pass,
                database="regimdata"
            )
            self.progress.emit(10)
            mycursor = DB.cursor()
            mycursor.execute(query)
            ScenarioQuery = mycursor.fetchall()
            self.progress.emit(40)
            if not ScenarioQuery:
                raise ValueError("No data found for the selected scenario.")

            Task = ScenarioQuery[0][0]
            SteelCarbonLimit = ScenarioQuery[0][1]
            SteelPhosphorLimit = ScenarioQuery[0][2]
            MinSteelTemp = ScenarioQuery[0][3]
            self.result_scenario.emit(str(Task), str(SteelCarbonLimit), str(SteelPhosphorLimit), str(MinSteelTemp))

            mycursor.close()

            query = f"SELECT mode_idMode FROM scenario WHERE ScanrioName = '{self.scenario}';"
            mycursor = DB.cursor()
            mycursor.execute(query)
            modeId = mycursor.fetchone()[0]
            mycursor.close()

            self.progress.emit(70)

            query = f"SELECT ModeName FROM mode WHERE idMode = '{modeId}';"
            mycursor = DB.cursor()
            mycursor.execute(query)
            modeName = mycursor.fetchone()[0]
            mycursor.close()

            self.progress.emit(90)
            self.result_mode.emit(str(modeName))
            self.progress.emit(100)

        except Exception as err:
            self.error.emit(str(err))
        finally:
            if mycursor: mycursor.close()
            if DB: DB.close()


class ConverterDiagram(QtWidgets.QFrame):
    """Schematic BOF-converter diagram drawn with QPainter."""

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPainterPath, QBrush, QLinearGradient, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w / 2.0

        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QtGui.QColor(13, 13, 26))
        bg.setColorAt(1, QtGui.QColor(20, 20, 40))
        p.fillRect(self.rect(), QBrush(bg))

        neck_w, top_w, bot_w = w * 0.18, w * 0.32, w * 0.44
        neck_top, body_top, body_bot = h * 0.04, h * 0.15, h * 0.85

        body = QPainterPath()
        body.moveTo(cx - neck_w / 2, neck_top)
        body.lineTo(cx + neck_w / 2, neck_top)
        body.lineTo(cx + top_w / 2, body_top)
        body.lineTo(cx + bot_w / 2, body_bot)
        body.quadTo(cx + bot_w / 2, h * 0.96, cx, h * 0.99)
        body.quadTo(cx - bot_w / 2, h * 0.96, cx - bot_w / 2, body_bot)
        body.lineTo(cx - top_w / 2, body_top)
        body.closeSubpath()

        fill = QLinearGradient(cx - bot_w / 2, body_top, cx + bot_w / 2, body_bot)
        fill.setColorAt(0, QtGui.QColor(38, 32, 22))
        fill.setColorAt(0.55, QtGui.QColor(55, 38, 18))
        fill.setColorAt(1, QtGui.QColor(72, 44, 8))
        p.fillPath(body, QBrush(fill))

        wall_pen = QPen(QtGui.QColor(0, 172, 200, 160))
        wall_pen.setWidth(2)
        p.setPen(wall_pen)
        p.drawPath(body)

        metal_y = h * 0.62
        metal_h = h * 0.28
        mg = QLinearGradient(0, metal_y, 0, metal_y + metal_h)
        mg.setColorAt(0, QtGui.QColor(255, 145, 0, 70))
        mg.setColorAt(1, QtGui.QColor(255, 55, 0, 155))
        metal_path = QPainterPath()
        metal_path.addRect(cx - bot_w / 2 + 4, metal_y, bot_w - 8, metal_h)
        clipped = body.intersected(metal_path)
        p.fillPath(clipped, QBrush(mg))

        lance_pen = QPen(QtGui.QColor(100, 210, 255, 220))
        lance_pen.setWidth(3)
        p.setPen(lance_pen)
        p.drawLine(int(cx), 0, int(cx), int(h * 0.54))

        spark_pen = QPen(QtGui.QColor(255, 228, 0, 190))
        spark_pen.setWidth(2)
        p.setPen(spark_pen)
        tip_y = h * 0.54
        for ang in range(0, 360, 40):
            r = math.radians(ang)
            sx = cx + math.cos(r) * 9
            sy = tip_y + math.sin(r) * 9
            p.drawLine(int(cx), int(tip_y), int(sx), int(sy))

        p.setPen(QPen(QtGui.QColor(100, 220, 255)))
        p.setFont(QtGui.QFont("Courier New", 7, QtGui.QFont.Bold))
        p.drawText(int(cx) + 4, int(h * 0.13), "O\u2082")

        p.setPen(QPen(QtGui.QColor(0, 212, 255, 90)))
        p.setFont(QtGui.QFont("Arial", 7))
        p.drawText(4, h - 4, "\u041a\u041e\u041d\u0412\u0415\u0420\u0422\u0415\u0420 \u0411\u041e\u0424")
        p.end()


class Ui_OperatorForm(object):
    scenarioProgress = pyqtSignal(int)
    finished = pyqtSignal(str)
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
            query = "select ScanrioName from scenario;"
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
                    self.ScenarioComboBox.addItem((str(data)))
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
                database="ferroalloydb"
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

    def GetScenario(self):
        try:

            scenario = self.ScenarioComboBox.currentText()
            query = "select ScenarioTask, SteelCarbonLimit, SteelPhosphorLimit, SteelTempLimit from scenario where ScanrioName = '" + scenario + "';"
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            Task = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            ScenarioQuery = mycursor.fetchall()
            Task = ScenarioQuery[0][0]
            SteelCarbonLimit = ScenarioQuery[0][1]
            SteelPhosphorLimit = ScenarioQuery[0][2]
            MinSteelTemp = ScenarioQuery[0][3]
            self.ScenarioTask.setPlainText(str(Task))
            self.SteelCarbonLimit.setText(str(SteelCarbonLimit))
            self.SteelPhosphorLimit.setText(str(SteelPhosphorLimit))
            self.MinSteelTempLimit.setText(str(MinSteelTemp))
            mycursor.close()

            query = "select mode_idMode from scenario where ScanrioName = '" + scenario + "';"
            modeId = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            modeId = mycursor.fetchone()[0]
            mycursor.close()

            query = "select ModeName from mode where idMode = '" + str(modeId) + "';"
            modeName = ""
            mycursor = DB.cursor()
            mycursor.execute(query)
            modeName = mycursor.fetchone()[0]
            mycursor.close()
            self.ModeComboBox.setCurrentText(str(modeName))

            self.chooseMods()
            self.calcMetalChargeClicked()
            self.calcTableClick()
            self.removeFluxeButtonClicked()
            global Protokol
            Protokol = ''
            global step
            step = 1




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

    def GetScenarioExample(self):

        # try:
        #
        #     scenario = self.ScenarioComboBox.currentText()
        #     query = "select ScenarioTask, SteelCarbonLimit, SteelPhosphorLimit, SteelTempLimit from scenario where ScanrioName = '" + scenario + "';"
        #     DB = mc.connect(
        #         host=DBhost,  # host="192.168.51.179" user="root", password="root",
        #         user=DBlogin,
        #         password=DBpass,
        #         database="regimdata"
        #     )
        #
        #     Task = ""
        #     mycursor = DB.cursor()
        #     mycursor.execute(query)
        #     ScenarioQuery = mycursor.fetchall()
        #     Task = ScenarioQuery[0][0]
        #     SteelCarbonLimit = ScenarioQuery[0][1]
        #     SteelPhosphorLimit = ScenarioQuery[0][2]
        #     MinSteelTemp = ScenarioQuery[0][3]
        #
        #     self.ScenarioTask.setPlainText(str(Task))
        #     self.SteelCarbonLimit.setText(str(SteelCarbonLimit))
        #     self.SteelPhosphorLimit.setText(str(SteelPhosphorLimit))
        #     self.MinSteelTempLimit.setText(str(MinSteelTemp))
        #
        #     mycursor.close()
        #
        #     query = "select mode_idMode from scenario where ScanrioName = '" + scenario + "';"
        #     modeId = ""
        #     mycursor = DB.cursor()
        #     mycursor.execute(query)
        #     modeId = mycursor.fetchone()[0]
        #     mycursor.close()
        #
        #     query = "select ModeName from mode where idMode = '" + str(modeId) + "';"
        #     modeName = ""
        #     mycursor = DB.cursor()
        #     mycursor.execute(query)
        #     modeName = mycursor.fetchone()[0]
        #     mycursor.close()
        #     self.ModeComboBox.setCurrentText(str(modeName))
        #     self.chooseMods()
        #     self.calcMetalChargeClicked()
        #     self.calcTableClick()
        #     self.slagCalcClicked()
        #     self.blastCalcClicked()
        #     self.MaterialBalanceCalcClicked()
        #     self.HeatBalanceCalcClicked()
        #     self.AddFeroBtnClicked()
        #     self.deoxCalc()
        #     self.getRecomendation()
        #     global Protokol
        #     Protokol = ''
        #     global step
        #     step = 1
        #
        # except Exception as err:
        #     msg = QMessageBox()
        #     msg.setIcon(QMessageBox.Critical)
        #     msg.setWindowTitle("Ошибка")
        #     msg.setText("Внимание")
        #     msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
        #     # msg.setInformativeText("Error: {0}".format(err))
        #     msg.exec_()
        #
        # finally:
        #     mycursor.close()
        #     DB.close()
        try:
            scenario = self.ScenarioComboBox.currentText()
            DB = mc.connect(
                host=DBhost,  # host="192.168.51.179" user="root", password="root",
                user=DBlogin,
                password=DBpass,
                database="regimdata"
            )
            self.thread = WorkerThread(scenario, DBhost, DBlogin, DBpass)
            self.thread.progress.connect(self.update_progress)
            self.thread.result_scenario.connect(self.update_scenario)
            self.thread.result_mode.connect(self.update_mode)
            self.thread.error.connect(self.show_error)
            self.thread.finished.connect(self.run_calculations)
            self.thread.start()
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            msg.exec_()

    def update_progress(self, value):
        self.scenarioProgress.setValue(value)

    def update_scenario(self, task, carbon, phosphor, temp):
        self.ScenarioTask.setPlainText(task)
        self.SteelCarbonLimit.setText(carbon)
        self.SteelPhosphorLimit.setText(phosphor)
        self.MinSteelTempLimit.setText(temp)

    def update_mode(self, mode):
        self.ModeComboBox.setCurrentText(mode)

    def show_error(self, error):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Ошибка")
        msg.setText("Внимание")
        msg.setInformativeText(f"Проверьте введенные данные! {error}")
        msg.exec_()

    def run_calculations(self):
        self.chooseMods()
        self.calcMetalChargeClicked()
        self.calcTableClick()
        self.slagCalcClicked()
        self.blastCalcClicked()
        self.MaterialBalanceCalcClicked()
        self.HeatBalanceCalcClicked()
        self.AddFeroBtnClicked()
        self.deoxCalc()
        self.getRecomendation()
        global Protokol
        Protokol = ''
        global step
        step = 1








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
            if getattr(self, 'converter3d', None):
                self.converter3d.update_state({
                    'state':      'charged',
                    'metalMass':  round(totalWeightValue, 1),
                    'metalLevel': min(1.0, totalWeightValue / 430.0) * 0.62,
                    'slagMass':   0,
                    'slagLevel':  0,
                })

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
                database="ferroalloydb"
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
            Fe2O3 = 0

            steelCarbon = float(self.steelCarbon.text())
            steelPhosphor = float(self.steelPhosphor.text())

            if (steelCarbon < 0.1):
                Fe2O3 = 9
            elif (steelCarbon >= 0.1 and steelCarbon <= 0.25):
                Fe2O3 = 5
            else:
                Fe2O3 = 4

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
            if getattr(self, 'converter3d', None):
                metal_mass = float(self.MetalCharge.text())
                self.converter3d.update_state({
                    'state':     'blowing',
                    'slagMass':  round(slagWeight, 1),
                    'slagLevel': min(1.0, slagWeight / 80.0),
                    'metalMass': round(metal_mass, 1),
                    'metalLevel': min(1.0, metal_mass / 430.0) * 0.62,
                    'temperature': 1500,
                })
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
            if getattr(self, 'converter3d', None):
                self.converter3d.update_state({
                    'blastFlow': round(totalBlastConsumptionM3, 0),
                })
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
            #totalOxygenRequired = float(self.TotalOxygenDemandBlast.text())
            totalOxygenRequired = float(self.SlagFeO.text()) * 16 / 72 + float(self.SlagFe2O3.text()) * 48 / 160
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
            #weightOfIronOxides = float(self.TotalOxygenDemandBlast.text())
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
            for row in range(incomingDataRowCount):
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
            self.OutputHeatTable.setItem(1, 0, QTableWidgetItem(str(round(PhysSlagHeat, 3))))

            #Общий расход тепла
            TotalHeatOut = PhysSteelHeat + PhysSlagHeat + PhysGasHeat + FeOxydesHeatLoses + heatLoses + heatCarbonDecom + heatDustLoses + emissionsHeatLoses
            self.TotalHeatCons.setText(str(round(TotalHeatOut, 3)))
            self.OutputHeatTable.setItem(8, 0, QTableWidgetItem(str(round(TotalHeatOut, 3))))

            #Температура жидкого металла в конце продувки
            self.LiquidSteelTemp.setText(str(round(SteelTemperature, 1)))

            #Температура перегрева
            # МОЖНО ДОБАВИТЬ ПРОВЕРКУ НА ТО, ЕСЛИ ТЕМПРЕАТУРА ПЕРЕГРЕВА ОТРИЦАТЕЛЬНАЯ ТО БАН
            meltTemperature = 1539.0 - 80.0 * float(self.steelCarbon.text())
            overheatTemperature = SteelTemperature - meltTemperature
            self.OverheatTemp.setText(str(round(overheatTemperature, 1)))

            #Выводим кол-во процентов в таблицы


            global heatBalanceCalcked
            heatBalanceCalcked = True
            if getattr(self, 'converter3d', None):
                # Only update temperature; tapping starts after getRecomendation
                self.converter3d.update_state({
                    'temperature': round(SteelTemperature, 0),
                })
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
            liningWeightLoss = 4.11155 * pow(10, -6) * float(self.LiquidSteelTemp.text()) * (limitSolubilityMgO * slagMgO)
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
            _0_6 = self.calcPhosphor()
            #_0_6 = float(self.OxidationTable.item(1,5).text())
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
            self.stepResult()

        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()


    def recomendationCalc(self):
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

        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            msg.exec_()


    def CheckConverterFunc(self):
        try:
            H = float(self.height.text())
            D = float(self.diametr.text())
            attitude = H / D
            msg = QMessageBox()
            if attitude > 2.1:
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Проверка конвертера")
                msg.setText("Внимание")
                msg.setInformativeText("Отношение высоты рабочего объема к диаметру выше максимально допустимого (" + str(round(attitude, 2)) + ">2.1)\nВозможно возникновение выбросов")
            elif attitude < 1.17:
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Проверка конвертера")
                msg.setText("Внимание")
                msg.setInformativeText("Отношение высоты рабочего объема к диаметру ниже минимально допустимого (" + str(round(attitude, 2)) + ">1.17)")
            else:
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Проверка конвертера")
                msg.setText("Внимание")
                msg.setInformativeText("Проверка конвертера выполнена успешно.\nОтношение высоты рабочего объема к диаметру находится в допустимых пределах\n(1.17>" + str(round(attitude, 2)) + ">2.1)")
            msg.exec_()
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


    def stepResult(self):
        try:
            Performer = self.PerformerName.text()
            global Protokol
            global step
            tmpFluxes = ""
            fluxesRowCount = self.FluxeTable.rowCount()
            for row in range(fluxesRowCount):
                name = str(self.FluxeTable.item(row, 0).text())
                weight = str(self.FluxeTable.item(row, 1).text())
                tmpFluxes += name + " массой " + weight + " Т., "
            Protokol += ("Шаг №" + str(step) + " Обучаемый: "+ str(Performer) + "\nРезультат плавки для следующего набора данных:\nЧугун: Температура [C]: " + str(self.castTemperature.text()) +\
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
                       ", Сера: " + str(self.SteelChemResult.item(0,3).text()) + ", Фосфор: " + str(self.SteelChemResult.item(0,4).text())) + "\n\n"
            step += 1
        except Exception as err:
            s = 0


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
            UserLogin = config.UserLogin
            global Protokol
            filetext = Protokol
            # tmpFluxes = ""
            # fluxesRowCount = self.FluxeTable.rowCount()
            # for row in range(fluxesRowCount):
            #     name = str(self.FluxeTable.item(row, 0).text())
            #     weight = str(self.FluxeTable.item(row, 1).text())
            #     tmpFluxes += name + " массой " + weight + " Т., "
            # filetext = "Обучаемый:" + UserLogin + "\nРезультат плавки для следующего набора данных:\nЧугун: Температура [C]: " + str(self.castTemperature.text()) +\
            #            ", Масса [Т] " + str(self.castWeight.text()) + " со следующим содержанием веществ[%масс]:\n" + \
            #            "Углерод: " + str(self.castCarbon.text()) + ", Сера:" + str(self.castSerum.text()) + \
            #            ", Кремний: " + str(self.castSilicon.text()) + ", Фосфор: " + str(self.castPhosphor.text()) +\
            #            ", Марганец: " + str(self.castManganese.text()) +"\nЛом: " +\
            #            "Масса [Т] " + str(self.scrapWeight.text()) + " со следующим содержанием веществ[%масс]:\n" + \
            #            "Углерод: " + str(self.scrapCarbon.text()) + ", Сера:" + str(self.scrapSerum.text()) + \
            #            ", Кремний: " + str(self.scrapSilicon.text()) + ", Фосфор: " + str(self.scrapPhosphor.text()) +\
            #            ", Марганец: " + str(self.scrapManganese.text()) + "\nс использованием флюсов: " + tmpFluxes + \
            #            "\nБыла получена сталь массой " + self.SteelWeightRes.text() + " кг, Температурой " + self.resultSteelTemperature.text() + \
            #            "C, со следующим содержанием веществ [%масс]:\n" + "Углерод: " + str(self.SteelChemResult.item(0,0).text()) + \
            #            ", Кремний: " + str(self.SteelChemResult.item(0,1).text()) + ", Марганец: " + str(self.SteelChemResult.item(0,2).text()) + \
            #            ", Сера: " + str(self.SteelChemResult.item(0,3).text()) + ", Фосфор: " + str(self.SteelChemResult.item(0,4).text())
            file.write(filetext)
            file.close()
        except Exception as err:
            s = 0


    def getRecomendation(self):
        try:
            self.calcPhosphor()
            steelTemperature = float(self.resultSteelTemperature.text())
            A = 0.255817 * steelTemperature - 335.0
            B = 0.066103 * steelTemperature - 85.0
            slagCaO = float(self.SlagCaOPerc.text())
            slagSiO2 = float(self.SlagSiO2Perc.text())
            slagFeO = float(self.SlagFeOPerc.text())
            slagMgO = float(self.SlagMgOPerc.text())
            limitSolubility = (A - B * slagCaO/slagSiO2) * 0.075 * slagFeO - 0.875
            liningWeightLoss = 4.11155*10**(-6) * steelTemperature * (limitSolubility * slagMgO)
            self.lining_weight_loss.setText(str(round(liningWeightLoss, 3)))
            slagСorrosionСriteria = limitSolubility - slagMgO
            self.limit_MgO.setText(str(round(limitSolubility, 3)))
            self.content_MgO.setText(str(round(slagMgO)))
            self.unsaturation_MgO.setText(str(round(slagСorrosionСriteria, 3)))
            self.steel_temp.setText(str(steelTemperature))
            slagBasicity = slagCaO / slagSiO2
            self.slag_basicity.setText(str(round(slagBasicity, 3)))
            if slagСorrosionСriteria > 3:
                self.recomendation.setPlainText("Необходимо увеличить количество магнезиального флюса на 50 кг и заново произвести расчёты\n")
            else:
                self.recomendation.setPlainText("Используется оптимальный расход флюсов\n")
            if self.SteelPhosphorLimit.text() != "":
                self.checkLimits()
            if getattr(self, 'converter3d', None):
                self.converter3d.update_state({
                    'state':       'complete',
                    'temperature': steelTemperature,
                })
        except Exception as err:
            s = 0


    def calcPhosphor(self):
        FeO = float(self.SlagFeOPerc.text())
        CaO = float(self.SlagCaOPerc.text())
        T = float(self.resultSteelTemperature.text())
        log_Lp = 22350 / T + 2.5 * math.log(FeO) + 0.08 * CaO - 16
        L_p = math.exp(log_Lp)
        L_p = 0.099 * L_p + 30
        ph = float(self.ChemPhosphor.text())
        stPh = ph / L_p * 100
        a = 0
        return stPh


    def checkLimits(self):
        try:
            problem = False
            _field = app_theme.field_style(get_theme())
            self.SteelWeightRes.setStyleSheet(_field)
            self.resultSteelTemperature.setStyleSheet(_field)
            self.SlagWeightRes.setStyleSheet(_field)
            checkResult = "Рассчеты завершены. Накладываемые ограничения не выполняются\n"
            actualSteelCarbon = float(self.DeoxidationBalance.item(0,0).text())
            actualSteelTemp = float(self.resultSteelTemperature.text())
            actualSteelPhosphor = float(self.DeoxidationBalance.item(0,6).text())
            steelCarbon = float(self.SteelCarbonLimit.text())
            minSteelTemp = float(self.MinSteelTempLimit.text())
            steelPhosphor = float(self.SteelPhosphorLimit.text())
            recText = self.recomendation.toPlainText()
            msg = QMessageBox()
            if actualSteelCarbon > steelCarbon:
                checkResult += "Содержание углерода в стали меньше минимально допустимого.\n"
                recText += "Содержание углерода в стали меньше минимально допустимого.\n"
                problem = True
            if actualSteelTemp < minSteelTemp:
                checkResult += "Температура стали меньше минимально допустимой.\n"
                recText += "Температура стали меньше минимально допустимой.\n"
                self.resultSteelTemperature.setStyleSheet("QLineEdit { background: #cc0000; color: #ffffff; border: 1px solid #ff4444; border-radius: 4px; }")
                problem = True
            if actualSteelPhosphor > steelPhosphor:
                checkResult += "Содержание фосфора в стали меньше минимально допустимого.\nРекомендуется увеличить содержание извести и провести рассчеты еще раз.\n"
                recText += "Содержание фосфора в стали меньше минимально допустимого.\nРекомендуется увеличить содержание извести и провести рассчеты еще раз.\n"
                problem = True
            if problem == True:
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Проверка Результата")
                msg.setText("Внимание")
                msg.setInformativeText(checkResult)
                app_theme.style_message_box(msg)
                msg.exec_()
            elif problem == False:
                tmp = self.recomendation.toPlainText()
                tmp += "\nПроверка результатов выполнена успешно, накладываемые ограничения выполняются"
                recText += "Ограничения сценария выполняются\n"
                self.recomendation.setPlainText(tmp)
            self.recomendation.setPlainText(recText)
        except Exception as err:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Внимание")
            msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
            # msg.setInformativeText("Error: {0}".format(err))
            app_theme.style_message_box(msg)
            msg.exec_()


    # ─────────────────────────────────────────────────────────────────────────
    # STYLE SYSTEM
    # ─────────────────────────────────────────────────────────────────────────

    def apply_styles(self, OperatorForm, theme=None):
        """Apply SCADA-style industrial stylesheet to the main window."""
        if theme is None:
            theme = get_theme()
        OperatorForm.setPalette(app_theme.palette(theme))
        OperatorForm.setStyleSheet(app_theme.operator_main_style(theme))

    def _apply_central_styles(self, theme=None):
        """Apply styles to the central widget and all child widgets."""
        if theme is None:
            theme = get_theme()
        self.centralwidget.setStyleSheet(app_theme.operator_central_style(theme))

    def refresh_theme(self):
        theme = get_theme()
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app_theme.apply_to_application(app, theme)
        if hasattr(self, '_oper_form') and self._oper_form:
            self.apply_styles(self._oper_form, theme)
        if hasattr(self, 'centralwidget'):
            self._apply_central_styles(theme)
        ts = app_theme.table_style(theme)
        for tbl in getattr(self, '_themed_tables', []):
            tbl.setStyleSheet(ts)
        if getattr(self, 'converter3d', None) and hasattr(self.converter3d, 'set_ui_theme'):
            self.converter3d.set_ui_theme(theme)
        if hasattr(self, '_header_frame'):
            self._header_frame.setStyleSheet(app_theme.header_bar_style(theme))
        if hasattr(self, '_title_lbl'):
            self._title_lbl.setStyleSheet(app_theme.header_title_style(theme))
        if hasattr(self, '_stages_lbl'):
            self._stages_lbl.setText(app_theme.help_rich_html(theme))
            self._stages_lbl.setStyleSheet(
                f"color: {app_theme.tokens(theme)['text_label']}; font-size: 11px;")
        if hasattr(self, '_hints_lbl'):
            self._hints_lbl.setText(app_theme.hints_rich_html(theme))
            self._hints_lbl.setStyleSheet(
                f"color: {app_theme.tokens(theme)['text_label']}; font-size: 10px;")
        for fr, cap, val, border, tcol in getattr(self, '_indicator_widgets', []):
            fr.setStyleSheet(app_theme.indicator_card_style(theme, border))
            cap.setStyleSheet(
                f"color: {app_theme.tokens(theme)['text_muted']}; "
                "font-size: 9px; font-weight: bold; border: none;")
            val.setStyleSheet(
                f"QLineEdit {{ background: transparent; border: none; "
                f"color: {tcol}; font-size: 20px; font-weight: bold; }}")
        if hasattr(self, 'theme_toggle'):
            self.theme_toggle.sync_from_settings()
        t = app_theme.tokens(theme)
        pe = (
            f"QPlainTextEdit {{ background: {t['table_bg']}; "
            f"border: 1px solid {t['group_border']}; color: {t['text']}; "
            "padding: 4px; font-size: 10pt; }"
        )
        if hasattr(self, "ScenarioTask"):
            self.ScenarioTask.setStyleSheet(pe)
        if hasattr(self, "recomendation"):
            self.recomendation.setStyleSheet(app_theme.recommendation_style(theme))
        if hasattr(self, "label_56"):
            self.label_56.setStyleSheet(
                f"color: {t['accent']}; font-size: 11px; font-weight: bold;")
        if hasattr(self, "GetResExample"):
            self.GetResExample.setMinimumHeight(28)
            self.GetResExample.setMaximumHeight(28)
            self.GetResExample.setStyleSheet(app_theme.primary_button_style(theme))

        pal = app_theme.palette(theme)
        if hasattr(self, "_left_scroll"):
            app_theme.apply_scroll_panel(self._left_scroll, self._left_panel, theme)
        if hasattr(self, "_right_scroll"):
            app_theme.apply_scroll_panel(self._right_scroll, self._right_panel, theme)
        if hasattr(self, "_center_panel"):
            self._center_panel.setPalette(pal)
            self._center_panel.setStyleSheet(app_theme.center_panel_style(theme))
        ro_field = app_theme.read_only_field_style(theme)
        for name in (
            "CO2ThrowRes", "SteelWeightRes", "SlagWeightRes",
            "resultSteelTemperature", "LiningWeightLoss",
        ):
            w = getattr(self, name, None)
            if w is not None:
                w.setStyleSheet(ro_field)
        for fr, cap, val, border, tcol in getattr(self, "_result_kpi_frames", []):
            fr.setStyleSheet(app_theme.indicator_card_style(theme, border))
            cap.setStyleSheet(
                f"color: {app_theme.tokens(theme)['text_muted']}; "
                "font-size: 9px; border: none;")
            val.setStyleSheet(
                f"QLineEdit {{ background: transparent; border: none; "
                f"color: {tcol}; font-size: 17px; font-weight: bold; "
                f"font-family: 'Courier New'; }}")
        ac = app_theme.html_accent(theme)
        for num_lbl, stg_lbl in getattr(self, "_stage_style_widgets", []):
            num_lbl.setStyleSheet(
                f"QLabel {{ background: rgba(0,120,168,0.12); "
                f"border: 1px solid {app_theme.tokens(theme)['group_border']}; "
                f"border-radius: 10px; color: {ac}; "
                "font-size: 10px; font-weight: bold; }}")
            stg_lbl.setStyleSheet(
                f"color: {app_theme.tokens(theme)['text_label']}; font-size: 11px;")
        if hasattr(self, "tabWidget"):
            self.tabWidget.setPalette(pal)
        for scroll in self.centralwidget.findChildren(QtWidgets.QScrollArea):
            if scroll not in (getattr(self, "_left_scroll", None),
                              getattr(self, "_right_scroll", None)):
                app_theme.apply_scroll_panel(scroll, scroll.widget(), theme)

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE LED TIMER
    # ─────────────────────────────────────────────────────────────────────────

    def _on_window_destroyed(self):
        """Stop timer and thread when the QMainWindow is destroyed."""
        try:
            self._led_timer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, 'thread') and self.thread.isRunning():
                self.thread.quit()
                self.thread.wait(500)
        except Exception:
            pass

    def _start_indicator_timer(self):
        # Parent the timer to centralwidget so Qt stops/destroys it automatically
        # when the window is closed, preventing stale callbacks on deleted widgets.
        self._led_timer = QtCore.QTimer(self.centralwidget)
        self._led_timer.timeout.connect(self._refresh_stage_leds)
        self._led_timer.start(300)

    def _refresh_stage_leds(self):
        # Detect deox completion: DeoxidationBalance table has cell (0,0) filled
        try:
            _item = self.DeoxidationBalance.item(0, 0)
            _deox_done = bool(_item and _item.text().strip())
        except Exception:
            _deox_done = False
        # Detect recommendation completion: recommendation text is not empty
        try:
            _rec_done = bool(self.recomendation.toPlainText().strip())
        except Exception:
            _rec_done = False

        flag_map = {
            "metalCharge":  metalChargeCalcked,
            "table":        tableCalcked,
            "slag":         slagCalcked,
            "blast":        blastCalcked,
            "matBalance":   materialBalanceCalcked,
            "heatBalance":  heatBalanceCalcked,
            "deox":         _deox_done,
            "recomendation": _rec_done,
        }
        for key, flag in flag_map.items():
            if key in self._stage_leds:
                color = "#00e855" if flag else "#3a3a4a"
                self._stage_leds[key].setStyleSheet(
                    f"color: {color}; font-size: 14px; background: transparent;")
        try:
            t = self.LiquidSteelTemp.text()
            self.ind_Temp.setText(t if t else "\u2014")
        except Exception:
            pass
        try:
            item = self.DeoxidationBalance.item(5, 0)
            c_val = item.text() if item else "\u2014"
            self.ind_Carbon.setText(c_val)
        except Exception:
            pass
        try:
            item = self.DeoxidationBalance.item(5, 6)
            p_val = item.text() if item else "\u2014"
            self.ind_Phosphor.setText(p_val)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # SETUP UI
    # ─────────────────────────────────────────────────────────────────────────

    def setupUi(self, OperatorForm):
        # Reset module-level calc flags so a fresh session starts with clean state
        global metalChargeCalcked, tableCalcked, slagCalcked, blastCalcked
        global materialBalanceCalcked, heatBalanceCalcked
        metalChargeCalcked = tableCalcked = slagCalcked = blastCalcked = False
        materialBalanceCalcked = heatBalanceCalcked = False

        # Store window reference; connect destroyed signal so the timer is
        # stopped even if Qt tears down the window before Python GC runs.
        self._oper_form = OperatorForm
        OperatorForm.destroyed.connect(self._on_window_destroyed)

        OperatorForm.setObjectName("OperatorForm")
        OperatorForm.resize(1650, 860)
        OperatorForm.setMinimumSize(QtCore.QSize(1280, 700))

        winIcon = QtGui.QIcon()
        winIcon.addPixmap(QtGui.QPixmap("Pictures/steel_ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        OperatorForm.setWindowIcon(winIcon)

        self.apply_styles(OperatorForm)

        # ── widget factory helpers ────────────────────────────────────────────
        def _icon(path):
            ic = QtGui.QIcon()
            ic.addPixmap(QtGui.QPixmap(path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            return ic

        def _ro_edit(obj_name):
            le = QtWidgets.QLineEdit()
            le.setObjectName(obj_name)
            le.setReadOnly(True)
            return le

        def _edit(obj_name, width=None):
            le = QtWidgets.QLineEdit()
            le.setObjectName(obj_name)
            if width:
                le.setFixedWidth(width)
            return le

        def _lbl(obj_name=""):
            lbl = QtWidgets.QLabel()
            lbl.setWordWrap(True)
            if obj_name:
                lbl.setObjectName(obj_name)
            return lbl

        def _icon_btn(path, w=28, h=28):
            btn = QtWidgets.QPushButton()
            btn.setFlat(True)
            btn.setAutoDefault(False)
            btn.setDefault(False)
            btn.setFocusPolicy(QtCore.Qt.NoFocus)
            btn.setIcon(_icon(path))
            btn.setFixedSize(w, h)
            return btn

        def _dark_table(tbl):
            tbl.setAlternatingRowColors(True)
            return tbl

        def _led():
            lbl = QtWidgets.QLabel("\u25cf")
            lbl.setFixedSize(16, 16)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("color: #3a3a4a; font-size: 13px; background: transparent;")
            return lbl

        # ════════════════════════════════════════════════════════════════════
        # CENTRAL WIDGET
        # ════════════════════════════════════════════════════════════════════
        self.centralwidget = QtWidgets.QWidget(OperatorForm)
        self.centralwidget.setObjectName("centralwidget")
        self._apply_central_styles()

        main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ════════════════════════════════════════════════════════════════════
        # HEADER BAR
        # ════════════════════════════════════════════════════════════════════
        self._header_frame = QtWidgets.QFrame()
        self._header_frame.setObjectName("header_frame")
        self._header_frame.setFixedHeight(52)
        hdr_h = QtWidgets.QHBoxLayout(self._header_frame)
        hdr_h.setContentsMargins(14, 4, 14, 4)
        hdr_h.setSpacing(10)

        self._title_lbl = QtWidgets.QLabel(
            "\u2699  \u041a\u041e\u041d\u0412\u0415\u0420\u0422\u0415\u0420\u041d\u0410\u042f "
            "\u041f\u041b\u0410\u0412\u041a\u0410  \u2014  \u041f\u0423\u041b\u042c\u0422 "
            "\u041e\u041f\u0415\u0420\u0410\u0422\u041e\u0420\u0410")
        hdr_h.addWidget(self._title_lbl)
        hdr_h.addStretch()

        self._indicator_widgets = []

        def _ind_frame(label_txt, obj_name, border_color, text_color):
            fr = QtWidgets.QFrame()
            fr.setFixedSize(175, 44)
            fh = QtWidgets.QHBoxLayout(fr)
            fh.setContentsMargins(8, 2, 8, 2)
            fh.setSpacing(4)
            cap = QtWidgets.QLabel(label_txt)
            cap.setFixedWidth(42)
            val = QtWidgets.QLineEdit()
            val.setObjectName(obj_name)
            val.setReadOnly(True)
            val.setText("\u2014")
            val.setAlignment(QtCore.Qt.AlignCenter)
            val.setFixedWidth(100)
            fh.addWidget(cap)
            fh.addWidget(val)
            self._indicator_widgets.append((fr, cap, val, border_color, text_color))
            return fr, val

        fr_t, self.ind_Temp     = _ind_frame("T [°C]", "ind_Temp",     "255,120,0",  "#ff6820")
        fr_c, self.ind_Carbon   = _ind_frame("C [%]",  "ind_Carbon",   "0,120,168",  "#0078b8")
        fr_p, self.ind_Phosphor = _ind_frame("P [%]",  "ind_Phosphor", "0,140,90",   "#00885a")
        hdr_h.addWidget(fr_t)
        hdr_h.addWidget(fr_c)
        hdr_h.addWidget(fr_p)
        main_layout.addWidget(self._header_frame)

        # ════════════════════════════════════════════════════════════════════
        # MAIN SPLITTER  (Left | Center | Right)
        # ════════════════════════════════════════════════════════════════════
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_splitter.setObjectName("main_splitter")
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(4)

        # ────────────────────────────────────────────────────────────────────
        # LEFT PANEL — INPUT ZONE
        # ────────────────────────────────────────────────────────────────────
        self._left_scroll = QtWidgets.QScrollArea()
        self._left_scroll.setWidgetResizable(True)
        self._left_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._left_scroll.setMinimumWidth(265)

        self._left_panel = QtWidgets.QWidget()
        lw = self._left_panel
        lw.setAutoFillBackground(True)
        ll = QtWidgets.QVBoxLayout(lw)
        ll.setContentsMargins(8, 8, 6, 8)
        ll.setSpacing(5)

        # ── Сценарий ─────────────────────────────────────────────────────
        self.groupBox_14 = QtWidgets.QGroupBox()
        self.groupBox_14.setObjectName("groupBox_14")
        g14 = QtWidgets.QGridLayout(self.groupBox_14)
        g14.setSpacing(5)
        g14.setColumnStretch(1, 1)
        self.label_27 = _lbl("label_27")
        self.ScenarioComboBox = QtWidgets.QComboBox()
        self.ScenarioComboBox.setObjectName("ScenarioComboBox")
        self.SelectScenarioButton = _icon_btn("GUI\\../Pictures/add.ico")
        self.SelectScenarioButton.setObjectName("SelectScenarioButton")
        self.SelectScenarioButton.clicked.connect(self.GetScenario)
        g14.addWidget(self.label_27, 0, 0)
        g14.addWidget(self.ScenarioComboBox, 0, 1)
        g14.addWidget(self.SelectScenarioButton, 0, 2)
        self.label_31 = _lbl("label_31")
        self.PerformerName = _edit("PerformerName")
        g14.addWidget(self.label_31, 1, 0)
        g14.addWidget(self.PerformerName, 1, 1, 1, 2)
        ll.addWidget(self.groupBox_14)

        # ── Ограничения ──────────────────────────────────────────────────
        self.groupBox_15 = QtWidgets.QGroupBox()
        self.groupBox_15.setObjectName("groupBox_15")
        g15 = QtWidgets.QGridLayout(self.groupBox_15)
        g15.setSpacing(4)
        g15.setColumnStretch(1, 1)
        self.label_32 = _lbl("label_32")
        self.MinSteelTempLimit = _edit("MinSteelTempLimit")
        g15.addWidget(self.label_32, 0, 0)
        g15.addWidget(self.MinSteelTempLimit, 0, 1)
        self.label_33 = _lbl("label_33")
        self.SteelPhosphorLimit = _edit("SteelPhosphorLimit")
        g15.addWidget(self.label_33, 1, 0)
        g15.addWidget(self.SteelPhosphorLimit, 1, 1)
        self.label_34 = _lbl("label_34")
        self.SteelCarbonLimit = _edit("SteelCarbonLimit")
        g15.addWidget(self.label_34, 2, 0)
        g15.addWidget(self.SteelCarbonLimit, 2, 1)
        ll.addWidget(self.groupBox_15)

        # ── Режим + Конвертер ─────────────────────────────────────────────
        mc_row = QtWidgets.QHBoxLayout()
        mc_row.setSpacing(5)

        self.groupBox_11 = QtWidgets.QGroupBox()
        self.groupBox_11.setObjectName("groupBox_11")
        g11h = QtWidgets.QHBoxLayout(self.groupBox_11)
        g11h.setSpacing(4)
        self.label_23 = _lbl("label_23")
        self.ModeComboBox = QtWidgets.QComboBox()
        self.ModeComboBox.setObjectName("ModeComboBox")
        self.AddNewMode = _icon_btn("GUI\\../Pictures/add.ico")
        self.AddNewMode.setObjectName("AddNewMode")
        self.AddNewMode.setEnabled(True)
        self.AddNewMode.clicked.connect(self.chooseMods)
        g11h.addWidget(self.label_23)
        g11h.addWidget(self.ModeComboBox, 1)
        g11h.addWidget(self.AddNewMode)
        mc_row.addWidget(self.groupBox_11, 2)

        self.groupBox_13 = QtWidgets.QGroupBox()
        self.groupBox_13.setObjectName("groupBox_13")
        g13g = QtWidgets.QGridLayout(self.groupBox_13)
        g13g.setSpacing(3)
        self.label_28 = _lbl("label_28")
        self.height = _edit("height", 54)
        self.label_30 = _lbl("label_30")
        self.diametr = _edit("diametr", 54)
        self.CheckConverter = _icon_btn("GUI\\../Pictures/testing.ico")
        self.CheckConverter.setObjectName("CheckConverter")
        self.CheckConverter.clicked.connect(self.CheckConverterFunc)
        g13g.addWidget(self.label_28, 0, 0)
        g13g.addWidget(self.height,   0, 1)
        g13g.addWidget(self.label_30, 1, 0)
        g13g.addWidget(self.diametr,  1, 1)
        g13g.addWidget(self.CheckConverter, 0, 2, 2, 1)
        mc_row.addWidget(self.groupBox_13, 1)
        ll.addLayout(mc_row)

        # ── Сталь-цель ────────────────────────────────────────────────────
        self.groupBox = QtWidgets.QGroupBox()
        self.groupBox.setObjectName("groupBox")
        self.groupBox_4 = QtWidgets.QGroupBox()
        self.groupBox_4.setObjectName("groupBox_4")
        g4 = QtWidgets.QGridLayout(self.groupBox_4)
        g4.setSpacing(4)
        g4.setColumnStretch(1, 1)
        g4.setColumnStretch(3, 1)
        self.label    = _lbl("label");    self.steelCarbon    = _edit("steelCarbon")
        self.label_3  = _lbl("label_3");  self.steelSerum     = _edit("steelSerum")
        self.label_2  = _lbl("label_2");  self.steelSilicon   = _edit("steelSilicon")
        self.label_4  = _lbl("label_4");  self.steelPhosphor  = _edit("steelPhosphor")
        self.label_26 = _lbl("label_26"); self.steelManganese = _edit("steelManganese")
        g4.addWidget(self.label, 0, 0);    g4.addWidget(self.steelCarbon, 0, 1)
        g4.addWidget(self.label_3, 0, 2);  g4.addWidget(self.steelSerum, 0, 3)
        g4.addWidget(self.label_2, 1, 0);  g4.addWidget(self.steelSilicon, 1, 1)
        g4.addWidget(self.label_4, 1, 2);  g4.addWidget(self.steelPhosphor, 1, 3)
        g4.addWidget(self.label_26, 2, 0); g4.addWidget(self.steelManganese, 2, 1)
        QtWidgets.QVBoxLayout(self.groupBox).addWidget(self.groupBox_4)
        ll.addWidget(self.groupBox)

        # ── Чугун ─────────────────────────────────────────────────────────
        self.groupBox_2 = QtWidgets.QGroupBox()
        self.groupBox_2.setObjectName("groupBox_2")
        g2v = QtWidgets.QVBoxLayout(self.groupBox_2)
        g2v.setContentsMargins(4, 4, 4, 4)
        g2top = QtWidgets.QGridLayout()
        g2top.setSpacing(4)
        g2top.setColumnStretch(1, 1)
        self.label_5 = _lbl("label_5"); self.castTemperature = _edit("castTemperature")
        self.label_6 = _lbl("label_6"); self.castWeight      = _edit("castWeight")
        g2top.addWidget(self.label_5, 0, 0); g2top.addWidget(self.castTemperature, 0, 1)
        g2top.addWidget(self.label_6, 1, 0); g2top.addWidget(self.castWeight,      1, 1)
        g2v.addLayout(g2top)
        self.groupBox_6 = QtWidgets.QGroupBox()
        self.groupBox_6.setObjectName("groupBox_6")
        g6 = QtWidgets.QGridLayout(self.groupBox_6)
        g6.setSpacing(4)
        g6.setColumnStretch(1, 1); g6.setColumnStretch(3, 1)
        self.label_7  = _lbl("label_7");  self.castCarbon   = _edit("castCarbon")
        self.label_9  = _lbl("label_9");  self.castSerum    = _edit("castSerum")
        self.label_8  = _lbl("label_8");  self.castSilicon  = _edit("castSilicon")
        self.label_10 = _lbl("label_10"); self.castPhosphor = _edit("castPhosphor")
        self.label_24 = _lbl("label_24"); self.castManganese= _edit("castManganese")
        g6.addWidget(self.label_7, 0, 0);  g6.addWidget(self.castCarbon,  0, 1)
        g6.addWidget(self.label_9, 0, 2);  g6.addWidget(self.castSerum,   0, 3)
        g6.addWidget(self.label_8, 1, 0);  g6.addWidget(self.castSilicon, 1, 1)
        g6.addWidget(self.label_10, 1, 2); g6.addWidget(self.castPhosphor,1, 3)
        g6.addWidget(self.label_24, 2, 0); g6.addWidget(self.castManganese,2,1)
        g2v.addWidget(self.groupBox_6)
        ll.addWidget(self.groupBox_2)

        # ── Лом ───────────────────────────────────────────────────────────
        self.groupBox_3 = QtWidgets.QGroupBox()
        self.groupBox_3.setObjectName("groupBox_3")
        g3v = QtWidgets.QVBoxLayout(self.groupBox_3)
        g3v.setContentsMargins(4, 4, 4, 4)
        g3top = QtWidgets.QGridLayout()
        g3top.setSpacing(4)
        g3top.setColumnStretch(1, 1)
        self.label_11 = _lbl("label_11"); self.scrapWeight = _edit("scrapWeight")
        g3top.addWidget(self.label_11, 0, 0); g3top.addWidget(self.scrapWeight, 0, 1)
        g3v.addLayout(g3top)
        self.groupBox_7 = QtWidgets.QGroupBox()
        self.groupBox_7.setObjectName("groupBox_7")
        g7 = QtWidgets.QGridLayout(self.groupBox_7)
        g7.setSpacing(4)
        g7.setColumnStretch(1, 1); g7.setColumnStretch(3, 1)
        self.label_12 = _lbl("label_12"); self.scrapCarbon   = _edit("scrapCarbon")
        self.label_13 = _lbl("label_13"); self.scrapSerum    = _edit("scrapSerum")
        self.label_14 = _lbl("label_14"); self.scrapSilicon  = _edit("scrapSilicon")
        self.label_15 = _lbl("label_15"); self.scrapPhosphor = _edit("scrapPhosphor")
        self.label_25 = _lbl("label_25"); self.scrapManganese= _edit("scrapManganese")
        g7.addWidget(self.label_12, 0, 0); g7.addWidget(self.scrapCarbon,  0, 1)
        g7.addWidget(self.label_13, 0, 2); g7.addWidget(self.scrapSerum,   0, 3)
        g7.addWidget(self.label_14, 1, 0); g7.addWidget(self.scrapSilicon, 1, 1)
        g7.addWidget(self.label_15, 1, 2); g7.addWidget(self.scrapPhosphor,1, 3)
        g7.addWidget(self.label_25, 2, 0); g7.addWidget(self.scrapManganese,2,1)
        g3v.addWidget(self.groupBox_7)
        ll.addWidget(self.groupBox_3)

        # ── Металлошихта / Хим. состав шихты ─────────────────────────────
        mc2_row = QtWidgets.QHBoxLayout()
        mc2_row.setSpacing(5)
        self.groupBox_5 = QtWidgets.QGroupBox()
        self.groupBox_5.setObjectName("groupBox_5")
        self.groupBox_5.setFixedWidth(148)
        g5h = QtWidgets.QHBoxLayout(self.groupBox_5)
        g5v = QtWidgets.QVBoxLayout()
        self.label_16 = _lbl("label_16")
        self.MetalCharge = _ro_edit("MetalCharge")
        g5v.addWidget(self.label_16)
        g5v.addWidget(self.MetalCharge)
        self.calcMetalCharge = QtWidgets.QPushButton()
        self.calcMetalCharge.setObjectName("calcMetalCharge")
        self.calcMetalCharge.setIcon(_icon("Pictures/calculate.ico"))
        self.calcMetalCharge.setIconSize(QtCore.QSize(26, 26))
        self.calcMetalCharge.setFlat(True)
        self.calcMetalCharge.setFixedSize(36, 36)
        self.calcMetalCharge.clicked.connect(self.calcMetalChargeClicked)
        g5h.addLayout(g5v)
        g5h.addWidget(self.calcMetalCharge)
        mc2_row.addWidget(self.groupBox_5)

        self.groupBox_8 = QtWidgets.QGroupBox()
        self.groupBox_8.setObjectName("groupBox_8")
        g8 = QtWidgets.QGridLayout(self.groupBox_8)
        g8.setSpacing(3)
        g8.setColumnStretch(1, 1); g8.setColumnStretch(3, 1)
        self.label_17 = _lbl("label_17"); self.ChemCarbon   = _ro_edit("ChemCarbon")
        self.label_19 = _lbl("label_19"); self.ChemSilicon  = _ro_edit("ChemSilicon")
        self.label_21 = _lbl("label_21"); self.ChemManganese= _ro_edit("ChemManganese")
        self.label_18 = _lbl("label_18"); self.ChemSerum    = _ro_edit("ChemSerum")
        self.label_20 = _lbl("label_20"); self.ChemPhosphor = _ro_edit("ChemPhosphor")
        g8.addWidget(self.label_17, 0, 0); g8.addWidget(self.ChemCarbon,   0, 1)
        g8.addWidget(self.label_19, 0, 2); g8.addWidget(self.ChemSilicon,  0, 3)
        g8.addWidget(self.label_21, 1, 0); g8.addWidget(self.ChemManganese,1, 1)
        g8.addWidget(self.label_18, 1, 2); g8.addWidget(self.ChemSerum,    1, 3)
        g8.addWidget(self.label_20, 2, 0); g8.addWidget(self.ChemPhosphor, 2, 1)
        mc2_row.addWidget(self.groupBox_8, 1)
        ll.addLayout(mc2_row)

        # ── Флюсы ─────────────────────────────────────────────────────────
        self.groupBox_10 = QtWidgets.QGroupBox()
        self.groupBox_10.setObjectName("groupBox_10")
        g10v = QtWidgets.QVBoxLayout(self.groupBox_10)
        g10v.setContentsMargins(4, 4, 4, 4)
        g10v.setSpacing(4)
        flux_ctrl = QtWidgets.QHBoxLayout()
        flux_ctrl.setSpacing(4)
        self.tip_flyusa_label = _lbl("tip_flyusa_label")
        self.FluxeType = QtWidgets.QComboBox()
        self.FluxeType.setObjectName("FluxeType")
        self.AddFluxe = _icon_btn("GUI\\../Pictures/add.ico")
        self.AddFluxe.setObjectName("AddFluxe")
        self.AddFluxe.clicked.connect(self.AddFluxeButtonClicked)
        self.RemoveFluxe = _icon_btn("GUI\\../Pictures/remove.ico")
        self.RemoveFluxe.setObjectName("RemoveFluxe")
        self.RemoveFluxe.clicked.connect(self.removeFluxeButtonClicked)
        flux_ctrl.addWidget(self.tip_flyusa_label)
        flux_ctrl.addWidget(self.FluxeType, 1)
        flux_ctrl.addWidget(self.AddFluxe)
        flux_ctrl.addWidget(self.RemoveFluxe)
        g10v.addLayout(flux_ctrl)
        self.FluxeTable = QtWidgets.QTableWidget()
        self.FluxeTable.setObjectName("FluxeTable")
        self.FluxeTable.setColumnCount(2)
        self.FluxeTable.setRowCount(0)
        self.FluxeTable.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem())
        self.FluxeTable.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem())
        self.FluxeTable.horizontalHeader().setStretchLastSection(True)
        self.FluxeTable.setMaximumHeight(120)
        _dark_table(self.FluxeTable)
        g10v.addWidget(self.FluxeTable)
        ll.addWidget(self.groupBox_10)

        ll.addStretch()
        self._left_scroll.setWidget(lw)
        main_splitter.addWidget(self._left_scroll)

        # ────────────────────────────────────────────────────────────────────
        # CENTER PANEL — PROCESS FLOW
        # ────────────────────────────────────────────────────────────────────
        self._center_panel = QtWidgets.QWidget()
        cw = self._center_panel
        cw.setObjectName("center_widget")
        cw.setMinimumWidth(230)
        cw.setAutoFillBackground(True)
        cv = QtWidgets.QVBoxLayout(cw)
        cv.setContentsMargins(10, 10, 10, 10)
        cv.setSpacing(5)

        # Scenario task
        self.label_29 = _lbl("label_29")
        cv.addWidget(self.label_29)
        self.ScenarioTask = QtWidgets.QPlainTextEdit()
        self.ScenarioTask.setReadOnly(True)
        self.ScenarioTask.setObjectName("ScenarioTask")
        self.ScenarioTask.setMinimumHeight(50)
        self.ScenarioTask.setMaximumHeight(80)
        cv.addWidget(self.ScenarioTask)

        # Scenario load progress
        self.scenarioProgress = QtWidgets.QProgressBar()
        self.scenarioProgress.setObjectName("scenarioProgress")
        self.scenarioProgress.setValue(0)
        self.scenarioProgress.setFixedHeight(12)
        cv.addWidget(self.scenarioProgress)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("QFrame { color: rgba(0,200,240,0.25); background: rgba(0,200,240,0.25); }")
        cv.addWidget(sep)

        seq_title = QtWidgets.QLabel(
            "\u041f\u041e\u0421\u041b\u0415\u0414\u041e\u0412\u0410\u0422\u0415\u041b\u042c\u041d\u041e\u0421\u0422\u042c  \u0420\u0410\u0421\u0427\u0401\u0422\u041e\u0412")
        seq_title.setAlignment(QtCore.Qt.AlignCenter)
        seq_title.setFixedHeight(16)
        seq_title.setStyleSheet(
            "color: rgba(0,200,240,0.70); font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        cv.addWidget(seq_title)

        self._stage_leds = {}
        self._stage_style_widgets = []

        def _stage_row(num, label_text, connect_fn, led_key, btn_attr,
                       guard_fn=None, guard_label=""):
            wrapper = QtWidgets.QWidget()
            wrapper.setFixedHeight(28)
            row = QtWidgets.QHBoxLayout(wrapper)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(5)
            num_lbl = QtWidgets.QLabel(str(num))
            num_lbl.setFixedSize(20, 20)
            num_lbl.setAlignment(QtCore.Qt.AlignCenter)
            led = _led()
            self._stage_leds[led_key] = led
            stg_lbl = QtWidgets.QLabel(label_text)
            self._stage_style_widgets.append((num_lbl, stg_lbl))
            calc_btn = QtWidgets.QPushButton()
            calc_btn.setIcon(_icon("Pictures/calculate.ico"))
            calc_btn.setIconSize(QtCore.QSize(20, 20))
            calc_btn.setFlat(True)
            calc_btn.setAutoDefault(False)
            calc_btn.setDefault(False)
            calc_btn.setFocusPolicy(QtCore.Qt.NoFocus)
            calc_btn.setFixedSize(28, 24)

            def _make_guarded(fn, gf, gl):
                def _on_click():
                    if gf is None or gf():
                        fn()
                    else:
                        QtWidgets.QMessageBox.warning(
                            None,
                            "Предыдущий этап не выполнен",
                            f"Сначала завершите этап:\n«{gl}»")
                return _on_click

            calc_btn.clicked.connect(_make_guarded(connect_fn, guard_fn, guard_label))
            setattr(self, btn_attr, calc_btn)
            row.addWidget(num_lbl)
            row.addWidget(led)
            row.addWidget(stg_lbl, 1)
            row.addWidget(calc_btn)
            return wrapper

        cv.addWidget(_stage_row(
            1, "Металлошихта",
            self.calcMetalChargeClicked, "metalCharge", "MetalChargeCalc"))
        cv.addWidget(_stage_row(
            2, "Табл. окисления",
            self.calcTableClick, "table", "CalcTable",
            guard_fn=lambda: metalChargeCalcked,
            guard_label="Металлошихта"))
        cv.addWidget(_stage_row(
            3, "Расчёт шлака",
            self.slagCalcClicked, "slag", "SlagCalc",
            guard_fn=lambda: tableCalcked,
            guard_label="Табл. окисления"))
        cv.addWidget(_stage_row(
            4, "Расчёт дутья",
            self.blastCalcClicked, "blast", "BlastCalc",
            guard_fn=lambda: slagCalcked,
            guard_label="Расчёт шлака"))
        cv.addWidget(_stage_row(
            5, "Матер. баланс",
            self.MaterialBalanceCalcClicked, "matBalance", "MaterialBalanceCalc",
            guard_fn=lambda: blastCalcked,
            guard_label="Расчёт дутья"))
        cv.addWidget(_stage_row(
            6, "Тепл. баланс",
            self.HeatBalanceCalcClicked, "heatBalance", "HeatBalanceCalc",
            guard_fn=lambda: materialBalanceCalcked,
            guard_label="Матер. баланс"))
        cv.addWidget(_stage_row(
            7, "Раскисление",
            self.deoxCalc, "deox", "SteelDeoxidationCalc",
            guard_fn=lambda: heatBalanceCalcked,
            guard_label="Тепл. баланс"))
        cv.addWidget(_stage_row(
            8, "Рекомендации",
            self.getRecomendation, "recomendation", "RecomendationCalc",
            guard_fn=lambda: heatBalanceCalcked,
            guard_label="Тепл. баланс"))

        cv.addSpacing(4)
        self.GetResExample = QtWidgets.QPushButton(
            "\u25ba  \u0417\u0410\u041f\u0423\u0421\u0422\u0418\u0422\u042c  \u0412\u0421\u0415  \u042d\u0422\u0410\u041f\u042b")
        self.GetResExample.setObjectName("GetResExample")
        self.GetResExample.setMinimumHeight(28)
        self.GetResExample.setMaximumHeight(28)
        self.GetResExample.clicked.connect(self.GetScenarioExample)
        cv.addWidget(self.GetResExample)
        cv.addStretch()
        main_splitter.addWidget(cw)

        # ────────────────────────────────────────────────────────────────────
        # RIGHT PANEL — MONITORING
        # ────────────────────────────────────────────────────────────────────
        self._right_scroll = QtWidgets.QScrollArea()
        self._right_scroll.setWidgetResizable(True)
        self._right_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._right_scroll.setMinimumWidth(270)

        self._right_panel = QtWidgets.QWidget()
        rw = self._right_panel
        rw.setAutoFillBackground(True)
        self._result_kpi_frames = []
        rl = QtWidgets.QVBoxLayout(rw)
        rl.setContentsMargins(6, 8, 8, 8)
        rl.setSpacing(5)

        # ── Результаты плавки ─────────────────────────────────────────────
        res_grp = QtWidgets.QGroupBox()
        res_grp.setObjectName("res_grp")
        res_v = QtWidgets.QVBoxLayout(res_grp)
        res_v.setContentsMargins(5, 5, 5, 5)
        res_v.setSpacing(4)

        temp_row = QtWidgets.QHBoxLayout()
        temp_row.setSpacing(6)

        def _big_result_frame(label_txt, border_rgb, text_color, obj_name):
            fr = QtWidgets.QFrame()
            fv = QtWidgets.QVBoxLayout(fr)
            fv.setContentsMargins(6, 3, 6, 3)
            cap = QtWidgets.QLabel(label_txt)
            val = _ro_edit(obj_name)
            val.setAlignment(QtCore.Qt.AlignCenter)
            fv.addWidget(cap)
            fv.addWidget(val)
            self._result_kpi_frames.append((fr, cap, val, border_rgb, text_color))
            return fr, val

        fr_lt, self.LiquidSteelTemp = _big_result_frame(
            "\u0422 \u0436\u0438\u0434\u043a\u043e\u0433\u043e \u043c\u0435\u0442\u0430\u043b\u043b\u0430, °C",
            "255,120,0", "#ff6820", "LiquidSteelTemp")
        fr_ot, self.OverheatTemp = _big_result_frame(
            "\u041f\u0435\u0440\u0435\u0433\u0440\u0435\u0432, °C",
            "255,180,0", "#ffaa00", "OverheatTemp")
        self.temperatura_zhidkovo_metalla_v_konce_produvki_label_2 = QtWidgets.QLabel()
        self.temperatura_zhidkovo_metalla_v_konce_produvki_label_2.setObjectName(
            "temperatura_zhidkovo_metalla_v_konce_produvki_label_2")
        self.temperatura_peregreva_label_2 = QtWidgets.QLabel()
        self.temperatura_peregreva_label_2.setObjectName("temperatura_peregreva_label_2")
        temp_row.addWidget(fr_lt, 1)
        temp_row.addWidget(fr_ot, 1)
        res_v.addLayout(temp_row)

        # Result data grid
        self.groupBox_12 = QtWidgets.QGroupBox()
        self.groupBox_12.setObjectName("groupBox_12")
        g12v = QtWidgets.QVBoxLayout(self.groupBox_12)
        g12v.setContentsMargins(5, 5, 5, 5)
        g12v.setSpacing(4)
        g12g = QtWidgets.QGridLayout()
        g12g.setSpacing(4)
        g12g.setColumnStretch(1, 1)
        self.label_43 = _lbl("label_43"); self.CO2ThrowRes           = _ro_edit("CO2ThrowRes")
        self.label_44 = _lbl("label_44"); self.SteelWeightRes        = _ro_edit("SteelWeightRes")
        self.label_45 = _lbl("label_45"); self.SlagWeightRes         = _ro_edit("SlagWeightRes")
        self.label_47 = _lbl("label_47"); self.resultSteelTemperature= _ro_edit("resultSteelTemperature")
        self.label_46 = _lbl("label_46"); self.LiningWeightLoss      = _ro_edit("LiningWeightLoss")
        for row_idx, (lbl, wdg) in enumerate([
                (self.label_43, self.CO2ThrowRes),
                (self.label_44, self.SteelWeightRes),
                (self.label_45, self.SlagWeightRes),
                (self.label_47, self.resultSteelTemperature),
                (self.label_46, self.LiningWeightLoss)]):
            g12g.addWidget(lbl, row_idx, 0)
            g12g.addWidget(wdg, row_idx, 1)
        g12v.addLayout(g12g)
        self.himicheskii_sostav_poluchennoi_stali_label_2 = _lbl("himicheskii_sostav_poluchennoi_stali_label_2")
        g12v.addWidget(self.himicheskii_sostav_poluchennoi_stali_label_2)
        self.SteelChemResult = QtWidgets.QTableWidget()
        self.SteelChemResult.setObjectName("SteelChemResult")
        self.SteelChemResult.setColumnCount(5)
        self.SteelChemResult.setRowCount(1)
        self.SteelChemResult.setVerticalHeaderItem(0, QtWidgets.QTableWidgetItem())
        for c in range(5):
            self.SteelChemResult.setHorizontalHeaderItem(c, QtWidgets.QTableWidgetItem())
        self.SteelChemResult.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.SteelChemResult.setMaximumHeight(62)
        _dark_table(self.SteelChemResult)
        g12v.addWidget(self.SteelChemResult)
        self.himicheskii_sostav_poluchennoi_stali_label_3 = _lbl("himicheskii_sostav_poluchennoi_stali_label_3")
        g12v.addWidget(self.himicheskii_sostav_poluchennoi_stali_label_3)
        self.SlagChemResult = QtWidgets.QTableWidget()
        self.SlagChemResult.setObjectName("SlagChemResult")
        self.SlagChemResult.setColumnCount(5)
        self.SlagChemResult.setRowCount(1)
        self.SlagChemResult.setVerticalHeaderItem(0, QtWidgets.QTableWidgetItem())
        for c in range(5):
            self.SlagChemResult.setHorizontalHeaderItem(c, QtWidgets.QTableWidgetItem())
        self.SlagChemResult.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.SlagChemResult.setMaximumHeight(62)
        _dark_table(self.SlagChemResult)
        g12v.addWidget(self.SlagChemResult)

        res_v.addWidget(self.groupBox_12)
        rl.addWidget(res_grp)

        # ── Дутьё ─────────────────────────────────────────────────────────
        self.raschet_dutya_group_box = QtWidgets.QGroupBox()
        self.raschet_dutya_group_box.setObjectName("raschet_dutya_group_box")
        rdg = QtWidgets.QGridLayout(self.raschet_dutya_group_box)
        rdg.setSpacing(4)
        rdg.setColumnStretch(1, 1)
        self.TotalOxygenDemandBlastLabel    = _lbl("TotalOxygenDemandBlastLabel")
        self.TotalConsumptionOfBlastKgLabel = _lbl("TotalConsumptionOfBlastKgLabel")
        self.ExcessBlastLabel               = _lbl("ExcessBlastLabel")
        self.TotalConsumptionOfBlastM3Label = _lbl("TotalConsumptionOfBlastM3Label")
        self.TotalOxygenDemandBlast    = _ro_edit("TotalOxygenDemandBlast")
        self.TotalConsumptionOfBlastKg = _ro_edit("TotalConsumptionOfBlastKg")
        self.ExcessBlast               = _ro_edit("ExcessBlast")
        self.TotalConsumptionOfBlastM3 = _ro_edit("TotalConsumptionOfBlastM3")
        for r, (lbl, wdg) in enumerate([
                (self.TotalOxygenDemandBlastLabel,    self.TotalOxygenDemandBlast),
                (self.TotalConsumptionOfBlastKgLabel, self.TotalConsumptionOfBlastKg),
                (self.ExcessBlastLabel,               self.ExcessBlast),
                (self.TotalConsumptionOfBlastM3Label, self.TotalConsumptionOfBlastM3)]):
            rdg.addWidget(lbl, r, 0)
            rdg.addWidget(wdg, r, 1)
        self.changeSetings = QtWidgets.QPushButton()
        self.changeSetings.setObjectName("changeSetings")
        self.changeSetings.setFlat(True)
        rdg.addWidget(self.changeSetings, 4, 0, 1, 2)
        rl.addWidget(self.raschet_dutya_group_box)
        rl.addStretch()

        self._right_scroll.setWidget(rw)
        main_splitter.addWidget(self._right_scroll)

        # ────────────────────────────────────────────────────────────────────
        # 3D CONVERTER PANEL
        # ────────────────────────────────────────────────────────────────────
        if create_converter_widget is not None:
            self.converter3d = create_converter_widget()
            main_splitter.addWidget(self.converter3d)
            main_splitter.setSizes([315, 195, 252, 398])
        else:
            self.converter3d = None
            main_splitter.setSizes([315, 215, 310])

        main_layout.addWidget(main_splitter, stretch=1)

        # ════════════════════════════════════════════════════════════════════
        # BOTTOM DETAIL TABS
        # ════════════════════════════════════════════════════════════════════
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setMinimumHeight(300)
        self.tabWidget.setMaximumHeight(300)

        # ── tab_7  Справка ────────────────────────────────────────────────
        self.tab_7 = QtWidgets.QWidget()
        self.tab_7.setObjectName("tab_7")
        t7l = QtWidgets.QVBoxLayout(self.tab_7)
        t7l.setContentsMargins(10, 8, 10, 8)
        t7l.setSpacing(8)

        self._stages_lbl = QtWidgets.QLabel()
        self._stages_lbl.setTextFormat(QtCore.Qt.RichText)
        self._stages_lbl.setWordWrap(True)
        self._stages_lbl.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        t7l.addWidget(self._stages_lbl, 1)

        self._hints_lbl = QtWidgets.QLabel()
        self._hints_lbl.setTextFormat(QtCore.Qt.RichText)
        self._hints_lbl.setWordWrap(True)
        t7l.addWidget(self._hints_lbl, 0)

        self.tabWidget.addTab(self.tab_7, "")

        # ── tab  Металлошихта (oxidation table) ──────────────────────────
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        tab_layout = QtWidgets.QVBoxLayout(self.tab)
        tab_layout.setContentsMargins(5, 5, 5, 5)
        self.groupBox_9 = QtWidgets.QGroupBox()
        self.groupBox_9.setObjectName("groupBox_9")
        gb9_h = QtWidgets.QHBoxLayout(self.groupBox_9)
        gb9_h.setSpacing(5)
        self.OxidationTable = QtWidgets.QTableWidget()
        self.OxidationTable.setObjectName("OxidationTable")
        self.OxidationTable.setColumnCount(8)
        self.OxidationTable.setRowCount(6)
        self.OxidationTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.OxidationTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.OxidationTable.verticalHeader().setDefaultSectionSize(22)
        for r in range(6):
            self.OxidationTable.setVerticalHeaderItem(r, QtWidgets.QTableWidgetItem())
        for c in range(8):
            self.OxidationTable.setHorizontalHeaderItem(c, QtWidgets.QTableWidgetItem())
        _dark_table(self.OxidationTable)
        gb9_h.addWidget(self.OxidationTable)
        tab_layout.addWidget(self.groupBox_9)
        self.tabWidget.addTab(self.tab, "")

        # ── tab_2  Шлак ───────────────────────────────────────────────────
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        t2l = QtWidgets.QVBoxLayout(self.tab_2)
        t2l.setContentsMargins(6, 6, 6, 6)
        t2l.setSpacing(5)

        self.shlak_group_box = QtWidgets.QGroupBox()
        self.shlak_group_box.setObjectName("shlak_group_box")
        shl_v = QtWidgets.QVBoxLayout(self.shlak_group_box)
        shl_v.setContentsMargins(4, 4, 4, 4)
        shl_v.setSpacing(4)
        shl_cols = QtWidgets.QHBoxLayout()
        shl_cols.setSpacing(5)

        self.him_sostav_shlaka_group_box = QtWidgets.QGroupBox()
        self.him_sostav_shlaka_group_box.setObjectName("him_sostav_shlaka_group_box")
        hss_g = QtWidgets.QGridLayout(self.him_sostav_shlaka_group_box)
        hss_g.setSpacing(3)
        hss_g.setColumnStretch(1, 1)
        self.SlagSiO2Label  = _lbl("SlagSiO2Label");  self.SlagSiO2  = _ro_edit("SlagSiO2")
        self.SlagCaOLabel   = _lbl("SlagCaOLabel");   self.SlagCaO   = _ro_edit("SlagCaO")
        self.SlagMgOLabel   = _lbl("SlagMgOLabel");   self.SlagMgO   = _ro_edit("SlagMgO")
        self.SlagAl2O3Label = _lbl("SlagAl2O3Label"); self.SlagAl2O3 = _ro_edit("SlagAl2O3")
        self.SlagOthersLabel= _lbl("SlagOthersLabel");self.SlagOthers= _ro_edit("SlagOthers")
        self.SlagFeOLabel   = _lbl("SlagFeOLabel");   self.SlagFeO   = _ro_edit("SlagFeO")
        self.SlagFe2O3Label = _lbl("SlagFe2O3Label"); self.SlagFe2O3 = _ro_edit("SlagFe2O3")
        self.SlagWeightLabel= _lbl("SlagWeightLabel");self.SlagWeight= _ro_edit("SlagWeight")
        for r, (lbl, wdg) in enumerate([
                (self.SlagSiO2Label,  self.SlagSiO2),
                (self.SlagCaOLabel,   self.SlagCaO),
                (self.SlagMgOLabel,   self.SlagMgO),
                (self.SlagAl2O3Label, self.SlagAl2O3),
                (self.SlagOthersLabel,self.SlagOthers),
                (self.SlagFeOLabel,   self.SlagFeO),
                (self.SlagFe2O3Label, self.SlagFe2O3),
                (self.SlagWeightLabel,self.SlagWeight)]):
            hss_g.addWidget(lbl, r, 0)
            hss_g.addWidget(wdg, r, 1)
        shl_cols.addWidget(self.him_sostav_shlaka_group_box, 1)

        self.him_sostav_shlaka_v_procentah_group_box = QtWidgets.QGroupBox()
        self.him_sostav_shlaka_v_procentah_group_box.setObjectName("him_sostav_shlaka_v_procentah_group_box")
        hssv_g = QtWidgets.QGridLayout(self.him_sostav_shlaka_v_procentah_group_box)
        hssv_g.setSpacing(3)
        hssv_g.setColumnStretch(1, 1)
        self.SlagSiO2Label_2  = _lbl("SlagSiO2Label_2");  self.SlagSiO2Perc  = _ro_edit("SlagSiO2Perc")
        self.SlagCaOLabel_2   = _lbl("SlagCaOLabel_2");   self.SlagCaOPerc   = _ro_edit("SlagCaOPerc")
        self.SlagMgOLabel_2   = _lbl("SlagMgOLabel_2");   self.SlagMgOPerc   = _ro_edit("SlagMgOPerc")
        self.SlagAl2O3Label_2 = _lbl("SlagAl2O3Label_2"); self.SlagAl2O3Perc = _ro_edit("SlagAl2O3Perc")
        self.SlagOthersLabel_2= _lbl("SlagOthersLabel_2");self.SlagOthersPerc= _ro_edit("SlagOthersPerc")
        self.SlagFeOLabel_2   = _lbl("SlagFeOLabel_2");   self.SlagFeOPerc   = _ro_edit("SlagFeOPerc")
        self.SlagFe2O3Label_2 = _lbl("SlagFe2O3Label_2"); self.SlagFe2O3Perc = _ro_edit("SlagFe2O3Perc")
        for r, (lbl, wdg) in enumerate([
                (self.SlagSiO2Label_2,  self.SlagSiO2Perc),
                (self.SlagCaOLabel_2,   self.SlagCaOPerc),
                (self.SlagMgOLabel_2,   self.SlagMgOPerc),
                (self.SlagAl2O3Label_2, self.SlagAl2O3Perc),
                (self.SlagOthersLabel_2,self.SlagOthersPerc),
                (self.SlagFeOLabel_2,   self.SlagFeOPerc),
                (self.SlagFe2O3Label_2, self.SlagFe2O3Perc)]):
            hssv_g.addWidget(lbl, r, 0)
            hssv_g.addWidget(wdg, r, 1)
        shl_cols.addWidget(self.him_sostav_shlaka_v_procentah_group_box, 1)
        shl_v.addLayout(shl_cols)
        t2l.addWidget(self.shlak_group_box, 1)
        self.tabWidget.addTab(self.tab_2, "")

        # ── tab_3  Материальный баланс ────────────────────────────────────
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        t3l = QtWidgets.QVBoxLayout(self.tab_3)
        t3l.setContentsMargins(5, 5, 5, 5)
        t3l.setSpacing(4)

        top3 = QtWidgets.QHBoxLayout()
        top3.setSpacing(8)
        self.ReclaimedIronWeightLabel = _lbl("ReclaimedIronWeightLabel")
        self.ReclaimedIronWeight = _ro_edit("ReclaimedIronWeight")
        self.ReclaimedIronWeight.setFixedWidth(80)
        self.vyhod_zhidkovo_metalla_pered_raskisleniem_label = _lbl(
            "vyhod_zhidkovo_metalla_pered_raskisleniem_label")
        self.LiquidIronYield = _ro_edit("LiquidIronYield")
        self.LiquidIronYield.setFixedWidth(80)
        top3.addWidget(self.ReclaimedIronWeightLabel)
        top3.addWidget(self.ReclaimedIronWeight)
        top3.addWidget(self.vyhod_zhidkovo_metalla_pered_raskisleniem_label)
        top3.addWidget(self.LiquidIronYield)
        top3.addStretch()
        t3l.addLayout(top3)

        mid3 = QtWidgets.QHBoxLayout()
        mid3.setSpacing(5)
        self.IncomingData = QtWidgets.QTableWidget()
        self.IncomingData.setObjectName("IncomingData")
        self.IncomingData.setColumnCount(2)
        self.IncomingData.setRowCount(0)
        self.IncomingData.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem())
        self.IncomingData.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem())
        self.IncomingData.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _dark_table(self.IncomingData)
        mid3.addWidget(self.IncomingData, 1)

        self.OutputData = QtWidgets.QTableWidget()
        self.OutputData.setObjectName("OutputData")
        self.OutputData.setColumnCount(2)
        self.OutputData.setRowCount(0)
        self.OutputData.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem())
        self.OutputData.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem())
        self.OutputData.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _dark_table(self.OutputData)
        mid3.addWidget(self.OutputData, 1)

        self.OutputDataGroupBox = QtWidgets.QGroupBox()
        self.OutputDataGroupBox.setObjectName("OutputDataGroupBox")
        odgb_v = QtWidgets.QVBoxLayout(self.OutputDataGroupBox)
        odgb_v.setContentsMargins(5, 5, 5, 5)
        odgb_v.setSpacing(3)
        odgb_g = QtWidgets.QGridLayout()
        odgb_g.setSpacing(3)
        odgb_g.setColumnMinimumWidth(0, 155)
        odgb_g.setColumnStretch(1, 1)
        self.MassOfOxidizedImpuritiesLabel  = _lbl("MassOfOxidizedImpuritiesLabel")
        self.MassOfOxidizedImpurities       = _ro_edit("MassOfOxidizedImpurities")
        self.MassOfOxidesPassingIntoSlagLabel = _lbl("MassOfOxidesPassingIntoSlagLabel")
        self.MassOfOxidesPassingIntoSlag    = _ro_edit("MassOfOxidesPassingIntoSlag")
        self.LossWithCarryOverLabel         = _lbl("LossWithCarryOverLabel")
        self.LossWithCarryOver              = _ro_edit("LossWithCarryOver")
        self.DustLossLabel                  = _lbl("DustLossLabel")
        self.DustLoss                       = _ro_edit("DustLoss")
        for r, (lbl, wdg) in enumerate([
                (self.MassOfOxidizedImpuritiesLabel,   self.MassOfOxidizedImpurities),
                (self.MassOfOxidesPassingIntoSlagLabel,self.MassOfOxidesPassingIntoSlag),
                (self.LossWithCarryOverLabel,           self.LossWithCarryOver),
                (self.DustLossLabel,                    self.DustLoss)]):
            lbl.setWordWrap(False)
            lbl.setStyleSheet("font-size: 10px; color: #b8c8d0;")
            odgb_g.addWidget(lbl, r, 0)
            odgb_g.addWidget(wdg, r, 1)
        odgb_v.addLayout(odgb_g)
        self.OutputDataTable = QtWidgets.QTableWidget()
        self.OutputDataTable.setObjectName("OutputDataTable")
        self.OutputDataTable.setColumnCount(3)
        self.OutputDataTable.setRowCount(7)
        self.OutputDataTable.verticalHeader().setDefaultSectionSize(20)
        for r in range(7):
            self.OutputDataTable.setVerticalHeaderItem(r, QtWidgets.QTableWidgetItem())
        for c in range(3):
            self.OutputDataTable.setHorizontalHeaderItem(c, QtWidgets.QTableWidgetItem())
        self.OutputDataTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _dark_table(self.OutputDataTable)
        odgb_v.addWidget(self.OutputDataTable, 1)
        mid3.addWidget(self.OutputDataGroupBox, 1)
        t3l.addLayout(mid3)
        self.tabWidget.addTab(self.tab_3, "")

        # ── tab_4  Тепловой баланс ────────────────────────────────────────
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        t4l = QtWidgets.QVBoxLayout(self.tab_4)
        t4l.setContentsMargins(0, 0, 0, 0)
        t4l.setSpacing(0)

        # Scroll area for content that may exceed tab height
        t4_scroll = QtWidgets.QScrollArea()
        t4_scroll.setWidgetResizable(True)
        t4_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        t4_inner = QtWidgets.QWidget()
        t4_inner_v = QtWidgets.QVBoxLayout(t4_inner)
        t4_inner_v.setContentsMargins(5, 5, 5, 5)
        t4_inner_v.setSpacing(4)
        heat_top = QtWidgets.QHBoxLayout()
        heat_top.setSpacing(5)

        def _heat_lbl(obj_name):
            lbl = QtWidgets.QLabel()
            lbl.setObjectName(obj_name)
            lbl.setWordWrap(False)
            lbl.setStyleSheet("font-size: 10px; color: #b8c8d0;")
            return lbl

        self.prihodnie_statii_group_box_2 = QtWidgets.QGroupBox()
        self.prihodnie_statii_group_box_2.setObjectName("prihodnie_statii_group_box_2")
        ps_v = QtWidgets.QVBoxLayout(self.prihodnie_statii_group_box_2)
        ps_v.setContentsMargins(5, 5, 5, 5)
        ps_v.setSpacing(3)
        ps_g = QtWidgets.QGridLayout()
        ps_g.setSpacing(3)
        ps_g.setColumnMinimumWidth(0, 130)
        ps_g.setColumnStretch(1, 1)
        self.phizicheskoe_teplo_zhidkovo_chuguna_label_2     = _heat_lbl("phizicheskoe_teplo_zhidkovo_chuguna_label_2")
        self.teplovoi_effect_reakcii_okisleniya_label_2      = _heat_lbl("teplovoi_effect_reakcii_okisleniya_label_2")
        self.himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2 = _heat_lbl("himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2")
        self.teplovoi_effect_reakcii_shlakoobrazovaniya_label_2= _heat_lbl("teplovoi_effect_reakcii_shlakoobrazovaniya_label_2")
        self.teplo_ot_dozhiganiya_co_label_2                 = _heat_lbl("teplo_ot_dozhiganiya_co_label_2")
        self.obshii_prihod_tepla_label_2                     = _heat_lbl("obshii_prihod_tepla_label_2")
        self.CastPhysHeat     = _ro_edit("CastPhysHeat")
        self.ThermalReactEffect = _ro_edit("ThermalReactEffect")
        self.ChemHeatOxyd     = _ro_edit("ChemHeatOxyd")
        self.ChemHeatSlag     = _ro_edit("ChemHeatSlag")
        self.HeatCO           = _ro_edit("HeatCO")
        self.TotalHeatInc     = _ro_edit("TotalHeatInc")
        for r, (lbl, wdg) in enumerate([
                (self.phizicheskoe_teplo_zhidkovo_chuguna_label_2,     self.CastPhysHeat),
                (self.teplovoi_effect_reakcii_okisleniya_label_2,      self.ThermalReactEffect),
                (self.himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2,self.ChemHeatOxyd),
                (self.teplovoi_effect_reakcii_shlakoobrazovaniya_label_2,self.ChemHeatSlag),
                (self.teplo_ot_dozhiganiya_co_label_2,                 self.HeatCO),
                (self.obshii_prihod_tepla_label_2,                     self.TotalHeatInc)]):
            ps_g.addWidget(lbl, r, 0)
            ps_g.addWidget(wdg, r, 1)
        ps_v.addLayout(ps_g)
        self.IncomingHeatTable = QtWidgets.QTableWidget()
        self.IncomingHeatTable.setObjectName("IncomingHeatTable")
        self.IncomingHeatTable.setColumnCount(1)
        self.IncomingHeatTable.setRowCount(6)
        self.IncomingHeatTable.verticalHeader().setDefaultSectionSize(20)
        for r in range(6):
            self.IncomingHeatTable.setVerticalHeaderItem(r, QtWidgets.QTableWidgetItem())
        for c in range(2):
            self.IncomingHeatTable.setHorizontalHeaderItem(c, QtWidgets.QTableWidgetItem())
        self.IncomingHeatTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _dark_table(self.IncomingHeatTable)
        ps_v.addWidget(self.IncomingHeatTable, 1)
        heat_top.addWidget(self.prihodnie_statii_group_box_2, 1)

        self.rashodnie_statii_group_box_2 = QtWidgets.QGroupBox()
        self.rashodnie_statii_group_box_2.setObjectName("rashodnie_statii_group_box_2")
        rs_v = QtWidgets.QVBoxLayout(self.rashodnie_statii_group_box_2)
        rs_v.setContentsMargins(5, 5, 5, 5)
        rs_v.setSpacing(3)
        rs_g = QtWidgets.QGridLayout()
        rs_g.setSpacing(3)
        rs_g.setColumnMinimumWidth(0, 130)
        rs_g.setColumnStretch(1, 1)
        self.phizicheskoe_teplo_zhidkovo_metalla_label_2   = _heat_lbl("phizicheskoe_teplo_zhidkovo_metalla_label_2")
        self.phizicheskoe_teplo_shlaka_label_2             = _heat_lbl("phizicheskoe_teplo_shlaka_label_2")
        self.phizicheskoe_teplo_othodyashih_gazov_label_2  = _heat_lbl("phizicheskoe_teplo_othodyashih_gazov_label_2")
        self.HeatConsDecompos_label                        = _heat_lbl("HeatConsDecompos_label")
        self.poteri_tepla_s_vynosami_i_vybrosami_label_2   = _heat_lbl("poteri_tepla_s_vynosami_i_vybrosami_label_2")
        self.HeatDustForm_label                            = _heat_lbl("HeatDustForm_label")
        self.teplo_na_razlozhenie_karbonatov_label_2       = _heat_lbl("teplo_na_razlozhenie_karbonatov_label_2")
        self.teplovie_poteri_label_2                       = _heat_lbl("teplovie_poteri_label_2")
        self.obshii_rashod_tepla_label_2                   = _heat_lbl("obshii_rashod_tepla_label_2")
        self.PhysHeatLiquidSteel = _ro_edit("PhysHeatLiquidSteel")
        self.PhysHeatSlag        = _ro_edit("PhysHeatSlag")
        self.PhysHeatOutGas      = _ro_edit("PhysHeatOutGas")
        self.HeatConsDecompos    = _ro_edit("HeatConsDecompos")
        self.HeatLosesRemove     = _ro_edit("HeatLosesRemove")
        self.HeatDustForm        = _ro_edit("HeatDustForm")
        self.HeatCarbonDecom     = _ro_edit("HeatCarbonDecom")
        self.HeatLoses           = _ro_edit("HeatLoses")
        self.TotalHeatCons       = _ro_edit("TotalHeatCons")
        for r, (lbl, wdg) in enumerate([
                (self.phizicheskoe_teplo_zhidkovo_metalla_label_2,  self.PhysHeatLiquidSteel),
                (self.phizicheskoe_teplo_shlaka_label_2,            self.PhysHeatSlag),
                (self.phizicheskoe_teplo_othodyashih_gazov_label_2, self.PhysHeatOutGas),
                (self.HeatConsDecompos_label,                       self.HeatConsDecompos),
                (self.poteri_tepla_s_vynosami_i_vybrosami_label_2,  self.HeatLosesRemove),
                (self.HeatDustForm_label,                           self.HeatDustForm),
                (self.teplo_na_razlozhenie_karbonatov_label_2,      self.HeatCarbonDecom),
                (self.teplovie_poteri_label_2,                      self.HeatLoses),
                (self.obshii_rashod_tepla_label_2,                  self.TotalHeatCons)]):
            rs_g.addWidget(lbl, r, 0)
            rs_g.addWidget(wdg, r, 1)
        rs_v.addLayout(rs_g)
        self.OutputHeatTable = QtWidgets.QTableWidget()
        self.OutputHeatTable.setObjectName("OutputHeatTable")
        self.OutputHeatTable.setColumnCount(1)
        self.OutputHeatTable.setRowCount(9)
        self.OutputHeatTable.verticalHeader().setDefaultSectionSize(20)
        for r in range(9):
            self.OutputHeatTable.setVerticalHeaderItem(r, QtWidgets.QTableWidgetItem())
        for c in range(2):
            self.OutputHeatTable.setHorizontalHeaderItem(c, QtWidgets.QTableWidgetItem())
        self.OutputHeatTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _dark_table(self.OutputHeatTable)
        rs_v.addWidget(self.OutputHeatTable, 1)
        heat_top.addWidget(self.rashodnie_statii_group_box_2, 1)
        t4_inner_v.addLayout(heat_top)
        t4_scroll.setWidget(t4_inner)
        t4l.addWidget(t4_scroll)
        self.tabWidget.addTab(self.tab_4, "")

        # ── tab_5  Раскисление ────────────────────────────────────────────
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        t5l = QtWidgets.QVBoxLayout(self.tab_5)
        t5l.setContentsMargins(5, 5, 5, 5)
        t5l.setSpacing(4)

        fero_row = QtWidgets.QHBoxLayout()
        fero_row.setSpacing(6)
        self.tip_ferrosplava_label_2 = _lbl("tip_ferrosplava_label_2")
        self.FeroType = QtWidgets.QComboBox()
        self.FeroType.setObjectName("FeroType")
        self.AddFero = _icon_btn("GUI\\../Pictures/add.ico")
        self.AddFero.setObjectName("AddFero")
        self.AddFero.clicked.connect(self.AddFeroBtnClicked)
        self.RemoveFero = _icon_btn("GUI\\../Pictures/remove.ico")
        self.RemoveFero.setObjectName("RemoveFero")
        self.RemoveFero.clicked.connect(self.removeFeroBtnClicked)
        fero_row.addWidget(self.tip_ferrosplava_label_2)
        fero_row.addWidget(self.FeroType, 1)
        fero_row.addWidget(self.AddFero)
        fero_row.addWidget(self.RemoveFero)
        fero_row.addStretch()
        self.label_52 = _lbl("label_52")
        self.rashod_pervovo_ferrosplava_line_edit_2 = _ro_edit("rashod_pervovo_ferrosplava_line_edit_2")
        self.rashod_pervovo_ferrosplava_line_edit_2.setFixedWidth(80)
        self.label_51 = _lbl("label_51")
        self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2 = _ro_edit(
            "vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2")
        self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2.setFixedWidth(80)
        fero_row.addWidget(self.label_52)
        fero_row.addWidget(self.rashod_pervovo_ferrosplava_line_edit_2)
        fero_row.addWidget(self.label_51)
        fero_row.addWidget(self.vyhod_pervovo_metalla_posle_raskisleniya_line_edit_2)
        t5l.addLayout(fero_row)

        self.ChemEmission = QtWidgets.QTableWidget()
        self.ChemEmission.setObjectName("ChemEmission")
        self.ChemEmission.setColumnCount(6)
        self.ChemEmission.setRowCount(0)
        self.ChemEmission.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ChemEmission.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        for c in range(6):
            self.ChemEmission.setHorizontalHeaderItem(c, QtWidgets.QTableWidgetItem())
        self.ChemEmission.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ChemEmission.setMaximumHeight(75)
        _dark_table(self.ChemEmission)
        t5l.addWidget(self.ChemEmission)

        self.balans_pri_raskislenii_stali_label_2 = _lbl("balans_pri_raskislenii_stali_label_2")
        t5l.addWidget(self.balans_pri_raskislenii_stali_label_2)

        self.DeoxidationBalance = QtWidgets.QTableWidget()
        self.DeoxidationBalance.setObjectName("DeoxidationBalance")
        self.DeoxidationBalance.setColumnCount(10)
        self.DeoxidationBalance.setRowCount(6)
        self.DeoxidationBalance.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        for r in range(6):
            self.DeoxidationBalance.setVerticalHeaderItem(r, QtWidgets.QTableWidgetItem())
        for c in range(10):
            self.DeoxidationBalance.setHorizontalHeaderItem(c, QtWidgets.QTableWidgetItem())
        self.DeoxidationBalance.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        _dark_table(self.DeoxidationBalance)
        t5l.addWidget(self.DeoxidationBalance, 1)
        self.tabWidget.addTab(self.tab_5, "")

        # ── tab_6  Рекомендации ───────────────────────────────────────────
        self.tab_6 = QtWidgets.QWidget()
        self.tab_6.setObjectName("tab_6")
        t6l = QtWidgets.QVBoxLayout(self.tab_6)
        t6l.setContentsMargins(8, 6, 8, 6)
        t6l.setSpacing(6)
        self.label_56 = _lbl("label_56")
        t6l.addWidget(self.label_56)
        self.recomendation = QtWidgets.QPlainTextEdit()
        self.recomendation.setObjectName("recomendation")
        self.recomendation.setReadOnly(True)
        t6l.addWidget(self.recomendation, 1)

        mgo_cols = QtWidgets.QHBoxLayout()
        mgo_cols.setSpacing(20)
        mgo_left = QtWidgets.QGridLayout()
        mgo_left.setSpacing(4)
        mgo_left.setColumnStretch(1, 1)
        mgo_right = QtWidgets.QGridLayout()
        mgo_right.setSpacing(4)
        mgo_right.setColumnStretch(1, 1)
        self.label_48 = _lbl("label_48"); self.limit_MgO         = QtWidgets.QLineEdit(); self.limit_MgO.setObjectName("limit_MgO")
        self.label_49 = _lbl("label_49"); self.content_MgO       = QtWidgets.QLineEdit(); self.content_MgO.setObjectName("content_MgO")
        self.label_50 = _lbl("label_50"); self.unsaturation_MgO  = QtWidgets.QLineEdit(); self.unsaturation_MgO.setObjectName("unsaturation_MgO")
        self.label_53 = _lbl("label_53"); self.steel_temp        = QtWidgets.QLineEdit(); self.steel_temp.setObjectName("steel_temp")
        self.label_54 = _lbl("label_54"); self.slag_basicity     = QtWidgets.QLineEdit(); self.slag_basicity.setObjectName("slag_basicity")
        self.label_55 = _lbl("label_55"); self.lining_weight_loss= QtWidgets.QLineEdit(); self.lining_weight_loss.setObjectName("lining_weight_loss")
        for r, (lbl, wdg) in enumerate([
                (self.label_48, self.limit_MgO),
                (self.label_49, self.content_MgO),
                (self.label_50, self.unsaturation_MgO)]):
            mgo_left.addWidget(lbl, r, 0); mgo_left.addWidget(wdg, r, 1)
        for r, (lbl, wdg) in enumerate([
                (self.label_53, self.steel_temp),
                (self.label_54, self.slag_basicity),
                (self.label_55, self.lining_weight_loss)]):
            mgo_right.addWidget(lbl, r, 0); mgo_right.addWidget(wdg, r, 1)
        mgo_cols.addLayout(mgo_left, 1)
        mgo_cols.addLayout(mgo_right, 1)
        t6l.addLayout(mgo_cols)
        self.tabWidget.addTab(self.tab_6, "")

        _sp_exp = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        for _tab_page in (self.tab_7, self.tab, self.tab_2,
                          self.tab_3, self.tab_4, self.tab_5, self.tab_6):
            _tab_page.setSizePolicy(_sp_exp)

        main_layout.addWidget(self.tabWidget)

        # ════════════════════════════════════════════════════════════════════
        # MENUBAR + STATUSBAR
        # ════════════════════════════════════════════════════════════════════
        OperatorForm.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(OperatorForm)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1340, 22))
        self.menubar.setObjectName("menubar")
        self.Menu = QtWidgets.QMenu(self.menubar)
        self.Menu.setObjectName("Menu")
        self.Help = QtWidgets.QMenu(self.menubar)
        self.Help.setObjectName("Help")
        self.Administrate = QtWidgets.QMenu(self.menubar)
        self.Administrate.setEnabled(True)
        self.Administrate.setObjectName("Administrate")
        OperatorForm.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(OperatorForm)
        self.statusbar.setObjectName("statusbar")
        OperatorForm.setStatusBar(self.statusbar)

        self.about    = QtWidgets.QAction(OperatorForm); self.about.setObjectName("about")
        self.SaveFile = QtWidgets.QAction(OperatorForm); self.SaveFile.setObjectName("SaveFile")
        self.SaveFile.setStatusTip("Save file")
        self.Exit     = QtWidgets.QAction(OperatorForm); self.Exit.setObjectName("Exit")
        self.addUser  = QtWidgets.QAction(OperatorForm); self.addUser.setEnabled(True); self.addUser.setObjectName("addUser")
        self.AddUser  = QtWidgets.QAction(OperatorForm); self.AddUser.setEnabled(True);  self.AddUser.setObjectName("AddUser")
        self.AddDbData= QtWidgets.QAction(OperatorForm); self.AddDbData.setEnabled(True); self.AddDbData.setObjectName("AddDbData")

        self.Menu.addAction(self.SaveFile)
        self.Menu.addSeparator()
        self.Menu.addAction(self.Exit)
        self.Help.addAction(self.about)
        self.Administrate.addAction(self.AddUser)
        self.Administrate.addAction(self.AddDbData)
        self.ViewMenu = QtWidgets.QMenu(self.menubar)
        self.ViewMenu.setObjectName("ViewMenu")
        self.theme_toggle = ThemeToggle()
        self.theme_toggle.theme_changed.connect(lambda _t: self.refresh_theme())
        toggle_action = QtWidgets.QWidgetAction(OperatorForm)
        toggle_action.setDefaultWidget(self.theme_toggle)
        self.ViewMenu.addAction(toggle_action)

        self.menubar.addAction(self.Menu.menuAction())
        self.menubar.addAction(self.Administrate.menuAction())
        self.menubar.addAction(self.ViewMenu.menuAction())
        self.menubar.addAction(self.Help.menuAction())

        manager().theme_changed.connect(lambda _t: self.refresh_theme())

        self.Exit.setShortcut("Ctrl+Q")
        self.Exit.triggered.connect(OperatorForm.close)
        self.about.triggered.connect(self.openAbout)
        self.SaveFile.triggered.connect(self.saveResult)

        self.retranslateUi(OperatorForm)
        QtCore.QMetaObject.connectSlotsByName(OperatorForm)

        self._themed_tables = [
            self.OxidationTable, self.FluxeTable,
            self.IncomingData, self.OutputData, self.OutputDataTable,
            self.IncomingHeatTable, self.OutputHeatTable,
            self.ChemEmission, self.DeoxidationBalance,
            self.SteelChemResult, self.SlagChemResult,
        ]
        for _tbl in self._themed_tables:
            _dark_table(_tbl)
            _tbl.setStyleSheet(app_theme.table_style(get_theme()))
        if self.converter3d and hasattr(self.converter3d, 'set_ui_theme'):
            self.converter3d.set_ui_theme(get_theme())
        self.refresh_theme()
    def retranslateUi(self, OperatorForm):
        _t = QtCore.QCoreApplication.translate
        OperatorForm.setWindowTitle(_t("OperatorForm", "Процесс плавки стали — Пульт оператора"))

        # ── Left panel labels ─────────────────────────────────────────────
        self.groupBox_14.setTitle(_t("OperatorForm", "Выбрать сценарий обучения"))
        self.label_27.setText(_t("OperatorForm", "Сценарий:"))
        self.label_31.setText(_t("OperatorForm", "Обучаемый:"))
        self.PerformerName.setPlaceholderText(_t("OperatorForm", "Введите ФИО"))
        self.label_29.setText(_t("OperatorForm", "Задача сценария:"))
        self.groupBox_15.setTitle(_t("OperatorForm", "Ограничения"))
        self.label_32.setText(_t("OperatorForm", "Мин. температура стали [℃]:"))
        self.label_33.setText(_t("OperatorForm", "Содержание P в стали [%масс]:"))
        self.label_34.setText(_t("OperatorForm", "Содержание C в стали [%масс]:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), _t("OperatorForm", "Схема"))

        # ── Default values ────────────────────────────────────────────────
        self.steelCarbon.setText("0.085");   self.steelSerum.setText("0.04")
        self.steelSilicon.setText("0.2");    self.steelPhosphor.setText("0.035")
        self.steelManganese.setText("0.5")

        self.castTemperature.setText("1400"); self.castWeight.setText("290")
        self.castCarbon.setText("4");         self.castSerum.setText("0.025")
        self.castPhosphor.setText("0.15");    self.castManganese.setText("0.7")
        self.castSilicon.setText("0.6")

        self.scrapWeight.setText("110");      self.scrapCarbon.setText("0.1")
        self.scrapSerum.setText("0.04");      self.scrapSilicon.setText("0.2")
        self.scrapManganese.setText("0.05");  self.scrapPhosphor.setText("0.4")

        # ── GroupBox and field labels ─────────────────────────────────────
        self.groupBox.setTitle(_t("OperatorForm", "Сталь"))
        self.groupBox_4.setTitle(_t("OperatorForm", "Химический состав, %масс"))
        self.label.setText(_t("OperatorForm", "Углерод (C):"))
        self.label_2.setText(_t("OperatorForm", "Кремний (Si):"))
        self.label_3.setText(_t("OperatorForm", "Сера (S):"))
        self.label_4.setText(_t("OperatorForm", "Фосфор (P):"))
        self.label_26.setText(_t("OperatorForm", "Марганец (Mn):"))
        self.groupBox_2.setTitle(_t("OperatorForm", "Чугун"))
        self.label_5.setText(_t("OperatorForm", "Температура [℃]:"))
        self.label_6.setText(_t("OperatorForm", "Масса [т]:"))
        self.groupBox_6.setTitle(_t("OperatorForm", "Химический состав, %масс"))
        self.label_7.setText(_t("OperatorForm", "Углерод (C):"))
        self.label_8.setText(_t("OperatorForm", "Кремний (Si):"))
        self.label_9.setText(_t("OperatorForm", "Сера (S):"))
        self.label_10.setText(_t("OperatorForm", "Фосфор (P):"))
        self.label_24.setText(_t("OperatorForm", "Марганец (Mn):"))
        self.groupBox_5.setTitle(_t("OperatorForm", "Металлошихта, т"))
        self.label_16.setText(_t("OperatorForm", "Масса:"))
        self.groupBox_3.setTitle(_t("OperatorForm", "Лом"))
        self.label_11.setText(_t("OperatorForm", "Масса [т]:"))
        self.groupBox_7.setTitle(_t("OperatorForm", "Химический состав, %масс"))
        self.label_12.setText(_t("OperatorForm", "Углерод (C):"))
        self.label_13.setText(_t("OperatorForm", "Кремний (Si):"))
        self.label_14.setText(_t("OperatorForm", "Сера (S):"))
        self.label_15.setText(_t("OperatorForm", "Фосфор (P):"))
        self.label_25.setText(_t("OperatorForm", "Марганец (Mn):"))
        self.groupBox_8.setTitle(_t("OperatorForm", "Химический состав шихты, %масс"))
        self.label_17.setText(_t("OperatorForm", "Углерод (C):"))
        self.label_18.setText(_t("OperatorForm", "Сера (S):"))
        self.label_19.setText(_t("OperatorForm", "Кремний (Si):"))
        self.label_20.setText(_t("OperatorForm", "Фосфор (P):"))
        self.label_21.setText(_t("OperatorForm", "Марганец (Mn):"))
        self.groupBox_9.setTitle(_t("OperatorForm", "Окисление элементов металлошихты (на 100кг металлошихты)"))
        #self.label_22.setText(_t("OperatorForm", "Масса:"))
        item = self.OxidationTable.verticalHeaderItem(0)
        item.setText(_t("OperatorForm", "Содержится в шихте"))
        item = self.OxidationTable.verticalHeaderItem(1)
        item.setText(_t("OperatorForm", "Остаётся после продувки"))
        item = self.OxidationTable.verticalHeaderItem(2)
        item.setText(_t("OperatorForm", "Удаляется после продувки"))
        item = self.OxidationTable.verticalHeaderItem(3)
        item.setText(_t("OperatorForm", "Требуется кислорода [кг]"))
        item = self.OxidationTable.verticalHeaderItem(4)
        item.setText(_t("OperatorForm", "Требуется кислорода [м^3]"))
        item = self.OxidationTable.verticalHeaderItem(5)
        item.setText(_t("OperatorForm", "Образуется оксидов"))
        item = self.OxidationTable.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "Всего C"))
        item = self.OxidationTable.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "Ок. C до CO"))
        item = self.OxidationTable.horizontalHeaderItem(2)
        item.setText(_t("OperatorForm", "Ок. C до CO2"))
        item = self.OxidationTable.horizontalHeaderItem(3)
        item.setText(_t("OperatorForm", "Si"))
        item = self.OxidationTable.horizontalHeaderItem(4)
        item.setText(_t("OperatorForm", "Mn"))
        item = self.OxidationTable.horizontalHeaderItem(5)
        item.setText(_t("OperatorForm", "P"))
        item = self.OxidationTable.horizontalHeaderItem(6)
        item.setText(_t("OperatorForm", "S"))
        item = self.OxidationTable.horizontalHeaderItem(7)
        item.setText(_t("OperatorForm", "Всего"))
        __sortingEnabled = self.OxidationTable.isSortingEnabled()
        self.OxidationTable.setSortingEnabled(False)
        self.OxidationTable.setSortingEnabled(__sortingEnabled)
        self.groupBox_11.setTitle(_t("OperatorForm", "Выбрать параметры из базы данных"))
        self.label_23.setText(_t("OperatorForm", "Марка стали:"))
        self.groupBox_13.setTitle(_t("OperatorForm", "Конвертер"))
        self.label_28.setText(_t("OperatorForm", "Высота, м:"))
        self.label_30.setText(_t("OperatorForm", "Диаметр, м:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _t("OperatorForm", "Металлошихта"))
        self.groupBox_10.setTitle(_t("OperatorForm", "Флюсы"))
        item = self.FluxeTable.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "Тип флюса"))
        item = self.FluxeTable.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "Масса [т]"))
        self.tip_flyusa_label.setText(_t("OperatorForm", "Тип флюса:"))
        self.shlak_group_box.setTitle(_t("OperatorForm", "Шлак"))
        self.him_sostav_shlaka_group_box.setTitle(_t("OperatorForm", "Химический состав, т"))
        self.SlagSiO2Label.setText(_t("OperatorForm", "SiO2:"))
        self.SlagCaOLabel.setText(_t("OperatorForm", "CaO:"))
        self.SlagMgOLabel.setText(_t("OperatorForm", "MgO:"))
        self.SlagAl2O3Label.setText(_t("OperatorForm", "Al2O3:"))
        self.SlagOthersLabel.setText(_t("OperatorForm", "Прочие:"))
        self.SlagFeOLabel.setText(_t("OperatorForm", "FeO:"))
        self.SlagFe2O3Label.setText(_t("OperatorForm", "Fe2O3:"))
        self.SlagWeightLabel.setText(_t("OperatorForm", "Масса [т]:"))
        self.him_sostav_shlaka_v_procentah_group_box.setTitle(_t("OperatorForm", "Химический состав, %"))
        self.SlagAl2O3Label_2.setText(_t("OperatorForm", "Al2O3:"))
        self.SlagFeOLabel_2.setText(_t("OperatorForm", "FeO:"))
        self.SlagFe2O3Label_2.setText(_t("OperatorForm", "Fe2O3:"))
        self.SlagSiO2Label_2.setText(_t("OperatorForm", "SiO2:"))
        self.SlagCaOLabel_2.setText(_t("OperatorForm", "CaO:"))
        self.SlagMgOLabel_2.setText(_t("OperatorForm", "MgO:"))
        self.SlagOthersLabel_2.setText(_t("OperatorForm", "Прочие:"))
        self.raschet_dutya_group_box.setTitle(_t("OperatorForm", "Параметры дутья"))
        self.TotalOxygenDemandBlastLabel.setText(_t("OperatorForm", "Общая потребность в кислороде дутья [кг]:"))
        self.TotalConsumptionOfBlastKgLabel.setText(_t("OperatorForm", "Общий расход дутья [кг]:"))
        self.ExcessBlastLabel.setText(_t("OperatorForm", "Избыток дутья [кг]:"))
        self.TotalConsumptionOfBlastM3Label.setText(_t("OperatorForm", "Общий расход дутья [м^3]:"))
        self.changeSetings.setText(_t("OperatorForm", "Изменить текущие настройки дутья"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _t("OperatorForm", "Шлак"))
        self.ReclaimedIronWeightLabel.setText(_t("OperatorForm", "Кол-во железа, восстановленного из неметаллических материалов [т]:"))
        item = self.IncomingData.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "Наименование"))
        item = self.IncomingData.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "кг"))
        item = self.OutputData.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "Наименование"))
        item = self.OutputData.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "кг"))
        self.vyhod_zhidkovo_metalla_pered_raskisleniem_label.setText(_t("OperatorForm", "Выход жидкого металла перед раскислением [т]:"))
        self.OutputDataGroupBox.setTitle(_t("OperatorForm", "Расходная часть"))
        self.MassOfOxidizedImpuritiesLabel.setText(_t("OperatorForm", "Масса окислившихся примесей [т]:"))
        self.MassOfOxidesPassingIntoSlagLabel.setText(_t("OperatorForm", "Масса оксидов железа, переходящих в шлак [т]:"))
        self.LossWithCarryOverLabel.setText(_t("OperatorForm", "Потери металла с выносами и выбросами [т]:"))
        self.DustLossLabel.setText(_t("OperatorForm", "Потери железа с пылью [т]:"))
        item = self.OutputDataTable.verticalHeaderItem(0)
        item.setText(_t("OperatorForm", "Окисление углерода"))
        item = self.OutputDataTable.verticalHeaderItem(1)
        item.setText(_t("OperatorForm", "Разложение CaCO3"))
        item = self.OutputDataTable.verticalHeaderItem(2)
        item.setText(_t("OperatorForm", "Дожигание части CO"))
        item = self.OutputDataTable.verticalHeaderItem(3)
        item.setText(_t("OperatorForm", "Разложение MgCO3"))
        item = self.OutputDataTable.verticalHeaderItem(4)
        item.setText(_t("OperatorForm", "Итого, кг"))
        item = self.OutputDataTable.verticalHeaderItem(5)
        item.setText(_t("OperatorForm", "Итого, м^3"))
        item = self.OutputDataTable.verticalHeaderItem(6)
        item.setText(_t("OperatorForm", "Состав газа, %"))
        item = self.OutputDataTable.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "CO"))
        item = self.OutputDataTable.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "CO2"))
        item = self.OutputDataTable.horizontalHeaderItem(2)
        item.setText(_t("OperatorForm", "Всего"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _t("OperatorForm", "Материальный баланс"))
        self.temperatura_zhidkovo_metalla_v_konce_produvki_label_2.setText(_t("OperatorForm", "Температура жидкого металла в конце продувки [°C]:"))
        self.rashodnie_statii_group_box_2.setTitle(_t("OperatorForm", "Расходные статьи"))
        self.phizicheskoe_teplo_zhidkovo_metalla_label_2.setText(_t("OperatorForm", "Физическое тепло жидкого металла [кДж]:"))
        self.HeatConsDecompos_label.setText(_t("OperatorForm", "Затраты тепла на разложение оксидов железа [кДж]:"))
        self.poteri_tepla_s_vynosami_i_vybrosami_label_2.setText(_t("OperatorForm", "Потери тепла с выносами и выбросами [кДж]:"))
        self.HeatDustForm_label.setText(_t("OperatorForm", "Затраты тепла на пылеобразование [кДж]:"))
        self.phizicheskoe_teplo_othodyashih_gazov_label_2.setText(_t("OperatorForm", "Физическое тепло отходящих газов [кДж]:"))
        self.phizicheskoe_teplo_shlaka_label_2.setText(_t("OperatorForm", "Физическое тепло шлака [кДж]:"))
        self.teplovie_poteri_label_2.setText(_t("OperatorForm", "Тепловые потери [кДж]:"))
        self.teplo_na_razlozhenie_karbonatov_label_2.setText(_t("OperatorForm", "Тепло на разложение карбонатов [кДж]:"))
        self.obshii_rashod_tepla_label_2.setText(_t("OperatorForm", "Общий расход тепла [кДж]:"))
        item = self.OutputHeatTable.verticalHeaderItem(0)
        item.setText(_t("OperatorForm", "Физ. тепло жидкого металла"))
        item = self.OutputHeatTable.verticalHeaderItem(1)
        item.setText(_t("OperatorForm", "Физ. тепло шлака"))
        item = self.OutputHeatTable.verticalHeaderItem(2)
        item.setText(_t("OperatorForm", "Затраты тепла на разл. оксидов железа"))
        item = self.OutputHeatTable.verticalHeaderItem(3)
        item.setText(_t("OperatorForm", "Физ. тепло отходящих газов"))
        item = self.OutputHeatTable.verticalHeaderItem(4)
        item.setText(_t("OperatorForm", "Потери тепла с выносами и выбросами"))
        item = self.OutputHeatTable.verticalHeaderItem(5)
        item.setText(_t("OperatorForm", "Затраты тепла на пылеобразование"))
        item = self.OutputHeatTable.verticalHeaderItem(6)
        item.setText(_t("OperatorForm", "Тепло на разложение карбонатов"))
        item = self.OutputHeatTable.verticalHeaderItem(7)
        item.setText(_t("OperatorForm", "Тепловые потери"))
        item = self.OutputHeatTable.verticalHeaderItem(8)
        item.setText(_t("OperatorForm", "Итого"))
        item = self.OutputHeatTable.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "Кол-во, кДж"))
        self.temperatura_peregreva_label_2.setText(_t("OperatorForm", "Температура перегрева [°C]:"))
        self.prihodnie_statii_group_box_2.setTitle(_t("OperatorForm", "Приходные статьи"))
        self.teplovoi_effect_reakcii_shlakoobrazovaniya_label_2.setText(_t("OperatorForm", "Тепловой эффект реакций шлакообразования [кДж]:"))
        self.teplovoi_effect_reakcii_okisleniya_label_2.setText(_t("OperatorForm", "Тепловой эффект реакции окисления [кДж]:"))
        self.himicheskoe_teplo_ot_obrazovaniya_oksidov_label_2.setText(_t("OperatorForm", "Химическое тепло от образования оксидов [кДж]:"))
        self.phizicheskoe_teplo_zhidkovo_chuguna_label_2.setText(_t("OperatorForm", "Физическое тепло жидкого чугуна [кДж]:"))
        self.teplo_ot_dozhiganiya_co_label_2.setText(_t("OperatorForm", "Тепло от дожигания CO [кДж]:"))
        self.obshii_prihod_tepla_label_2.setText(_t("OperatorForm", "Общий приход тепла [кДж]:"))
        item = self.IncomingHeatTable.verticalHeaderItem(0)
        item.setText(_t("OperatorForm", "Физ. тепло жидкого чугуна"))
        item = self.IncomingHeatTable.verticalHeaderItem(1)
        item.setText(_t("OperatorForm", "Тепл. эффект реакции оксиления"))
        item = self.IncomingHeatTable.verticalHeaderItem(2)
        item.setText(_t("OperatorForm", "Хим. тепло обр. оксидов железа шлака"))
        item = self.IncomingHeatTable.verticalHeaderItem(3)
        item.setText(_t("OperatorForm", "Тепл. эффект реакции шлакообразования"))
        item = self.IncomingHeatTable.verticalHeaderItem(4)
        item.setText(_t("OperatorForm", "Тепло от дожигания CO"))
        item = self.IncomingHeatTable.verticalHeaderItem(5)
        item.setText(_t("OperatorForm", "Итого"))
        item = self.IncomingHeatTable.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "Кол-во, кДж"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _t("OperatorForm", "Тепловой баланс"))
        self.tip_ferrosplava_label_2.setText(_t("OperatorForm", "Тип ферросллава:"))
        self.balans_pri_raskislenii_stali_label_2.setText(_t("OperatorForm", "Баланс элементов при раскислении стали"))
        self.label_51.setText(_t("OperatorForm", "Выход металла после раскисления [кг]:"))
        self.label_52.setText(_t("OperatorForm", "Расход ферросплава [кг]:"))
        item = self.ChemEmission.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "Тип"))
        item = self.ChemEmission.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "C, %"))
        item = self.ChemEmission.horizontalHeaderItem(2)
        item.setText(_t("OperatorForm", "Si, %"))
        item = self.ChemEmission.horizontalHeaderItem(3)
        item.setText(_t("OperatorForm", "Mn, %"))
        item = self.ChemEmission.horizontalHeaderItem(4)
        item.setText(_t("OperatorForm", "P, %"))
        item = self.ChemEmission.horizontalHeaderItem(5)
        item.setText(_t("OperatorForm", "S, %"))
        item = self.DeoxidationBalance.verticalHeaderItem(0)
        item.setText(_t("OperatorForm", "Содержится перед раскислением, %"))
        item = self.DeoxidationBalance.verticalHeaderItem(1)
        item.setText(_t("OperatorForm", "Содержится перед раскислением, кг"))
        item = self.DeoxidationBalance.verticalHeaderItem(2)
        item.setText(_t("OperatorForm", "Вносится первым ферросплавом, кг"))
        item = self.DeoxidationBalance.verticalHeaderItem(3)
        item.setText(_t("OperatorForm", "Содержится после раскисления, кг"))
        item = self.DeoxidationBalance.verticalHeaderItem(4)
        item.setText(_t("OperatorForm", "Образуется оксида, кг"))
        item = self.DeoxidationBalance.verticalHeaderItem(5)
        item.setText(_t("OperatorForm", "Состав стали после раскисления, %"))
        item = self.DeoxidationBalance.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "Ост. C"))
        item = self.DeoxidationBalance.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "C до CO"))
        item = self.DeoxidationBalance.horizontalHeaderItem(2)
        item.setText(_t("OperatorForm", "Ост. Si"))
        item = self.DeoxidationBalance.horizontalHeaderItem(3)
        item.setText(_t("OperatorForm", "Si до SiO2"))
        item = self.DeoxidationBalance.horizontalHeaderItem(4)
        item.setText(_t("OperatorForm", "Ост. Mn"))
        item = self.DeoxidationBalance.horizontalHeaderItem(5)
        item.setText(_t("OperatorForm", "Mn до MnO"))
        item = self.DeoxidationBalance.horizontalHeaderItem(6)
        item.setText(_t("OperatorForm", "P"))
        item = self.DeoxidationBalance.horizontalHeaderItem(7)
        item.setText(_t("OperatorForm", "S"))
        item = self.DeoxidationBalance.horizontalHeaderItem(8)
        item.setText(_t("OperatorForm", "Fe"))
        item = self.DeoxidationBalance.horizontalHeaderItem(9)
        item.setText(_t("OperatorForm", "Всего"))
        self.groupBox_12.setTitle(_t("OperatorForm", "Результат плавки"))
        item = self.SteelChemResult.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "C"))
        item = self.SteelChemResult.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "Si"))
        item = self.SteelChemResult.horizontalHeaderItem(2)
        item.setText(_t("OperatorForm", "Mn"))
        item = self.SteelChemResult.horizontalHeaderItem(3)
        item.setText(_t("OperatorForm", "S"))
        item = self.SteelChemResult.horizontalHeaderItem(4)
        item.setText(_t("OperatorForm", "P"))
        self.himicheskii_sostav_poluchennoi_stali_label_2.setText(_t("OperatorForm", "Химический состав полученной стали:"))
        self.label_43.setText(_t("OperatorForm", "Выбросы CO2 [кг]:"))
        self.label_44.setText(_t("OperatorForm", "Масса стали [кг]:"))
        self.label_45.setText(_t("OperatorForm", "Масса шлака [т]:"))
        self.label_46.setText(_t("OperatorForm", "Потеря массы футеровки [кг]:"))
        self.label_47.setText(_t("OperatorForm", "Температура выхода стали [°C]:"))
        item = self.SlagChemResult.horizontalHeaderItem(0)
        item.setText(_t("OperatorForm", "SiO2"))
        item = self.SlagChemResult.horizontalHeaderItem(1)
        item.setText(_t("OperatorForm", "Al2O3"))
        item = self.SlagChemResult.horizontalHeaderItem(2)
        item.setText(_t("OperatorForm", "CaO"))
        item = self.SlagChemResult.horizontalHeaderItem(3)
        item.setText(_t("OperatorForm", "FeO"))
        item = self.SlagChemResult.horizontalHeaderItem(4)
        item.setText(_t("OperatorForm", "MgO"))
        self.himicheskii_sostav_poluchennoi_stali_label_3.setText(_t("OperatorForm", "Химический состав шлака:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _t("OperatorForm", "Раскисление стали"))
        self.label_48.setText(_t("OperatorForm", "Предельная растворимость MgO:"))
        self.label_49.setText(_t("OperatorForm", "Содержание MgO в шлаке [%]:"))
        self.label_50.setText(_t("OperatorForm", "Ненасыщенность шлака по MgO:"))
        self.label_53.setText(_t("OperatorForm", "Температура выхода стали [°C]:"))
        self.label_54.setText(_t("OperatorForm", "Основность шлака:"))
        self.label_55.setText(_t("OperatorForm", "Потеря массы футеровки:"))
        self.label_56.setText(_t("OperatorForm", "Рекомендация:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), _t("OperatorForm", "Рекомендации"))
        self.Menu.setTitle(_t("OperatorForm", "Файл"))
        self.ViewMenu.setTitle(_t("OperatorForm", "Вид"))
        self.Help.setTitle(_t("OperatorForm", "Справка"))
        self.Administrate.setTitle(_t("OperatorForm", "Администрирование"))
        self.about.setText(_t("OperatorForm", "О программе"))
        self.SaveFile.setText(_t("OperatorForm", "Сохранить результат"))
        self.Exit.setText(_t("OperatorForm", "Выйти"))
        self.addUser.setText(_t("OperatorForm", "Добавить пользователя"))
        self.AddUser.setText(_t("OperatorForm", "Добавить пользователя"))
        self.AddDbData.setText(_t("OperatorForm", "Добавить данные в бд"))
        # ── Tab text for bottom detail tabs ──────────────────────────────
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), _t("OperatorForm", "Схема"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab),   _t("OperatorForm", "Окисление"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _t("OperatorForm", "Шлак"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _t("OperatorForm", "Мат. баланс"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _t("OperatorForm", "Тепл. баланс"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _t("OperatorForm", "Раскисление"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), _t("OperatorForm", "Рекомендации"))

        # ── Startup ───────────────────────────────────────────────────────
        self.getSettings()
        self.getFluxes()
        self.getModes()
        self.AddNewMode.setEnabled(1)
        self.tab_4.setEnabled(1)
        self.tab_5.setEnabled(1)
        self._start_indicator_timer()



if __name__ == "__main__":
    import sys
    from theme_settings import get_theme

    app = QtWidgets.QApplication(sys.argv)
    app_theme.apply_to_application(app, get_theme())
    OperatorForm = QtWidgets.QMainWindow()
    ui = Ui_OperatorForm()
    ui.setupUi(OperatorForm)
    OperatorForm.show()
    sys.exit(app.exec_())

