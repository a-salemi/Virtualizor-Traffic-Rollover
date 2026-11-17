# ⚡ VirtuRoll (Virtualizor-Traffic-Rollover)

<p align="center">
  <img src="https://img.shields.io/badge/VirtuRoll-Версия%202.0.0-6366f1?style=for-the-badge&logo=fastapi&logoColor=white" alt="VirtuRoll Version" />
  <img src="https://img.shields.io/badge/Virtualizor-API%204085-06b6d4?style=for-the-badge&logo=linux&logoColor=white" alt="Virtualizor" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Telegram-Оповещения%20и%20Бэкапы-229ed9?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot" />
  <img src="https://img.shields.io/badge/Лицензия-MIT-emerald?style=for-the-badge" alt="License MIT" />
</p>

<p align="center">
  <b>Автоматический механизм переноса (Rollover) трафика и управление множеством нод для Virtualizor.</b><br>
  <i>Предотвращает утечки трафика при ежемесячном сбросе счетчиков для предоплаченных тарифов VPS. 100% Bare-Metal (Без Docker).</i>
</p>

<p align="center">
  <b>🌐 Другие языки / Other Languages:</b><br>
  <a href="README.md"><b>English</b></a> •
  <a href="README.fa.md"><b>فارسی (Persian)</b></a> •
  <a href="README.ru.md"><b>Русский (Russian)</b></a> •
  <a href="README.zh.md"><b>简体中文 (Chinese)</b></a> •
  <a href="README.tr.md"><b>Türkçe (Turkish)</b></a> •
  <a href="README.ar.md"><b>العربية (Arabic)</b></a>
</p>

---

## 📖 Содержание
- [Проблема](#-проблема)
- [Решение](#-решение)
- [Ключевые возможности](#-ключевые-возможности)
- [Быстрая установка одной командой](#-быстрая-установка-одной-командой-ubuntu--debian)
- [Обновление](#-обновление-установленной-версии)
- [Подключение панелей Virtualizor](#-подключение-панелей-virtualizor)
- [Настройка Telegram бота и отправки бэкапов](#-настройка-telegram-бота-и-отправки-бэкапов)
- [Управление службой systemd](#-управление-службой-systemd)
- [Лицензия](#-лицензия)

---

## 🛑 Проблема

По умолчанию в **Virtualizor** все лимиты трафика привязаны к календарному месяцу. В 00:00 первого числа каждого месяца:
1. Virtualizor сбрасывает счетчик использованного трафика каждого VPS на **`0 GB`**.
2. Если клиент купил предоплаченный пакет на **5 ТБ** и использовал 4 ТБ, 1-го числа следующего месяца он получает новые 5 ТБ вместо оставшегося 1 ТБ.
3. Это приводит к огромным потерям трафика и убыткам для провайдера хостинга.

---

## ✨ Решение

**VirtuRoll** работает как легковесный фоновый демон. Он непрерывно отслеживает дельту расхода трафика, считая гипервизор Virtualizor единственным достоверным источником:

$$\text{Фактический остаток} = \text{Лимит ноды} - \text{Израсходовано}$$

Когда Virtualizor сбрасывает счетчики первого числа месяца, VirtuRoll автоматически:
1. Вычисляет реальный остаток трафика каждого VPS.
2. Обновляет активный лимит трафика в панели Virtualizor через Admin API (`POST /index.php?act=editvs`) в соответствии с реальным остатком.
3. Безопасно исключает серверы с безлимитным трафиком (`bandwidth = 0`).
4. Записывает событие в журнал аудита и отправляет уведомление в **Telegram**.

---

## 🌟 Ключевые возможности

| Возможность | Описание |
| :--- | :--- |
| 🔄 **Событийный перенос** | Не зависит от часовых поясов и cron. Распознает момент сброса и мгновенно корректирует квоту. |
| 🎛️ **Управление несколькими нодами** | Добавляйте, редактируйте и синхронизируйте несколько панелей Virtualizor во вкладке **Панели**. |
| 📊 **Телеметрия сервера** | Сглаженный мониторинг нагрузки CPU (без скачков), RAM, SWAP, диска и аптайма. |
| 🤖 **Telegram бот с бэкапами** | Моментальные алерты о переносе, пополнении баланса и прямая отправка файлов `.json` бэкапа в чат. Поддержка **SOCKS5**. |
| 💎 **Стеклянный интерфейс** | Темная и светлая темы, поддержка 6 языков (EN, FA, RU, ZH, TR, AR) с поддержкой RTL. |
| 📜 **Прозрачный аудит** | Детальный журнал операций, обновление и очистка истории в один клик. |

---

## ⚡ Быстрая установка одной командой (Ubuntu / Debian)

Запустите с правами `root`:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/a-salemi/Virtualizor-Traffic-Rollover/main/install.sh)"
```

---

## 🔄 Обновление установленной версии

```bash
cd /opt/virturoll && git pull && ./venv/bin/pip install -r backend/requirements.txt && systemctl restart virturoll
```

---

## ⚙️ Подключение панелей Virtualizor

1. В панели **Virtualizor** перейдите в **Configuration** -> **API Credentials** и создайте ключ.
2. В **Allowed IPs** обязательно укажите IP-адрес вашего сервера VirtuRoll.
3. В панели VirtuRoll откройте вкладку **Панели** -> **+ Добавить панель**.
4. Введите IP/домен, порт (`4085`), API Key и API Password.

---

## 🤖 Настройка Telegram бота и отправки бэкапов

1. Создайте бота через [@BotFather](https://t.me/BotFather) и получите токен.
2. Узнайте свой Chat ID через [@userinfobot](https://t.me/userinfobot).
3. В VirtuRoll перейдите в **Настройки** -> **Уведомления Telegram Bot** и сохраните данные.
4. Во вкладке **Резервное копирование** нажмите **Отправить бэкап в Telegram** для мгновенной доставки базы данных.

---

## 🛠️ Управление службой systemd

```bash
sudo systemctl status virturoll   # Проверить статус
sudo journalctl -u virturoll -f   # Просмотр логов
sudo systemctl restart virturoll  # Перезапуск
sudo systemctl stop virturoll     # Остановка
```

---

## 📄 Лицензия

Проект распространяется под лицензией [MIT License](LICENSE).  
Автор: Amir Salemi (2026).
