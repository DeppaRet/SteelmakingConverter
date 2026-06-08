"""Диалог управления типами лома и матрицей стехиометрических реакций.

Режимы:
- editable=False (оператор): только просмотр. Чекбоксы IsActive, спинбоксы
  CO_Fraction отключены; кнопки добавления/удаления типов скрыты.
- editable=True (разработчик): полное редактирование матрицы и типов лома.

Флаги влияния (МБ/Шл/Д/Т) во всех режимах доступны только для просмотра —
они задаются при заполнении БД.
"""
from functools import partial

from PyQt5 import QtCore, QtWidgets
import mysql.connector as mc

try:
    import app_theme
    from theme_settings import get_theme
except Exception:  # pragma: no cover - тема необязательна
    app_theme = None
    get_theme = None

CARBON_ELEMENTS = ("C_CO", "C_CO2")

COLUMNS = ["№", "Уравнение", "Акт", "Доля CO", "МБ", "Шл", "Д", "Т"]
COL_NUMBER, COL_EQUATION, COL_ACTIVE, COL_CO, COL_MB, COL_SLAG, COL_BLAST, COL_HEAT = range(8)


class ScrapTypeDialog(QtWidgets.QDialog):
    def __init__(self, db_host, db_login, db_pass, editable=False, parent=None):
        super().__init__(parent)
        self.db_host = db_host
        self.db_login = db_login
        self.db_pass = db_pass
        self.editable = editable

        self.setWindowTitle(
            "Управление типами лома и матрицей реакций"
            if editable else "Типы лома и матрица реакций (просмотр)"
        )
        self.resize(900, 600)

        self._build_ui()
        self.load_scrap_types()
        self._apply_theme()

    # ── Подключение к БД ────────────────────────────────────────────────
    def _connect(self):
        return mc.connect(
            host=self.db_host, user=self.db_login,
            password=self.db_pass, database="regimdata"
        )

    # ── Построение интерфейса ───────────────────────────────────────────
    def _build_ui(self):
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Левая панель: типы лома
        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Типы лома"))
        self.typeList = QtWidgets.QListWidget()
        self.typeList.currentItemChanged.connect(self._on_type_item_changed)
        left.addWidget(self.typeList, stretch=1)

        self.addTypeButton = QtWidgets.QPushButton("+ Добавить")
        self.addTypeButton.clicked.connect(self.add_scrap_type)
        self.delTypeButton = QtWidgets.QPushButton("- Удалить")
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

        # Правая панель: таблица реакций
        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("Реакции для выбранного типа лома"))
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(COL_EQUATION, QtWidgets.QHeaderView.Stretch)
        right.addWidget(self.table, stretch=1)

        legend = QtWidgets.QLabel(
            "Акт — реакция активна (редактируется в режиме разработчика). "
            "МБ/Шл/Д/Т — влияние на материальный баланс / шлак / дутьё / тепло "
            "(только просмотр)."
        )
        legend.setWordWrap(True)
        right.addWidget(legend)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        self.closeButton = QtWidgets.QPushButton("Закрыть")
        self.closeButton.clicked.connect(self.accept)
        btn_row.addWidget(self.closeButton)
        right.addLayout(btn_row)

        root.addLayout(right, stretch=1)

    def _apply_theme(self):
        if app_theme is None or get_theme is None:
            return
        try:
            theme = get_theme()
            self.setPalette(app_theme.palette(theme))
            self.table.setStyleSheet(app_theme.table_style(theme))
        except Exception:
            pass

    # ── Типы лома ───────────────────────────────────────────────────────
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

    # ── Загрузка реакций для типа ───────────────────────────────────────
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

            self.table.setItem(row, COL_NUMBER, self._ro_item(str(number)))
            self.table.setItem(row, COL_EQUATION, self._ro_item(equation))

            # IsActive — редактируемый чекбокс (в просмотре отключён)
            chk = QtWidgets.QCheckBox()
            chk.setChecked(bool(is_active))
            chk.setEnabled(self.editable)
            chk.toggled.connect(partial(self.on_reaction_toggled, id_reaction))
            self.table.setCellWidget(row, COL_ACTIVE, self._center(chk))

            # CO_Fraction — спинбокс только для углеродных реакций
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

            self.table.setItem(row, COL_MB, self._flag_item(aff_mb))
            self.table.setItem(row, COL_SLAG, self._flag_item(aff_slag))
            self.table.setItem(row, COL_BLAST, self._flag_item(aff_blast))
            self.table.setItem(row, COL_HEAT, self._flag_item(aff_heat))
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(COL_EQUATION, QtWidgets.QHeaderView.Stretch)

    @staticmethod
    def _ro_item(text):
        item = QtWidgets.QTableWidgetItem(text)
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

    # ── Редактирование (только при editable=True) ───────────────────────
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
        name, ok = QtWidgets.QInputDialog.getText(self, "Новый тип лома", "Название типа:")
        if not ok or not name.strip():
            return
        name = name.strip()
        try:
            DB = self._connect()
            cur = DB.cursor()
            cur.execute("INSERT INTO scraptype (ScrapTypeName, Description) VALUES (%s, %s)", (name, ""))
            new_id = cur.lastrowid
            # Копируем матрицу реакций от стандартного типа (id=1)
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
            self._warn("Стандартный тип лома (id=1) удалить нельзя.")
            return
        try:
            DB = self._connect()
            cur = DB.cursor()
            cur.execute("SELECT COUNT(*) FROM scrapdata WHERE ScrapType_idScrapType = %s", (type_id,))
            used = cur.fetchone()[0]
            if used:
                cur.close(); DB.close()
                self._warn("Тип лома используется в записях лома (scrapdata) и не может быть удалён.")
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

    # ── Сообщения ───────────────────────────────────────────────────────
    def _error(self, err):
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Critical)
        box.setWindowTitle("Ошибка")
        box.setText("Ошибка работы с базой данных")
        box.setInformativeText(str(err))
        box.exec_()

    def _warn(self, text):
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle("Внимание")
        box.setText(text)
        box.exec_()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dlg = ScrapTypeDialog("localhost", "root", "root", editable=True)
    dlg.show()
    sys.exit(app.exec_())
