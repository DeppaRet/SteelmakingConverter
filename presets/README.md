# Пресеты управляющих воздействий

JSON-файлы с настройками панели «Управляющие воздействия» на форме оператора.

## Формат (schema_version 1)

```json
{
  "schema_version": 1,
  "scenario_name": "Имя сценария из regimdata",
  "timestamp": "2026-05-19T14:30:00",
  "controls": {
    "blast_volume_m3": 8500,
    "blast_flow_m3_min": 920,
    "blow_time_min": 18.5,
    "lance_height_m": 1.4,
    "locks": {
      "blast_volume_m3": true,
      "blast_flow_m3_min": true,
      "blow_time_min": false
    },
    "computed_key": "blow_time_min"
  }
}
```

## Поля

| Поле | Описание |
|------|----------|
| `blast_volume_m3` | Общий объём дутья на плавку, м³ |
| `blast_flow_m3_min` | Расход кислорода через фурму, м³/мин |
| `blow_time_min` | Время продувки, мин |
| `lance_height_m` | Высота сопла фурмы над ванной, м |
| `locks` | Какие два параметра из тройки V/i/τ зафиксированы |
| `computed_key` | Какой параметр тройки вычисляется автоматически |

Пресеты **не записываются** в MySQL — только локальные файлы для воспроизводимости обучения.
