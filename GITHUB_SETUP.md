# Инструкции по передаче проекта на GitHub

## Предварительная подготовка

### 1. Создать GitHub репозиторий

1. Перейти на https://github.com/new
2. Заполнить параметры:
   - **Repository name**: `dashboard-lipetsk` (или другое имя)
   - **Description**: "Interactive dashboard for assessing effectiveness of municipal heads in Lipetsk region"
   - **Public/Private**: Выбрать согласно политике
   - **Initialize**: НЕ инициализировать (у нас уже есть локальный git)
   - **License**: Выбрать лицензию (MIT, Apache 2.0 и т.д.)
3. Нажать "Create repository"

### 2. Получить данные репозитория

После создания GitHub покажет инструкции:
```
git remote add origin https://github.com/YOUR_USERNAME/dashboard-lipetsk.git
git branch -M main
git push -u origin main
```

## Выполнение загрузки

### Вариант 1: HTTPS (требует token)

```bash
cd "C:\Users\cobra\Desktop\Дашборд Липецкой области\Дашборд Губернатора главы регионов\Проект"

# 1. Добавить удалённый репозиторий
git remote add origin https://github.com/YOUR_USERNAME/dashboard-lipetsk.git

# 2. Переименовать ветку в main (если нужно)
git branch -M main

# 3. Отправить код на GitHub
git push -u origin main

# 4. Проверить статус
git remote -v
```

### Вариант 2: SSH (рекомендуется)

```bash
# 1. Если SSH ключи уже настроены
git remote add origin git@github.com:YOUR_USERNAME/dashboard-lipetsk.git
git branch -M main
git push -u origin main

# 2. Если SSH ключей нет, создать их
ssh-keygen -t ed25519 -C "your_email@example.com"
# Скопировать публичный ключ в GitHub Settings > SSH Keys
```

## Быстрая загрузка (шаг за шагом)

```bash
# 1. Перейти в проект
cd "C:\Users\cobra\Desktop\Дашборд Липецкой области\Дашборд Губернатора главы регионов\Проект"

# 2. Проверить текущий remote
git remote -v
# Если ничего не выводит - это нормально

# 3. Добавить GitHub репозиторий (замените на ваш)
git remote add origin https://github.com/YOUR_USERNAME/dashboard-lipetsk.git

# 4. Отправить основную ветку
git push -u origin main

# 5. Проверить результат
git log --oneline

# 6. Открыть https://github.com/YOUR_USERNAME/dashboard-lipetsk
```

## Настройка GitHub

### После загрузки кода

#### 1. Защита веток (Branch Protection)

```
Settings > Branches > Add rule
├─ Pattern name: main
├─ Require pull request reviews: ✓ (2 reviewers)
├─ Require status checks to pass: ✓
├─ Require branches to be up to date: ✓
├─ Require approval of reviewers: ✓
└─ Dismiss stale review approvals: ✓
```

#### 2. Настройка CI/CD

Создать `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build
```

#### 3. Шаблоны Issues и PRs

Создать `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: Report a bug
---

## Description
<!-- Describe the bug -->

## Steps to reproduce
1. ...

## Expected behavior
<!-- What should happen -->

## Actual behavior
<!-- What actually happens -->

## Environment
- OS: ...
- Browser: ...
- Version: ...
```

#### 4. README в главной папке GitHub

GitHub будет показывать `README.md` на главной странице репо.

Текущий `README.md` в проекте уже полный и готовый! ✅

### 5. Topics (Tags)

Добавить Topics для лучшей видимости:
- dashboard
- lipetsk
- russia
- governance
- react
- fastapi
- postgresql
- docker

### 6. Описание репо

В Settings > General > Description:
```
Interactive dashboard for assessing governance effectiveness
in Lipetsk region municipalities with real-time analytics and reporting.
```

## Команда Git

```bash
# Просмотр истории
git log --oneline
git log --graph --oneline --all

# Синхронизация с GitHub
git fetch origin
git pull origin main

# Создание новой ветки
git checkout -b feature/new-feature
git push -u origin feature/new-feature

# Merge в main
# Создать Pull Request на GitHub и после одобрения merge

# Проверка статуса
git status
git diff
```

## Проверка списка файлов перед загрузкой

```bash
cd Проект

# Что будет загружено
git ls-files

# Что будет проигнорировано
cat .gitignore

# Размер репо
du -sh .git

# Статус
git status
```

## Если что-то пошло не так

### Удалить remote и добавить заново

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/dashboard-lipetsk.git
git push -u origin main
```

### Если неправильная ветка

```bash
# Просмотр всех веток
git branch -a

# Удалить ветку локально
git branch -d branch_name

# Удалить ветку на GitHub
git push origin --delete branch_name

# Создать main если её нет
git checkout -b main
git push -u origin main
```

## Проверка статуса на GitHub

```bash
# После push проверить:
# 1. Открыть https://github.com/YOUR_USERNAME/dashboard-lipetsk
# 2. Должны видеть файлы проекта
# 3. Должны видеть commits в истории
# 4. README должен отобразиться на главной странице
```

## Дальнейшая разработка

После загрузки на GitHub:

### 1. Клонировать для работы

```bash
git clone https://github.com/YOUR_USERNAME/dashboard-lipetsk.git
cd dashboard-lipetsk
```

### 2. Создать feature ветку

```bash
git checkout -b feature/add-export
# ... делать изменения ...
git add .
git commit -m "Add PDF export functionality"
git push -u origin feature/add-export
```

### 3. Создать Pull Request

На GitHub:
1. Автоматически предложит создать PR
2. Добавить описание изменений
3. Запросить review
4. После approval - merge в main

## Рекомендуемые GitHub Actions

### Автоматическое развёртывание

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: |
          # SSH в production server
          # git pull
          # docker-compose up -d
```

### Автоматическое тестирование

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: npm install
      - run: npm test
      - run: pytest
```

## Полезные ссылки

- [GitHub Docs](https://docs.github.com)
- [Git Documentation](https://git-scm.com/doc)
- [GitHub CLI](https://cli.github.com)
- [GitHub Actions](https://github.com/features/actions)

## Финальная проверка

```bash
# Убедиться что всё коммитено
git status
# Output: On branch main, nothing to commit

# Убедиться что всё загружено
git log -1 --oneline
# Output: должен совпадать с последним коммитом на GitHub

# Проверить origin
git remote -v
# Output: origin https://github.com/YOUR_USERNAME/dashboard-lipetsk.git (fetch)
#        origin https://github.com/YOUR_USERNAME/dashboard-lipetsk.git (push)
```

---

**Готово!** Ваш проект успешно загружен на GitHub и готов к совместной разработке! 🚀
