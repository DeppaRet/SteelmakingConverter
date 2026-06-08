from PyQt5 import QtCore, QtGui, QtWidgets
import mysql.connector as mc
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

import app_theme
from theme_settings import manager, get_theme
from theme_toggle import ThemeToggle


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

    def openScrapTypeDialog(self):
        from ScrapTypeDialog import ScrapTypeDialog
        dialog = ScrapTypeDialog(
            "localhost", "root", "root",
            editable=True, parent=getattr(self, "_dev_form", None)
        )
        dialog.exec_()

    def refresh_theme(self):
        theme = get_theme()
        if hasattr(self, '_dev_form') and self._dev_form:
            self._dev_form.setPalette(app_theme.palette(theme))
            t = app_theme.tokens(theme)
            self._dev_form.setStyleSheet(f"""
                QWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {t['gradient_start']}, stop:1 {t['gradient_end']});
                }}
                QLabel {{ color: {t['text']}; background: transparent; }}
                QGroupBox {{
                    color: {t['accent2']}; font-weight: bold;
                    border: 1px solid {t['group_border']};
                    border-radius: 8px; margin-top: 10px; padding: 5px;
                    background: {t['panel_bg']};
                }}
                QLineEdit, QComboBox {{
                    background: {t['input_bg']};
                    border: 1px solid {t['input_border']};
                    border-radius: 4px; color: {t['text']};
                }}
                {app_theme.pushbutton_rules(t)}
                QTableWidget {{
                    background: {t['table_bg']}; color: {t['text']};
                    gridline-color: {t['input_border']};
                }}
                QHeaderView::section {{
                    background: {t['table_header']}; color: {t['text']};
                }}
            """)
        if hasattr(self, 'theme_toggle'):
            self.theme_toggle.sync_from_settings()
        root = getattr(self, '_dev_form', None)
        if root:
            for tbl in root.findChildren(QtWidgets.QTableWidget):
                tbl.setStyleSheet(app_theme.table_style(theme))
                tbl.setPalette(app_theme.palette(theme))

    def setupUi(self, Form):
        self._dev_form = Form
        Form.setObjectName("Form")
        Form.resize(1000, 620)
        Form.setMinimumSize(800, 500)

        # Central widget + root layout
        _central = QtWidgets.QWidget()
        root_hbox = QtWidgets.QHBoxLayout(_central)
        root_hbox.setContentsMargins(8, 8, 8, 8)
        root_hbox.setSpacing(8)

        # ── Left: table viewer ────────────────────────────────────────────────
        left_w = QtWidgets.QWidget()
        left_vbox = QtWidgets.QVBoxLayout(left_w)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(6)

        hdr_row = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel()
        self.label.setObjectName("label")
        self.label.setFont(QtGui.QFont("Times New Roman", 12))
        hdr_row.addWidget(self.label)

        self.choosenTable = QtWidgets.QComboBox()
        self.choosenTable.setObjectName("choosenTable")
        for _ in range(8):
            self.choosenTable.addItem("")
        self.choosenTable.setMinimumWidth(140)
        hdr_row.addWidget(self.choosenTable)

        self.displayTableButton = QtWidgets.QPushButton()
        self.displayTableButton.setObjectName("displayTableButton")
        self.displayTableButton.clicked.connect(self.showChoosenTable)
        hdr_row.addWidget(self.displayTableButton)

        self.scrapTypesButton = QtWidgets.QPushButton()
        self.scrapTypesButton.setObjectName("scrapTypesButton")
        self.scrapTypesButton.clicked.connect(self.openScrapTypeDialog)
        hdr_row.addWidget(self.scrapTypesButton)

        hdr_row.addStretch()
        left_vbox.addLayout(hdr_row)

        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        left_vbox.addWidget(self.tableWidget, stretch=1)

        root_hbox.addWidget(left_w, stretch=1)

        # ── Right: data-entry forms in scroll area ────────────────────────────
        right_scroll = QtWidgets.QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        right_scroll.setMinimumWidth(420)
        right_scroll.viewport().setAutoFillBackground(False)

        right_w = QtWidgets.QWidget()
        right_w.setAttribute(Qt.WA_TranslucentBackground)
        right_vbox = QtWidgets.QVBoxLayout(right_w)
        right_vbox.setContentsMargins(0, 0, 4, 0)
        right_vbox.setSpacing(8)

        # Mode group
        self.groupBox = QtWidgets.QGroupBox()
        self.groupBox.setObjectName("groupBox")
        mode_grid = QtWidgets.QGridLayout(self.groupBox)
        mode_grid.setSpacing(6)
        mode_grid.setColumnStretch(1, 1)
        mode_grid.setColumnStretch(3, 1)

        self.label_2 = QtWidgets.QLabel(); self.label_2.setObjectName("label_2")
        self.modeName = QtWidgets.QLineEdit(); self.modeName.setObjectName("modeName")
        mode_grid.addWidget(self.label_2, 0, 0)
        mode_grid.addWidget(self.modeName, 0, 1)

        self.label_3 = QtWidgets.QLabel(); self.label_3.setObjectName("label_3")
        self.modeSteelName = QtWidgets.QComboBox(); self.modeSteelName.setObjectName("modeSteelName")
        mode_grid.addWidget(self.label_3, 0, 2)
        mode_grid.addWidget(self.modeSteelName, 0, 3)

        self.label_4 = QtWidgets.QLabel(); self.label_4.setObjectName("label_4")
        self.modeCastSteel = QtWidgets.QComboBox(); self.modeCastSteel.setObjectName("modeCastSteel")
        mode_grid.addWidget(self.label_4, 1, 0)
        mode_grid.addWidget(self.modeCastSteel, 1, 1)

        self.label_5 = QtWidgets.QLabel(); self.label_5.setObjectName("label_5")
        self.modeScrap = QtWidgets.QComboBox(); self.modeScrap.setObjectName("modeScrap")
        mode_grid.addWidget(self.label_5, 1, 2)
        mode_grid.addWidget(self.modeScrap, 1, 3)

        self.addModeButton = QtWidgets.QPushButton()
        self.addModeButton.setObjectName("addModeButton")
        self.addModeButton.clicked.connect(self.addMode)
        mode_grid.addWidget(self.addModeButton, 2, 0, 1, 4)

        right_vbox.addWidget(self.groupBox)

        # Scrap + Flux side-by-side
        mid_hbox = QtWidgets.QHBoxLayout()
        mid_hbox.setSpacing(8)

        self.groupBox_2 = QtWidgets.QGroupBox()
        self.groupBox_2.setObjectName("groupBox_2")
        scrap_vbox = QtWidgets.QVBoxLayout(self.groupBox_2)

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
        sc_grid = QtWidgets.QGridLayout(self.groupBox_7)
        sc_grid.setSpacing(6)
        sc_grid.setColumnStretch(1, 1); sc_grid.setColumnStretch(3, 1)
        self.label_12 = QtWidgets.QLabel(); self.label_12.setObjectName("label_12")
        self.scrapCarbon = QtWidgets.QLineEdit(); self.scrapCarbon.setObjectName("scrapCarbon")
        self.label_14 = QtWidgets.QLabel(); self.label_14.setObjectName("label_14")
        self.scrapSerum = QtWidgets.QLineEdit(); self.scrapSerum.setObjectName("scrapSerum")
        sc_grid.addWidget(self.label_12, 0, 0); sc_grid.addWidget(self.scrapCarbon, 0, 1)
        sc_grid.addWidget(self.label_14, 0, 2); sc_grid.addWidget(self.scrapSerum, 0, 3)
        self.label_13 = QtWidgets.QLabel(); self.label_13.setObjectName("label_13")
        self.scrapSilicon = QtWidgets.QLineEdit(); self.scrapSilicon.setObjectName("scrapSilicon")
        self.label_15 = QtWidgets.QLabel(); self.label_15.setObjectName("label_15")
        self.scrapPhosphor = QtWidgets.QLineEdit(); self.scrapPhosphor.setObjectName("scrapPhosphor")
        sc_grid.addWidget(self.label_13, 1, 0); sc_grid.addWidget(self.scrapSilicon, 1, 1)
        sc_grid.addWidget(self.label_15, 1, 2); sc_grid.addWidget(self.scrapPhosphor, 1, 3)
        self.label_25 = QtWidgets.QLabel(); self.label_25.setObjectName("label_25")
        self.scrapManganese = QtWidgets.QLineEdit(); self.scrapManganese.setObjectName("scrapManganese")
        sc_grid.addWidget(self.label_25, 2, 0); sc_grid.addWidget(self.scrapManganese, 2, 1)
        scrap_vbox.addWidget(self.groupBox_7)

        mid_hbox.addWidget(self.groupBox_2, stretch=1)

        # Flux in mode
        self.groupBox_10 = QtWidgets.QGroupBox()
        self.groupBox_10.setObjectName("groupBox_10")
        flux_vbox = QtWidgets.QVBoxLayout(self.groupBox_10)
        flux_vbox.setSpacing(4)

        self.tip_flyusa_label = QtWidgets.QLabel(); self.tip_flyusa_label.setObjectName("tip_flyusa_label")
        flux_vbox.addWidget(self.tip_flyusa_label)

        self.FluxeType = QtWidgets.QComboBox()
        self.FluxeType.setEditable(False); self.FluxeType.setObjectName("FluxeType")
        flux_vbox.addWidget(self.FluxeType)

        flux_tbl_row = QtWidgets.QHBoxLayout()
        self.FluxeTable = QtWidgets.QTableWidget()
        self.FluxeTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.FluxeTable.setObjectName("FluxeTable")
        self.FluxeTable.setColumnCount(1); self.FluxeTable.setRowCount(0)
        _fh = QtWidgets.QTableWidgetItem()
        self.FluxeTable.setHorizontalHeaderItem(0, _fh)
        self.FluxeTable.horizontalHeader().setStretchLastSection(True)
        flux_tbl_row.addWidget(self.FluxeTable)

        flux_btn_col = QtWidgets.QVBoxLayout()
        self.AddFluxeButton = QtWidgets.QPushButton(); self.AddFluxeButton.setText("")
        _icon_add = QtGui.QIcon()
        _icon_add.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/add.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.AddFluxeButton.setIcon(_icon_add)
        self.AddFluxeButton.setObjectName("AddFluxeButton")
        self.AddFluxeButton.clicked.connect(self.AddFluxeButtonClicked)
        flux_btn_col.addWidget(self.AddFluxeButton)
        self.RemoveFluxeButton = QtWidgets.QPushButton(); self.RemoveFluxeButton.setText("")
        _icon_rm = QtGui.QIcon()
        _icon_rm.addPixmap(QtGui.QPixmap("SteelmakingConverter/GUI\\../Pictures/remove.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RemoveFluxeButton.setIcon(_icon_rm)
        self.RemoveFluxeButton.setObjectName("RemoveFluxeButton")
        self.RemoveFluxeButton.clicked.connect(self.removeFluxeButtonClicked)
        flux_btn_col.addWidget(self.RemoveFluxeButton)
        flux_btn_col.addStretch()
        flux_tbl_row.addLayout(flux_btn_col)
        flux_vbox.addLayout(flux_tbl_row)

        mid_hbox.addWidget(self.groupBox_10)
        right_vbox.addLayout(mid_hbox)

        # Cast group
        self.groupBox_3 = QtWidgets.QGroupBox()
        self.groupBox_3.setObjectName("groupBox_3")
        cast_vbox = QtWidgets.QVBoxLayout(self.groupBox_3)

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
        cc_grid = QtWidgets.QGridLayout(self.groupBox_6)
        cc_grid.setSpacing(6)
        cc_grid.setColumnStretch(1, 1); cc_grid.setColumnStretch(3, 1)
        self.label_17 = QtWidgets.QLabel(); self.label_17.setObjectName("label_17")
        self.castCarbon = QtWidgets.QLineEdit(); self.castCarbon.setObjectName("castCarbon")
        self.label_19 = QtWidgets.QLabel(); self.label_19.setObjectName("label_19")
        self.castSerum = QtWidgets.QLineEdit(); self.castSerum.setObjectName("castSerum")
        cc_grid.addWidget(self.label_17, 0, 0); cc_grid.addWidget(self.castCarbon, 0, 1)
        cc_grid.addWidget(self.label_19, 0, 2); cc_grid.addWidget(self.castSerum, 0, 3)
        self.label_18 = QtWidgets.QLabel(); self.label_18.setObjectName("label_18")
        self.castSilicon = QtWidgets.QLineEdit(); self.castSilicon.setObjectName("castSilicon")
        self.label_20 = QtWidgets.QLabel(); self.label_20.setObjectName("label_20")
        self.castPhosphor = QtWidgets.QLineEdit(); self.castPhosphor.setObjectName("castPhosphor")
        cc_grid.addWidget(self.label_18, 1, 0); cc_grid.addWidget(self.castSilicon, 1, 1)
        cc_grid.addWidget(self.label_20, 1, 2); cc_grid.addWidget(self.castPhosphor, 1, 3)
        self.label_24 = QtWidgets.QLabel(); self.label_24.setObjectName("label_24")
        self.castManganese = QtWidgets.QLineEdit(); self.castManganese.setObjectName("castManganese")
        cc_grid.addWidget(self.label_24, 2, 0); cc_grid.addWidget(self.castManganese, 2, 1)
        cast_vbox.addWidget(self.groupBox_6)
        right_vbox.addWidget(self.groupBox_3)
        right_vbox.addStretch()

        right_scroll.setWidget(right_w)
        root_hbox.addWidget(right_scroll, stretch=1)

        self.menu_view = QtWidgets.QMenu(Form)
        self.theme_toggle = ThemeToggle()
        self.theme_toggle.theme_changed.connect(lambda _t: self.refresh_theme())
        toggle_action = QtWidgets.QWidgetAction(Form)
        toggle_action.setDefaultWidget(self.theme_toggle)
        self.menu_view.addAction(toggle_action)
        menubar = QtWidgets.QMenuBar(Form)
        menubar.addMenu(self.menu_view)

        if hasattr(Form, 'setCentralWidget'):
            wrapper = QtWidgets.QWidget()
            outer = QtWidgets.QVBoxLayout(wrapper)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.addWidget(menubar)
            outer.addWidget(_central)
            Form.setCentralWidget(wrapper)
        else:
            _outer = QtWidgets.QVBoxLayout(Form)
            _outer.setContentsMargins(0, 0, 0, 0)
            _outer.addWidget(menubar)
            _outer.addWidget(_central)

        manager().theme_changed.connect(lambda _t: self.refresh_theme())

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        self.refresh_theme()

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Добро пожаловать, разработчик модели"))
        self.menu_view.setTitle(_translate("Form", "Вид"))
        self.label.setText(_translate("Form", "Таблица:"))
        self.choosenTable.setItemText(0, _translate("Form", "Режимы"))
        self.choosenTable.setItemText(1, _translate("Form", "Сталь"))
        self.choosenTable.setItemText(2, _translate("Form", "Состав стали"))
        self.choosenTable.setItemText(3, _translate("Form", "Чугун"))
        self.choosenTable.setItemText(4, _translate("Form", "Состав чугуна"))
        self.choosenTable.setItemText(5, _translate("Form", "Лом"))
        self.choosenTable.setItemText(6, _translate("Form", "Состав лома"))
        self.choosenTable.setItemText(7, _translate("Form", "Флюсы"))
        self.displayTableButton.setText(_translate("Form", "Отобразить"))
        self.scrapTypesButton.setText(_translate("Form", "Типы лома и реакции"))
        self.groupBox.setTitle(_translate("Form", "Добавление режима"))
        self.label_2.setText(_translate("Form", "Название:"))
        self.label_3.setText(_translate("Form", "Сталь:"))
        self.label_4.setText(_translate("Form", "Чугун:"))
        self.label_5.setText(_translate("Form", "Лом:"))
        self.addModeButton.setText(_translate("Form", "Добавить режим"))
        self.groupBox_2.setTitle(_translate("Form", "Добавление данных о ломе"))
        self.label_11.setText(_translate("Form", "Масса (Т):"))
        self.addScrapDataButton.setText(_translate("Form", "Добавить"))
        self.groupBox_7.setTitle(_translate("Form", "Химический состав"))
        self.label_12.setText(_translate("Form", "Углерод (C):"))
        self.label_14.setText(_translate("Form", "Сера (S):"))
        self.label_13.setText(_translate("Form", "Кремний (Si):"))
        self.label_15.setText(_translate("Form", "Фосфор (P):"))
        self.label_25.setText(_translate("Form", "Марганец (Mn):"))
        self.groupBox_10.setTitle(_translate("Form", "Флюсы в режиме"))
        self.tip_flyusa_label.setText(_translate("Form", "Тип флюса:"))
        item = self.FluxeTable.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Тип флюса"))
        self.groupBox_3.setTitle(_translate("Form", "Добавление данных о чугуне"))
        self.label_10.setText(_translate("Form", "Температура (℃):"))
        self.label_16.setText(_translate("Form", "Масса (Т):"))
        self.addCastButton.setText(_translate("Form", "Добавить"))
        self.groupBox_6.setTitle(_translate("Form", "Химический состав"))
        self.label_17.setText(_translate("Form", "Углерод (C):"))
        self.label_19.setText(_translate("Form", "Сера (S):"))
        self.label_18.setText(_translate("Form", "Кремний (Si):"))
        self.label_20.setText(_translate("Form", "Фосфор (P):"))
        self.label_24.setText(_translate("Form", "Марганец (Mn):"))
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
