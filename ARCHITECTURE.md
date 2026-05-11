# Steelmaking Converter — Архитектура

Десктопное PyQt5-приложение для обучения операторов управлению сталеплавильным конвертером.
Роль-ориентированная навигация, расчётный движок плавки, MySQL-backend.

**3 роли пользователей · 3 MySQL-базы данных · 8 модулей Python · 6 Qt .ui-форм**

---

## Поток авторизации

| Шаг | Описание |
|-----|----------|
| Запуск | `main.py` → `QApplication` → `Ui_LoginForm.setupUi()` |
| Ввод данных | Пользователь вводит логин и пароль |
| Хэширование | `hashAuth.Hash.getHash(password)` → MD5 |
| Проверка роли | `SELECT Roles_idRoles FROM users WHERE Login=… AND Password=…` |
| Роль 1 | Открыть `AdminForm.Ui_AdminFom` |
| Роль 2 | Открыть `OperForm.Ui_OperatorForm` |
| Роль 3 | Открыть `DeveloperForm.Ui_Form` |
| Настройки | `SettingsButton` → `connSettings.Ui_ConnectionSettings` (`dev.ini`) |

---

## Модули программы

| Файл | Класс | Роль | Описание |
|------|-------|------|----------|
| `main.py` | `Ui_LoginForm` | Точка входа | Экран авторизации. Читает `dev.ini`, подключается к `users_db`, определяет роль и открывает нужную форму. |
| `AdminForm.py` | `Ui_AdminFom` | Роль 1 — Администратор | Управление пользователями (`users_db`) и справочными данными (`regimdata`). Экспорт таблиц в Excel через pandas. |
| `OperForm.py` | `Ui_OperatorForm` | Роль 2 — Оператор | Симулятор конвертерной плавки. Загрузка сценария, ввод параметров шихты, расчёт шлака / дутья / теплового и материального балансов. Асинхронные запросы через `WorkerThread(QThread)`. |
| `DeveloperForm.py` | `Ui_Form` | Роль 3 — Разработчик модели | Просмотр и редактирование справочных таблиц `regimdata`: режимы, стали, чугун, лом, флюсы, сценарии. |
| `connSettings.py` | `Ui_ConnectionSettings` | Настройки подключения | Диалог конфигурации MySQL (хост, порт, логин, пароль). Читает и сохраняет `dev.ini`. Кнопка теста соединения. |
| `AboutForm.py` | `Ui_Dialog` | О программе | Информационный диалог с описанием продукта и автором. |
| `hashAuth.py` | `Hash` | Аутентификация | Хэширование пароля через MD5 (`hashlib`) перед сравнением с БД. |
| `neuro.py` | *(закомментировано)* | Нейросетевой модуль | Заготовка Sequential-модели Keras (2 скрытых слоя по 128, ReLU). Вход — 20 параметров плавки, выход — 17 параметров металла и шлака. Отключён. |

---

## Слой GUI

Файлы `GUI/*.ui` — проекты Qt Designer. Из них генерируются `file*.py` через `pyuic5`.
Бизнес-логика живёт в основных модулях (`AdminForm.py`, `OperForm.py` и т.д.), которые переопределяют сгенерированные классы.

| Авто-генерированный файл | Источник / назначение |
|--------------------------|-----------------------|
| `fileAdmin.py` | Авто-генерация из `GUI/AdminForm.ui` (pyuic5) |
| `fileConn.py` | Авто-генерация из `GUI/ConnectionSettings.ui` |
| `filenameconverted.py` | Авто-генерация (предположительно `OperForm.ui`) |

---

## Базы данных MySQL

### users_db
- `users` (Login, Password, Roles_idRoles)
- `userroles` (idRoles, RoleName)

### regimdata
- `mode` (idMode, ModeName, …)
- `steeldata` + `steelcomposition` (C, S, P, Si)
- `caststeeldata` + `caststeelcomposition` (чугун: масса, T, C/S/P/Si/Mn)
- `scrapdata` + `scrapcomposition` (лом: масса, C/S/P/Si/Mn)
- `fluxedata` + `fluxecomposition` (CaO, SiO2, MgO, Fe2O3, FeO, MnO, Al2O3, CaCO3, MgCO3)
- `scenario` (ScanrioName, ScenarioTask, лимиты C/P/T, mode_idMode)
- `v_combined_data` (представление — сводные данные режима)

### ferroalloydb
- `ferroalloy` (Name, состав)

---

## Конфигурация и состояние

| Файл / объект | Назначение |
|---------------|------------|
| `dev.ini` | Хранит хост, логин, пароль MySQL. Читается через `configparser`. |
| `config.py` → `UserLogin` | Глобальная переменная с логином текущей сессии. |
| `createini.py` | Служебный скрипт для создания / тестирования `dev.ini` (не в продакшне). |
| `build_code.py` | Вспомогательный скрипт сборки. |
| `Data from programm.xlsx` | Экспорт таблицы режимов (AdminForm → pandas → openpyxl). |
| `Scenario.xlsx` | Экспорт таблицы сценариев (AdminForm → pandas → openpyxl). |

---

## Расчётный движок (OperForm) — обзор этапов

Форма оператора реализует пошаговый расчёт плавки. Каждый этап защищён флагом (`*Calcked`).
Тяжёлые операции с БД вынесены в `WorkerThread(QThread)` с сигналами `progress` / `result_scenario` / `result_mode` / `error`.

| Этап | Флаг | Описание |
|------|------|----------|
| Металлошихта | `metalChargeCalcked` | Расчёт масс чугуна и лома, состава шихты по C/Si/Mn/P/S |
| Таблица флюсов | `tableCalcked` | До 16 объектов `FluxeComposition` с составами CaO/SiO2/MgO/… |
| Шлак | `slagCalcked` | Расчёт состава и массы шлака |
| Дутьё | `blastCalcked` | Расчёт параметров кислородного дутья |
| Материальный баланс | `materialBalanceCalcked` | Сводный баланс масс входа и выхода |
| Тепловой баланс | `heatBalanceCalcked` | Тепловой баланс плавки |

---

## Функции OperForm.py — детальное описание

Класс `WorkerThread(QThread)` и класс `Ui_OperatorForm`.
Все расчётные функции выполняются последовательно: каждая проверяет флаг предыдущего этапа и при необходимости запускает его автоматически.

### WorkerThread — фоновый поток

| Метод | Сигналы | Описание |
|-------|---------|----------|
| `__init__(scenario, db_host, db_login, db_pass)` | — | Сохраняет параметры подключения и имя сценария. |
| `run()` | `progress(int)`, `result_scenario(str×4)`, `result_mode(str)`, `error(str)` | Выполняет два SQL-запроса к `regimdata`: загружает задание и лимиты (C, P, T) сценария, затем имя режима. Шаги прогресса: 0→10→40→70→90→100%. |

### Инициализация и загрузка данных

| Метод | Флаг/зависимость | Описание |
|-------|-----------------|----------|
| `getSettings()` | — | Читает `dev.ini` через `ConfigParser` и записывает `DBhost` / `DBlogin` / `DBpass` в глобальные переменные модуля. |
| `getModes()` | — | Загружает список сценариев (`regimdata.scenario`), режимов (`regimdata.mode`) и ферросплавов (`ferroalloydb.ferroalloy`) в соответствующие ComboBox-ы при старте формы. |
| `GetScenario()` | — | Ручная (синхронная) загрузка выбранного сценария: задание, лимиты C/P/T, имя режима → вызывает `chooseMods()`. |
| `GetScenarioExample()` | — | Устаревший вариант `GetScenario` (код закомментирован). Не используется. |
| `update_progress(value)` | slot ← `WorkerThread.progress` | Обновляет `QProgressBar scenarioProgress`. |
| `update_scenario(task, carbon, phosphor, temp)` | slot ← `WorkerThread.result_scenario` | Заполняет поля задания сценария и числовых лимитов. |
| `update_mode(mode)` | slot ← `WorkerThread.result_mode` | Устанавливает текущий режим в `ModeComboBox`. |
| `show_error(error)` | slot ← `WorkerThread.error` | Показывает `QMessageBox` с описанием ошибки потока. |
| `run_calculations()` | — | Оркестратор: последовательно вызывает `chooseMods` → `calcMetalChargeClicked` → `calcTableClick` → `slagCalcClicked` → `blastCalcClicked` → `MaterialBalanceCalcClicked` → `HeatBalanceCalcClicked` → `AddFeroBtnClicked` → `deoxCalc` → `getRecomendation`, затем сбрасывает `Protokol` и `step`. |
| `chooseMods()` | — | По имени режима из БД загружает: состав стали-цели (C/S/P/Si/Mn), данные чугуна (масса, T, состав), данные лома (масса, состав). Вызывает `getFluxeInMode()`. |
| `getFluxeInMode(modeId)` | — | Заполняет таблицу `FluxeTable` из связки `fluxedata_has_mode`: название флюса и его масса, привязанные к текущему режиму. |

### Управление флюсами и ферросплавами

| Метод | Описание |
|-------|----------|
| `getFluxes()` | Загружает все доступные флюсы из `regimdata.fluxedata` в ComboBox `FluxeType`. |
| `AddFluxeButtonClicked()` | Добавляет строку с выбранным флюсом в `FluxeTable` (оператор задаёт массу вручную). |
| `removeFluxeButtonClicked()` | Очищает `FluxeTable` (`setRowCount(0)`). |
| `AddFeroBtnClicked()` | Загружает состав выбранного ферросплава из `ferroalloydb` и отображает в таблице `ChemEmission`. |
| `removeFeroBtnClicked()` | Очищает таблицу `ChemEmission`. |

### Расчётный движок — последовательность этапов

| Метод | Флаг | Что вычисляет |
|-------|------|---------------|
| `calcMetalChargeClicked()` | `metalChargeCalcked` | Масса металлошихты = m_чугун + m_лом. Средневзвешенный химический состав шихты по C, S, Si, P, Mn. |
| `calcTableClick()` | `tableCalcked` | Таблица окисления (`OxidationTable`, 6 строк × 8 столбцов): содержание элементов до и после продувки, убыль C/Si/Mn/P/S, расход O₂ (кг и м³) на каждый элемент, суммарные оксиды. Степени удаления Mn/P/S зависят от содержания C в стали-цели (три диапазона). Si принимается = 0 после продувки. |
| `slagCalcClicked()` | `slagCalcked` | Состав и масса шлака: SiO₂, CaO (учёт CaCO₃→CaO), MgO (учёт MgCO₃→MgO), Al₂O₃ — из флюсов; FeO = 20 + 0.218/C + 0.031/P; Fe₂O₃ = 4–9 в зависимости от %C. Полная масса шлака и процентный состав. |
| `blastCalcClicked()` | `blastCalcked` | Суммарная потребность в кислороде = O₂ из `OxidationTable` + O₂ на FeO/Fe₂O₃ шлака + O₂ на дожигание CO − O₂ из FeO/Fe₂O₃ флюсов. Расход дутья в кг (чистота 99.5%) и м³; избыток дутья 8%. |
| `MaterialBalanceCalcClicked()` | `materialBalanceCalcked` | Полный материальный баланс. Вход: чугун, лом, флюсы, дутьё. Выход: жидкий металл, шлак, газы (CO/CO₂ из реакций C + из разложения CaCO₃/MgCO₃), пыль (0.02% × G_шихты). Выход жидкого металла. Таблица `OutputDataTable` (газовый состав, м³). |
| `HeatBalanceCalcClicked()` | `heatBalanceCalcked` | Полный тепловой баланс. Приход: физ. тепло чугуна (61.9+0.88T)×G, тепло реакций окисления (C→CO/CO₂, Si, Mn, P), тепло образования FeO/Fe₂O₃, тепло шлакообразования (CaO, SiO₂), дожигание CO. Расход: физ. тепло газов, разложение FeO×3707+Fe₂O₃×5278, выносы, пыль, карбонаты, потери 3%. Расчёт T стали и температуры перегрева (T_стали − (1539 − 80×%C)). |
| `deoxCalc()` | `heatBalanceCalcked` | Раскисление. Растворимость MgO: A=0.256T−335, B=0.066T−85; lim\_MgO = (A−B×CaO/SiO₂)×0.075×FeO − 0.875. Износ футеровки. Расход ферросплава для обеспечения целевого %Mn в стали с учётом угара Mn (17.5–27.5% в зависимости от %C). Выход металла после раскисления. |
| `recomendationCalc()` | `heatBalanceCalcked` | Проверяет, что ферросплав выбран. Основная логика рекомендаций вынесена в `getRecomendation()`. |

### Вспомогательные и сервисные методы

| Метод | Описание |
|-------|----------|
| `calcPhosphor()` | Вычисляет коэффициент распределения фосфора L_p = exp(22350/T + 2.5·ln(FeO) + 0.08·CaO − 16) с поправкой. Возвращает %P в стали = %P_шихты / L_p × 100. |
| `getRecomendation()` | Вызывает `calcPhosphor()`, рассчитывает насыщение MgO и износ футеровки, основность шлака CaO/SiO₂. Если недосыщение MgO > 3 → рекомендует увеличить магнезиальный флюс на 50 кг. Вызывает `checkLimits()` если заданы лимиты сценария. |
| `checkLimits()` | Сравнивает фактические C, T, P стали с лимитами сценария. При нарушении подсвечивает поля красным (QLineEdit stylesheet) и добавляет предупреждения в поле `recomendation`. |
| `CheckConverterFunc()` | Проверяет отношение H/D конвертера: допустимый диапазон 1.17…2.1. При выходе за пределы — предупреждение о возможных выбросах. |
| `stepResult()` | Формирует текстовый снимок текущего шага обучения (входные данные + результаты) и накапливает в глобальной переменной `Protokol`. Инкрементирует счётчик шагов. |
| `saveResult()` | Открывает диалог `tkinter.filedialog.asksaveasfile` (txt/html), записывает в файл весь накопленный `Protokol`. |
| `openAbout()` | Создаёт `QDialog` и открывает `AboutForm.Ui_Dialog`. |
| `setupUi(OperatorForm)` | Генерирует весь интерфейс формы программно (вкладки, таблицы, поля, кнопки, стили). Не использует `.ui`-файл. |
| `retranslateUi(OperatorForm)` | Устанавливает текстовые метки, вызывает `getSettings()` и `getModes()`. |

---

## Ключевые зависимости

| Библиотека | Назначение |
|-----------|------------|
| `PyQt5` | GUI-фреймворк, виджеты, потоки (QThread) |
| `mysql-connector-python` | Подключение к MySQL, CRUD-запросы |
| `pandas` + `openpyxl` | Экспорт таблиц в `.xlsx` |
| `configparser` | Чтение / запись `dev.ini` |
| `hashlib` (MD5) | Хэширование паролей при логине |
| `TensorFlow / Keras` *(откл.)* | Нейросетевая модель — заготовка в `neuro.py` |
