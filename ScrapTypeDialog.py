"""Диалог управления типами лома и матрицей стехиометрических реакций."""
from functools import partial

from PyQt5 import QtCore, QtWidgets
import mysql.connector as mc

from i18n import tr, msg_critical, msg_warning

try:
    import app_theme
    from theme_settings import get_theme
except Exception:  # pragma: no cover
    app_theme = None
    get_theme = None

CARBON_ELEMENTS = ("C_CO", "C_CO2")

COLUMN_KEYS = ["№", "Уравнение", "Акт", "Доля CO", "МБ", "Шл", "Д", "Т"]
COL_NUMBER, COL_EQUATION, COL_ACTIVE, COL_CO, COL_MB, COL_SLAG, COL_BLAST, COL_HEAT = range(8)


class ScrapTypeDialog(QtWidgets.QDialog):
    def __init__(self, db_host, db_login, db_pass, editable=False, parent=None):
        super().__init__(parent)
        self.db_host = db_host
        self.db_login = db_login
        self.db_pass = db_pass
        self.editable = editable
        self.resize(900, 600)
        self._build_ui()
        self.retranslate_ui()
        self.load_scrap_types()
        self._apply_theme()

    def _connect(self):
        return mc.connect(
            host=self.db_host, user=self.db_login,
            password=self.db_pass, database="regimdata"
        )

    def _build_ui(self):
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        left = QtWidgets.QVBoxLayout()
        self._types_lbl = QtWidgets.QLabel()
        left.addWidget(self._types_lbl)
        self.typeList = QtWidgets.QListWidget()
        self.typeList.currentItemChanged.connect(self._on_type_item_changed)
        left.addWidget(self.typeList, stretch=1)

        self.addTypeButton = QtWidgets.QPushButton()
        self.addTypeButton.clicked.connect(self.add_scrap_type)
        self.delTypeButton = QtWidgets.QPushButton()
        self.delTypeButton.clicked.connect(self.delete_scrap_type)
        left.addWidget(self.addTypeButton)
        left.addWidget(self.delTypeButton)
        if not self.editable:
            self.addTypeButton.hide()
            self.delTypeButton.hide()

        left_w = QtWidgets.QWidget()
        left_w.setLayout(left)
        left_w.setMaximumWidth(240)
        root.addWidget(left_w)

        right = QtWidgets.QVBoxLayout()
        self._reactions_lbl = QtWidgets.QLabel()
        right.addWidget(self._reactions_lbl)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(len(COLUMN_KEYS))
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(COL_EQUATION, QtWidgets.QHeaderView.Stretch)
        right.addWidget(self.table, stretch=1)

        self._legend_lbl = QtWidgets.QLabel()
        self._legend_lbl.setWordWrap(True)
        right.addWidget(self._legend_lbl)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        self.closeButton = QtWidgets.QPushButton()
        self.closeButton.clicked.connect(self.accept)
        btn_row.addWidget(self.closeButton)
        right.addLayout(btn_row)

        root.addLayout(right, stretch=1)

    def retranslate_ui(self):
        if self.editable:
            self.setWindowTitle(tr("ScrapTypeDialog", "Управление типами лома и матрицей реакций"))
        else:
            self.setWindowTitle(tr("ScrapTypeDialog", "Типы лома и матрица реакций (просмотр)"))
        self._types_lbl.setText(tr("ScrapTypeDialog", "Типы лома"))
        self._reactions_lbl.setText(tr("ScrapTypeDialog", "Реакции для выбранного типа лома"))
        self.table.setHorizontalHeaderLabels([
            tr("ScrapTypeDialog", col) for col in COLUMN_KEYS
        ])
        self._legend_lbl.setText(tr(
            "ScrapTypeDialog",
            "Акт — реакция активна (редактируется в режиме разработчика). "
            "МБ/Шл/Д/Т — влияние на материальный баланс / шлак / дутьё / тепло "
            "(только просмотр)."
        ))
        self.addTypeButton.setText(tr("ScrapTypeDialog", "+ Добавить"))
        self.delTypeButton.setText(tr("ScrapTypeDialog", "- Удалить"))
        self.closeButton.setText(tr("ScrapTypeDialog", "Закрыть"))

    def refresh_language(self):
        self.retranslate_ui()

    def _apply_theme(self):
        if app_theme is None or get_theme is None:
            return
        try:
            theme = get_theme()
            self.setPalette(app_theme.palette(theme))
            self.table.setStyleSheet(app_theme.table_style(theme))
        except Exception:
            pass

    def load_scrap_types(self):
        try:
            DB = self._connect()
            cur = DB.cursor()
            cur.execute("SELECT idScrapType, ScrapTypeName FROM scraptype ORDER BY idScrapType;")
            rows = cur.fetchall()
            cur.close(); DB.close()
        except mc.Error as err:
            self._error(err)
            return
        self.typeList.blockSignals(True)
        self.typeList.clear()
        for type_id, name in rows:
            item = QtWidgets.QListWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, type_id)
            self.typeList.addItem(item)
        self.typeList.blockSignals(False)
        if self.typeList.count():
            self.typeList.setCurrentRow(0)

    def _current_type_id(self):
        item = self.typeList.currentItem()
        return item.data(QtCore.Qt.UserRole) if item else None

    def _on_type_item_changed(self, current, _previous=None):
        if current is not None:
            self.on_type_selected(current.data(QtCore.Qt.UserRole))

    def on_type_selected(self, type_id):
        if type_id is None:
            return
        try:
            DB = self._connect()
            cur = DB.cursor()
            cur.execute("""
                SELECT r.idReaction, r.ReactionNumber, r.ElementSymbol, r.ReactionEquation,
                       r.AffectsMaterialBalance, r.AffectsSlag, r.AffectsBlast, r.AffectsHeatBalance,
                       COALESCE(str.IsActive, 0)      AS IsActive,
                       COALESCE(str.CO_Fraction, 0.9) AS CO_Fraction
                FROM reaction r
                LEFT JOIN scraptype_reaction str
                       ON r.idReaction = str.Reaction_idReaction
                      AND str.ScrapType_idScrapType = %s
                ORDER BY r.ReactionNumber
            """, (type_id,))
            rows = cur.fetchall()
            cur.close(); DB.close()
        except mc.Error as err:
            self._error(err)
            return
        self._populate_table(rows)

    def _populate_table(self, rows):
        self.table.setRowCount(0)
        for r in rows:
            (id_reaction, number, element, equation,
             aff_mb, aff_slag, aff_blast, aff_heat,
             is_active, co_fraction) = r
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, COL_NUMBER,   self._ro_item(str(number)))
            self.table.setItem(row, COL_EQUATION, self._ro_item(equation))

            chk = QtWidgets.QCheckBox()
            chk.setChecked(bool(is_active))
            chk.setEnabled(self.editable)
            chk.toggled.connect(partial(self.on_reaction_toggled, id_reaction))
            self.table.setCellWidget(row, COL_ACTIVE, self._center(chk))

            if element in CARBON_ELEMENTS:
                spin = QtWidgets.QDoubleSpinBox()
                spin.setRange(0.0, 1.0)
                spin.setSingleStep(0.05)
                spin.setDecimals(2)
                spin.setValue(float(co_fraction))
                spin.setEnabled(self.editable)
                spin.valueChanged.connect(partial(self.on_co_fraction_changed, id_reaction))
                self.table.setCellWidget(row, COL_CO, self._center(spin))
            else:
                self.table.setItem(row, COL_CO, self._ro_item("—"))

            self.table.setItem(row, COL_MB,   self._flag_item(aff_mb))
            self.table.setItem(row, COL_SLAG, self._flag_item(aff_slag))
            self.table.setItem(row, COL_BLAST, self._flag_item(aff_blast))
            self.table.setItem(row, COL_HEAT, self._flag_item(aff_heat))

    @staticmethod
    def _ro_item(text):
        item = QtWidgets.QTableWidgetItem(str(text))
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        return item

    @staticmethod
    def _flag_item(value):
        item = QtWidgets.QTableWidgetItem("✓" if value else "")
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        return item

    @staticmethod
    def _center(widget):
        holder = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(holder)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(QtCore.Qt.AlignCenter)
        lay.addWidget(widget)
        return holder

    def on_reaction_toggled(self, reaction_id, checked):
        if not self.editable:
            return
        type_id = self._current_type_id()
        if type_id is None:
            return
        try:
            DB = self._connect()
            cur = DB.cursor()
            cur.execute("""
                INSERT INTO scraptype_reaction (ScrapType_idScrapType, Reaction_idReaction, IsActive, CO_Fraction)
                VALUES (%s, %s, %s, 0.9)
                ON DUPLICATE KEY UPDATE IsActive = VALUES(IsActive)
            """, (type_id, reaction_id, 1 if checked else 0))
            DB.commit()
            cur.close(); DB.close()
        except mc.Error as err:
            self._error(err)

    def on_co_fraction_changed(self, reaction_id, value):
        if not self.editable:
            return
        type_id = self._current_type_id()
        if type_id is None:
            return
        try:
            DB = self._connect()
            cur = DB.cursor()
            cur.execute("""
                INSERT INTO scraptype_reaction (ScrapType_idScrapType, Reaction_idReaction, IsActive, CO_Fraction)
                VALUES (%s, %s, 1, %s)
                ON DUPLICATE KEY UPDATE CO_Fraction = VALUES(CO_Fraction)
            """, (type_id, reaction_id, float(value)))
            DB.commit()
            cur.close(); DB.close()
        except mc.Error as err:
            self._error(err)

    def add_scrap_type(self):
        if not self.editable:
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self,
            tr("ScrapTypeDialog", "Новый тип лома"),
            tr("ScrapTypeDialog", "Название типа:"),
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        try:
            DB = self._connect()
            cur = DB.cursor()
            cur.execute("INSERT INTO scraptype (ScrapTypeName, Description) VALUES (%s, %s)", (name, ""))
            new_id = cur.lastrowid
            cur.execute("""
                INSERT INTO scraptype_reaction (ScrapType_idScrapType, Reaction_idReaction, IsActive, CO_Fraction)
                SELECT %s, Reaction_idReaction, IsActive, CO_Fraction
                FROM scraptype_reaction
                WHERE ScrapType_idScrapType = 1
            """, (new_id,))
            DB.commit()
            cur.close(); DB.close()
        except mc.Error as err:
            self._error(err)
            return
        self.load_scrap_types()
        self._select_type(new_id)

    def delete_scrap_type(self):
        if not self.editable:
            return
        type_id = self._current_type_id()
        if type_id is None:
            return
        if type_id == 1:
            self._warn(tr("ScrapTypeDialog", "Стандартный тип лома (id=1) удалить нельзя."))
            return
        try:
            DB = self._connect()
            cur = DB.cursor()
            cur.execute("SELECT COUNT(*) FROM scrapdata WHERE ScrapType_idScrapType = %s", (type_id,))
            used = cur.fetchone()[0]
            if used:
                cur.close(); DB.close()
                self._warn(tr(
                    "ScrapTypeDialog",
                    "Тип лома используется в записях лома (scrapdata) и не может быть удалён."
                ))
                return
            cur.execute("DELETE FROM scraptype_reaction WHERE ScrapType_idScrapType = %s", (type_id,))
            cur.execute("DELETE FROM scraptype WHERE idScrapType = %s", (type_id,))
            DB.commit()
            cur.close(); DB.close()
        except mc.Error as err:
            self._error(err)
            return
        self.load_scrap_types()

    def _select_type(self, type_id):
        for i in range(self.typeList.count()):
            if self.typeList.item(i).data(QtCore.Qt.UserRole) == type_id:
                self.typeList.setCurrentRow(i)
                return

    def _error(self, err):
        msg_critical(
            self,
            "Ошибка",
            "Ошибка работы с базой данных",
            str(err),
        )

    def _warn(self, text):
        msg_warning(self, "Внимание", text)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dlg = ScrapTypeDialog("localhost", "root", "root", editable=True)
    dlg.show()
    sys.exit(app.exec_())
