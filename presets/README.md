# Пресеты управляющих воздействий

JSON-файлы с настройками панели «Управляющие воздействия» на форме оператора.

## Формат (schema_version 3)

```json
{
  "schema_version": 3,
  "scenario_name": "Имя сценария из regimdata",
  "timestamp": "2026-05-20T14:30:00",
  "controls": {
    "target_carbon": 0.10,
    "o2_losses": 7.5,
    "blast_flow_m3_min": 920,
    "blow_time_min": 18.5,
    "lance_height_m": 1.4,
    "locks": {
      "blast_flow_m3_min": true,
      "blow_time_min": false
    },
    "computed_key": "blow_time_min",
    "p_o2_manual_enabled": false
  }
}
```

## Поля

| Поле | Описание |
|------|----------|
| `target_carbon` | Целевое содержание углерода в стали [C]_М, % |
| `o2_losses` | Потери O₂ при продувке, % (формула 25) |
| `blast_flow_m3_min` | Расход O₂ через фурму i, м³/мин (информационный) |
| `blow_time_min` | Время продувки τ, мин (информационный) |
| `lance_height_m` | Высота сопла фурмы h_c, м (влияет на η_CO и Z) |
| `locks` | Какой параметр из пары i/τ вычисляется |
| `computed_key` | `blast_flow_m3_min` или `blow_time_min` |
| `p_o2_manual_enabled` | Ручной режим П_O₂ (иначе авторасчёт от h_c) |

**Объём дутья V** в пресет не входит — это результат расчёта (`blastCalcClicked`), отображается read-only на панели.

## Совместимость

Пресеты `schema_version: 1` и `2` загружаются (поле `p_o2_manual_enabled` по умолчанию false).

Пресеты `schema_version: 1` с полем `blast_volume_m3` загружаются: объём используется только как справочный для связи i/τ на панели, не подменяет расчётный V.

Пресеты **не записываются** в MySQL — только локальные файлы для воспроизводимости обучения.
