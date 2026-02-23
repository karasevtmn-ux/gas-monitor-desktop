# GAS Monitor Desktop (MVP 0.2)

## Требования
- Windows 10/11
- Python 3.11+ (рекомендуется с python.org)

## Установка
Откройте PowerShell в папке проекта и выполните:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Запуск
```powershell
python app.py
```

## Где хранятся данные
- База SQLite: `%LOCALAPPDATA%\GASMonitor\data.sqlite3`
- Логи: `%LOCALAPPDATA%\GASMonitor\logs\app.log`
- Бэкапы: `%LOCALAPPDATA%\GASMonitor\backups\` (хранение 7 дней)

## Настройка SMTP
Откройте кнопку `SMTP` в приложении:
- host, port, username, sender, recipient
- пароль вводится и сохраняется в защищённое хранилище Windows (Windows Credential Manager) через keyring.

## Как работает мониторинг
- Каждые 10 минут приложение проверяет, какие ссылки попадают в окно 01:00–05:00 по местному времени суда.
- Для каждой ссылки выполняется максимум 1 успешная проверка в сутки.
- При временной ошибке: повтор каждые 30 минут.
- Если 3 ошибки подряд — статус "problem" и письмо о проблемной ссылке.

## Упаковка в .exe (опционально)
Установите PyInstaller:
```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name GASMonitor app.py
```
Готовый exe будет в папке `dist`.


## Сборка EXE на Windows (рекомендуемый способ)

В проекте есть готовый скрипт сборки:

```powershell
.\build\build_exe.ps1
```

Или из cmd:

```cmd
build\build_exe.cmd
```

Результат: `.\dist\GASMonitor.exe`
