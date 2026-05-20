# Диаграммы дипломной работы

В этой папке хранятся исходники диаграмм для диплома.

Основной формат исходников: PlantUML (`.puml`).

Список диаграмм:

- `01_system_architecture.puml` — общая архитектура сервиса.
- `02_message_processing.puml` — последовательность обработки сообщения.
- `03_safety_flow.puml` — safety-flow и профиль состояния.
- `04_qwen_under_the_hood.puml` — устройство Qwen под капотом.
- `05_response_pipeline.puml` — конвейер формирования ответа.
- `07_er_model.puml` — ER-модель базы данных.

Файлы `.png` в этой папке являются текущими изображениями для Word-черновика. Если установлен PlantUML, их можно перерендерить из `.puml`.

Пример команды для перегенерации PNG:

```powershell
plantuml -tpng docs\thesis\diagrams\*.puml
```
