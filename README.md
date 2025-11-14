# GitHub Subscriptions Digest

Автоматический дайджест обновлений из GitHub репозиториев с AI-суммаризацией на русском языке.

## 📋 Обзор

Этот проект автоматически агрегирует, суммирует (с помощью Google Gemini AI) и отображает последние обновления (релизы и коммиты) из репозиториев, на которые вы подписаны в GitHub.

### Основные возможности

- 🤖 **AI-суммаризация**: Автоматическое создание кратких обзоров на русском языке с помощью Google Gemini
- 📅 **Ежедневные обновления**: GitHub Actions запускается каждый день для проверки новых релизов и коммитов
- 🌐 **Статический сайт**: Генерация красивого статического сайта с темой "Linux Terminal"
- 🚀 **Бесплатный хостинг**: Использует GitHub Pages для размещения сайта
- 📦 **Serverless**: Полностью serverless архитектура на базе GitHub Actions

## 🏗️ Архитектура

- **Runner**: GitHub Actions
- **Язык**: Python 3.14+ (async-first)
- **Хранилище данных**: `digest_data.json` (JSON файл)
- **Генератор сайта**: Jinja2
- **AI/Суммаризация**: Google Gemini API
- **Хостинг**: GitHub Pages

## 📁 Структура проекта

```
.
├── core/                      # Основная логика приложения
│   ├── __init__.py            # Публичный API модуля
│   ├── models.py              # Pydantic модели данных
│   ├── github_client.py       # Клиент GitHub API
│   ├── ai_summarizer.py       # Gemini AI суммаризация
│   ├── data_manager.py        # Управление digest_data.json
│   └── site_generator.py      # Генератор статического сайта
├── templates/                 # Jinja2 шаблоны
│   ├── base.html
│   ├── index.html
│   ├── project.html
│   └── update.html
├── static/                    # Статические файлы (CSS)
│   └── style.css
├── .github/workflows/         # GitHub Actions
│   └── daily-digest.yml
├── main.py                    # Основной скрипт (для GitHub Actions)
├── seed_data.py               # Скрипт первоначальной загрузки данных
└── requirements.txt           # Python зависимости
```

## 🚀 Быстрый старт

### Предварительные требования

1. **GitHub Personal Access Token (PAT)**
   - Перейдите в [Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
   - Создайте новый token с scope `repo`
   - Сохраните токен в безопасном месте

2. **Google Gemini API Key**
   - Получите API ключ на [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Сохраните ключ в безопасном месте

3. **Python 3.14+**
   - Установите Python 3.14 или новее

### Установка и настройка

#### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/YOUR_USERNAME/GitHub-Subscriptions-Digest.git
cd GitHub-Subscriptions-Digest
```

#### Шаг 2: Установка зависимостей

```bash
python -m pip install -r requirements.txt
```

#### Шаг 3: Первоначальная загрузка данных

Запустите скрипт `seed_data.py` для создания начальной базы данных:

```bash
export GH_PAT='your_github_token_here'
python seed_data.py
```

Этот скрипт:
- Получит список всех ваших подписок
- Загрузит последний релиз ИЛИ коммит для каждого репозитория
- Создаст файл `digest_data.json` (без AI-суммаризации)

**ВАЖНО**: Скрипт НЕ вызывает Gemini API для экономии квот.

#### Шаг 4: Создание и настройка gh-pages ветки

```bash
# Создать новую orphan ветку gh-pages
git checkout --orphan gh-pages

# Очистить staging area
git rm -rf .

# Скопировать digest_data.json из main ветки
git checkout main -- digest_data.json

# Создать .nojekyll для отключения Jekyll
touch .nojekyll

# Закоммитить
git add digest_data.json .nojekyll
git commit -m "Initial digest data"

# Запушить в gh-pages
git push -u origin gh-pages

# Вернуться в main
git checkout main
```

#### Шаг 5: Настройка секретов в GitHub

1. Перейдите в **Settings > Secrets and variables > Actions**
2. Создайте следующие секреты:
   - `GH_PAT`: Ваш GitHub Personal Access Token
   - `GEMINI_API_KEY`: Ваш Google Gemini API ключ

#### Шаг 6: Включение GitHub Pages

1. Перейдите в **Settings > Pages**
2. В разделе "Source" выберите ветку `gh-pages` и папку `/ (root)`
3. Нажмите "Save"

#### Шаг 7: Запуск GitHub Action

1. Перейдите в **Actions**
2. Выберите workflow "Daily GitHub Subscriptions Digest"
3. Нажмите "Run workflow" для ручного запуска

После успешного выполнения ваш сайт будет доступен по адресу:
```
https://YOUR_USERNAME.github.io/GitHub-Subscriptions-Digest/
```

## 🔧 Использование

### Автоматический режим

GitHub Action автоматически запускается каждый день в 05:00 UTC. Он:
1. Проверяет все ваши подписки
2. Ищет новые релизы и коммиты
3. Генерирует AI-суммаризацию для новых обновлений
4. Обновляет `digest_data.json`
5. Генерирует статический сайт
6. Публикует на GitHub Pages

### Ручной запуск

Вы можете запустить workflow вручную через вкладку **Actions** в вашем репозитории.

### Локальное тестирование

Для локального тестирования генерации сайта:

```bash
export GH_PAT='your_token'
export GEMINI_API_KEY='your_api_key'
python main.py
```

Сгенерированный сайт будет в директории `_site/`.

## 📊 Структура данных

Файл `digest_data.json` содержит всю информацию о проектах и обновлениях:

```json
{
  "last_run_timestamp": "2025-11-14T10:00:05Z",
  "projects": [
    {
      "name": "owner/repo-name",
      "url": "https://github.com/owner/repo-name",
      "last_checked": "2025-11-14T10:00:00Z",
      "updates": [
        {
          "id": "update-uuid-123",
          "type": "release",
          "date": "2025-11-14T09:30:00Z",
          "title": "v1.2.0 Release",
          "summary_ru": "Краткое обобщение на русском...",
          "source_content": "Original release notes...",
          "source_url": "https://github.com/owner/repo-name/releases/v1.2.0"
        }
      ]
    }
  ]
}
```

## 🎨 Дизайн

Сайт использует тему "Linux Terminal" с:
- Темным фоном (`#1e1e1e`)
- Светлым текстом (`#d4d4d4`)
- Зелеными акцентами (`#00a000`)
- Моноширинным шрифтом (`Consolas, Monaco, Menlo`)

## 🔐 Безопасность

- Никогда не коммитьте токены или API ключи в репозиторий
- Используйте GitHub Secrets для хранения конфиденциальной информации
- GitHub PAT должен иметь минимально необходимые права (`repo`)

## 🛠️ Разработка

### Принципы кода

Проект следует принципам, описанным в `CLAUDE.md`:

- **Functional Programming**: Чистые функции, иммутабельность, композиция
- **Async-first**: Использование `async/await` для всех I/O операций
- **Модульность**: Фасад паттерн через `__init__.py`
- **Type Safety**: Pydantic для валидации данных
- **Structured Logging**: JSON логирование для production

### Зависимости

- `httpx`: Async HTTP клиент для GitHub API
- `pydantic`: Валидация данных и type hints
- `jinja2`: Шаблонизация HTML
- `google-generativeai`: Google Gemini AI API

## 📝 Логирование

Все операции логируются в структурированном JSON формате:

```json
{
  "timestamp": "2025-11-14T10:00:00Z",
  "level": "INFO",
  "module": "core.github_client",
  "message": "Fetching user subscriptions",
  "context": "github_api",
  "operation": "fetch_subscriptions"
}
```

## 🐛 Устранение неполадок

### GitHub Action не запускается

- Убедитесь, что workflow файл находится в `.github/workflows/`
- Проверьте, что секреты `GH_PAT` и `GEMINI_API_KEY` настроены
- Проверьте логи в разделе **Actions**

### Gemini API ошибки

- Проверьте, что API ключ действителен
- Убедитесь, что у вас есть квота на использование Gemini API
- Gemini API может иметь rate limits

### GitHub Pages не отображается

- Убедитесь, что ветка `gh-pages` существует
- Проверьте настройки в **Settings > Pages**
- Дождитесь завершения deployment (может занять несколько минут)

## 🤝 Вклад

Вклад приветствуется! Пожалуйста:
1. Форкните репозиторий
2. Создайте feature ветку
3. Сделайте коммит с изменениями
4. Отправьте pull request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 🙏 Благодарности

- GitHub Actions за serverless CI/CD
- Google Gemini за AI суммаризацию
- GitHub Pages за бесплатный хостинг
- Jinja2 за отличный шаблонизатор

---

**Приятного использования! 🚀**

Если у вас есть вопросы или предложения, создайте issue в этом репозитории.
