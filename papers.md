# Статьи и материалы по моделям сегментации

Образовательные и справочные ссылки по трём моделям instance-сегментации, использованным в проекте (CarDD).

## YOLOv8 (Ultralytics)

- [Документация Ultralytics](https://docs.ultralytics.com/) — официальная докуметация YOLO: модели, режимы `train/val/predict/export`, туториалы и примеры.
- [JSON2YOLO](https://github.com/ultralytics/JSON2YOLO) — утилита для конвертации аннотаций из COCO/JSON в формат разметки YOLO.
- [Datasets (обзор форматов)](https://docs.ultralytics.com/datasets) — какие форматы датасетов поддерживает YOLO для разных задач (detect, segment, pose, ...).
- [Формат YAML датасета для сегментации](https://docs.ultralytics.com/datasets/segment#dataset-yaml-format) — спецификация `data.yaml`: пути к данным и список классов для instance-сегментации.
- [Статья на Habr](https://habr.com/ru/articles/821971/) — русскоязычный разбор YOLO (архитектура и обучение). *(описание по теме — проверь содержание)*

## Mask R-CNN

- [Статья на Habr](https://habr.com/ru/articles/421299/) — русскоязычный разбор Mask R-CNN: как устроена instance-сегментация (RPN, RoIAlign, ветка масок). *(описание по теме — проверь содержание)*

## Mask2Former

- [What is Mask2Former? (Roboflow)](https://blog.roboflow.com/what-is-mask2former/) — обзорная статья: идея универсальной сегментации (semantic / instance / panoptic одной архитектурой) и чем подход отличается от предыдущих.
- [Mask2Former (Hugging Face blog)](https://huggingface.co/blog/mask2former) — как работает Mask2Former и как пользоваться им через библиотеку `transformers`.