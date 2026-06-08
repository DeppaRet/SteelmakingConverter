# Cursor Prompt: Интеграция матрицы стехиометрических коэффициентов в SteelmakingConverter

## Контекст проекта

Приложение **SteelmakingConverter** — PyQt5-программа расчёта кислородно-конвертерной плавки по методике НФ МИСиС (Шаповалов А.Н., файл `OperForm.py`). Расчёт идёт по цепочке:

1. `calcMetalChargeClicked()` — состав металлошихты (чугун + лом)
2. `calcTableClick()` — расчёт окисления примесей (Таблица 5 методички)
3. `slagCalcClicked()` — состав и количество шлака (Таблица 8)
4. `blastCalcClicked()` — расход дутья (раздел 7)
5. `MaterialBalanceCalcClicked()` — материальный баланс (раздел 8)
6. `HeatBalanceCalcClicked()` — тепловой баланс (раздел 9)

БД: MySQL, база `regimdata`. Ключевые таблицы: `scrapcomposition`, `scrapdata`, `mode`, `fluxecomposition`, `fluxedata`.

---

## Суть задачи

В `calcTableClick()` стехиометрические коэффициенты **зашиты как литералы**:

```python
carbonToCOOxygen   = carbonToCO  * 16/12        # жёсткий коэффициент
siliconOxygen      = siliconRemove * 32/28       # жёсткий коэффициент
manganesOxygen     = manganeseRemove * 16/55     # жёсткий коэффициент
phosphorOxygen     = phosphorRemove * 5*16/2/31  # жёсткий коэффициент
```

Нужно:
1. Вынести коэффициенты в БД, привязав их к **типу лома**
2. Добавить поддержку новых элементов в ломе: **Cr, V, Al, Ti**
3. Переписать расчётные функции через **итерацию по реакциям из БД**
4. Создать **UI-диалог** управления типами лома и их реакциями

---

## ЧАСТЬ 1: Изменения в базе данных (MySQL, `regimdata`)

### 1.1 Новая таблица `scraptype`

```sql
CREATE TABLE scraptype (
    idScrapType   INT AUTO_INCREMENT PRIMARY KEY,
    ScrapTypeName VARCHAR(100) NOT NULL UNIQUE,
    Description   TEXT
);
INSERT INTO scraptype (ScrapTypeName, Description)
VALUES ('Стандартный', 'Низкоуглеродистая сталь обычного качества, без легирующих');
```

### 1.2 Новая таблица `reaction` — справочник всех реакций

```sql
CREATE TABLE reaction (
    idReaction       INT AUTO_INCREMENT PRIMARY KEY,
    ElementSymbol    VARCHAR(5)   NOT NULL,  -- 'C_CO','C_CO2','Si','Mn','P','S','Cr','V','Al','Ti'
    ElementName      VARCHAR(50)  NOT NULL,
    ReactionEquation VARCHAR(200),
    nu_Element       FLOAT NOT NULL,         -- стехиометрический коэффициент элемента
    M_Element        FLOAT NOT NULL,         -- молярная масса элемента, г/моль
    nu_O2            FLOAT NOT NULL,         -- коэффициент O2
    M_O2             FLOAT DEFAULT 32.0,
    nu_Product       FLOAT NOT NULL,         -- коэффициент продукта (оксида)
    M_Product        FLOAT NOT NULL,         -- молярная масса продукта, г/моль
    ProductFormula   VARCHAR(20),
    HeatEffect_kJ_kg FLOAT DEFAULT 0.0,      -- кДж на кг удалённого элемента
    ProducesGas      TINYINT(1) DEFAULT 0,   -- 1 если CO/CO2
    NeedsO2          TINYINT(1) DEFAULT 1    -- 0 для серы (FeS+CaO=CaS+FeO)
);

INSERT INTO reaction VALUES
(NULL,'C_CO', 'Углерод→CO',   '[C]+0.5{O2}={CO}',     1,12.0, 0.5,32.0, 1,28.0,  'CO',   14770.0,1,1),
(NULL,'C_CO2','Углерод→CO2',  '[C]+{O2}={CO2}',        1,12.0, 1.0,32.0, 1,44.0,  'CO2',  0.0,    1,1),
(NULL,'Si',  'Кремний',       '[Si]+{O2}=(SiO2)',      1,28.0, 1.0,32.0, 1,60.0,  'SiO2', 26970.0,0,1),
(NULL,'Mn',  'Марганец',      '[Mn]+0.5{O2}=(MnO)',    1,55.0, 0.5,32.0, 1,71.0,  'MnO',  7000.0, 0,1),
(NULL,'P',   'Фосфор',        '4/5[P]+{O2}=2/5(P2O5)',0.8,31.0,1.0,32.0,0.4,142.0,'P2O5', 21730.0,0,1),
(NULL,'S',   'Сера→CaS',      '[FeS]+(CaO)=(CaS)+(FeO)',1,32.0,0.0,32.0,1,72.0,  'CaS',  0.0,    0,0),
(NULL,'Cr',  'Хром',          '2[Cr]+1.5{O2}=(Cr2O3)',2,52.0, 1.5,32.0, 1,152.0, 'Cr2O3',11730.0,0,1),
(NULL,'V',   'Ванадий',       '2[V]+2.5{O2}=(V2O5)',  2,51.0, 2.5,32.0, 1,182.0, 'V2O5', 18420.0,0,1),
(NULL,'Al',  'Алюминий',      '2[Al]+1.5{O2}=(Al2O3)',2,27.0, 1.5,32.0, 1,102.0, 'Al2O3',31090.0,0,1),
(NULL,'Ti',  'Титан',         '[Ti]+{O2}=(TiO2)',      1,48.0, 1.0,32.0, 1,80.0,  'TiO2', 19700.0,0,1);
```

### 1.3 Новая таблица `scraptype_reaction` — привязка реакций к типу лома

```sql
CREATE TABLE scraptype_reaction (
    idScrapTypeReaction   INT AUTO_INCREMENT PRIMARY KEY,
    ScrapType_idScrapType INT NOT NULL,
    Reaction_idReaction   INT NOT NULL,
    IsActive              TINYINT(1) DEFAULT 1,
    CO_Fraction           FLOAT DEFAULT 0.9,  -- доля C→CO (для C_CO/C_CO2)
    FOREIGN KEY (ScrapType_idScrapType) REFERENCES scraptype(idScrapType),
    FOREIGN KEY (Reaction_idReaction)   REFERENCES reaction(idReaction),
    UNIQUE KEY uq (ScrapType_idScrapType, Reaction_idReaction)
);
-- Стандартный тип: C, Si, Mn, P, S
INSERT INTO scraptype_reaction (ScrapType_idScrapType, Reaction_idReaction, IsActive, CO_Fraction)
SELECT 1, idReaction, 1, 0.9 FROM reaction
WHERE ElementSymbol IN ('C_CO','C_CO2','Si','Mn','P','S');
```

### 1.4 Расширение существующих таблиц

```sql
-- Новые элементы в составе лома
ALTER TABLE scrapcomposition
    ADD COLUMN ScrapCr FLOAT DEFAULT 0.0,
    ADD COLUMN ScrapV  FLOAT DEFAULT 0.0,
    ADD COLUMN ScrapAl FLOAT DEFAULT 0.0,
    ADD COLUMN ScrapTi FLOAT DEFAULT 0.0;

-- Привязка типа лома к записи scrapdata
ALTER TABLE scrapdata
    ADD COLUMN ScrapType_idScrapType INT DEFAULT 1,
    ADD FOREIGN KEY (ScrapType_idScrapType) REFERENCES scraptype(idScrapType);
```

---

## ЧАСТЬ 2: Изменения в коде `OperForm.py`

### 2.1 Новый класс `Reaction` и функция загрузки из БД

Добавить сразу после класса `FluxeComposition`:

```python
class Reaction:
    """Строка матрицы стехиометрических коэффициентов."""
    def __init__(self, row):
        self.id           = row[0]
        self.element      = row[1]   # 'C_CO', 'Si', 'Mn', ...
        self.name         = row[2]
        self.nu_element   = row[4]
        self.M_element    = row[5]
        self.nu_O2        = row[6]
        self.M_O2         = row[7]
        self.nu_product   = row[8]
        self.M_product    = row[9]
        self.product      = row[10]
        self.heat_kJ_kg   = row[11]
        self.produces_gas = bool(row[12])
        self.needs_O2     = bool(row[13])
        self.co_fraction  = 0.9  # только для C_CO / C_CO2

    def oxygen_per_kg_element(self):
        """Формула 12 методички: расход O₂ (кг) на 1 кг элемента."""
        if not self.needs_O2:
            return 0.0
        return (self.nu_O2 * self.M_O2) / (self.nu_element * self.M_element)

    def oxygen_m3_per_kg_element(self):
        return self.oxygen_per_kg_element() * 22.4 / 32.0

    def product_per_kg_element(self):
        """Формула 14 методички: масса оксида (кг) на 1 кг элемента."""
        return (self.nu_product * self.M_product) / (self.nu_element * self.M_element)


def load_reactions_for_scrap_type(scrap_type_id, db_host, db_login, db_pass):
    """Возвращает list[Reaction] для данного типа лома."""
    DB = mc.connect(host=db_host, user=db_login, password=db_pass, database="regimdata")
    cursor = DB.cursor()
    cursor.execute("""
        SELECT r.*, str.IsActive, str.CO_Fraction
        FROM reaction r
        JOIN scraptype_reaction str ON r.idReaction = str.Reaction_idReaction
        WHERE str.ScrapType_idScrapType = %s AND str.IsActive = 1
        ORDER BY r.idReaction;
    """, (scrap_type_id,))
    rows = cursor.fetchall()
    cursor.close(); DB.close()
    result = []
    for row in rows:
        r = Reaction(row)
        r.co_fraction = float(row[15])
        result.append(r)
    return result
```

### 2.2 Рефакторинг `calcTableClick()` — замена захардкоженных коэффициентов

Найти блок с `carbonToCOOxygen = ...` (строки ~720–760) и заменить на:

```python
# --- НАЧАЛО НОВОГО БЛОКА ---
scrap_type_id = getattr(self, 'current_scrap_type_id', 1)
reactions = load_reactions_for_scrap_type(scrap_type_id, DBhost, DBlogin, DBpass)

charge_elements = {
    'C_CO':  chemCarbonValue,   'C_CO2': chemCarbonValue,
    'Si':    chemSiliconValue,  'Mn':    chemManganesevalue,
    'P':     chemPhosphorValue, 'S':     chemSerumValue,
    'Cr':    getattr(self, 'scrapCr', 0.0),
    'V':     getattr(self, 'scrapV',  0.0),
    'Al':    getattr(self, 'scrapAl', 0.0),
    'Ti':    getattr(self, 'scrapTi', 0.0),
}
after_elements = {
    'C_CO': steelCarbonValue, 'C_CO2': 0.0,
    'Si': 0.0, 'Mn': manganeseAfter, 'P': phosphorAfter, 'S': serumAfter,
    'Cr': 0.0, 'V': 0.0, 'Al': 0.0, 'Ti': 0.0,
}

self.reaction_results = {}
total_O2_kg = total_O2_m3 = 0.0

for reaction in reactions:
    el = reaction.element
    if el not in charge_elements:
        continue
    if el == 'C_CO':
        g_removed = (charge_elements['C_CO'] - steelCarbonValue) * reaction.co_fraction
    elif el == 'C_CO2':
        g_removed = (charge_elements['C_CO'] - steelCarbonValue) * (1.0 - reaction.co_fraction)
    else:
        g_removed = max(0.0, charge_elements[el] - after_elements.get(el, 0.0))

    self.reaction_results[el] = {
        'removed':  g_removed,
        'O2_kg':    g_removed * reaction.oxygen_per_kg_element(),
        'O2_m3':    g_removed * reaction.oxygen_m3_per_kg_element(),
        'oxide_kg': g_removed * reaction.product_per_kg_element(),
        'product':  reaction.product,
        'is_gas':   reaction.produces_gas,
        'heat':     g_removed * reaction.heat_kJ_kg,
    }
    if reaction.needs_O2:
        total_O2_kg += self.reaction_results[el]['O2_kg']
        total_O2_m3 += self.reaction_results[el]['O2_m3']

self.total_O2_kg = total_O2_kg
self.total_O2_m3 = total_O2_m3
# Старые переменные для совместимости с OxidationTable (строки 0..5):
carbonToCO     = self.reaction_results.get('C_CO',  {}).get('removed', carbonRemove * 0.9)
carbonToCO2    = self.reaction_results.get('C_CO2', {}).get('removed', carbonRemove * 0.1)
carbonToCOOxygen  = self.reaction_results.get('C_CO',  {}).get('O2_kg', 0.0)
carbonToCO2Oxygen = self.reaction_results.get('C_CO2', {}).get('O2_kg', 0.0)
siliconOxygen     = self.reaction_results.get('Si',    {}).get('O2_kg', 0.0)
manganesOxygen    = self.reaction_results.get('Mn',    {}).get('O2_kg', 0.0)
phosphorOxygen    = self.reaction_results.get('P',     {}).get('O2_kg', 0.0)
summOxygen        = total_O2_kg
# ... остальное заполнение OxidationTable не трогать ...
# --- КОНЕЦ НОВОГО БЛОКА ---
```

### 2.3 Обновить `slagCalcClicked()` — добавить оксиды новых элементов

После строки `slagOthers = (oxidesManganes + oxidesPhosphor + oxidesSerum) * metalChargeWeight/100` добавить:

```python
# Оксиды новых элементов (Cr2O3, V2O5, Al2O3, TiO2) из reaction_results
if hasattr(self, 'reaction_results'):
    for el, res in self.reaction_results.items():
        if el in ('C_CO','C_CO2','Si','Mn','P','S'):
            continue  # уже учтены выше
        if not res['is_gas']:
            oxide_kg = res['oxide_kg'] * metalChargeWeight / 100.0
            if res['product'] == 'Al2O3':
                slagAl2O3 += oxide_kg
            else:
                slagOthers += oxide_kg
```

### 2.4 Обновить `HeatBalanceCalcClicked()` — тепловой эффект реакций

Заменить строку `HeatReactOfOxidation = (14770.0 * ...`:

```python
if hasattr(self, 'reaction_results'):
    HeatReactOfOxidation = (
        sum(res['heat'] for res in self.reaction_results.values())
        * float(self.MetalCharge.text()) * 10.0
    )
else:
    HeatReactOfOxidation = (14770.0*TotalRemovedCarbon + 26970.0*TotalRemovedSilicon +
                             7000.0*TotalRemovedMagn + 21730.0*TotalRemovedPhosph) * \
                            float(self.MetalCharge.text()) * 10.0
```

### 2.5 Обновить `chooseMods()` — загрузка типа лома и новых элементов

После блока чтения `scrapData` добавить:

```python
# Тип лома
cursor.execute("SELECT ScrapType_idScrapType FROM scrapdata WHERE idScrapData = %s;", (scrapId,))
row = cursor.fetchone()
self.current_scrap_type_id = row[0] if row else 1

# Новые элементы (индексы 6..9 после ALTER TABLE scrapcomposition)
self.scrapCr = float(scrapData[0][6]) if len(scrapData[0]) > 6 and scrapData[0][6] else 0.0
self.scrapV  = float(scrapData[0][7]) if len(scrapData[0]) > 7 and scrapData[0][7] else 0.0
self.scrapAl = float(scrapData[0][8]) if len(scrapData[0]) > 8 and scrapData[0][8] else 0.0
self.scrapTi = float(scrapData[0][9]) if len(scrapData[0]) > 9 and scrapData[0][9] else 0.0
```

---

## ЧАСТЬ 3: Изменения в интерфейсе (PyQt5)

### 3.1 Поля нового состава лома на главной форме

Добавить в раздел ввода лома:
- `QLabel("Тип лома:")` + `QComboBox(scrapTypeCombo)` — заполняется из `scraptype`
- `QLabel("Cr, %")` + `QLineEdit(scrapCrInput)`, аналогично V, Al, Ti

```python
def loadScrapTypeCombo(self):
    DB = mc.connect(host=DBhost, user=DBlogin, password=DBpass, database="regimdata")
    cursor = DB.cursor()
    cursor.execute("SELECT idScrapType, ScrapTypeName FROM scraptype ORDER BY idScrapType;")
    self.scrapTypeCombo.clear()
    for row in cursor.fetchall():
        self.scrapTypeCombo.addItem(row[1], userData=row[0])
    cursor.close(); DB.close()
```

Вызвать `loadScrapTypeCombo()` при запуске формы.

### 3.2 Новый файл `ScrapTypeDialog.py`

Создать отдельный файл с классом `ScrapTypeDialog(QDialog)`.

**Макет окна:**
```
┌──────────────────────────────────────────────────────────────┐
│  Управление типами лома и реакциями                          │
├─────────────────────┬────────────────────────────────────────┤
│ Типы лома           │ Реакции для выбранного типа            │
│ ┌─────────────────┐ │ ┌──────────────────────────────────┐   │
│ │ Стандартный     │ │ │ ☑ Углерод→CO   доля CO: [0.90]   │   │
│ │ Легированный    │ │ │ ☑ Углерод→CO2                    │   │
│ │ Инструментальный│ │ │ ☑ Кремний→SiO2                   │   │
│ └─────────────────┘ │ │ ☑ Марганец→MnO                   │   │
│ [+ Добавить]        │ │ ☑ Фосфор→P2O5                    │   │
│ [- Удалить]         │ │ ☑ Сера→CaS                       │   │
│                     │ │ ☐ Хром→Cr2O3                     │   │
│                     │ │ ☐ Ванадий→V2O5                   │   │
│                     │ │ ☐ Алюминий→Al2O3                 │   │
│                     │ │ ☐ Титан→TiO2                     │   │
│                     │ └──────────────────────────────────┘   │
│                     │ Уравнение: [C] + 0.5{O2} = {CO}       │
│                     │ Тепл. эффект: 14770 кДж/кг С           │
│                     │             [Сохранить]  [Отмена]      │
└─────────────────────┴────────────────────────────────────────┘
```

**Методы:**
- `load_scrap_types()` — SELECT из `scraptype`
- `on_type_selected(type_id)` — загружает реакции из `scraptype_reaction JOIN reaction`
- `on_reaction_toggled(reaction_id, checked)` — UPDATE `IsActive`
- `on_co_fraction_changed(value)` — UPDATE `CO_Fraction` для C_CO/C_CO2
- `add_scrap_type()` — INSERT в `scraptype`, скопировать реакции от id=1
- `delete_scrap_type()` — DELETE с проверкой (тип не должен использоваться в `scrapdata`)

### 3.3 Кнопка «Типы лома» в меню

```python
# В setupUi или в методе инициализации меню:
self.actionScrapTypes = QAction("Типы лома и реакции", self)
self.actionScrapTypes.triggered.connect(self.openScrapTypeDialog)
self.menubar.addAction(self.actionScrapTypes)

def openScrapTypeDialog(self):
    from ScrapTypeDialog import ScrapTypeDialog
    dialog = ScrapTypeDialog(DBhost, DBlogin, DBpass, parent=self)
    if dialog.exec_() == QDialog.Accepted:
        self.loadScrapTypeCombo()
```

### 3.4 Динамическое расширение `OxidationTable` для новых элементов

```python
def update_oxidation_table_rows(self):
    """Добавляет строки для Cr/V/Al/Ti если они ненулевые."""
    EXTRA = {'Cr':'Хром','V':'Ванадий','Al':'Алюминий','Ti':'Титан'}
    if not hasattr(self, 'reaction_results'):
        return
    for el, label in EXTRA.items():
        res = self.reaction_results.get(el)
        if not res or res['removed'] <= 0:
            continue
        row = self.OxidationTable.rowCount()
        self.OxidationTable.insertRow(row)
        self.OxidationTable.setItem(row, 0, QTableWidgetItem(label))
        self.OxidationTable.setItem(row, 3, QTableWidgetItem(str(round(res['removed'],  3))))
        self.OxidationTable.setItem(row, 4, QTableWidgetItem(str(round(res['O2_kg'],    3))))
        self.OxidationTable.setItem(row, 5, QTableWidgetItem(str(round(res['O2_m3'],    3))))
        self.OxidationTable.setItem(row, 6, QTableWidgetItem(str(round(res['oxide_kg'], 3))))
```

Вызывать `update_oxidation_table_rows()` в конце `calcTableClick()`.

---

## ЧАСТЬ 4: Что НЕ нужно менять

- **Степени удаления Mn/P/S** — эмпирические значения из методички, не зависят от стехиометрии
- **Формулы физического тепла** металла/шлака/газа (`PhysCastHeat`, `PhysGasHeat`, формулы 38-40)
- **`calcMetalChargeClicked()`** — баланс масс шихты
- **Работа с флюсами** (`FluxeComposition`, `getFluxeInMode()`)
- **Индексы 0..5 строк `OxidationTable`** для C/Si/Mn/P/S — не трогать, новые элементы добавляются снизу

---

## ЧАСТЬ 5: Порядок реализации

1. **SQL**: выполнить CREATE TABLE и ALTER TABLE из части 1
2. **Класс `Reaction`** + `load_reactions_for_scrap_type()` → в `OperForm.py`
3. **Рефакторинг расчётов**: `calcTableClick()` → `slagCalcClicked()` → `HeatBalanceCalcClicked()`
4. **`chooseMods()`**: добавить загрузку `current_scrap_type_id` и Cr/V/Al/Ti
5. **Создать `ScrapTypeDialog.py`**
6. **UI**: добавить `scrapTypeCombo`, поля Cr/V/Al/Ti, кнопку «Типы лома»
7. **Регрессионный тест**: при типе лома id=1 (стандартный) результаты должны совпадать с текущими

---

## Технические ограничения (строго соблюдать)

- Фреймворк: **PyQt5** (не PyQt6, не PySide)
- СУБД: **MySQL**, подключение через `mysql.connector`
- Глобальные переменные подключения: `DBhost`, `DBlogin`, `DBpass` — использовать везде
- Новые SQL-запросы писать с **параметризацией** `%s`, не f-string (безопасность)
- `ScrapTypeDialog` — строго в **отдельном файле** `ScrapTypeDialog.py`
- Не менять индексацию строк OxidationTable для элементов C/Si/Mn/P/S
