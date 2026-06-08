-- =====================================================================
-- Миграция: матрица стехиометрических коэффициентов (30 реакций)
-- База: regimdata (MySQL)
-- Идемпотентность: повторный запуск не должен падать.
-- =====================================================================

USE regimdata;

-- ---------------------------------------------------------------------
-- 1.1 Таблица типов лома
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scraptype (
    idScrapType   INT AUTO_INCREMENT PRIMARY KEY,
    ScrapTypeName VARCHAR(100) NOT NULL UNIQUE,
    Description   TEXT
);

INSERT INTO scraptype (ScrapTypeName, Description)
SELECT 'Стандартный', 'Низкоуглеродистая сталь обычного качества, без легирующих'
WHERE NOT EXISTS (SELECT 1 FROM scraptype WHERE ScrapTypeName = 'Стандартный');

-- ---------------------------------------------------------------------
-- 1.2 Полный справочник всех 30 реакций
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reaction (
    idReaction             INT AUTO_INCREMENT PRIMARY KEY,
    ReactionNumber         INT NOT NULL,
    ElementSymbol          VARCHAR(10)  NOT NULL,
    ElementName            VARCHAR(100) NOT NULL,
    ReactionEquation       VARCHAR(300) NOT NULL,
    nu_Element             FLOAT NOT NULL,
    M_Element              FLOAT NOT NULL,
    nu_O2                  FLOAT NOT NULL DEFAULT 0.0,
    M_O2                   FLOAT NOT NULL DEFAULT 32.0,
    nu_Product             FLOAT NOT NULL,
    M_Product              FLOAT NOT NULL,
    ProductFormula         VARCHAR(30)  NOT NULL,
    HeatEffect_kJ_kg       FLOAT NOT NULL DEFAULT 0.0,
    ProducesGas            TINYINT(1) NOT NULL DEFAULT 0,
    NeedsO2                TINYINT(1) NOT NULL DEFAULT 1,
    AffectsMaterialBalance TINYINT(1) NOT NULL DEFAULT 0,
    AffectsSlag            TINYINT(1) NOT NULL DEFAULT 0,
    AffectsBlast           TINYINT(1) NOT NULL DEFAULT 0,
    AffectsHeatBalance     TINYINT(1) NOT NULL DEFAULT 0,
    UNIQUE KEY uq_reaction_number (ReactionNumber)
);

-- Предзаполнение всех 30 реакций (только если таблица пуста)
INSERT INTO reaction
    (ReactionNumber, ElementSymbol, ElementName, ReactionEquation,
     nu_Element, M_Element, nu_O2, M_O2, nu_Product, M_Product, ProductFormula,
     HeatEffect_kJ_kg, ProducesGas, NeedsO2,
     AffectsMaterialBalance, AffectsSlag, AffectsBlast, AffectsHeatBalance)
SELECT * FROM (
    -- РЕАКЦИИ ОКИСЛЕНИЯ КИСЛОРОДОМ ДУТЬЯ
    SELECT  1 AS ReactionNumber,'C_CO2' AS ElementSymbol,'Углерод -> CO2' AS ElementName,'C + O2 = CO2' AS ReactionEquation,
            1 AS nu_Element,12.0 AS M_Element,1.0 AS nu_O2,32.0 AS M_O2,1 AS nu_Product,44.0 AS M_Product,'CO2' AS ProductFormula,
            32708.0 AS HeatEffect_kJ_kg,1 AS ProducesGas,1 AS NeedsO2,1 AS AffectsMaterialBalance,0 AS AffectsSlag,1 AS AffectsBlast,1 AS AffectsHeatBalance
    UNION ALL SELECT  2,'C_CO','Углерод -> CO','C + 1/2 O2 = CO',          1,12.0,0.5,32.0,1,28.0,'CO',      9196.0,1,1,1,0,1,1
    UNION ALL SELECT  3,'CO_burn','CO -> CO2 (дожигание)','CO + 1/2 O2 = CO2',1,28.0,0.5,32.0,1,44.0,'CO2',  10107.0,1,1,0,0,1,1
    UNION ALL SELECT  4,'Si','Кремний -> SiO2','Si + O2 = SiO2',           1,28.0,1.0,32.0,1,60.0,'SiO2',  30536.0,0,1,1,1,1,1
    UNION ALL SELECT  5,'Mn','Марганец -> MnO','Mn + 1/2 O2 = MnO',        1,55.0,0.5,32.0,1,71.0,'MnO',    7000.0,0,1,1,1,1,1
    UNION ALL SELECT  6,'Fe_FeO','Железо -> FeO','Fe + 1/2 O2 = FeO',      1,56.0,0.5,32.0,1,72.0,'FeO',    4767.0,0,1,1,1,1,1
    UNION ALL SELECT  7,'Fe_Fe3O4','Железо -> Fe3O4','3Fe + 2O2 = Fe3O4',  3,56.0,2.0,32.0,1,232.0,'Fe3O4', 5555.0,0,1,1,1,1,1
    UNION ALL SELECT  8,'Fe_Fe2O3','Железо -> Fe2O3','2Fe + 1.5O2 = Fe2O3',2,56.0,1.5,32.0,1,160.0,'Fe2O3', 5278.0,0,1,1,1,1,1
    UNION ALL SELECT  9,'P','Фосфор -> P2O5','2P + 2.5O2 = P2O5',          2,31.0,2.5,32.0,1,142.0,'P2O5',  24343.0,0,1,1,1,1,1
    UNION ALL SELECT 10,'Cr','Хром -> Cr2O3','2Cr + 1.5O2 = Cr2O3',        2,52.0,1.5,32.0,1,152.0,'Cr2O3', 10865.0,0,1,1,1,1,1
    UNION ALL SELECT 11,'Al','Алюминий -> Al2O3','2Al + 1.5O2 = Al2O3',    2,27.0,1.5,32.0,1,102.0,'Al2O3', 31000.0,0,1,1,1,1,1
    UNION ALL SELECT 12,'Ca_CaO','Кальций -> CaO','Ca + 1/2 O2 = CaO',     1,40.0,0.5,32.0,1,56.0,'CaO',   15650.0,0,1,0,1,1,0
    UNION ALL SELECT 13,'Ti','Титан -> TiO2','Ti + O2 = TiO2',             1,48.0,1.0,32.0,1,80.0,'TiO2',  19667.0,0,1,1,1,1,1
    UNION ALL SELECT 14,'V','Ванадий -> V2O5','2V + 2.5O2 = V2O5',         2,51.0,2.5,32.0,1,182.0,'V2O5',  15225.0,0,1,1,1,1,1
    UNION ALL SELECT 15,'S_SO2','Сера -> SO2 (газ)','S + O2 = SO2',        1,32.0,1.0,32.0,1,64.0,'SO2',    9278.0,1,1,1,0,1,1
    -- РЕАКЦИИ СУЛЬФИДИРОВАНИЯ (не требуют O2 из дутья)
    UNION ALL SELECT 16,'Mg_S','Mg + S = MgS','Mg + S = MgS',             1,24.0,0.0,32.0,1,56.0,'MgS',       0.0,0,0,0,1,0,0
    UNION ALL SELECT 17,'Mn_S','Mn + S = MnS','Mn + S = MnS',             1,55.0,0.0,32.0,1,87.0,'MnS',       0.0,0,0,0,1,0,0
    UNION ALL SELECT 18,'Ca_S','Ca + S = CaS','Ca + S = CaS',             1,40.0,0.0,32.0,1,72.0,'CaS',       0.0,0,0,0,1,0,0
    -- РЕАКЦИИ С УЧАСТИЕМ FeO
    UNION ALL SELECT 19,'Ca_FeO','Ca + FeO = CaO + Fe','Ca + FeO = CaO + Fe',1,40.0,0.0,32.0,1,56.0,'CaO',   0.0,0,0,0,1,0,0
    UNION ALL SELECT 20,'Mn_FeO','Mn + FeO = MnO + Fe','Mn + FeO = MnO + Fe',1,55.0,0.0,32.0,1,71.0,'MnO',   0.0,0,0,1,1,0,0
    -- РЕАКЦИИ ШЛАКООБРАЗОВАНИЯ
    UNION ALL SELECT 21,'P2O5_3CaO','P2O5 + 3CaO = 3CaO*P2O5','P2O5 + 3CaO = 3CaO*P2O5',1,142.0,0.0,32.0,1,310.0,'3CaO*P2O5',0.0,0,0,0,1,0,0
    UNION ALL SELECT 22,'P2O5_4CaO','P2O5 + 4CaO = 4CaO*P2O5','P2O5 + 4CaO = 4CaO*P2O5',1,142.0,0.0,32.0,1,366.0,'4CaO*P2O5',0.0,0,0,0,1,0,0
    UNION ALL SELECT 23,'SiO2_2CaO','SiO2 + 2CaO = 2CaO*SiO2','SiO2 + 2CaO = 2CaO*SiO2',1,60.0,0.0,32.0,1,172.0,'2CaO*SiO2',0.0,0,0,0,1,0,0
    UNION ALL SELECT 24,'SiO2_2FeO','SiO2 + 2FeO = 2FeO*SiO2','SiO2 + 2FeO = 2FeO*SiO2',1,60.0,0.0,32.0,1,204.0,'2FeO*SiO2',0.0,0,0,0,1,0,0
    UNION ALL SELECT 25,'P_FeO_CaO','2P+5FeO+3CaO=3CaO*P2O5+5Fe','2P + 5FeO + 3CaO = 3CaO*P2O5 + 5Fe',2,31.0,0.0,32.0,1,310.0,'3CaO*P2O5',0.0,0,0,1,1,0,0
    -- ГАЗОФАЗНЫЕ И ПРОЧИЕ
    UNION ALL SELECT 26,'CaO_CO2','CaO + CO2 = CaCO3','CaO + CO2 = CaCO3', 1,56.0,0.0,32.0,1,100.0,'CaCO3',    0.0,0,0,0,0,0,0
    UNION ALL SELECT 27,'C_H2','C + 2H2 = CH4','C + 2H2 = CH4',           1,12.0,0.0,32.0,1,16.0,'CH4',        0.0,1,0,0,0,0,0
    UNION ALL SELECT 28,'H2_O2','H2 + 1/2 O2 = H2O','H2 + 1/2 O2 = H2O',  1,2.0,0.5,32.0,1,18.0,'H2O',         0.0,1,1,0,0,1,0
    UNION ALL SELECT 29,'P_alt','Фосфор (альт. запись)','4/5 P + O2 = 2/5 P2O5',0.8,31.0,1.0,32.0,0.4,142.0,'P2O5',21730.0,0,1,1,1,1,1
    -- ДЕСУЛЬФУРАЦИЯ В ШЛАК
    UNION ALL SELECT 30,'FeS_CaO','FeS + CaO = CaS + FeO','FeS + CaO = CaS + FeO',1,88.0,0.0,32.0,1,72.0,'CaS',0.0,0,0,1,1,0,0
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM reaction);

-- ---------------------------------------------------------------------
-- 1.3 Привязка реакций к типу лома
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scraptype_reaction (
    idScrapTypeReaction   INT AUTO_INCREMENT PRIMARY KEY,
    ScrapType_idScrapType INT NOT NULL,
    Reaction_idReaction   INT NOT NULL,
    IsActive              TINYINT(1) DEFAULT 1,
    CO_Fraction           FLOAT DEFAULT 0.9,
    FOREIGN KEY (ScrapType_idScrapType) REFERENCES scraptype(idScrapType),
    FOREIGN KEY (Reaction_idReaction)   REFERENCES reaction(idReaction),
    UNIQUE KEY uq (ScrapType_idScrapType, Reaction_idReaction)
);

-- Стандартный тип (id=1): активны C_CO, C_CO2, Si, Mn, P, FeS_CaO; остальные присутствуют, но IsActive=0
INSERT INTO scraptype_reaction (ScrapType_idScrapType, Reaction_idReaction, IsActive, CO_Fraction)
SELECT 1, r.idReaction,
    CASE WHEN r.ElementSymbol IN ('C_CO','C_CO2','Si','Mn','P','FeS_CaO') THEN 1 ELSE 0 END,
    0.9
FROM reaction r
WHERE NOT EXISTS (
    SELECT 1 FROM scraptype_reaction str
    WHERE str.ScrapType_idScrapType = 1 AND str.Reaction_idReaction = r.idReaction
);

-- ---------------------------------------------------------------------
-- 1.4 Расширение существующих таблиц (идемпотентно через information_schema)
-- ---------------------------------------------------------------------
SET @db := DATABASE();

-- scrapcomposition: ScrapCr / ScrapV / ScrapAl / ScrapTi
SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA=@db AND TABLE_NAME='scrapcomposition' AND COLUMN_NAME='ScrapCr')=0,
    'ALTER TABLE scrapcomposition ADD COLUMN ScrapCr FLOAT DEFAULT 0.0', 'SELECT 1');
PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;

SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA=@db AND TABLE_NAME='scrapcomposition' AND COLUMN_NAME='ScrapV')=0,
    'ALTER TABLE scrapcomposition ADD COLUMN ScrapV FLOAT DEFAULT 0.0', 'SELECT 1');
PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;

SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA=@db AND TABLE_NAME='scrapcomposition' AND COLUMN_NAME='ScrapAl')=0,
    'ALTER TABLE scrapcomposition ADD COLUMN ScrapAl FLOAT DEFAULT 0.0', 'SELECT 1');
PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;

SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA=@db AND TABLE_NAME='scrapcomposition' AND COLUMN_NAME='ScrapTi')=0,
    'ALTER TABLE scrapcomposition ADD COLUMN ScrapTi FLOAT DEFAULT 0.0', 'SELECT 1');
PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;

-- scrapdata: ScrapType_idScrapType + FK
SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
     WHERE TABLE_SCHEMA=@db AND TABLE_NAME='scrapdata' AND COLUMN_NAME='ScrapType_idScrapType')=0,
    'ALTER TABLE scrapdata ADD COLUMN ScrapType_idScrapType INT DEFAULT 1', 'SELECT 1');
PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;

SET @sql := IF(
    (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
     WHERE TABLE_SCHEMA=@db AND TABLE_NAME='scrapdata' AND CONSTRAINT_NAME='fk_scrapdata_scraptype')=0,
    'ALTER TABLE scrapdata ADD CONSTRAINT fk_scrapdata_scraptype FOREIGN KEY (ScrapType_idScrapType) REFERENCES scraptype(idScrapType)',
    'SELECT 1');
PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;
