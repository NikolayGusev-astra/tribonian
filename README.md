# Google Drive Folder Summarizer

Модульная Python-программа для автоматической суммаризации содержимого публичных папок Google Drive с использованием LLM через OpenRouter API.

## Описание

Программа скачивает все файлы из указанной публичной Google Drive папки, извлекает контент из каждого файла (PDF, изображения, текстовые файлы) и генерирует единое структурированное саммари через бесплатные LLM-модели.

### Поддерживаемые форматы

- **PDF** — извлечение текста через PyPDF2
- **Изображения** (JPG, PNG, WEBP, GIF, BMP, TIFF) — распознавание через vision-модели с предобработкой (конвертация в PNG, sharpening, contrast boost)
- **Текстовые файлы** (TXT, MD, CSV, JSON, XML, HTML, LOG, RST) — прямое чтение

## Особенности

- ✅ **Модульная архитектура** — легко добавлять новые типы файлов и процессоры
- ✅ **Fallback-цепочка моделей** — автоматический переключение между моделями при блокировке/rate-limit
- ✅ **Предобработка изображений** — улучшение качества сканов для лучшего OCR
- ✅ **Бесплатные модели** — использует `:free` модели OpenRouter (с возможностью переключения на платные)
- ✅ **CLI интерфейс** — удобный запуск из командной строки

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/NikolayGusev-astra/tribonian.git
cd tribonian
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Получите API ключ OpenRouter:
   - Зарегистрируйтесь на [https://openrouter.ai/keys](https://openrouter.ai/keys)
   - Скопируйте ключ в `.env`:
   ```
   OPENROUTER_API_KEY=sk-or-v1-ваш-ключ-здесь
   ```

## Использование

### Базовый запуск

```bash
python -m gdrive_summarizer.main --url "https://drive.google.com/drive/folders/ID_ПАПКИ"
```

### Параметры

- `--url` (обязательный) — URL публичной Google Drive папки
- `--output` (опционально) — директория для скачанных файлов (по умолчанию: `./downloads`)
- `--save` (опционально) — файл для сохранения саммари (по умолчанию: `summary.txt`)
- `-v, --verbose` — подробный вывод (DEBUG-уровень логирования)

### Пример

```bash
python -m gdrive_summarizer.main \
  --url "https://drive.google.com/drive/folders/1x6EKNkVw6PlFVTr6cGrsVscmRuwqGrXd" \
  --output ./my_downloads \
  --save my_summary.txt \
  -v
```

## Архитектура

```
gdrive_summarizer/
├── config.py              # Конфигурация из .env
├── downloader.py          # Скачивание папки через gdown
├── llm_client.py          # HTTP-клиент OpenRouter (text + vision)
├── summarizer.py          # Оркестрация: скачать → извлечь → саммари
├── main.py                # CLI точка входа
└── processors/
    ├── base.py            # Базовый класс BaseProcessor + реестр
    ├── pdf_processor.py   # Извлечение текста из PDF
    ├── image_processor.py # Vision API для изображений
    └── text_processor.py  # Чтение текстовых файлов
```

## Расширяемость

### Добавление нового типа файла

1. Создайте класс-наследник `BaseProcessor`:
```python
from gdrive_summarizer.processors.base import BaseProcessor, register_processor

class MyProcessor(BaseProcessor):
    def extract(self, file_path: Path) -> str:
        # Ваша логика извлечения
        return extracted_text

register_processor(".myext", MyProcessor)
```

2. Импортируйте модуль в `summarizer.py` для автоматической регистрации.

### Смена LLM-модели

Измените в `.env`:
```
TEXT_MODEL=google/gemma-3-27b-it:free
VISION_MODEL=google/gemma-3-27b-it:free
```

Или используйте платные модели (например, `google/gemini-2.5-flash`).

## Технические детали

- **Fallback-цепочка для vision**: при блокировке/rate-limit автоматически пробуются альтернативные модели
- **Предобработка изображений**: все изображения конвертируются в PNG + применяется sharpening и contrast boost (+30%) для улучшения OCR на сканах
- **Retry с экспоненциальным back-off**: автоматические повторы при rate-limit ошибках (429, 402, 503)

## Лицензия

MIT

## Примечание

Этот проект создан в рамках тестового задания для вакансии в **Трибониан** (Tribonian).
