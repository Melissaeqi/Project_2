import flask
import requests
from flask import Flask, render_template, request

# Создаем экземпляр Flask приложения
app = Flask(__name__)

# API-ключ для доступа к AccuWeather API
API_KEY = "G8jXGh6NmvTSBHTZq4WhT14gLOi6amFj"

@app.route('/')
def index():
    # Главная тестовая страница Flask приложения
    return 'Flask работает корректно'

# Класс для работы с местоположением и погодой через API AccuWeather
class WeatherLocation():
    def __init__(self, api_key):
        # Инициализация объекта с переданным API-ключом
        self.api_key = api_key

    def get_key_on_lat_lon(self, lat, lon):
        """
        Получение ключа местоположения по координатам (широта и долгота).
        """
        url = "http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
        params = {
            "apikey": self.api_key, # API-ключ
            "q": f"{lat},{lon}",    # Координаты (широта, долгота)
            "language": "ru-ru"     # Язык ответа
        }
        # Выполняем GET-запрос к API
        response = requests.get(url, params=params)

        # Проверяем статус ответа и обрабатываем данные
        if response.status_code == 200:
            locationKey = response.json()["Key"]  # Извлекаем ключ местоположения
            return locationKey
        elif response.status_code == 401:
            raise Exception("Неверный API-ключ.")
        elif response.status_code == 404:
            raise Exception("Ресурс не найден.")
        else:
            raise Exception(f"Ошибка {response.status_code}: {response.text}")

    def get_weather_on_key(self, locationKey):
        """
        Получение текущих погодных данных по ключу местоположения.
        """
        url = f"http://dataservice.accuweather.com/currentconditions/v1/{locationKey}"
        params = {
            "apikey": self.api_key,  # API-ключ
            "details": "true",      # Полные данные
            "language": "ru-ru"     # Язык ответа
        }
        # Выполняем GET-запрос к API
        response = requests.get(url, params=params)

        # Извлекаем данные из ответа
        weather_data = response.json()
        result = {
            "Температура (°C)": weather_data[0]["Temperature"]["Metric"]["Value"],        # Температура в градусах Цельсия
            "Влажность (%)": weather_data[0]["RelativeHumidity"],                         # Влажность в процентах
            "Скорость ветра (км/ч)": weather_data[0]["Wind"]["Speed"]["Metric"]["Value"], # Скорость ветра
            "Вероятность дождя (%)": weather_data[0].get("PrecipitationProbability", 0)   # Вероятность осадков (может отсутствовать)
        }
        # Проверяем статус ответа
        if response.status_code == 200:
            return result
        elif response.status_code == 401:
            raise Exception("Неверный API-ключ.")
        elif response.status_code == 404:
            raise Exception("Ресурс не найден.")
        else:
            raise Exception(f"Ошибка {response.status_code}: {response.text}")

    def check_bad_weather(self, temperature: float, wind_speed: float, precipitation_probability: float):
        """
            Функция для определения неблагоприятных погодных условий.

            Параметры:
            - temperature (float): Температура в градусах Цельсия.
            - wind_speed (float): Скорость ветра в км/ч.
            - precipitation_probability (float): Вероятность осадков в %.

            Условия:
            - температура ниже -10°C или выше 30°C,
            - скорость ветра выше 40 км/ч,
            -вероятность осадков выше 70%

            Возвращает:
            - "Хорошая погода" / "Плохая погода"
        """
        if (temperature < -10 or temperature > 30) or (wind_speed > 40) or (precipitation_probability > 70):
            return "Плохая погода"
        return  "Хорошая погода"


temperature = -9.0
wind_speed = 35.0
precipitation_probability = 50.0
print(WeatherLocation(API_KEY).check_bad_weather(45, 70, 30))

# # Тестовые координаты
# lat = '37.7749'   # Широта
# lon = '-122.4194' # Долгота
#
# # Получение ключа местоположения и данных о погоде
# print(
#     WeatherLocation(API_KEY).get_key_on_lat_lon(lat, lon),     # Получаем ключ местоположения
#     WeatherLocation(API_KEY).get_weather_on_key(               # Получаем данные погоды по ключу
#         WeatherLocation(API_KEY).get_key_on_lat_lon(lat, lon)  # Вызов метода получения ключа
#     )
# )

if __name__ == '__main__':
    # Запускаем Flask приложение
    app.run(debug=True)
