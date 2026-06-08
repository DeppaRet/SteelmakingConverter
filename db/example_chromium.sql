-- =====================================================================
-- Пример поверочного расчёта с хромом.
-- Воспроизводит набор данных, на котором проверялся учёт легирующих
-- элементов в материальном балансе:
--   лом 210 т, C=0.1 S=0.04 P=0.4 Si=0.2 Mn=0.05, ScrapCr=1.0 %,
--   тип лома с активной реакцией Cr -> Cr2O3.
-- Идемпотентно: повторный запуск не создаёт дубликатов.
-- =====================================================================

USE regimdata;

-- ---------------------------------------------------------------------
-- 1. Тип лома «Хромистый (поверочный пример)»
--    Реакции копируются со «Стандартного» (id=1) + активируется Cr.
-- ---------------------------------------------------------------------
INSERT INTO scraptype (ScrapTypeName, Description)
SELECT 'Хромистый (поверочный пример)',
       'Демонстрационный легированный лом: углеродистая основа + 1% Cr. Используется для поверочного расчёта учёта легирующих в материальном балансе.'
WHERE NOT EXISTS (
    SELECT 1 FROM scraptype WHERE ScrapTypeName = 'Хромистый (поверочный пример)'
);

SET @cr_type := (SELECT idScrapType FROM scraptype WHERE ScrapTypeName = 'Хромистый (поверочный пример)');

-- Привязка всех реакций: как у стандартного типа, плюс активный Cr.
INSERT INTO scraptype_reaction (ScrapType_idScrapType, Reaction_idReaction, IsActive, CO_Fraction)
SELECT @cr_type, r.idReaction,
    CASE WHEN r.ElementSymbol IN ('C_CO','C_CO2','Si','Mn','P','FeS_CaO','Cr') THEN 1 ELSE 0 END,
    0.9
FROM reaction r
WHERE NOT EXISTS (
    SELECT 1 FROM scraptype_reaction str
    WHERE str.ScrapType_idScrapType = @cr_type AND str.Reaction_idReaction = r.idReaction
);

-- На случай повторного запуска: гарантируем, что Cr активен.
UPDATE scraptype_reaction str
JOIN reaction r ON r.idReaction = str.Reaction_idReaction
SET str.IsActive = 1
WHERE str.ScrapType_idScrapType = @cr_type AND r.ElementSymbol = 'Cr';

-- ---------------------------------------------------------------------
-- 2. Состав лома (как у comp id=1, но ScrapCr = 1.0 %)
-- ---------------------------------------------------------------------
INSERT INTO scrapcomposition
    (ScrapCarbon, ScrapSerum, ScrapPhosphor, ScrapSilicon, ScrapManganese,
     ScrapCr, ScrapV, ScrapAl, ScrapTi)
SELECT 0.1, 0.04, 0.4, 0.2, 0.05, 1.0, 0.0, 0.0, 0.0
WHERE NOT EXISTS (
    SELECT 1 FROM scrapcomposition
    WHERE ScrapCarbon=0.1 AND ScrapSerum=0.04 AND ScrapPhosphor=0.4
      AND ScrapSilicon=0.2 AND ScrapManganese=0.05 AND ScrapCr=1.0
      AND ScrapV=0.0 AND ScrapAl=0.0 AND ScrapTi=0.0
);

SET @cr_comp := (
    SELECT idScrapComposition FROM scrapcomposition
    WHERE ScrapCarbon=0.1 AND ScrapSerum=0.04 AND ScrapPhosphor=0.4
      AND ScrapSilicon=0.2 AND ScrapManganese=0.05 AND ScrapCr=1.0
      AND ScrapV=0.0 AND ScrapAl=0.0 AND ScrapTi=0.0
    ORDER BY idScrapComposition LIMIT 1
);

-- ---------------------------------------------------------------------
-- 3. Завалка лома: 210 т, состав с Cr, хромистый тип
-- ---------------------------------------------------------------------
INSERT INTO scrapdata (ScrapWeight, ScrapComposition_idScrapComposition, ScrapType_idScrapType)
SELECT 210.0, @cr_comp, @cr_type
WHERE NOT EXISTS (
    SELECT 1 FROM scrapdata
    WHERE ScrapWeight=210.0 AND ScrapComposition_idScrapComposition=@cr_comp
      AND ScrapType_idScrapType=@cr_type
);

SET @cr_scrap := (
    SELECT idScrapData FROM scrapdata
    WHERE ScrapWeight=210.0 AND ScrapComposition_idScrapComposition=@cr_comp
      AND ScrapType_idScrapType=@cr_type
    ORDER BY idScrapData LIMIT 1
);

-- ---------------------------------------------------------------------
-- 4. Режим «Пример Cr (поверочный)» — переиспользует сталь/ковш режима #1
-- ---------------------------------------------------------------------
INSERT INTO mode (ModeName, SteelData_idSteelData, ScrapData_idScrapData,
                  CastSteelData_idCastSteelData, Converter_idConverter)
SELECT 'Пример Cr (поверочный)',
       m.SteelData_idSteelData, @cr_scrap,
       m.CastSteelData_idCastSteelData, m.Converter_idConverter
FROM mode m
WHERE m.idMode = 1
  AND NOT EXISTS (SELECT 1 FROM mode WHERE ModeName = 'Пример Cr (поверочный)');
