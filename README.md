# **Проект 3.** Веб-сервис с прогнозом погоды для заданного маршрута

Weather Checker — это интерактивное веб-приложение, созданное с использованием Dash, которое позволяет проверять погодные условия на заданном маршруте, включая начальный, промежуточные и конечный города.

## Функциональность

- Пользователь вводит начальный, опционально промежуточные и конечный города.
- Приложение запрашивает данные о погоде через AccuWeather.
- Проверяются неблагоприятные погодные условия:
 - Температура ниже 20°C или выше 30°C.(наиболее комфортная температура)
 - Скорость ветра выше 40 км/ч. 
 - Вероятность осадков выше 70%. 

## Ответы на вопросы

Линейный график
- Линии хорошо отражают тенденции и позволяют выявить тренды, прост и интуитивен, особенно для временных данных. 
Столбчатый график
- Для отображения вероятности осадков или распределения значений параметров по разным городам, хорошо подходит для сравнения значений, таких как осадки в процентах
Улучшение пользовательского опыта с помощью интерактивных графиков
- Возможность выделения параметров: Пользователь может выбирать, какие линии отображать на графике (например, только температура или влажность).
-  Подсказки: При наведении на точку на графике отображать более понятную информацию (например, "День 1: Температура 25°С").
-  Географический маршрут, добавить интерактивную карту маршрута с указанием погодных условий в каждом городе.


### 1. Главная страница

- После запуска приложения перейдите по адресу:

http://127.0.0.1:8050

- На главной странице отобразится интерфейс для ввода данных о маршруте и выбора параметров прогноза. 

### 2. Ввод городов

- Перейдя на страницу:

http://127.0.0.1:8050

- Введите в поля начальный, опционально промежуточный и конечный город:
- Пример:
  - Начальный город: Москва
  - Конечный город: Санкт-Петербург
    
- После ввода данных выберите параметры:
  - Период прогноза (1–5 дней).
  - Метеопараметр для отображения на графике (температура, скорость ветра, вероятность осадков или влажность).
- Нажмите "Найти".

#### Результат успешного запроса:
На экране отобразятся:

- Прогноз погоды для всех указанных городов на выбранный период.
- Интерактивный график выбранного метеопараметра.
- Сообщения о благоприятных или неблагоприятных погодных 

#### Результат при ошибке ввода:

Если пользователь ввёл пробелы, то отобразиться ошибка:
- "Ошибка: Введите название "конечного/начального/...":

Если пользователь ввёл несуществующий город, то отобразиться ошибка:
- Город 'Пример' не найден.

Другие ошибки:
- Ошибка "номер":" Неверный API, Город или ресурс не найден, Ошибка сервера API, КВОта закончилась на API клююче
- Ошибка при получение данных о вероятности дождя 



Если в название города содержаться цифры, то отобразиться ошибка: 
- "Ошибка: Названия городов не должны содержать цифры."
