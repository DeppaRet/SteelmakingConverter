"""Диалог просмотра полной матрицы стехиометрических коэффициентов.

Строки  — химические соединения (реагенты и продукты всех 30 реакций).
Колонки — реакции (номер 1-30; полное уравнение доступно во всплывающей подсказке).
Значение: стехиометрический коэффициент со знаком
          (отрицательный → расходуется, положительный → образуется).
Последний столбец «Итого» — количество реакций, в которых участвует данное вещество.
Последняя строка «Итого» — количество веществ, задействованных в данной реакции.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import mysql.connector as mc

try:
    import app_theme
    from theme_settings import get_theme
except Exception:
    app_theme = None
    get_theme = None

# ── Сопоставление ElementSymbol → строка-вещество для первичного реагента ──────
ELEM_TO_ROW: dict[str, str] = {
    "C_CO":       "C",
    "C_CO2":      "C",
    "C_H2":       "C",
    "CO_burn":    "CO",
    "Si":         "Si",
    "SiO2_2CaO":  "SiO2",
    "SiO2_2FeO":  "SiO2",
    "Mn":         "Mn",
    "Mn_S":       "Mn",
    "Mn_FeO":     "Mn",
    "Fe_FeO":     "Fe",
    "Fe_Fe3O4":   "Fe",
    "Fe_Fe2O3":   "Fe",
    "P":          "P",
    "P_alt":      "P",
    "P_FeO_CaO":  "P",
    "P2O5_3CaO":  "P2O5",
    "P2O5_4CaO":  "P2O5",
    "Cr":         "Cr",
    "Al":         "Al",
    "Ca_CaO":     "Ca",
    "Ca_S":       "Ca",
    "Ca_FeO":     "Ca",
    "CaO_CO2":    "CaO",
    "Ti":         "Ti",
    "V":          "V",
    "S_SO2":      "S",
    "Mg_S":       "Mg",
    "H2_O2":      "H2",
    "FeS_CaO":    "FeS",
}

# ── Дополнительные реагенты (помимо основного элемента и O2) ───────────────────
EXTRA_REACTANTS: dict[str, list[tuple[str, float]]] = {
    "Mg_S":       [("S",   -1)],
    "Mn_S":       [("S",   -1)],
    "Ca_S":       [("S",   -1)],
    "Ca_FeO":     [("FeO", -1)],
    "Mn_FeO":     [("FeO", -1)],
    "P2O5_3CaO":  [("CaO", -3)],
    "P2O5_4CaO":  [("CaO", -4)],
    "SiO2_2CaO":  [("CaO", -2)],
    "SiO2_2FeO":  [("FeO", -2)],
    "P_FeO_CaO":  [("FeO", -5), ("CaO", -3)],
    "CaO_CO2":    [("CO2", -1)],
    "C_H2":       [("H2",  -2)],
    "FeS_CaO":    [("CaO", -1)],
}

# ── Дополнительные продукты (помимо основного продукта) ───────────────────────
EXTRA_PRODUCTS: dict[str, list[tuple[str, float]]] = {
    "Ca_FeO":    [("Fe", +1)],
    "Mn_FeO":   [("Fe", +1)],
    "P_FeO_CaO": [("Fe", +5)],
    "FeS_CaO":  [("FeO", +1)],
}

# ── Желаемый порядок строк (вещества) ─────────────────────────────────────────
SPECIES_ORDER: list[str] = [
    "C", "O2", "CO", "Si", "Mn", "Fe", "P", "Cr", "Al", "Ca", "Ti", "V",
    "S", "Mg", "H2", "FeS",
    "CO2", "SiO2", "MnO", "FeO", "Fe3O4", "Fe2O3", "P2O5",
    "Cr2O3", "Al2O3", "CaO", "TiO2", "V2O5", "SO2",
    "MgS", "MnS", "CaS",
    "3CaO*P2O5", "4CaO*P2O5", "2CaO*SiO2", "2FeO*SiO2",
    "CaCO3", "CH4", "H2O",
]

# ── Цвета текста в ячейках (фон наследуется от темы) ─────────────────────────
# Достаточно яркие, чтобы читаться и на светлом, и на тёмном фоне
CLR_REACTANT = QtGui.QColor(220,  80,  80)   # красный — расходуется
CLR_PRODUCT  = QtGui.QColor( 80, 200, 100)   # зелёный — образуется
CLR_ZERO_FG  = QtGui.QColor(110, 110, 110)   # серый текст «—»


class StoichiometryMatrixDialog(QtWidgets.QDialog):
    """Диалог просмотра матрицы стехиометрических коэффициентов."""

    def __init__(self, db_host: str, db_login: str, db_pass: str,
                 parent=None):
        super().__init__(parent)
        self._db_host  = db_host
        self._db_login = db_login
        self._db_pass  = db_pass

        self.setWindowTitle("Матрица стехиометрических коэффициентов")
        self.resize(1500, 700)
        self._build_ui()
        self._apply_theme()
        self._load()

    # ── Применение темы оформления ────────────────────────────────────────────
    def _apply_theme(self):
        if app_theme is None or get_theme is None:
            return
        try:
            theme = get_theme()
            self.setPalette(app_theme.palette(theme))
            self.table.setStyleSheet(app_theme.table_style(theme))
        except Exception:
            pass

    # ── Подключение к БД ──────────────────────────────────────────────────────
    def _connect(self):
        return mc.connect(
            host=self._db_host,
            user=self._db_login,
            password=self._db_pass,
            database="regimdata",
        )

    # ── Построение интерфейса ─────────────────────────────────────────────────
    def _build_ui(self):
        vbox = QtWidgets.QVBoxLayout(self)

        info = QtWidgets.QLabel(
            "Стехиометрическая матрица реакций.  "
            "Строки — химические соединения; столбцы — реакции "
            "(полное уравнение — во всплывающей подсказке на заголовке столбца).  "
            "Красный — расходуется, зелёный — образуется.  "
            "\u03a3 (столбец) — кол-во реакций с данным веществом; "
            "\u03a3 (строка) — кол-во веществ в данной реакции."
        )
        info.setWordWrap(True)
        vbox.addWidget(info)

        self.table = QtWidgets.QTableWidget()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.horizontalHeader().setDefaultSectionSize(38)
        vbox.addWidget(self.table, stretch=1)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        btn_close = QtWidgets.QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        vbox.addLayout(btn_row)

    # ── Загрузка данных из БД ─────────────────────────────────────────────────
    def _load(self):
        try:
            db  = self._connect()
            cur = db.cursor()
            cur.execute("""
                SELECT ReactionNumber, ElementSymbol, ReactionEquation,
                       nu_Element, nu_O2, nu_Product, ProductFormula
                FROM reaction
                ORDER BY ReactionNumber
            """)
            db_rows = cur.fetchall()
            cur.close()
            db.close()
        except mc.Error as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка БД", str(e))
            return
        self._populate(db_rows)

    # ── Построение матрицы и заполнение таблицы ───────────────────────────────
    def _populate(self, db_rows):
        n_rxn = len(db_rows)

        # matrix[species][col_index] = coefficient
        matrix: dict[str, dict[int, float]] = {}
        equations: list[tuple[int, str]] = []

        def add(species: str, col: int, coeff: float):
            if coeff == 0:
                return
            if species not in matrix:
                matrix[species] = {}
            matrix[species][col] = matrix[species].get(col, 0.0) + coeff

        for i, row in enumerate(db_rows):
            number, el_sym, equation, nu_el, nu_o2, nu_pr, product = row
            equations.append((number, equation or ""))

            el_row = ELEM_TO_ROW.get(el_sym, el_sym)

            # Основной реагент
            add(el_row, i, -float(nu_el))

            # O2
            if nu_o2:
                add("O2", i, -float(nu_o2))

            # Основной продукт
            if product:
                add(product, i, float(nu_pr))

            # Дополнительные реагенты/продукты
            for sp, c in EXTRA_REACTANTS.get(el_sym, []):
                add(sp, i, c)
            for sp, c in EXTRA_PRODUCTS.get(el_sym, []):
                add(sp, i, c)

        # Порядок строк: сначала из SPECIES_ORDER, потом всё остальное по алфавиту
        present = set(matrix.keys())
        ordered_species = [s for s in SPECIES_ORDER if s in present]
        ordered_species += sorted(present - set(ordered_species))

        n_sp = len(ordered_species)

        # Таблица: n_rxn столбцов + 1 (Σ)  |  n_sp строк + 1 (Σ)
        self.table.setColumnCount(n_rxn + 1)
        self.table.setRowCount(n_sp + 1)

        # Заголовки столбцов — номера реакций
        for i, (num, eq) in enumerate(equations):
            h = QtWidgets.QTableWidgetItem(str(num))
            h.setToolTip(eq)
            self.table.setHorizontalHeaderItem(i, h)
        self.table.setHorizontalHeaderItem(n_rxn, QtWidgets.QTableWidgetItem("Σ"))

        # Заголовки строк — названия веществ
        for j, sp in enumerate(ordered_species):
            self.table.setVerticalHeaderItem(j, QtWidgets.QTableWidgetItem(sp))
        self.table.setVerticalHeaderItem(n_sp, QtWidgets.QTableWidgetItem("Σ"))

        rxn_counts = [0] * n_rxn  # сколько веществ участвуют в каждой реакции

        for j, sp in enumerate(ordered_species):
            sp_count = 0
            for i in range(n_rxn):
                coeff = matrix[sp].get(i, 0.0)
                if coeff == 0.0:
                    item = self._dash_item()
                else:
                    item = self._coeff_item(coeff)
                    sp_count += 1
                    rxn_counts[i] += 1
                self.table.setItem(j, i, item)
            self.table.setItem(j, n_rxn, self._total_item(str(sp_count)))

        # Итоговая строка
        for i in range(n_rxn):
            self.table.setItem(n_sp, i, self._total_item(str(rxn_counts[i])))
        self.table.setItem(n_sp, n_rxn,
                           self._total_item(str(sum(1 for d in matrix.values()
                                                    for c in d.values() if c != 0))))

        # Ширина столбцов и высота строк по содержимому
        self.table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

    # ── Вспомогательные методы создания ячеек ────────────────────────────────
    @staticmethod
    def _fmt(v: float) -> str:
        """Форматирует коэффициент: целое или дробное; добавляет «+» для ≥ 0."""
        if v == int(v):
            return f"{int(v):+d}"
        return f"{v:+g}"

    @classmethod
    def _coeff_item(cls, v: float) -> QtWidgets.QTableWidgetItem:
        item = QtWidgets.QTableWidgetItem(cls._fmt(v))
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        item.setForeground(QtGui.QBrush(CLR_PRODUCT if v > 0 else CLR_REACTANT))
        item.setBackground(QtGui.QBrush())          # прозрачный фон — тема сама красит
        return item

    @staticmethod
    def _dash_item() -> QtWidgets.QTableWidgetItem:
        item = QtWidgets.QTableWidgetItem("—")
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        item.setForeground(QtGui.QBrush(CLR_ZERO_FG))
        item.setBackground(QtGui.QBrush())          # прозрачный фон
        return item

    @staticmethod
    def _total_item(text: str) -> QtWidgets.QTableWidgetItem:
        item = QtWidgets.QTableWidgetItem(text)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        item.setBackground(QtGui.QBrush())          # прозрачный фон
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        return item
