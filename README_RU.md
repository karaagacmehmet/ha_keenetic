[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/akinin/ha_keenetic?style=flat&color=%23A349A4)](https://github.com/akinin/ha_keenetic)
# Интеграция Keenetic Router для Home Assistant
[English ver.](README.md)

Это пользовательская интеграция для маршрутизаторов Keenetic в Home Assistant. Она предоставляет подробную информацию о вашем роутере Keenetic, включая состояние WiFi сетей, ethernet портов и mesh-сети.

## Возможности

- Мониторинг системной информации роутера (CPU, память, время работы)
- Управление WiFi сетями (включение/выключение)
- Просмотр состояния и статистики ethernet портов
- Мониторинг узлов mesh-сети
- Просмотр детальной статистики интерфейсов

## Установка

### Через HACS (Рекомендуется)

1. Откройте HACS
2. Нажмите "Integrations"
3. Нажмите кнопку "+"
4. Найдите "Keenetic Router"
5. Нажмите "Install"
6. Перезагрузите Home Assistant

### Ручная установка

1. Скачайте последний релиз
2. Скопируйте папку `ha_keenetic` в директорию `custom_components`
3. Перезагрузите Home Assistant

## Настройка

1. Перейдите в Configuration > Integrations
2. Нажмите кнопку "+"
3. Найдите "Keenetic Router"
4. Введите данные вашего роутера:
   - IP адрес (по умолчанию: 192.168.1.1)
   - Порт (по умолчанию: 81)
   - Имя пользователя (по умолчанию: admin)
   - Пароль

## Поддерживаемые устройства

Интеграция протестирована со следующими моделями:
- Keenetic Giga
- Keenetic Hero 4g
- Keenetic Sprinter SE

Другие модели Keenetic также должны работать.

## Доступные сущности

### Сенсоры
- Системная информация (CPU, память, время работы)
- Состояние WiFi сетей
- Состояние Ethernet портов
- Состояние узлов Mesh-сети

### Переключатели
- WiFi сети (включение/выключение)

## Участие в разработке

Приветствуются любые предложения по улучшению проекта.

## Лицензия

Этот проект распространяется под лицензией MIT - подробности смотрите в файле [LICENSE](LICENSE).
