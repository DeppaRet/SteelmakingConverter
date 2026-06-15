import logging
import math
import os
from typing import Any

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
from control_inputs import (
    ControlInputsPanel,
    KEY_COMPUTED,
    KEY_FLOW,
    KEY_LANCE,
    KEY_LOCKS,
    KEY_O2_LOSSES,
    KEY_P_O2_MANUAL,
    KEY_TARGET_C,
    KEY_TIME,
    SIGNAL_BLOW_INTENSITY,
    SIGNAL_BLOW_TIME,
    SIGNAL_LANCE,
    SIGNAL_O2_LOSSES,
    SIGNAL_TARGET_C,
    TRIPLET_KEYS,
)
from dynamics_charts import DynamicsChartsWidget
from dynamics_indicators import DynamicsIndicatorsPanel
from melt_dynamics import CALIB_DEFAULTS, MeltDynamicsEngine
from theme_settings import manager, get_theme
from theme_toggle import ThemeToggle
from view_toggles import ViewTogglesBar
from locale_settings import manager as locale_manager, get_language
from i18n import msg_critical, msg_warning, tr

logger = logging.getLogger(__name__)


class DynamicsSimulationWorker(QThread):
    """Фоновый прогон MeltDynamicsEngine до целевого [C]."""

    finished_ok = pyqtSignal(list, dict)
    failed = pyqtSignal(str)

    def __init__(
        self,
        initial_state: dict,
        control_params: dict,
        c_target: float,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._initial = initial_state
        self._control = control_params
        self._c_target = c_target

    def run(self) -> None:
        try:
            engine = MeltDynamicsEngine(
                initial_state=self._initial,
                control_params=self._control,
            )
            snapshots = engine.run_until_target(self._c_target)
            last = snapshots[-1] if snapshots else {}
            self.finished_ok.emit(snapshots, last)
        except Exception as exc:
            self.failed.emit(str(exc))


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


class Reaction:
    """Строка матрицы стехиометрических коэффициентов."""

    def __init__(self, row):
        # порядок колонок соответствует SELECT в load_reactions_for_scrap_type
        (self.id, self.number, self.element, self.name, self.equation,
         self.nu_element, self.M_element, self.nu_O2, self.M_O2,
         self.nu_product, self.M_product, self.product,
         self.heat_kJ_kg, self.produces_gas, self.needs_O2,
         self.affects_material, self.affects_slag,
         self.affects_blast, self.affects_heat,
         self.is_active, co_frac) = row
        self.produces_gas = bool(self.produces_gas)
        self.needs_O2 = bool(self.needs_O2)
        self.affects_material = bool(self.affects_material)
        self.affects_slag = bool(self.affects_slag)
        self.affects_blast = bool(self.affects_blast)
        self.affects_heat = bool(self.affects_heat)
        self.co_fraction = float(co_frac) if co_frac is not None else 0.9

    def oxygen_per_kg_element(self):
        """Формула (3) методички: расход O2 (кг) на 1 кг элемента."""
        if not self.needs_O2 or self.nu_O2 == 0:
            return 0.0
        return (self.nu_O2 * self.M_O2) / (self.nu_element * self.M_element)

    def oxygen_m3_per_kg_element(self):
        """Формула (4) методички: объём O2 (м3) на 1 кг элемента."""
        return self.oxygen_per_kg_element() * 22.4 / 32.0

    def product_per_kg_element(self):
        """Формула (14) методички: масса оксида (кг) на 1 кг элемента."""
        return (self.nu_product * self.M_product) / (self.nu_element * self.M_element)


def load_reactions_for_scrap_type(scrap_type_id, db_host, db_login, db_pass):
    """Возвращает list[Reaction] — активные реакции для данного типа лома."""
    DB = mc.connect(host=db_host, user=db_login, password=db_pass, database="regimdata")
    cur = DB.cursor()
    cur.execute("""
        SELECT r.idReaction, r.ReactionNumber, r.ElementSymbol, r.ElementName,
               r.ReactionEquation, r.nu_Element, r.M_Element, r.nu_O2, r.M_O2,
               r.nu_Product, r.M_Product, r.ProductFormula, r.HeatEffect_kJ_kg,
               r.ProducesGas, r.NeedsO2,
               r.AffectsMaterialBalance, r.AffectsSlag, r.AffectsBlast, r.AffectsHeatBalance,
               str.IsActive, str.CO_Fraction
        FROM reaction r
        JOIN scraptype_reaction str ON r.idReaction = str.Reaction_idReaction
        WHERE str.ScrapType_idScrapType = %s AND str.IsActive = 1
        ORDER BY r.ReactionNumber
    """, (scrap_type_id,))
    rows = cur.fetchall()
    cur.close()
    DB.close()
    return [Reaction(row) for row in rows]

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

    def _show_critical(self, info, title="Ошибка", text="Внимание"):
        msg_critical(getattr(self, '_oper_form', None), title, text, info)

    def _show_warning(self, info, title="Внимание", text="Внимание"):
        msg_warning(getattr(self, '_oper_form', None), title, text, info)

    _STATIC_TABLE_LABELS = frozenset({
        "Чугун жидкий", "Лом", "Дутьё", "Итого",
        "Металл жидкий", "Шлак", "Газ", "Избыток дутья",
        "Выносы и выбросы", "Потери с пылью",
    })

    def _tl(self, text: str) -> str:
        return tr("OperatorForm", text)

    def _set_recommendation_lines(self, *lines_ru: str) -> None:
        self._recommendation_lines_ru = list(lines_ru)
        text = "\n".join(tr("OperatorForm", line) for line in lines_ru)
        if text:
            text += "\n"
        self.recomendation.setPlainText(text)

    def _append_recommendation_line(self, line_ru: str) -> None:
        lines = getattr(self, "_recommendation_lines_ru", [])
        if line_ru not in lines:
            lines.append(line_ru)
        self._recommendation_lines_ru = lines
        current = self.recomendation.toPlainText().rstrip("\n")
        addition = tr("OperatorForm", line_ru)
        self.recomendation.setPlainText(
            (current + "\n" + addition).strip() + "\n" if current else addition + "\n"
        )

    def _refresh_recommendation_text(self) -> None:
        lines = getattr(self, "_recommendation_lines_ru", None)
        if not lines:
            return
        text = "\n".join(tr("OperatorForm", line) for line in lines)
        if text:
            text += "\n"
        self.recomendation.setPlainText(text)

    def _refresh_static_table_labels(self) -> None:
        from i18n import canonical_label

        for tbl in (
            getattr(self, "IncomingData", None),
            getattr(self, "OutputData", None),
        ):
            if tbl is None:
                continue
            for row in range(tbl.rowCount()):
                item = tbl.item(row, 0)
                if item is None:
                    continue
                key = canonical_label(item.text())
                if key in self._STATIC_TABLE_LABELS:
                    item.setText(tr("OperatorForm", key))

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
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")

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
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")

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
            msg_critical(
                getattr(self, '_oper_form', None),
                "Ошибка", "Внимание", "Проверьте введенные данные! {0}".format(err),
            )

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
        msg_critical(
            getattr(self, '_oper_form', None),
            "Ошибка", "Внимание", f"Проверьте введенные данные! {error}",
        )

    def run_calculations(self, *, reload_mode_from_db: bool = True) -> None:
        """Полный пересчёт этапов. reload_mode_from_db=False — не трогать поля режима (кнопка панели)."""
        if reload_mode_from_db:
            self.chooseMods()
        self._run_calculation_stages()

    def _run_calculation_stages(self):
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

            # Тип лома для текущего режима
            mycursor.execute(
                "SELECT ScrapType_idScrapType FROM scrapdata WHERE idScrapData = %s;",
                (scrapId,)
            )
            scrapTypeRow = mycursor.fetchone()
            self.current_scrap_type_id = scrapTypeRow[0] if scrapTypeRow and scrapTypeRow[0] else 1

            # Новые элементы лома (индексы 6..9 после ALTER TABLE scrapcomposition)
            self.scrapCr = float(scrapData[0][6]) if len(scrapData[0]) > 6 and scrapData[0][6] else 0.0
            self.scrapV  = float(scrapData[0][7]) if len(scrapData[0]) > 7 and scrapData[0][7] else 0.0
            self.scrapAl = float(scrapData[0][8]) if len(scrapData[0]) > 8 and scrapData[0][8] else 0.0
            self.scrapTi = float(scrapData[0][9]) if len(scrapData[0]) > 9 and scrapData[0][9] else 0.0
            self._sync_scrap_type_ui()

            query = "select ScrapWeight from scrapdata where idScrapData = " + str(scrapId) +";"
            mycursor.execute(query)
            scrapWeight = mycursor.fetchall()
            self.scrapWeight.setText(str(scrapWeight[0][0]))
            self._scenario_scrap_weight_t = float(scrapWeight[0][0])
            self._scenario_target_carbon = float(steelComposition[0][1])
            mycursor.close()
            DB.close()
            self.getFluxeInMode(modeId)

            self._balance_tau_min = None
            self._balance_v_m3 = None
            self._balance_blast_i_display = None
            self._recalc_scrap_from_target_c = False
            if hasattr(self, "control_panel"):
                try:
                    limit_c = float(self.SteelCarbonLimit.text())
                    self.control_panel.set_target_carbon_range(limit_c)
                except (ValueError, AttributeError):
                    pass
                c_val = self._field_float(self.steelCarbon)
                self.control_panel.set_target_carbon_value(c_val)
                self.user_target_C = c_val

        except Exception as err:
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")

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
            scrapManganeseValue = float(self.scrapManganese.text())

            # Массы чугуна и лома — тонны [т] (поля «Масса [т]», ScrapWeight/CastSteelWeight в БД).
            scrapWeightValue = float(self.scrapWeight.text())
            # Пересчёт лома [т] — только если оператор изменил целевой [C] на панели.
            if getattr(self, "_recalc_scrap_from_target_c", False):
                # === CONTROL INPUTS: разд. 3 методики Шаповалова (чувствительность к [C]_М) ===
                scrapWeightValue = self._recalc_scrap_weight_for_target_carbon()
                self.scrapWeight.setText(str(round(scrapWeightValue, 3)))
                self._recalc_scrap_from_target_c = False

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
                self._last_3d_process_state = "charged"
                self.converter3d.update_state({
                    'state':      'charged',
                    'metalMass':  round(totalWeightValue, 1),
                    'metalLevel': min(1.0, totalWeightValue / 430.0) * 0.62,
                    'slagMass':   0,
                    'slagLevel':  0,
                })
            self._update_control_scenario_context()

        except Exception as err:  # mc.Error
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")
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

            steelCarbonValue = self._get_target_carbon()
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

            # --- НОВЫЙ БЛОК: расчёт через матрицу стехиометрических коэффициентов ---
            self._read_scrap_extra_inputs()
            scrap_type_id = getattr(self, 'current_scrap_type_id', 1)
            reactions = load_reactions_for_scrap_type(scrap_type_id, DBhost, DBlogin, DBpass)

            charge_elements = {
                'C_CO2':   chemCarbonValue,   'C_CO':    chemCarbonValue,
                'Si':      chemSiliconValue,  'Mn':      chemManganesevalue,
                'P':       chemPhosphorValue, 'P_alt':   chemPhosphorValue,
                'FeS_CaO': chemSerumValue,    'S_SO2':   chemSerumValue,
                'Cr': getattr(self, 'scrapCr', 0.0),
                'V':  getattr(self, 'scrapV',  0.0),
                'Al': getattr(self, 'scrapAl', 0.0),
                'Ti': getattr(self, 'scrapTi', 0.0),
            }
            after_elements = {
                'C_CO2': 0.0, 'C_CO': steelCarbonValue,
                'Si': 0.0, 'Mn': manganeseAfter, 'P': phosphorAfter, 'P_alt': phosphorAfter,
                'FeS_CaO': serumAfter, 'S_SO2': serumAfter,
                'Cr': 0.0, 'V': 0.0, 'Al': 0.0, 'Ti': 0.0,
            }

            self.reaction_results = {}
            total_O2_kg = total_O2_m3 = 0.0

            for reaction in reactions:
                el = reaction.element
                if el not in charge_elements:
                    continue
                if el == 'C_CO':
                    g_removed = max(0.0, (charge_elements['C_CO'] - steelCarbonValue) * reaction.co_fraction)
                elif el == 'C_CO2':
                    g_removed = max(0.0, (charge_elements['C_CO2'] - steelCarbonValue) * (1.0 - reaction.co_fraction))
                else:
                    g_removed = max(0.0, charge_elements[el] - after_elements.get(el, 0.0))

                self.reaction_results[el] = {
                    'removed':          g_removed,
                    'O2_kg':            g_removed * reaction.oxygen_per_kg_element()    if reaction.affects_blast else 0.0,
                    'O2_m3':            g_removed * reaction.oxygen_m3_per_kg_element() if reaction.affects_blast else 0.0,
                    'oxide_kg':         g_removed * reaction.product_per_kg_element()   if reaction.affects_slag  else 0.0,
                    'product':          reaction.product,
                    'is_gas':           reaction.produces_gas,
                    'heat':             g_removed * reaction.heat_kJ_kg                 if reaction.affects_heat  else 0.0,
                    'affects_material': reaction.affects_material,
                    'affects_slag':     reaction.affects_slag,
                    'affects_blast':    reaction.affects_blast,
                }
                if reaction.affects_blast:
                    total_O2_kg += self.reaction_results[el]['O2_kg']
                    total_O2_m3 += self.reaction_results[el]['O2_m3']

            self.total_O2_kg = total_O2_kg
            self.total_O2_m3 = total_O2_m3

            # Переменные-псевдонимы для совместимости с OxidationTable (строки 0..5)
            carbonToCO        = self.reaction_results.get('C_CO',  {}).get('removed',  carbonRemove * 0.9)
            carbonToCO2       = self.reaction_results.get('C_CO2', {}).get('removed',  carbonRemove * 0.1)
            carbonToCOOxygen  = self.reaction_results.get('C_CO',  {}).get('O2_kg',    0.0)
            carbonToCO2Oxygen = self.reaction_results.get('C_CO2', {}).get('O2_kg',    0.0)
            siliconOxygen     = self.reaction_results.get('Si',    {}).get('O2_kg',    0.0)
            manganesOxygen    = self.reaction_results.get('Mn',    {}).get('O2_kg',    0.0)
            phosphorOxygen    = self.reaction_results.get('P',     {}).get('O2_kg',
                                self.reaction_results.get('P_alt', {}).get('O2_kg',    0.0))
            summOxygen        = total_O2_kg
            # --- КОНЕЦ НОВОГО БЛОКА ---

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

            self.update_oxidation_table_rows()
            global tableCalcked
            tableCalcked = True
        except Exception as err:  # mc.Error
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")
        return

    def update_oxidation_table_rows(self):
        """Добавляет строки для Cr/V/Al/Ti/S(газ), если они ненулевые."""
        EXTRA = {
            'Cr': 'Хром', 'V': 'Ванадий', 'Al': 'Алюминий',
            'Ti': 'Титан', 'S_SO2': 'Сера->SO2',
        }
        # Убираем ранее добавленные строки сверх базовых 6 (C/Si/Mn/P/S не трогаем)
        self.OxidationTable.setRowCount(6)
        if not hasattr(self, 'reaction_results'):
            return
        for el, label in EXTRA.items():
            res = self.reaction_results.get(el)
            if not res or res['removed'] <= 0:
                continue
            row = self.OxidationTable.rowCount()
            self.OxidationTable.insertRow(row)
            # Название элемента — в заголовок строки, не в ячейку данных
            self.OxidationTable.setVerticalHeaderItem(row, QTableWidgetItem(label))
            # col 0 (Всего): содержалось/удалено из шихты, %
            self.OxidationTable.setItem(row, 0, QTableWidgetItem(str(round(res['removed'],  4))))
            self.OxidationTable.setItem(row, 1, QTableWidgetItem("-"))
            self.OxidationTable.setItem(row, 2, QTableWidgetItem("-"))
            # col 3: O2 кг, col 4: O2 м³, col 5: оксид кг (переиспользуем колонки Si/Mn/P)
            self.OxidationTable.setItem(row, 3, QTableWidgetItem(str(round(res['O2_kg'],    4))))
            self.OxidationTable.setItem(row, 4, QTableWidgetItem(str(round(res['O2_m3'],    4))))
            self.OxidationTable.setItem(row, 5, QTableWidgetItem(str(round(res['oxide_kg'], 4))))
            self.OxidationTable.setItem(row, 6, QTableWidgetItem("-"))
            self.OxidationTable.setItem(row, 7, QTableWidgetItem(str(round(res['oxide_kg'], 4))))

    def loadScrapTypeCombo(self):
        """Заполняет combo типов лома из таблицы scraptype."""
        try:
            DB = mc.connect(host=DBhost, user=DBlogin, password=DBpass, database="regimdata")
            cur = DB.cursor()
            cur.execute("SELECT idScrapType, ScrapTypeName FROM scraptype ORDER BY idScrapType;")
            rows = cur.fetchall()
            cur.close(); DB.close()
            if not hasattr(self, 'scrapTypeCombo'):
                return
            self.scrapTypeCombo.blockSignals(True)
            self.scrapTypeCombo.clear()
            for row in rows:
                self.scrapTypeCombo.addItem(row[1], userData=row[0])
            self.scrapTypeCombo.blockSignals(False)
        except Exception as err:
            logger.warning("loadScrapTypeCombo failed: %s", err)

    def _sync_scrap_type_ui(self):
        """Синхронизирует combo и поля Cr/V/Al/Ti с загруженными значениями."""
        if hasattr(self, 'scrapTypeCombo'):
            idx = self.scrapTypeCombo.findData(getattr(self, 'current_scrap_type_id', 1))
            if idx >= 0:
                self.scrapTypeCombo.blockSignals(True)
                self.scrapTypeCombo.setCurrentIndex(idx)
                self.scrapTypeCombo.blockSignals(False)
        if hasattr(self, 'scrapCrInput'):
            self.scrapCrInput.setText(str(getattr(self, 'scrapCr', 0.0)))
            self.scrapVInput.setText(str(getattr(self, 'scrapV', 0.0)))
            self.scrapAlInput.setText(str(getattr(self, 'scrapAl', 0.0)))
            self.scrapTiInput.setText(str(getattr(self, 'scrapTi', 0.0)))

    def onScrapTypeChanged(self, _index=-1):
        """Пользователь выбрал тип лома в combo на главной форме."""
        if not hasattr(self, 'scrapTypeCombo'):
            return
        data = self.scrapTypeCombo.currentData()
        if data is not None:
            self.current_scrap_type_id = data

    def _read_scrap_extra_inputs(self):
        """Читает Cr/V/Al/Ti из полей ввода в self.scrapCr/V/Al/Ti."""
        def _val(widget):
            try:
                return float(widget.text())
            except (ValueError, AttributeError):
                return 0.0
        if hasattr(self, 'scrapCrInput'):
            self.scrapCr = _val(self.scrapCrInput)
            self.scrapV = _val(self.scrapVInput)
            self.scrapAl = _val(self.scrapAlInput)
            self.scrapTi = _val(self.scrapTiInput)

    def openScrapTypeDialog(self):
        """Открывает диалог матрицы реакций (только просмотр для оператора)."""
        from ScrapTypeDialog import ScrapTypeDialog
        dialog = ScrapTypeDialog(DBhost, DBlogin, DBpass, editable=False, parent=self.centralwidget)
        dialog.exec_()
        self.loadScrapTypeCombo()
        self._sync_scrap_type_ui()

    def openStoichiometryMatrixDialog(self):
        """Открывает диалог просмотра полной матрицы стехиометрических коэффициентов."""
        from StoichiometryMatrixDialog import StoichiometryMatrixDialog
        dlg = StoichiometryMatrixDialog(DBhost, DBlogin, DBpass, parent=self.centralwidget)
        dlg.exec_()

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
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")
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
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")

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
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")
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

            steelCarbon = self._get_target_carbon()
            FeO = 20.0 + 0.218 / steelCarbon + 0.031 / float(self.steelPhosphor.text())
            Fe2O3 = 0
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

            # Оксиды новых элементов (Cr2O3, V2O5, TiO2, Al2O3 и пр.) из матрицы реакций
            if hasattr(self, 'reaction_results'):
                ALREADY_COUNTED = {'C_CO', 'C_CO2', 'CO_burn', 'Si', 'Mn', 'P', 'P_alt', 'FeS_CaO', 'S_SO2'}
                for el, res in self.reaction_results.items():
                    if el in ALREADY_COUNTED:
                        continue
                    if res['affects_slag'] and not res['is_gas'] and res['oxide_kg'] > 0:
                        oxide_total = res['oxide_kg'] * metalChargeWeight / 100.0
                        if res['product'] == 'Al2O3':
                            slagAl2O3 += oxide_total
                        else:
                            slagOthers += oxide_total

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
                self._last_3d_process_state = "blowing"
                self.converter3d.update_state({
                    'state':     'blowing',
                    'slagMass':  round(slagWeight, 1),
                    'slagLevel': min(1.0, slagWeight / 80.0),
                    'metalMass': round(metal_mass, 1),
                    'metalLevel': min(1.0, metal_mass / 430.0) * 0.62,
                    'temperature': 1500,
                })
        except Exception as err:
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")

    # === CONTROL INPUTS START ===
    # Панель управления и симуляция — вкладка «Симуляция»; в центре — только этапы расчёта.

    def _init_control_user_state(self) -> None:
        self._user_controls: dict[str, Any] = {}
        self.user_target_C: float | None = None
        self.user_o2_losses: float | None = None
        self.user_eta_co: float | None = None
        self.user_z_co: float | None = None
        self.userBlowFlow: float | None = None
        self.userBlowTime: float | None = None
        self.userLanceHeight: float | None = None
        self._recalc_scrap_from_target_c: bool = False
        self._scenario_scrap_weight_t: float | None = None
        self._scenario_target_carbon: float | None = None
        self._control_scenario_mass_t: float = 200.0
        self._last_3d_process_state: str = "idle"
        self._sim_worker: DynamicsSimulationWorker | None = None
        self._sim_engine: MeltDynamicsEngine | None = None
        self._sim_playback_idx = 0
        self._sim_snapshots: list[dict] = []
        self._balance_tau_min: float | None = None
        self._balance_v_m3: float | None = None
        self._balance_blast_i_display: float | None = None

    def _si_pig_iron_pct(self) -> float:
        try:
            return self._field_float(self.castCarbon, 0.5)
        except AttributeError:
            return 0.5

    def _resolve_balance_free_params(self) -> dict[str, float]:
        """η_CO, Z, P_O2 для 8 этапов баланса — без крутилок симуляции."""
        mass = self._metal_charge_mass_t()
        h_c = self._recommended_lance_ranges(mass)["optimal"]
        i_ud_ref = CALIB_DEFAULTS.get("i_ud_ref", 4.0)
        i_total = max(400.0, i_ud_ref * mass)
        si_pig = self._si_pig_iron_pct()
        preview = MeltDynamicsEngine.preview_free_params(
            h_c, i_total, mass, si_pig
        )
        return {
            "eta_co": preview["eta_co"],
            "z_co": preview["z_co"],
            "p_o2": preview["p_o2"],
            "k_p": preview["k_p"],
            "g_v": preview["g_v"],
            "i_ud": preview["i_ud"],
            "efficiency": preview["efficiency"],
            "h_c": h_c,
            "i_total": i_total,
        }

    def _resolve_sim_free_params(self) -> dict[str, float]:
        """η_CO, Z, P_O2 для вкладки «Симуляция» — с учётом крутилок оператора."""
        h_c = 1.15
        i_total = 600.0
        if hasattr(self, "control_panel"):
            h_c = self.control_panel.lance_height_value()
            i_total = self.control_panel.intensity_value()
        g_st = self._metal_charge_mass_t()
        si_pig = self._si_pig_iron_pct()
        preview = MeltDynamicsEngine.preview_free_params(
            h_c, i_total, g_st, si_pig
        )
        if hasattr(self, "control_panel") and self.control_panel.p_o2_manual_mode():
            p_o2 = self.control_panel.p_o2_manual_value()
        else:
            p_o2 = preview["p_o2"]
        return {
            "eta_co": preview["eta_co"],
            "z_co": preview["z_co"],
            "p_o2": p_o2,
            "k_p": preview["k_p"],
            "g_v": preview["g_v"],
            "i_ud": preview["i_ud"],
            "efficiency": preview["efficiency"],
            "h_c": h_c,
            "i_total": i_total,
        }

    def _charge_temperature_for_dynamics(self) -> float:
        """T заливки чугуна для динамики (не LiquidSteelTemp — финал теплобаланса)."""
        t = self._field_float(self.castTemperature, 1400.0)
        if t > 1550.0:
            t = 1400.0
        return max(1250.0, min(1500.0, t))

    def _build_melt_initial_state(self) -> dict[str, float]:
        """Начальное состояние для пошаговой симуляции."""
        g_metal = self._metal_charge_mass_t()
        return {
            "G_metal_t": g_metal,
            "C": self._field_float(self.ChemCarbon, 4.0),
            "Si": self._field_float(self.ChemSilicon, 0.5),
            "Mn": self._field_float(self.ChemManganese, 0.3),
            "T": self._charge_temperature_for_dynamics(),
            "FeO_slag": 12.0,
            "Si_pig": self._si_pig_iron_pct(),
            "V_O2_total": 0.0,
        }

    def _blast_rates_from_balance_volume(self, v_m3: float) -> tuple[float, float]:
        """i и τ из балансного V (Ф-2); τ≈V/17 мин — без крутилок симуляции."""
        v_m3 = max(float(v_m3), 1.0)
        tau = max(12.0, min(25.0, v_m3 / 17.0))
        return v_m3 / tau, tau

    def _balance_blow_intensity(self) -> float | None:
        """i_баланс = V/τ после «Расчёт дутья» (эталон для масштаба v_C)."""
        tau = self._balance_blow_tau_min()
        v_m3 = getattr(self, "_balance_v_m3", None)
        if tau and tau > 1.0 and v_m3 and float(v_m3) > 1.0:
            return float(v_m3) / float(tau)
        return None

    def _balance_blow_tau_min(self) -> float | None:
        """τ продувки из баланса: Ф-2 τ=V/i после «Расчёт дутья» (None = ещё не считали)."""
        global blastCalcked
        if not blastCalcked:
            return None
        if getattr(self, "_balance_tau_min", None) is not None:
            if self._balance_tau_min >= 1.0:
                return self._balance_tau_min
        if hasattr(self, "TotalConsumptionOfBlastM3"):
            try:
                v_m3 = float(self.TotalConsumptionOfBlastM3.text())
                if v_m3 > 1.0:
                    _i, tau = self._blast_rates_from_balance_volume(v_m3)
                    if tau >= 1.0:
                        return tau
            except (ValueError, TypeError):
                pass
        return None

    def _is_simulation_tab_active(self) -> bool:
        return (
            hasattr(self, "tab_simulation")
            and self.tabWidget.currentWidget() is self.tab_simulation
        )

    def _on_tab_widget_changed(self, _index: int) -> None:
        if self._is_simulation_tab_active():
            self._ensure_sim_engine()

    def _dynamic_T_end_target(self) -> float:
        """Целевая T конца продувки: из теплобаланса или T чугуна + ~265 °C."""
        t0 = self._charge_temperature_for_dynamics()
        global heatBalanceCalcked
        if heatBalanceCalcked and hasattr(self, "LiquidSteelTemp"):
            try:
                t_bal = float(self.LiquidSteelTemp.text())
                if t_bal > t0 + 30.0:
                    return min(1720.0, t_bal)
            except (ValueError, TypeError):
                pass
        return min(1720.0, t0 + 265.0)

    def _build_melt_control_params(self) -> dict[str, float]:
        h_c = self.userLanceHeight or 1.15
        i_total = self.userBlowFlow or 600.0
        target_c = self._get_sim_target_carbon()
        if hasattr(self, "control_panel"):
            h_c = self.control_panel.lance_height_value()
            i_total = self.control_panel.intensity_value()
            target_c = self.control_panel.target_carbon_value()
        cp: dict[str, float] = {
            "h_c": h_c,
            "i_total": i_total,
            "target_c": target_c,
            "T_end_target": self._dynamic_T_end_target(),
            "tau_target_min": self._balance_blow_tau_min() or 17.0,
        }
        i_bal = self._balance_blow_intensity()
        if i_bal is not None and i_bal > 1.0:
            cp["i_balance_ref"] = i_bal
        return cp

    def _update_dynamic_auto_fields(self) -> None:
        if not hasattr(self, "_auto_eta_co"):
            return
        free = self._resolve_sim_free_params()
        self.user_eta_co = free["eta_co"]
        self.user_z_co = free["z_co"]
        if not (
            hasattr(self, "control_panel") and self.control_panel.p_o2_manual_mode()
        ):
            self.user_o2_losses = free["p_o2"]
        self._auto_eta_co.setText(f"{free['eta_co']:.1f}")
        self._auto_z_co.setText(f"{free['z_co']:.3f}")
        manual_po2 = (
            hasattr(self, "control_panel") and self.control_panel.p_o2_manual_mode()
        )
        if manual_po2:
            self._auto_p_o2.setProperty("class", "control_auto_strikethrough")
        else:
            self._auto_p_o2.setProperty("class", "control_blow_volume_readonly")
        self._auto_p_o2.setText(f"{free['p_o2']:.1f}")
        self._auto_p_o2.style().unpolish(self._auto_p_o2)
        self._auto_p_o2.style().polish(self._auto_p_o2)
        self._auto_k_p.setText(f"{free['k_p']:.0f}")
        self._auto_g_v.setText(f"{free['g_v']:.2f}")
        if hasattr(self, "control_panel"):
            self.control_panel.refresh_derived_display(
                self._metal_charge_mass_t(), self._si_pig_iron_pct()
            )
        if hasattr(self, "dynamics_indicators"):
            self.dynamics_indicators.set_target_carbon(self._get_sim_target_carbon())
            snap = {
                "eta_CO": free["eta_co"],
                "Z": free["z_co"],
                "h_c": free["h_c"],
                "C": self._field_float(self.ChemCarbon, 4.0),
                "Phi": 0.0,
                "dh_foam": 0.0,
            }
            self.dynamics_indicators.set_state(snap)
        self._sync_sim_tab_layout()

    def _sim_left_scroll_content_height(self) -> int:
        """Суммарная высота левой колонки «Симуляция» (всё внутри одной прокрутки)."""
        if not hasattr(self, "control_panel"):
            return 0
        return (
            self.control_panel.scroll_content_min_height()
            + 22
            + 78
            + 52
            + 36
            + 24
        )

    def _on_sim_panel_geometry_changed(self) -> None:
        """Высота inner-виджета прокрутки (без повторного _refresh)."""
        if not hasattr(self, "sim_left_inner"):
            return
        h = self._sim_left_scroll_content_height()
        if getattr(self, "_sim_scroll_inner_h", None) == h:
            return
        self._sim_scroll_inner_h = h
        self.sim_left_inner.setMinimumHeight(h)

    def _sync_sim_tab_layout(self) -> None:
        """Синхронизировать группу крутилок и высоту прокрутки (один проход)."""
        if not hasattr(self, "sim_left_inner"):
            return
        if not hasattr(self, "control_panel"):
            return
        self.control_panel._refresh_tab_panel_min_height()
        self._on_sim_panel_geometry_changed()

    def _metal_charge_mass_t(self) -> float:
        """Масса металлической шихты [т]; 0 в поле → запас из сценария (иначе v_C=0)."""
        try:
            m = float(self.MetalCharge.text())
        except (ValueError, AttributeError):
            m = 0.0
        if m <= 1.0:
            m = float(getattr(self, "_control_scenario_mass_t", 200.0))
        return max(m, 50.0)

    def _calc_specific_intensity(self, i_m3_min: float, g_st: float) -> float:
        """Ф-1: i_уд = i / G_ст [м³/(т·мин)]. Источники [1], [2]."""
        if g_st <= 0:
            return 0.0
        return i_m3_min / g_st

    def _intensity_hint_level(self, i_ud: float) -> str:
        if i_ud > 6.0:
            return "danger"
        if i_ud < 2.5 or i_ud > 5.5:
            return "warning"
        return ""

    def _calc_blow_time(self, v_m3: float, i_m3_min: float) -> float:
        """Ф-2: τ = V / i [мин]. Источник [2], [3]."""
        if i_m3_min <= 0:
            return 0.0
        return v_m3 / i_m3_min

    def _calc_flow_from_time(self, v_m3: float, tau_min: float) -> float:
        """Ф-2: i = V / τ [м³/мин]."""
        if tau_min <= 0:
            return 0.0
        return v_m3 / tau_min

    def _calc_jet_velocity(
        self,
        t_gas_k: float = 303.0,
        p2_pa: float = 1.2e6,
        p1_pa: float = 1.2e5,
    ) -> float:
        """Ф-3: скорость истечения O₂ из сопла [м/с]. Источник [1]."""
        k = 1.4
        r_gas = 8.3143 / 0.032
        term = 1.0 - (p1_pa / p2_pa) ** ((k - 1.0) / k)
        if term <= 0:
            return 0.0
        return math.sqrt(2.0 * k / (k - 1.0) * r_gas * t_gas_k * term)

    def _calc_jet_impulse(self, i_m3_min: float, omega: float, n_nozzles: int = 5) -> float:
        """Ф-4: импульс струи [Н]. Источник [1]."""
        rho = 1.429
        v_g = i_m3_min / 60.0
        return rho * v_g * omega / max(n_nozzles, 1)

    def _calc_archimedes_star(self, i_g: float, h_c: float) -> float:
        """Ф-5: модифицированный критерий Архимеда. Источник [1]."""
        rho = 7000.0
        g = 9.81
        if h_c <= 0:
            return 0.0
        return i_g / (rho * g * h_c ** 3)

    def _calc_penetration_depth(self, h_c: float, ar_star: float) -> float:
        """Ф-6: глубина лунки h_л [м]. Шаповалов, МИСиС, 2014, гл. 2."""
        if h_c <= 0:
            return 0.0
        return 0.78 * h_c * (max(ar_star, 1e-12) ** 0.35)

    def _recommended_lance_ranges(self, mass_t: float) -> dict[str, float]:
        """Ф-7: диапазоны положения фурмы по массе плавки. Источник [1]."""
        if mass_t <= 200:
            return {
                "initial_min": 2.0, "initial_max": 3.0,
                "working_min": 1.0, "working_max": 1.3,
                "optimal": 1.15,
            }
        if mass_t <= 300:
            return {
                "initial_min": 2.5, "initial_max": 3.5,
                "working_min": 1.3, "working_max": 1.6,
                "optimal": 1.45,
            }
        return {
            "initial_min": 3.5, "initial_max": 4.5,
            "working_min": 1.7, "working_max": 2.0,
            "optimal": 1.85,
        }

    def _lance_hint_level(self, h_c: float, mass_t: float) -> str:
        if h_c < 0.8 or h_c > 4.5:
            return "danger"
        r = self._recommended_lance_ranges(mass_t)
        if h_c < r["working_min"] or h_c > r["working_max"]:
            return "warning"
        return ""

    def _get_target_carbon(self) -> float:
        """Целевое [C]_М для 8 этапов баланса (поле сценария / БД)."""
        return self._field_float(self.steelCarbon)

    def _get_sim_target_carbon(self) -> float:
        """Целевое [C]_М для симуляции (крутилка или поле сценария)."""
        if self.user_target_C is not None:
            return float(self.user_target_C)
        if hasattr(self, "control_panel"):
            return self.control_panel.target_carbon_value()
        return self._get_target_carbon()

    def _recalc_scrap_weight_for_target_carbon(self) -> float:
        """Масса лома [т] при изменении целевого [C]_М (разд. 3 методики Шаповалова).

        Полная формула (3) G_лом = G_ч·(C_ч−[C]_М)/(C_лом−[C]_М) даёт нереалистичные
        значения, когда C_лом и [C]_М близки (типовые режимы из БД). Для симулятора
        пересчитываем от базы сценария: ~2% изменения массы лома на 0,05% [C]_М.
        """
        base_scrap = self._scenario_scrap_weight_t
        base_target = self._scenario_target_carbon
        if base_scrap is None or base_target is None:
            return self._field_float(self.scrapWeight)
        target_c = self._get_sim_target_carbon()
        delta_c = base_target - target_c
        factor = 1.0 + 0.02 * (delta_c / 0.05)
        return max(0.0, base_scrap * factor)

    def _sync_blast_triplet_info(
        self, values: dict[str, Any], v_m3: float
    ) -> dict[str, float]:
        """Ф-2: связь i и τ через расчётный V (информационно, не влияет на химию)."""
        i = float(values[KEY_FLOW])
        tau = float(values[KEY_TIME])
        computed = values.get(KEY_COMPUTED, KEY_TIME)
        if computed == KEY_FLOW:
            i = self._calc_flow_from_time(v_m3, max(tau, 0.1))
        else:
            tau = self._calc_blow_time(v_m3, max(i, 1.0))
        return {KEY_FLOW: i, KEY_TIME: tau}

    def _get_informational_blow_rates(self, v_m3: float) -> tuple[float, float]:
        """Расход i и время τ по балансному V (Ф-2), согласованные с крутилками."""
        return self._blast_rates_from_balance_volume(v_m3)

    def _sync_blast_panel_display(self, v_m3: float, i_flow: float, tau_min: float) -> None:
        """Обновить расчётный V и информационные i, τ на панели (Ф-2)."""
        if not hasattr(self, "control_panel"):
            return
        self.control_panel.set_blow_volume_display(v_m3)
        self.control_panel.set_informational_blow_rates(i_flow, tau_min)

    def _control_param_label(self, key: str) -> str:
        return {
            KEY_TARGET_C: "Целевое [C]",
            KEY_O2_LOSSES: "Потери O₂",
            KEY_FLOW: "Расход O₂",
            KEY_TIME: "Время продувки",
            KEY_LANCE: "Положение фурмы",
        }.get(key, key)

    def _log_control_changes(self) -> None:
        global Protokol
        if not hasattr(self, "control_panel"):
            return
        for key, old_v, new_v in self.control_panel.drain_change_log():
            t = QtCore.QTime.currentTime().toString("HH:mm:ss")
            label = self._control_param_label(key)
            suffix = {
                KEY_TARGET_C: "%",
                KEY_O2_LOSSES: "%",
                KEY_FLOW: "м³/мин",
                KEY_TIME: "мин",
                KEY_LANCE: "м",
            }.get(key, "")
            Protokol += (
                f"[{t}] Оператор изменил «{label}» с {old_v:g} → {new_v:g} {suffix}\n"
            )
            if key == KEY_TARGET_C:
                self._recalc_scrap_from_target_c = True

    def _update_control_hints(self, i_ud: float, h_c: float) -> None:
        if not hasattr(self, "control_panel"):
            return
        global metalChargeCalcked
        if not metalChargeCalcked:
            self.control_panel.apply_range_hints({})
            return
        mass = self._metal_charge_mass_t()
        hints = {
            KEY_FLOW: self._intensity_hint_level(i_ud),
            KEY_LANCE: self._lance_hint_level(h_c, mass),
        }
        tau = self._user_controls.get(KEY_TIME, 17.0)
        if tau > 25 or tau < 12:
            hints[KEY_TIME] = "warning"
        self.control_panel.apply_range_hints(hints)

    def _push_controls_to_3d(self, i_flow: float, h_c: float, h_l: float) -> None:
        """Обновить 3D по результатам баланса (не с крутилок симуляции)."""
        if not getattr(self, "converter3d", None):
            return
        state = getattr(self, "_last_3d_process_state", "blowing")
        if state == "idle" and i_flow > 0:
            state = "blowing"
        self._balance_blast_i_display = float(i_flow)
        self.converter3d.update_state({
            "blastFlow": round(i_flow, 0),
            "lanceHeight": round(h_c, 3),
            "penetrationDepth": round(h_l, 3),
            "reactionZoneActive": i_flow > 0 and state == "blowing",
        })

    def _apply_user_controls_from_panel(self, values: dict[str, Any] | None = None) -> None:
        if not hasattr(self, "control_panel"):
            return
        if values is None:
            values = self.control_panel.get_signal_values()
        self._user_controls = dict(values)

        self.user_target_C = values.get(SIGNAL_TARGET_C)
        self.user_o2_losses = values.get(SIGNAL_O2_LOSSES)
        self.userLanceHeight = values.get(SIGNAL_LANCE)
        self.userBlowFlow = values.get(SIGNAL_BLOW_INTENSITY)
        self.userBlowTime = values.get(SIGNAL_BLOW_TIME)

        h_c = self.userLanceHeight or 1.15
        if self.userLanceHeight is not None:
            free = self._resolve_sim_free_params()
            self.user_eta_co = free["eta_co"]
            self.user_z_co = free["z_co"]
            if not self.control_panel.p_o2_manual_mode():
                self.user_o2_losses = free["p_o2"]
        else:
            self.user_eta_co = None
            self.user_z_co = None
        self._update_dynamic_auto_fields()

        i = self.userBlowFlow or 600.0
        tau = self.userBlowTime or 17.0

        g_st = self._metal_charge_mass_t()
        i_ud = self._calc_specific_intensity(i, g_st)
        omega = self._calc_jet_velocity()
        i_g = self._calc_jet_impulse(i, omega)
        ar_star = self._calc_archimedes_star(i_g, h_c)
        h_l = self._calc_penetration_depth(h_c, ar_star)

        self._update_control_hints(i_ud, h_c)

    def _on_controls_changed(self, values: dict[str, Any]) -> None:
        self._log_control_changes()
        self._apply_user_controls_from_panel(values)
        if getattr(self, "_recalc_scrap_from_target_c", False):
            scrap_t = self._recalc_scrap_weight_for_target_carbon()
            self.scrapWeight.setText(str(round(scrap_t, 3)))
            self._recalc_scrap_from_target_c = False
        logger.debug("controls changed: %s", self._user_controls)
        if self._is_simulation_tab_active():
            self._apply_live_sim_controls()

    def _ensure_sim_step_timer(self) -> QtCore.QTimer:
        if not hasattr(self, "_sim_step_timer"):
            self._sim_step_timer = QtCore.QTimer(
                getattr(self, "_oper_form", None)
            )
            self._sim_step_timer.setInterval(
                int(CALIB_DEFAULTS.get("sim_live_step_ms", 900))
            )
            self._sim_step_timer.timeout.connect(self._sim_live_step)
        return self._sim_step_timer

    def _ensure_sim_engine(self) -> bool:
        if self._sim_engine is not None:
            return True
        if not self.ScenarioComboBox.currentText().strip():
            return False
        self._apply_user_controls_from_panel()
        try:
            initial = self._build_melt_initial_state()
            control = self._build_melt_control_params()
            self._sim_engine = MeltDynamicsEngine(
                initial_state=initial,
                control_params=control,
            )
            self._sim_t_charge = float(initial["T"])
        except Exception as exc:
            logger.warning("sim engine init failed: %s", exc)
            self._sim_engine = None
            return False
        return True

    def _apply_live_sim_controls(self) -> None:
        """Передать новые крутилки в идущую симуляцию без сброса истории."""
        if not self._ensure_sim_engine():
            return
        self._apply_user_controls_from_panel()
        cp = self._build_melt_control_params()
        tau = self._balance_blow_tau_min()
        if tau is not None and tau > 0:
            cp["tau_target_min"] = tau
        self._sim_engine.apply_controls(cp)
        if hasattr(self, "dynamics_indicators"):
            self.dynamics_indicators.set_target_carbon(self._get_sim_target_carbon())
        if self._sim_snapshots:
            self._update_sim_temp_hint(self._sim_snapshots[-1])
        if not self._sim_engine.is_finished():
            self._ensure_sim_step_timer().start()

    def _refresh_sim_ui(self, snap: dict) -> None:
        if hasattr(self, "dynamics_charts"):
            self.dynamics_charts.update_curves(self._sim_snapshots)
        if hasattr(self, "dynamics_indicators"):
            self.dynamics_indicators.set_target_carbon(self._get_sim_target_carbon())
            self.dynamics_indicators.set_state(snap)
        self._update_sim_temp_hint(snap)
        if getattr(self, "converter3d", None):
            self._push_sim_foam_to_3d(snap)

    def _sim_live_step(self) -> None:
        if self._sim_engine is None or self._sim_engine.is_finished():
            self._ensure_sim_step_timer().stop()
            return
        snap = self._sim_engine.step()
        self._sim_snapshots.append(snap)
        self._refresh_sim_ui(snap)

    def _start_simulation_session(self, *, reset: bool) -> bool:
        if not self.ScenarioComboBox.currentText().strip():
            return False
        timer = self._ensure_sim_step_timer()
        if reset:
            timer.stop()
            self._apply_user_controls_from_panel()
            try:
                initial = self._build_melt_initial_state()
                control = self._build_melt_control_params()
                i_bal = self._balance_blow_intensity()
                if i_bal is not None:
                    control["i_balance_ref"] = i_bal
                    tau_bal = self._balance_blow_tau_min()
                    if tau_bal is not None and tau_bal > 1.0:
                        control["tau_target_min"] = float(tau_bal)
                self._sim_engine = MeltDynamicsEngine(
                    initial_state=initial,
                    control_params=control,
                )
                self._sim_t_charge = float(initial["T"])
                self._sim_snapshots = []
                if hasattr(self, "dynamics_charts"):
                    self.dynamics_charts.clear()
                self._update_sim_temp_hint(None)
            except Exception as exc:
                logger.warning("simulation reset failed: %s", exc)
                return False
        elif not self._ensure_sim_engine():
            return False
        if self._sim_engine.is_finished():
            return True
        timer.start()
        self._sim_live_step()
        return True

    def _on_simulate_melt(self) -> None:
        if not self.ScenarioComboBox.currentText().strip():
            msg_warning(
                None,
                "Сценарий",
                "Сначала выберите и загрузите сценарий.",
            )
            return
        if not self._start_simulation_session(reset=True):
            msg_warning(
                None,
                "Симуляция",
                "Не удалось запустить расчёт. Загрузите сценарий и выполните расчёт дутья.",
            )

    def _on_simulation_finished(self, snapshots: list, last: dict) -> None:
        """Legacy: ответ QThread (сейчас расчёт синхронный в _run_dynamics_preview)."""
        self._sim_snapshots = snapshots
        if hasattr(self, "dynamics_charts"):
            self.dynamics_charts.update_curves(snapshots)
        if hasattr(self, "dynamics_indicators") and last:
            self.dynamics_indicators.set_target_carbon(self._get_sim_target_carbon())
            self.dynamics_indicators.set_state(last)
        self._update_sim_temp_hint(last)

    def _update_sim_temp_hint(self, snap: dict | None) -> None:
        if not hasattr(self, "_sim_temp_hint"):
            return
        t0 = getattr(self, "_sim_t_charge", self._charge_temperature_for_dynamics())
        t_end = self._dynamic_T_end_target()
        tau_bal = self._balance_blow_tau_min()
        tau_bal_txt = (
            f"{tau_bal:.1f} мин" if tau_bal is not None and tau_bal > 0 else "н/д (расчёт дутья)"
        )
        parts = [
            f"T чугуна: {t0:.0f} °C",
            f"цель T: {t_end:.0f} °C",
            f"τ баланс: {tau_bal_txt}",
        ]
        if snap is not None:
            parts.append(f"T: {float(snap.get('T', 0)):.0f} °C")
            parts.append(f"τ сим: {float(snap.get('t_min', 0)):.1f} мин")
        global heatBalanceCalcked
        if heatBalanceCalcked and hasattr(self, "LiquidSteelTemp"):
            try:
                t_bal = float(self.LiquidSteelTemp.text())
                parts.append(f"T баланс: {t_bal:.0f} °C")
            except (ValueError, TypeError):
                pass
        self._sim_temp_hint.setText(" | ".join(parts))

    def _push_sim_foam_to_3d(self, snap: dict) -> None:
        if not getattr(self, "converter3d", None):
            return
        phi = float(snap.get("Phi", 0.0))
        self.converter3d.update_state({
            "state": "blowing",
            "foamDelta": round(float(snap.get("dh_foam", 0.0)), 3),
            "phi": round(phi, 3),
            "phiAlarm": phi >= CALIB_DEFAULTS["phi_alarm"],
            "temperature": round(float(snap.get("T", 0.0))),
        })

    def _sim_playback_tick(self) -> None:
        if not self._sim_snapshots:
            self._sim_playback_timer.stop()
            return
        idx = self._sim_playback_idx
        if idx >= len(self._sim_snapshots):
            self._sim_playback_timer.stop()
            return
        prefix = self._sim_snapshots[: idx + 1]
        snap = prefix[-1]
        if hasattr(self, "dynamics_charts"):
            self.dynamics_charts.update_curves(prefix)
        if hasattr(self, "dynamics_indicators"):
            self.dynamics_indicators.set_state(snap)
        self._update_sim_temp_hint(snap)
        self._push_sim_foam_to_3d(snap)
        self._sim_playback_idx += 1
        if self._sim_playback_idx >= len(self._sim_snapshots):
            self._sim_playback_timer.stop()

    def _on_simulation_failed(self, message: str) -> None:
        btn = getattr(self.control_panel, "_btn_simulate", None)
        if btn is not None:
            btn.setEnabled(True)
            btn.setText(tr("OperatorForm", "Симулировать плавку"))
        msg_critical(None, "Симуляция", "Внимание", message)

    def _on_control_apply_recalc(self) -> None:
        if not self.ScenarioComboBox.currentText().strip():
            msg_warning(
                None,
                "Сценарий",
                "Сначала выберите и загрузите сценарий.",
            )
            return
        # Пересчёт с текущими крутилками и полями формы, без перезагрузки режима из БД.
        self.run_calculations(reload_mode_from_db=False)

    def _refresh_control_recommended(self, v_calc: float, i_rec: float, tau_rec: float) -> None:
        if not hasattr(self, "control_panel"):
            return
        mass = self._metal_charge_mass_t()
        lr = self._recommended_lance_ranges(mass)
        self.control_panel.set_recommended({
            KEY_FLOW: i_rec,
            KEY_TIME: tau_rec,
            KEY_LANCE: lr["optimal"],
            KEY_O2_LOSSES: 7.5,
        })

    def _update_control_scenario_context(self) -> None:
        if not hasattr(self, "control_panel"):
            return
        self._control_scenario_mass_t = self._metal_charge_mass_t()
        self.control_panel.set_scenario_name(self.ScenarioComboBox.currentText())
        try:
            limit_c = float(self.SteelCarbonLimit.text())
            self.control_panel.set_target_carbon_range(limit_c)
        except (ValueError, AttributeError):
            pass
        self.control_panel.set_target_carbon_value(self._field_float(self.steelCarbon))
        self._apply_user_controls_from_panel()

    # === CONTROL INPUTS END ===

    @staticmethod
    def _safe_float(value, default: float = 0.0) -> float:
        """Пустые ячейки и «-» в таблицах → default (без ValueError)."""
        if value is None:
            return default
        text = str(value).strip().replace(",", ".")
        if text in ("", "-", "—"):
            return default
        return float(text)

    def _field_float(self, widget, default: float = 0.0) -> float:
        try:
            return self._safe_float(widget.text(), default)
        except AttributeError:
            return default

    def _cell_float(self, table, row: int, col: int, default: float = 0.0) -> float:
        item = table.item(row, col)
        if item is None:
            return default
        return self._safe_float(item.text(), default)

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

            ironOxygenRequired = (
                self._field_float(self.SlagFeO) * 16 / 72
                + self._field_float(self.SlagFe2O3) * 48 / 160
            )
            # === DYNAMIC EXTENSION v3: формула (20), η_CO из Ф-Д2 ===
            free = self._resolve_balance_free_params()
            eta_CO = free["eta_co"]
            po2 = free["p_o2"]
            # === END DYNAMIC EXTENSION ===
            carbonOxygenRequired = (
                self._cell_float(self.OxidationTable, 5, 1) / 100
                * metalChargeWeight * (eta_CO / 100.0) * 16 / 28
            )
            # === END CONTROL INPUTS ===
            summaryOxygenRequired = totalOxygenRequired + ironOxygenRequired + carbonOxygenRequired - tmpOxygenRequired

            # === DYNAMIC EXTENSION v3: формула (25), П_O2 из Ф-Д6 ===
            # V_D = (V_K + V_K · П_O2 / 100) · 100 / 99,5
            chem_kg = summaryOxygenRequired * (1.0 + po2 / 100.0) * 100.0 / 99.5
            chem_m3 = chem_kg * 22.4 / 32
            # === END DYNAMIC EXTENSION ===

            totalBlastConsumptionM3 = chem_m3
            totalBlastConsumptionKg = chem_kg
            excessBlast = chem_kg * 0.08
            i_flow, tau_min = self._blast_rates_from_balance_volume(chem_m3)
            self._balance_v_m3 = float(chem_m3)
            self._balance_tau_min = float(tau_min)

            self.TotalOxygenDemandBlast.setText(str(round(summaryOxygenRequired, 3)))
            self.TotalConsumptionOfBlastKg.setText(str(round(totalBlastConsumptionKg, 3)))
            self.ExcessBlast.setText(str(round(excessBlast, 3)))
            self.TotalConsumptionOfBlastM3.setText(
                str(round(totalBlastConsumptionM3, 3))
            )

            if hasattr(self, "control_panel"):
                self._sync_blast_panel_display(chem_m3, i_flow, tau_min)

            self._refresh_control_recommended(chem_m3, i_flow, tau_min)

            global blastCalcked
            blastCalcked = True
            h_c = self._recommended_lance_ranges(
                self._metal_charge_mass_t()
            )["optimal"]
            omega = self._calc_jet_velocity()
            i_g = self._calc_jet_impulse(i_flow, omega)
            h_l = self._calc_penetration_depth(
                h_c, self._calc_archimedes_star(i_g, h_c)
            )
            self._last_3d_process_state = "blowing"
            self._push_controls_to_3d(i_flow, h_c, h_l)
        except Exception as err:
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")

    def MaterialBalanceCalcClicked(self):
        try:
            global blastCalcked
            if (blastCalcked == False):
                self.blastCalcClicked()
                blastCalcked = True
            #totalOxygenRequired = float(self.TotalOxygenDemandBlast.text())
            totalOxygenRequired = (
                self._field_float(self.SlagFeO) * 16 / 72
                + self._field_float(self.SlagFe2O3) * 48 / 160
            )
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

            metalChargeWeight = self._field_float(self.MetalCharge)

            # Учёт легирующих элементов (Cr/V/Al/Ti), удалённых из металла через
            # матрицу реакций (флаг AffectsMaterialBalance). C/Si/Mn/P/S уже входят
            # в summRemove (OxidationTable строка 2, столбец 7).
            extra_removed_pct = 0.0
            self._extra_material_rows = []
            if hasattr(self, 'reaction_results'):
                ALREADY_IN_SUMM = {'C_CO', 'C_CO2', 'CO_burn', 'Si', 'Mn', 'P', 'P_alt', 'FeS_CaO', 'S_SO2'}
                for el, res in self.reaction_results.items():
                    if el in ALREADY_IN_SUMM:
                        continue
                    if res['affects_material'] and res['removed'] > 0:
                        extra_removed_pct += res['removed']
                        self._extra_material_rows.append((el, res))

            weightOfOxedizedImpurities = (
                (self._cell_float(self.OxidationTable, 2, 7) + extra_removed_pct) / 100 * metalChargeWeight
            )
            self.MassOfOxidizedImpurities.setText(str(round(weightOfOxedizedImpurities, 3)))

            weightOfIronOxides = (
                self._field_float(self.SlagFeO) + self._field_float(self.SlagFe2O3)
                - totalOxygenRequired
            )
            self.MassOfOxidesPassingIntoSlag.setText(str(round(weightOfIronOxides, 3)))
            self.LossWithCarryOver.setText(str(round(0.02 * metalChargeWeight, 3)))

            oxidesToCO = self._cell_float(self.OxidationTable, 5, 1)
            oxidesToCO2 = self._cell_float(self.OxidationTable, 5, 2)
            self.OutputDataTable.setItem(0, 0, QTableWidgetItem(str(round(oxidesToCO * metalChargeWeight / 100, 3))))
            self.OutputDataTable.setItem(0, 1, QTableWidgetItem(str(round(oxidesToCO2 * metalChargeWeight / 100, 3))))
            self.OutputDataTable.setItem(0, 2, QTableWidgetItem(str(round(
                self._cell_float(self.OutputDataTable, 0, 0)
                + self._cell_float(self.OutputDataTable, 0, 1), 3))))
            self.OutputDataTable.setItem(1, 0, QTableWidgetItem(str("-")))
            self.OutputDataTable.setItem(1, 1, QTableWidgetItem(str(round(totalCaCO3 * 44/96, 3))))
            self.OutputDataTable.setItem(1, 2, QTableWidgetItem(str(round(totalCaCO3 * 44/96, 3))))
            co0 = self._cell_float(self.OutputDataTable, 0, 0)
            # === DYNAMIC EXTENSION v3: формула (20), η_CO из Ф-Д2 ===
            free = self._resolve_balance_free_params()
            co_burn_frac = free["eta_co"] / 100.0
            # === END DYNAMIC EXTENSION ===
            self.OutputDataTable.setItem(2, 0, QTableWidgetItem(str(round(-co_burn_frac * co0, 3))))
            self.OutputDataTable.setItem(2, 1, QTableWidgetItem(str(round(co_burn_frac * co0 * 44 / 28, 3))))
            # === END CONTROL INPUTS ===
            self.OutputDataTable.setItem(2, 2, QTableWidgetItem(str(round(
                self._cell_float(self.OutputDataTable, 2, 0)
                + self._cell_float(self.OutputDataTable, 2, 1), 3))))
            self.OutputDataTable.setItem(3, 0, QTableWidgetItem(str("-")))
            self.OutputDataTable.setItem(3, 1, QTableWidgetItem(str(round(totalMgCO3 * 44 / 84, 3))))
            self.OutputDataTable.setItem(3, 2, QTableWidgetItem(str(round(totalMgCO3 * 44 / 84, 3))))
            tmp = self._cell_float(self.OutputDataTable, 0, 0) + self._cell_float(self.OutputDataTable, 2, 0)
            self.OutputDataTable.setItem(4, 0, QTableWidgetItem(str(round(tmp, 3))))
            tmp = (
                self._cell_float(self.OutputDataTable, 0, 1)
                + self._cell_float(self.OutputDataTable, 1, 1)
                + self._cell_float(self.OutputDataTable, 2, 1)
                + self._cell_float(self.OutputDataTable, 3, 1)
            )
            self.OutputDataTable.setItem(4, 1, QTableWidgetItem(str(round(tmp, 3))))
            tmp = (
                self._cell_float(self.OutputDataTable, 0, 2)
                + self._cell_float(self.OutputDataTable, 1, 2)
                + self._cell_float(self.OutputDataTable, 2, 2)
                + self._cell_float(self.OutputDataTable, 3, 2)
            )
            self.OutputDataTable.setItem(4, 2, QTableWidgetItem(str(round(tmp, 3))))
            g4_0 = self._cell_float(self.OutputDataTable, 4, 0)
            g4_1 = self._cell_float(self.OutputDataTable, 4, 1)
            g4_2 = self._cell_float(self.OutputDataTable, 4, 2)
            g5_0 = g4_0 * 22.4 / 28
            g5_1 = g4_1 * 22.4 / 44
            self.OutputDataTable.setItem(5, 0, QTableWidgetItem(str(round(g5_0, 3))))
            self.OutputDataTable.setItem(5, 1, QTableWidgetItem(str(round(g5_1, 3))))
            self.OutputDataTable.setItem(5, 2, QTableWidgetItem(str(round(g5_0 + g5_1, 3))))
            pct_den = g4_2 if abs(g4_2) > 1e-9 else 1.0
            self.OutputDataTable.setItem(6, 0, QTableWidgetItem(str(round(g4_0 / pct_den * 100, 3))))
            self.OutputDataTable.setItem(6, 1, QTableWidgetItem(str(round(g4_1 / pct_den * 100, 3))))
            self.OutputDataTable.setItem(6, 2, QTableWidgetItem(str(100)))

            tmp = 0.00001 * 200 * 70 * self._cell_float(self.OutputDataTable, 5, 2)
            self.DustLoss.setText(str(round(tmp, 3)))

            oxidesPassingIntoSlag = self._field_float(self.MassOfOxidesPassingIntoSlag)
            oxidizedImpurities = self._field_float(self.MassOfOxidizedImpurities)
            lossWithCarryOver = self._field_float(self.LossWithCarryOver)
            dustLoss = self._field_float(self.DustLoss)
            reclaimedIronWeight = self._field_float(self.ReclaimedIronWeight)
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
            self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem(self._tl("Чугун жидкий")))
            self.IncomingData.setItem(incomingDataRowCount, 1, QTableWidgetItem(str(round(
                self._field_float(self.castWeight) * 1000, 3))))

            incomingDataRowCount += 1
            self.IncomingData.insertRow(incomingDataRowCount)
            self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem(self._tl("Лом")))
            self.IncomingData.setItem(incomingDataRowCount, 1, QTableWidgetItem(str(round(
                self._field_float(self.scrapWeight) * 1000, 3))))

            incomingDataRowCount += 1
            for row in range(fluxesRowCount):
                self.IncomingData.insertRow(incomingDataRowCount)
                self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem(str(listOfNamesForClass[row].name)))
                self.IncomingData.setItem(incomingDataRowCount, 1,
                                          QTableWidgetItem(str(round(listOfNamesForClass[row].fluxeWeight * 1000, 2))))
                incomingDataRowCount += 1

            self.IncomingData.insertRow(incomingDataRowCount)
            self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem(self._tl("Дутьё")))
            self.IncomingData.setItem(incomingDataRowCount, 1,
                                      QTableWidgetItem(str(round(
                                          self._field_float(self.TotalConsumptionOfBlastKg) * 1000, 3))))
            incomingDataRowCount += 1

            summary = 0
            for row in range(incomingDataRowCount):
                summary += self._cell_float(self.IncomingData, row, 1)

            self.IncomingData.insertRow(incomingDataRowCount)
            self.IncomingData.setItem(incomingDataRowCount, 0, QTableWidgetItem(self._tl("Итого")))
            self.IncomingData.setItem(incomingDataRowCount, 1, QTableWidgetItem(str(int(summary))))

            outRowCount = self.OutputData.rowCount()
            if outRowCount > 0:
                while outRowCount > 0:
                    self.OutputData.removeRow(0)
                    outRowCount -= 1

            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem(self._tl("Металл жидкий")))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(liquidIron * 1000, 3))))

            outRowCount+=1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem(self._tl("Шлак")))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(
                self._field_float(self.SlagWeight) * 1000, 3))))

            outRowCount+=1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem(self._tl("Газ")))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(g4_2 * 1000, 3))))

            outRowCount+=1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem(self._tl("Избыток дутья")))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(
                self._field_float(self.ExcessBlast) * 1000, 3))))

            outRowCount += 1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem(self._tl("Выносы и выбросы")))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(
                lossWithCarryOver * 1000, 3))))

            outRowCount += 1
            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem(self._tl("Потери с пылью")))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(dustLoss * 1000, 3))))

            outRowCount += 1
            summary = 0
            for row in range(outRowCount-1):
                summary += self._cell_float(self.OutputData, row, 1)

            self.OutputData.insertRow(outRowCount)
            self.OutputData.setItem(outRowCount, 0, QTableWidgetItem(self._tl("Итого")))
            self.OutputData.setItem(outRowCount, 1, QTableWidgetItem(str(round(summary, 3))))

            # Справочная разбивка по легирующим (не входит в сумму «Итого»:
            # их масса уже учтена внутри статей «Металл жидкий» и «Шлак»)
            extra_rows = getattr(self, '_extra_material_rows', [])
            if extra_rows:
                EL_NAMES = {'Cr': 'Хром', 'V': 'Ванадий', 'Al': 'Алюминий', 'Ti': 'Титан'}
                italic = QtGui.QFont()
                italic.setItalic(True)

                def _add_ref_row(text, value):
                    r = self.OutputData.rowCount()
                    self.OutputData.insertRow(r)
                    name_item = QTableWidgetItem(text)
                    name_item.setFont(italic)
                    val_item = QTableWidgetItem(value)
                    val_item.setFont(italic)
                    self.OutputData.setItem(r, 0, name_item)
                    self.OutputData.setItem(r, 1, val_item)

                _add_ref_row("Справочно: окисление легирующих", "удал.Me / оксид в шлак, кг")
                for el, res in extra_rows:
                    removed_kg = res['removed'] * metalChargeWeight / 100 * 1000
                    oxide_kg = res['oxide_kg'] * metalChargeWeight / 100 * 1000
                    label = "  в т.ч. {0} -> {1}".format(EL_NAMES.get(el, el), res['product'])
                    _add_ref_row(label, "{0} / {1}".format(round(removed_kg, 3), round(oxide_kg, 3)))

            self.IncomingData.resizeColumnsToContents()
            self.OutputData.resizeColumnsToContents()
            global materialBalanceCalcked
            materialBalanceCalcked = True

        except Exception as err:
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")

    def HeatBalanceCalcClicked(self):
        try:
            global materialBalanceCalcked
            if(materialBalanceCalcked == False):
                self.MaterialBalanceCalcClicked()
                materialBalanceCalcked = True
            #Физическое тепло жидкого чугуна
            PhysCastHeat = (
                self._field_float(self.castWeight) * 1000.0
                * (61.9 + 0.88 * self._field_float(self.castTemperature))
            )
            self.CastPhysHeat.setText(str(round(PhysCastHeat, 3)))
            self.IncomingHeatTable.setItem(0, 0, QTableWidgetItem(str(PhysCastHeat)))

            #Тепло от реакции окисления
            TotalRemovedCarbon = self._cell_float(self.OxidationTable, 2, 0)
            TotalRemovedSilicon = self._cell_float(self.OxidationTable, 2, 3)
            TotalRemovedMagn = self._cell_float(self.OxidationTable, 2, 4)
            TotalRemovedPhosph = self._cell_float(self.OxidationTable, 2, 5)
            if hasattr(self, 'reaction_results'):
                HeatReactOfOxidation = (
                    sum(res['heat'] for res in self.reaction_results.values())
                    * self._field_float(self.MetalCharge) * 10.0
                )
            else:
                HeatReactOfOxidation = (
                    14770.0 * TotalRemovedCarbon + 26970.0 * TotalRemovedSilicon
                    + 7000.0 * TotalRemovedMagn + 21730.0 * TotalRemovedPhosph
                ) * self._field_float(self.MetalCharge) * 10.0
            self.ThermalReactEffect.setText(str(round(HeatReactOfOxidation, 3)))
            self.IncomingHeatTable.setItem(1, 0, QTableWidgetItem(str(HeatReactOfOxidation)))

            #Химическое тепло от образования оксидов
            ChemHeatOxidAppear = (
                3707.0 * self._field_float(self.SlagFeO) * 1000.0
                + 5278.0 * self._field_float(self.SlagFe2O3) * 1000.0
            )
            self.ChemHeatOxyd.setText(str(round(ChemHeatOxidAppear, 3)))
            self.IncomingHeatTable.setItem(2, 0, QTableWidgetItem(str(round(ChemHeatOxidAppear, 3))))

            #Тепловой эффект реакции шлакообразования
            ChemSlagHeat = (
                628.0 * self._field_float(self.SlagCaO) * 1000.0
                + 1464.0 * self._field_float(self.SlagSiO2) * 1000.0
            )
            self.ChemHeatSlag.setText(str(round(ChemSlagHeat, 2)))
            self.IncomingHeatTable.setItem(3, 0, QTableWidgetItem(str(round(ChemSlagHeat, 3))))
            
            #Тепло от дожигания CO
            # === DYNAMIC EXTENSION v3: формула (36), η_CO и Z из Ф-Д2, Ф-Д3 ===
            # Q_CO = 101 · g_CO · η_СО · Z
            # Используем параметры с учётом управляющих воздействий оператора
            # (высота фурмы, интенсивность дутья), если панель управления подключена.
            g_CO = abs(self._cell_float(self.OutputDataTable, 2, 0)) * 1000.0
            free = self._resolve_sim_free_params()
            HeatOfBurningCO = 101.0 * g_CO * free["eta_co"] * free["z_co"]
            # === END DYNAMIC EXTENSION ===
            self.HeatCO.setText(str(round(HeatOfBurningCO, 2)))
            self.IncomingHeatTable.setItem(4, 0, QTableWidgetItem(str(round(HeatOfBurningCO, 3))))

            #Общий приход тепла
            TotalHeatInc = PhysCastHeat + HeatReactOfOxidation + ChemHeatOxidAppear + ChemSlagHeat + HeatOfBurningCO
            self.TotalHeatInc.setText(str(TotalHeatInc))
            self.IncomingHeatTable.setItem(5, 0, QTableWidgetItem(str(round(TotalHeatInc, 2))))

            #Расходные статьи
            #
            # Физическое тепло отходящих газов
            COKilo = self._cell_float(self.OutputDataTable, 4, 0) * 1000
            CO2Kilo = self._cell_float(self.OutputDataTable, 4, 1) * 1000
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
            emissions = self._cell_float(self.OutputData, 4, 1)
            emissionsHeatLoses =  (54.8 + 0.84 * 1550.0) * emissions
            self.HeatLosesRemove.setText(str(round(emissionsHeatLoses, 3)))
            self.OutputHeatTable.setItem(4, 0, QTableWidgetItem(str(round(FeOxydesHeatLoses, 3))))

            #Затраты тепла на пылеобразование
            dustFeLoses = self._cell_float(self.OutputData, 5, 1)
            heatDustLoses = (54.8 + 0.84 * 2000.0) * dustFeLoses
            self.HeatDustForm.setText(str(round(heatDustLoses, 3)))
            self.OutputHeatTable.setItem(5, 0, QTableWidgetItem(str(round(heatDustLoses, 3))))

            #Тепло на разложение карбонатов
            totalCaCO3Decom = self._cell_float(self.OutputDataTable, 1, 2)
            totalMgCO3Decom = self._cell_float(self.OutputDataTable, 3, 2)
            heatCarbonDecom =  4038.0 * (totalCaCO3Decom * 1000.0 + totalMgCO3Decom * 1000.0)
            self.HeatCarbonDecom.setText(str(round(heatCarbonDecom, 3)))
            self.OutputHeatTable.setItem(6, 0, QTableWidgetItem(str(round(heatCarbonDecom, 3))))

            #Тепловые потери
            heatLoses = TotalHeatInc * 0.03 #можно брать из базы как настраиваемый параметр
            self.HeatLoses.setText(str(round(heatLoses, 3)))
            self.OutputHeatTable.setItem(7, 0, QTableWidgetItem(str(round(heatLoses, 3))))

            #Температура жидкого металла в конце продувки
            liquid_yield = self._field_float(self.LiquidIronYield)
            slag_weight = self._field_float(self.SlagWeight)
            heat_denom = 0.84 * liquid_yield * 1000 + 2.09 * slag_weight * 1000
            if abs(heat_denom) < 1e-9:
                heat_denom = 1.0
            SteelTemperature = (
                TotalHeatInc - PhysGasHeat - FeOxydesHeatLoses - emissionsHeatLoses
                - heatDustLoses - heatCarbonDecom - heatLoses
                - 54.8 * liquid_yield * 1000.0 + 1379 * slag_weight * 1000
            ) / heat_denom

            #Физическое тепло жидкого металла
            PhysSteelHeat = (54.8 + 0.84 * SteelTemperature) * liquid_yield * 1000
            self.PhysHeatLiquidSteel.setText(str(round(PhysSteelHeat, 3)))
            self.OutputHeatTable.setItem(0, 0, QTableWidgetItem(str(round(PhysSteelHeat, 3))))

            #Физическое тепло шлака
            PhysSlagHeat = (2.09 * SteelTemperature - 1379.0) * slag_weight * 1000
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
            meltTemperature = 1539.0 - 80.0 * self._get_target_carbon()
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
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")

    def deoxCalc(self):
        try:
            global heatBalanceCalcked
            if(heatBalanceCalcked == False):
                self.HeatBalanceCalcClicked()
                heatBalanceCalcked = True
            if(self.ChemEmission.rowCount() == 0):
                self._show_critical("Не выбран феросплав!", "Ошибка", "Внимание")
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
            lining_base = (
                4.11155 * pow(10, -6) * float(self.LiquidSteelTemp.text())
                * (limitSolubilityMgO * slagMgO)
            )
            liningWeightLoss = lining_base
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
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")


    def recomendationCalc(self):
        try:
            global heatBalanceCalcked
            if(heatBalanceCalcked == False):
                self.HeatBalanceCalcClicked()
                heatBalanceCalcked = True
            if(self.ChemEmission.rowCount() == 0):
                self._show_critical("Не выбран феросплав!", "Ошибка", "Внимание")
                return

        except Exception as err:
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")


    def CheckConverterFunc(self):
        try:
            H = float(self.height.text())
            D = float(self.diametr.text())
            attitude = H / D
            att_s = str(round(attitude, 2))
            if attitude > 2.1:
                msg_critical(
                    getattr(self, '_oper_form', None),
                    "Проверка конвертера",
                    "Внимание",
                    tr("OperatorForm",
                       "Отношение высоты рабочего объема к диаметру выше максимально допустимого ({0}>2.1)\n"
                       "Возможно возникновение выбросов").format(att_s),
                )
            elif attitude < 1.17:
                msg_critical(
                    getattr(self, '_oper_form', None),
                    "Проверка конвертера",
                    "Внимание",
                    tr("OperatorForm",
                       "Отношение высоты рабочего объема к диаметру ниже минимально допустимого ({0}<1.17)").format(att_s),
                )
            else:
                from i18n import msg_info
                msg_info(
                    getattr(self, '_oper_form', None),
                    "Проверка конвертера",
                    "Внимание",
                    tr("OperatorForm",
                       "Проверка конвертера выполнена успешно.\n"
                       "Отношение высоты рабочего объема к диаметру находится в допустимых пределах\n"
                       "(1.17>{0}>2.1)").format(att_s),
                )
        except Exception as err:
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")


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
                self._set_recommendation_lines(
                    "Необходимо увеличить количество магнезиального флюса на 50 кг и заново произвести расчёты"
                )
            else:
                self._set_recommendation_lines(
                    "Используется оптимальный расход флюсов"
                )
            if self.SteelPhosphorLimit.text() != "":
                self.checkLimits()
            if getattr(self, 'converter3d', None):
                self._last_3d_process_state = "complete"
                self.converter3d.update_state({
                    'state':       'complete',
                    'temperature': steelTemperature,
                    'blastFlow':   0,
                    'reactionZoneActive': False,
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
            checkResult = tr("OperatorForm", "Рассчеты завершены. Накладываемые ограничения не выполняются") + "\n"
            actualSteelCarbon = float(self.DeoxidationBalance.item(0,0).text())
            actualSteelTemp = float(self.resultSteelTemperature.text())
            actualSteelPhosphor = float(self.DeoxidationBalance.item(0,6).text())
            steelCarbon = float(self.SteelCarbonLimit.text())
            minSteelTemp = float(self.MinSteelTempLimit.text())
            steelPhosphor = float(self.SteelPhosphorLimit.text())
            extra_lines: list[str] = []
            if actualSteelCarbon > steelCarbon:
                line = "Содержание углерода в стали меньше минимально допустимого."
                checkResult += tr("OperatorForm", line) + "\n"
                extra_lines.append(line)
                problem = True
            if actualSteelTemp < minSteelTemp:
                line = "Температура стали меньше минимально допустимой."
                checkResult += tr("OperatorForm", line) + "\n"
                extra_lines.append(line)
                self.resultSteelTemperature.setStyleSheet("QLineEdit { background: #cc0000; color: #ffffff; border: 1px solid #ff4444; border-radius: 4px; }")
                problem = True
            if actualSteelPhosphor > steelPhosphor:
                line = (
                    "Содержание фосфора в стали меньше минимально допустимого.\n"
                    "Рекомендуется увеличить содержание извести и провести рассчеты еще раз."
                )
                checkResult += tr("OperatorForm", line) + "\n"
                extra_lines.append(line)
                problem = True
            base_lines = list(getattr(self, "_recommendation_lines_ru", []))
            rec_lines = base_lines + extra_lines
            if problem == True:
                from i18n import msg_info
                msg_info(
                    getattr(self, '_oper_form', None),
                    "Проверка Результата",
                    "Внимание",
                    checkResult,
                )
            elif problem == False:
                ok_line = "Проверка результатов выполнена успешно, накладываемые ограничения выполняются"
                ok_short = "Ограничения сценария выполняются"
                rec_lines = base_lines + [ok_line, ok_short]
            self._recommendation_lines_ru = rec_lines
            self._refresh_recommendation_text()
        except Exception as err:
            self._show_critical("Проверьте введенные данные! {0}".format(err), "Ошибка", "Внимание")


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
        self._refresh_locale_dependent_text()
        if hasattr(self, '_stages_lbl'):
            self._stages_lbl.setStyleSheet(
                f"color: {app_theme.tokens(theme)['text_label']}; font-size: 11px;")
        if hasattr(self, '_hints_lbl'):
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
        if hasattr(self, 'view_toggles'):
            self.view_toggles.theme_toggle.sync_from_settings()
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
        if hasattr(self, "_center_scroll"):
            app_theme.apply_scroll_panel(self._center_scroll, self._center_panel, theme)
        if hasattr(self, "control_panel"):
            self.control_panel.set_theme(theme)
            self.control_panel._btn_apply.setStyleSheet(
                app_theme.primary_button_style(theme))
            if hasattr(self, "dynamics_charts"):
                self.dynamics_charts.set_theme(theme)
            if hasattr(self, "dynamics_indicators"):
                self.dynamics_indicators.set_theme(theme)
        ro_field = app_theme.read_only_field_style(theme)
        for name in (
            "CO2ThrowRes", "SteelWeightRes", "SlagWeightRes",
            "resultSteelTemperature", "LiningWeightLoss",
        ):
            w = getattr(self, name, None)
            if w is not None:
                w.setStyleSheet(ro_field)
        for item in getattr(self, "_result_kpi_frames", []):
            fr, cap, val, border, tcol = item[:5]
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
            if scroll not in (
                getattr(self, "_left_scroll", None),
                getattr(self, "_right_scroll", None),
                getattr(self, "_center_scroll", None),
            ):
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
        self._left_scroll.setMinimumWidth(320)

        self._left_panel = QtWidgets.QWidget()
        lw = self._left_panel
        lw.setAutoFillBackground(True)
        lw.setMinimumWidth(300)
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
        self.AddNewMode.setFixedSize(32, 32)
        g11h.addWidget(self.AddNewMode, 0, QtCore.Qt.AlignRight)
        mc_row.addWidget(self.groupBox_11, 3)

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
        _LBL_W  = 100  # одинаковая ширина всех подписей → поля выравниваются
        _FLD_H  = 26   # единая высота всех полей ввода (QLineEdit + QComboBox)

        g7 = QtWidgets.QGridLayout(self.groupBox_7)
        g7.setSpacing(4)
        g7.setColumnStretch(1, 1); g7.setColumnStretch(3, 1)

        def _rlbl(name):
            lbl = _lbl(name)
            lbl.setFixedWidth(_LBL_W)
            lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            return lbl

        def _fedit(name):
            w = _edit(name)
            w.setFixedHeight(_FLD_H)
            return w

        self.label_12 = _rlbl("label_12"); self.scrapCarbon   = _fedit("scrapCarbon")
        self.label_13 = _rlbl("label_13"); self.scrapSerum    = _fedit("scrapSerum")
        self.label_14 = _rlbl("label_14"); self.scrapSilicon  = _fedit("scrapSilicon")
        self.label_15 = _rlbl("label_15"); self.scrapPhosphor = _fedit("scrapPhosphor")
        self.label_25 = _rlbl("label_25"); self.scrapManganese= _fedit("scrapManganese")
        g7.addWidget(self.label_12, 0, 0); g7.addWidget(self.scrapCarbon,  0, 1)
        g7.addWidget(self.label_13, 0, 2); g7.addWidget(self.scrapSerum,   0, 3)
        g7.addWidget(self.label_14, 1, 0); g7.addWidget(self.scrapSilicon, 1, 1)
        g7.addWidget(self.label_15, 1, 2); g7.addWidget(self.scrapPhosphor,1, 3)
        g7.addWidget(self.label_25, 2, 0); g7.addWidget(self.scrapManganese,2,1)

        # Тип лома и легирующие элементы (Cr/V/Al/Ti)
        self.label_scrapType = _rlbl("label_scrapType")
        self.label_scrapType.setText("Тип лома:")
        self.scrapTypeCombo = QtWidgets.QComboBox()
        self.scrapTypeCombo.setObjectName("scrapTypeCombo")
        self.scrapTypeCombo.setFixedHeight(_FLD_H)
        self.scrapTypeCombo.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.scrapTypeCombo.currentIndexChanged.connect(self.onScrapTypeChanged)
        g7.addWidget(self.label_scrapType, 2, 2); g7.addWidget(self.scrapTypeCombo, 2, 3)

        self.label_scrapCr = _rlbl("label_scrapCr"); self.label_scrapCr.setText("Cr, %")
        self.scrapCrInput = _fedit("scrapCrInput")
        self.label_scrapV = _rlbl("label_scrapV"); self.label_scrapV.setText("V, %")
        self.scrapVInput = _fedit("scrapVInput")
        self.label_scrapAl = _rlbl("label_scrapAl"); self.label_scrapAl.setText("Al, %")
        self.scrapAlInput = _fedit("scrapAlInput")
        self.label_scrapTi = _rlbl("label_scrapTi"); self.label_scrapTi.setText("Ti, %")
        self.scrapTiInput = _fedit("scrapTiInput")
        for _w in (self.scrapCrInput, self.scrapVInput, self.scrapAlInput, self.scrapTiInput):
            _w.setText("0.0")
        g7.addWidget(self.label_scrapCr, 3, 0); g7.addWidget(self.scrapCrInput, 3, 1)
        g7.addWidget(self.label_scrapV,  3, 2); g7.addWidget(self.scrapVInput,  3, 3)
        g7.addWidget(self.label_scrapAl, 4, 0); g7.addWidget(self.scrapAlInput, 4, 1)
        g7.addWidget(self.label_scrapTi, 4, 2); g7.addWidget(self.scrapTiInput, 4, 3)
        g3v.addWidget(self.groupBox_7)
        ll.addWidget(self.groupBox_3)

        # ── Металлошихта / Хим. состав шихты ─────────────────────────────
        mc2_row = QtWidgets.QHBoxLayout()
        mc2_row.setSpacing(5)
        self.groupBox_5 = QtWidgets.QGroupBox()
        self.groupBox_5.setObjectName("groupBox_5")
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
        # CENTER PANEL — этапы расчёта (управление и симуляция — вкладка «Симуляция»)
        # ────────────────────────────────────────────────────────────────────
        self._center_scroll = QtWidgets.QScrollArea()
        self._center_scroll.setObjectName("center_scroll")
        self._center_scroll.setWidgetResizable(True)
        self._center_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._center_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        self._center_panel = QtWidgets.QWidget()
        cw = self._center_panel
        cw.setObjectName("center_widget")
        cw.setMinimumWidth(280)
        cw.setAutoFillBackground(True)
        cv = QtWidgets.QVBoxLayout(cw)
        cv.setContentsMargins(10, 10, 10, 10)
        cv.setSpacing(6)

        # Scenario task
        self.label_29 = _lbl("label_29")
        cv.addWidget(self.label_29)
        self.ScenarioTask = QtWidgets.QPlainTextEdit()
        self.ScenarioTask.setReadOnly(True)
        self.ScenarioTask.setObjectName("ScenarioTask")
        self.ScenarioTask.setMinimumHeight(44)
        self.ScenarioTask.setMaximumHeight(64)
        cv.addWidget(self.ScenarioTask)

        # Scenario load progress
        self.scenarioProgress = QtWidgets.QProgressBar()
        self.scenarioProgress.setObjectName("scenarioProgress")
        self.scenarioProgress.setValue(0)
        self.scenarioProgress.setFixedHeight(12)
        cv.addWidget(self.scenarioProgress)

        sep_stages = QtWidgets.QFrame()
        sep_stages.setFrameShape(QtWidgets.QFrame.HLine)
        sep_stages.setFixedHeight(1)
        sep_stages.setStyleSheet(
            "QFrame { background: rgba(0,200,240,0.35); border: none; }")
        cv.addWidget(sep_stages)

        self._stages_section = QtWidgets.QWidget()
        self._stages_section.setObjectName("stages_section")
        stages_lay = QtWidgets.QVBoxLayout(self._stages_section)
        stages_lay.setContentsMargins(0, 0, 0, 0)
        stages_lay.setSpacing(5)

        seq_title = QtWidgets.QLabel(tr("OperatorForm", "ПОСЛЕДОВАТЕЛЬНОСТЬ  РАСЧЁТОВ"))
        self._seq_title = seq_title
        seq_title.setAlignment(QtCore.Qt.AlignCenter)
        seq_title.setFixedHeight(16)
        seq_title.setStyleSheet(
            "color: rgba(0,200,240,0.70); font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        stages_lay.addWidget(seq_title)

        self._stage_leds = {}
        self._stage_style_widgets = []

        self._stage_label_widgets: list[tuple] = []

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
            stg_lbl = QtWidgets.QLabel(tr("OperatorForm", label_text))
            self._stage_label_widgets.append((stg_lbl, label_text))
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
                        msg_warning(
                            None,
                            "Предыдущий этап не выполнен",
                            tr("OperatorForm", "Сначала завершите этап:\n«{0}»").format(
                                tr("OperatorForm", gl)
                            ),
                        )
                return _on_click

            calc_btn.clicked.connect(_make_guarded(connect_fn, guard_fn, guard_label))
            setattr(self, btn_attr, calc_btn)
            row.addWidget(num_lbl)
            row.addWidget(led)
            row.addWidget(stg_lbl, 1)
            row.addWidget(calc_btn)
            return wrapper

        stages_lay.addWidget(_stage_row(
            1, "Металлошихта",
            self.calcMetalChargeClicked, "metalCharge", "MetalChargeCalc"))
        stages_lay.addWidget(_stage_row(
            2, "Табл. окисления",
            self.calcTableClick, "table", "CalcTable",
            guard_fn=lambda: metalChargeCalcked,
            guard_label="Металлошихта"))
        stages_lay.addWidget(_stage_row(
            3, "Расчёт шлака",
            self.slagCalcClicked, "slag", "SlagCalc",
            guard_fn=lambda: tableCalcked,
            guard_label="Табл. окисления"))
        stages_lay.addWidget(_stage_row(
            4, "Расчёт дутья",
            self.blastCalcClicked, "blast", "BlastCalc",
            guard_fn=lambda: slagCalcked,
            guard_label="Расчёт шлака"))
        stages_lay.addWidget(_stage_row(
            5, "Матер. баланс",
            self.MaterialBalanceCalcClicked, "matBalance", "MaterialBalanceCalc",
            guard_fn=lambda: blastCalcked,
            guard_label="Расчёт дутья"))
        stages_lay.addWidget(_stage_row(
            6, "Тепл. баланс",
            self.HeatBalanceCalcClicked, "heatBalance", "HeatBalanceCalc",
            guard_fn=lambda: materialBalanceCalcked,
            guard_label="Матер. баланс"))
        stages_lay.addWidget(_stage_row(
            7, "Раскисление",
            self.deoxCalc, "deox", "SteelDeoxidationCalc",
            guard_fn=lambda: heatBalanceCalcked,
            guard_label="Тепл. баланс"))
        stages_lay.addWidget(_stage_row(
            8, "Рекомендации",
            self.getRecomendation, "recomendation", "RecomendationCalc",
            guard_fn=lambda: heatBalanceCalcked,
            guard_label="Тепл. баланс"))

        stages_lay.addSpacing(4)
        self.GetResExample = QtWidgets.QPushButton(
            "\u25ba  \u0417\u0410\u041f\u0423\u0421\u0422\u0418\u0422\u042c  \u0412\u0421\u0415  \u042d\u0422\u0410\u041f\u042b")
        self.GetResExample.setObjectName("GetResExample")
        self.GetResExample.setMinimumHeight(28)
        self.GetResExample.setMaximumHeight(28)
        self.GetResExample.clicked.connect(self.GetScenarioExample)
        stages_lay.addWidget(self.GetResExample)

        cv.addWidget(self._stages_section, 0)
        cv.addStretch(1)

        self._center_scroll.setWidget(cw)
        main_splitter.addWidget(self._center_scroll)

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

        def _big_result_frame(label_key, border_rgb, text_color, obj_name):
            fr = QtWidgets.QFrame()
            fv = QtWidgets.QVBoxLayout(fr)
            fv.setContentsMargins(6, 3, 6, 3)
            cap = QtWidgets.QLabel(tr("OperatorForm", label_key))
            val = _ro_edit(obj_name)
            val.setAlignment(QtCore.Qt.AlignCenter)
            fv.addWidget(cap)
            fv.addWidget(val)
            self._result_kpi_frames.append((fr, cap, val, border_rgb, text_color, label_key))
            return fr, val

        fr_lt, self.LiquidSteelTemp = _big_result_frame(
            "Т жидкого металла, °C",
            "255,120,0", "#ff6820", "LiquidSteelTemp")
        fr_ot, self.OverheatTemp = _big_result_frame(
            "Перегрев, °C",
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
            main_splitter.setSizes([340, 320, 230, 350])
            main_splitter.setStretchFactor(0, 2)
            main_splitter.setStretchFactor(1, 3)
            main_splitter.setStretchFactor(2, 2)
            main_splitter.setStretchFactor(3, 4)
        else:
            self.converter3d = None
            main_splitter.setSizes([340, 320, 310])
            main_splitter.setStretchFactor(0, 2)
            main_splitter.setStretchFactor(1, 3)
            main_splitter.setStretchFactor(2, 2)

        main_layout.addWidget(main_splitter, stretch=1)

        # ════════════════════════════════════════════════════════════════════
        # BOTTOM DETAIL TABS
        # ════════════════════════════════════════════════════════════════════
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setMinimumHeight(270)
        self.tabWidget.setMaximumHeight(310)
        self.tabWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )

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

        # ── tab_simulation  Симуляция (после «Схема») ─────────────────────
        # === CONTROL INPUTS + DYNAMIC EXTENSION v3 ===
        self._init_control_user_state()
        presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")
        self.control_panel = ControlInputsPanel()
        self.control_panel.configure_for_tab_embed()
        self.control_panel.set_presets_dir(presets_dir)
        self.control_panel.controls_changed.connect(self._on_controls_changed)
        self.control_panel.layout_geometry_changed.connect(
            self._on_sim_panel_geometry_changed
        )
        self.control_panel.apply_recalc_requested.connect(self._on_control_apply_recalc)
        self.control_panel.simulate_requested.connect(self._on_simulate_melt)

        auto_row = QtWidgets.QWidget()
        auto_row.setObjectName("sim_auto_row")
        auto_grid = QtWidgets.QGridLayout(auto_row)
        auto_grid.setContentsMargins(0, 2, 0, 2)
        auto_grid.setHorizontalSpacing(8)
        auto_grid.setVerticalSpacing(4)

        for idx, (title, attr) in enumerate((
            ("η_CO (авто)", "_auto_eta_co"),
            ("Z (авто)", "_auto_z_co"),
            ("П_O₂ (авто)", "_auto_p_o2"),
            ("K_П (авто)", "_auto_k_p"),
            ("G_В (авто)", "_auto_g_v"),
        )):
            row, col = divmod(idx, 2)
            lbl = QtWidgets.QLabel(title)
            lbl.setProperty("class", "control_info_hint")
            fld = QtWidgets.QLineEdit()
            fld.setReadOnly(True)
            fld.setMaximumHeight(22)
            fld.setProperty("class", "control_blow_volume_readonly")
            auto_grid.addWidget(lbl, row, col * 2)
            auto_grid.addWidget(fld, row, col * 2 + 1)
            setattr(self, attr, fld)

        self.dynamics_charts = DynamicsChartsWidget(
            compact=True, expand_in_tab=True
        )
        self.dynamics_indicators = DynamicsIndicatorsPanel(compact=True)

        self.tab_simulation = QtWidgets.QWidget()
        self.tab_simulation.setObjectName("tab_simulation")
        sim_root = QtWidgets.QVBoxLayout(self.tab_simulation)
        sim_root.setContentsMargins(4, 4, 4, 4)
        sim_root.setSpacing(0)

        sim_split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        sim_split.setObjectName("simulation_splitter")
        sim_split.setChildrenCollapsible(False)

        sim_left = QtWidgets.QWidget()
        sim_left.setObjectName("simulation_left")
        sim_left.setMinimumWidth(320)
        sim_left_lay = QtWidgets.QVBoxLayout(sim_left)
        sim_left_lay.setContentsMargins(0, 0, 0, 0)
        sim_left_lay.setSpacing(0)

        sim_left_scroll = QtWidgets.QScrollArea()
        sim_left_scroll.setObjectName("simulation_left_scroll")
        sim_left_scroll.setWidgetResizable(True)
        sim_left_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        sim_left_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        sim_left_inner = QtWidgets.QWidget()
        self.sim_left_inner = sim_left_inner
        sim_left_inner.setObjectName("simulation_left_inner")
        sim_left_inner_lay = QtWidgets.QVBoxLayout(sim_left_inner)
        sim_left_inner_lay.setContentsMargins(6, 6, 10, 6)
        sim_left_inner_lay.setSpacing(6)
        sim_left_inner_lay.addWidget(self.control_panel, 0)

        auto_title = QtWidgets.QLabel("Расчётные параметры")
        auto_title.setProperty("class", "control_knob_title")
        sim_left_inner_lay.addWidget(auto_title, 0)

        auto_row.setFixedHeight(78)
        sim_left_inner_lay.addWidget(auto_row, 0)

        self.dynamics_indicators.setFixedHeight(52)
        sim_left_inner_lay.addWidget(self.dynamics_indicators, 0)

        sim_btn_wrap = QtWidgets.QWidget()
        sim_btn_wrap.setObjectName("simulation_btn_wrap")
        sim_btn_wrap.setFixedHeight(36)
        sim_btn_wrap.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        sim_btn_bar = QtWidgets.QHBoxLayout(sim_btn_wrap)
        sim_btn_bar.setObjectName("simulation_btn_bar")
        sim_btn_bar.setContentsMargins(0, 0, 0, 0)
        sim_btn_bar.setSpacing(6)
        self.control_panel.detach_main_buttons_for_tab(sim_btn_bar)
        sim_left_inner_lay.addWidget(sim_btn_wrap, 0)
        sim_left_inner_lay.addStretch(0)

        sim_left_scroll.setWidget(sim_left_inner)
        sim_left_lay.addWidget(sim_left_scroll, 1)

        self.sim_left_scroll = sim_left_scroll
        self._sync_sim_tab_layout()

        sim_right = QtWidgets.QWidget()
        sim_right.setObjectName("simulation_right")
        sim_right.setMinimumWidth(360)
        sim_right_lay = QtWidgets.QVBoxLayout(sim_right)
        sim_right_lay.setContentsMargins(4, 4, 4, 4)
        sim_right_lay.setSpacing(0)
        charts_title = QtWidgets.QLabel("Динамика плавки")
        charts_title.setProperty("class", "control_knob_title")
        sim_right_lay.addWidget(charts_title, 0)
        self._sim_temp_hint = QtWidgets.QLabel(
            "«Симулировать» — старт с начала. Крутилки меняют режим без сброса плавки. "
            "τ и T — по балансу после «Рассчитать»."
        )
        self._sim_temp_hint.setProperty("class", "control_info_hint")
        self._sim_temp_hint.setWordWrap(True)
        sim_right_lay.addWidget(self._sim_temp_hint, 0)
        sim_right_lay.addWidget(self.dynamics_charts, 1)

        sim_split.addWidget(sim_left)
        sim_split.addWidget(sim_right)
        sim_split.setStretchFactor(0, 2)
        sim_split.setStretchFactor(1, 3)
        sim_split.setSizes([420, 580])

        sim_root.addWidget(sim_split, 1)
        self.tabWidget.insertTab(1, self.tab_simulation, "")
        self.tabWidget.currentChanged.connect(self._on_tab_widget_changed)
        self._update_dynamic_auto_fields()
        # === END CONTROL INPUTS + DYNAMIC EXTENSION ===

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
        t2l.setContentsMargins(0, 0, 0, 0)
        t2_scroll = QtWidgets.QScrollArea()
        t2_scroll.setWidgetResizable(True)
        t2_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        t2_inner = QtWidgets.QWidget()
        t2_inner_l = QtWidgets.QVBoxLayout(t2_inner)
        t2_inner_l.setContentsMargins(6, 6, 6, 6)
        t2_inner_l.setSpacing(5)

        self.shlak_group_box = QtWidgets.QGroupBox()
        self.shlak_group_box.setObjectName("shlak_group_box")
        shl_v = QtWidgets.QVBoxLayout(self.shlak_group_box)
        shl_v.setContentsMargins(4, 4, 4, 4)
        shl_v.setSpacing(4)
        shl_cols = QtWidgets.QHBoxLayout()
        shl_cols.setSpacing(5)

        _slag_row_h = 26

        self.him_sostav_shlaka_group_box = QtWidgets.QGroupBox()
        self.him_sostav_shlaka_group_box.setObjectName("him_sostav_shlaka_group_box")
        hss_g = QtWidgets.QGridLayout(self.him_sostav_shlaka_group_box)
        hss_g.setSpacing(4)
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
            lbl.setWordWrap(False)
            lbl.setStyleSheet("font-size: 10px; color: #b8c8d0;")
            wdg.setFixedHeight(22)
            hss_g.setRowMinimumHeight(r, _slag_row_h)
            hss_g.addWidget(lbl, r, 0)
            hss_g.addWidget(wdg, r, 1)
        shl_cols.addWidget(self.him_sostav_shlaka_group_box, 1)

        self.him_sostav_shlaka_v_procentah_group_box = QtWidgets.QGroupBox()
        self.him_sostav_shlaka_v_procentah_group_box.setObjectName("him_sostav_shlaka_v_procentah_group_box")
        hssv_g = QtWidgets.QGridLayout(self.him_sostav_shlaka_v_procentah_group_box)
        hssv_g.setSpacing(4)
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
            lbl.setWordWrap(False)
            lbl.setStyleSheet("font-size: 10px; color: #b8c8d0;")
            wdg.setFixedHeight(22)
            hssv_g.setRowMinimumHeight(r, _slag_row_h)
            hssv_g.addWidget(lbl, r, 0)
            hssv_g.addWidget(wdg, r, 1)
        shl_cols.addWidget(self.him_sostav_shlaka_v_procentah_group_box, 1)
        shl_v.addLayout(shl_cols)
        t2_inner_l.addWidget(self.shlak_group_box)
        t2_scroll.setWidget(t2_inner)
        t2l.addWidget(t2_scroll)
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
            wdg.setFixedHeight(22)
            odgb_g.setRowMinimumHeight(r, 26)
            odgb_g.addWidget(lbl, r, 0)
            odgb_g.addWidget(wdg, r, 1)
        odgb_v.addLayout(odgb_g, 0)
        self.OutputDataTable = QtWidgets.QTableWidget()
        self.OutputDataTable.setObjectName("OutputDataTable")
        self.OutputDataTable.setColumnCount(3)
        self.OutputDataTable.setRowCount(7)
        _tbl_row_h = 24
        self.OutputDataTable.verticalHeader().setDefaultSectionSize(_tbl_row_h)
        self.OutputDataTable.verticalHeader().setMinimumWidth(140)
        self.OutputDataTable.setMinimumHeight(7 * _tbl_row_h + 36)
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
            wdg.setFixedHeight(22)
            ps_g.setRowMinimumHeight(r, 26)
            ps_g.addWidget(lbl, r, 0)
            ps_g.addWidget(wdg, r, 1)
        ps_v.addLayout(ps_g, 0)
        self.IncomingHeatTable = QtWidgets.QTableWidget()
        self.IncomingHeatTable.setObjectName("IncomingHeatTable")
        self.IncomingHeatTable.setColumnCount(1)
        self.IncomingHeatTable.setRowCount(6)
        _heat_tbl_row_h = 24
        self.IncomingHeatTable.verticalHeader().setDefaultSectionSize(_heat_tbl_row_h)
        self.IncomingHeatTable.verticalHeader().setMinimumWidth(200)
        self.IncomingHeatTable.setMinimumHeight(6 * _heat_tbl_row_h + 36)
        for r in range(6):
            self.IncomingHeatTable.setVerticalHeaderItem(r, QtWidgets.QTableWidgetItem())
        self.IncomingHeatTable.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem())
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
            wdg.setFixedHeight(22)
            rs_g.setRowMinimumHeight(r, 26)
            rs_g.addWidget(lbl, r, 0)
            rs_g.addWidget(wdg, r, 1)
        rs_v.addLayout(rs_g, 0)
        self.OutputHeatTable = QtWidgets.QTableWidget()
        self.OutputHeatTable.setObjectName("OutputHeatTable")
        self.OutputHeatTable.setColumnCount(1)
        self.OutputHeatTable.setRowCount(9)
        self.OutputHeatTable.verticalHeader().setDefaultSectionSize(_heat_tbl_row_h)
        self.OutputHeatTable.verticalHeader().setMinimumWidth(220)
        self.OutputHeatTable.setMinimumHeight(9 * _heat_tbl_row_h + 36)
        for r in range(9):
            self.OutputHeatTable.setVerticalHeaderItem(r, QtWidgets.QTableWidgetItem())
        self.OutputHeatTable.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem())
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
        for _tab_page in (self.tab_7, self.tab_simulation, self.tab, self.tab_2,
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
        self.actionScrapTypes = QtWidgets.QAction(OperatorForm)
        self.actionScrapTypes.setObjectName("actionScrapTypes")
        self.actionScrapTypes.triggered.connect(self.openScrapTypeDialog)

        self.actionStoichiometryMatrix = QtWidgets.QAction(OperatorForm)
        self.actionStoichiometryMatrix.setObjectName("actionStoichiometryMatrix")
        self.actionStoichiometryMatrix.triggered.connect(self.openStoichiometryMatrixDialog)

        self.Menu.addAction(self.SaveFile)
        self.Menu.addSeparator()
        self.Menu.addAction(self.Exit)
        self.Help.addAction(self.about)
        self.Administrate.addAction(self.AddUser)
        self.Administrate.addAction(self.AddDbData)
        self.Administrate.addAction(self.actionScrapTypes)
        self.Administrate.addAction(self.actionStoichiometryMatrix)
        self.ViewMenu = QtWidgets.QMenu(self.menubar)
        self.ViewMenu.setObjectName("ViewMenu")
        self.view_toggles = ViewTogglesBar()
        self.view_toggles.theme_toggle.theme_changed.connect(lambda _t: self.refresh_theme())
        self.view_toggles.language_toggle.language_changed.connect(
            lambda _l: self.refresh_language(OperatorForm)
        )
        toggle_action = QtWidgets.QWidgetAction(OperatorForm)
        toggle_action.setDefaultWidget(self.view_toggles)
        self.ViewMenu.addAction(toggle_action)

        self.menubar.addAction(self.Menu.menuAction())
        self.menubar.addAction(self.Administrate.menuAction())
        self.menubar.addAction(self.ViewMenu.menuAction())
        self.menubar.addAction(self.Help.menuAction())

        manager().theme_changed.connect(lambda _t: self.refresh_theme())
        locale_manager().language_changed.connect(
            lambda _l: self.refresh_language(OperatorForm)
        )

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
        if self.converter3d and hasattr(self.converter3d, 'set_ui_language'):
            self.converter3d.set_ui_language(get_language())
        self.refresh_theme()
        self.refresh_language(OperatorForm)

    def _refresh_locale_dependent_text(self) -> None:
        theme = get_theme()
        if hasattr(self, '_stages_lbl'):
            self._stages_lbl.setText(app_theme.help_rich_html(theme))
        if hasattr(self, '_hints_lbl'):
            self._hints_lbl.setText(app_theme.hints_rich_html(theme))
        if hasattr(self, '_title_lbl'):
            self._title_lbl.setText(
                tr("OperatorForm", "⚙  КОНВЕРТЕРНАЯ ПЛАВКА  —  ПУЛЬТ ОПЕРАТОРА")
            )
        if hasattr(self, 'control_panel'):
            self.control_panel.refresh_language()
        if hasattr(self, 'dynamics_indicators'):
            self.dynamics_indicators.refresh_language()
        if hasattr(self, 'dynamics_charts'):
            self.dynamics_charts.refresh_language()
        if getattr(self, 'converter3d', None) and hasattr(self.converter3d, 'set_ui_language'):
            self.converter3d.set_ui_language(get_language())
        self._refresh_static_table_labels()
        self._refresh_recommendation_text()
        for lbl, key in getattr(self, "_stage_label_widgets", []):
            lbl.setText(tr("OperatorForm", key))
        for item in getattr(self, "_result_kpi_frames", []):
            if len(item) >= 6:
                _fr, cap, _val, _border, _tcol, key = item
                cap.setText(tr("OperatorForm", key))
        if hasattr(self, "_seq_title"):
            self._seq_title.setText(tr("OperatorForm", "ПОСЛЕДОВАТЕЛЬНОСТЬ  РАСЧЁТОВ"))

    def refresh_language(self, OperatorForm):
        self.retranslateUi(OperatorForm)
        if hasattr(self, 'view_toggles'):
            self.view_toggles.language_toggle.sync_from_settings()
        self._refresh_locale_dependent_text()

    def retranslateUi(self, OperatorForm):
        from i18n import tr as _t
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
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_simulation), _t("OperatorForm", "Симуляция")
        )

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
        self.actionScrapTypes.setText(_t("OperatorForm", "Типы лома и реакции"))
        self.actionStoichiometryMatrix.setText(_t("OperatorForm", "Матрица стехиометрии"))
        if hasattr(self, "label_scrapType"):
            self.label_scrapType.setText(_t("OperatorForm", "Тип лома:"))
        # ── Tab text for bottom detail tabs ──────────────────────────────
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), _t("OperatorForm", "Схема"))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_simulation), _t("OperatorForm", "Симуляция")
        )
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab),   _t("OperatorForm", "Окисление"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _t("OperatorForm", "Шлак"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _t("OperatorForm", "Мат. баланс"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _t("OperatorForm", "Тепл. баланс"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _t("OperatorForm", "Раскисление"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), _t("OperatorForm", "Рекомендации"))

        # ── Startup ───────────────────────────────────────────────────────
        if hasattr(self, "GetResExample"):
            self.GetResExample.setText(_t("OperatorForm", "►  ЗАПУСТИТЬ  ВСЕ  ЭТАПЫ"))
        self.getSettings()
        self.getFluxes()
        self.getModes()
        self.loadScrapTypeCombo()
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

