import flask
import requests
from flask import Flask, render_template, request

# Создаем экземпляр Flask приложения
app = Flask(__name__)

# API-ключ для доступа к AccuWeather API
API_KEY = "axg6AzdAAAMLmEfXuNjGB8RhfThj3fBW"

@app.route('/')
def index():
    return "Flask работает корректно"


@app.route("/check-weather", methods=["GET", "POST"])
def check_weather():
    """
    Обработка данных маршрута, получение погоды и проверка условий.
    """
    if request.method == "GET":
        return render_template("index.html")

    if request.method == "POST":
        start_city = request.form.get("start").strip()  # Получаем начальный город
        end_city = request.form.get("end").strip()  # Получаем конечный город

        # Проверяем, что оба поля не пустые
        if not start_city or not end_city:
                error = "Ошибка: Введите оба города. Поля не должны быть пустыми или состоять только из пробелов."
                return render_template("error.html", error_message=error)

        # Проверяем, что названия городов не содержат цифр
        if any(char.isdigit() for char in start_city) or any(char.isdigit() for char in end_city):
                error = "Ошибка: Названия городов не должны содержать цифры."
                return render_template("error.html", error_message=error)

        # Инициализация класса для работы с погодой
        weather_location = WeatherLocation(API_KEY)

        try:
            # Получаем ключи местоположений для обоих городов
            start_key = weather_location.get_key_on_city(start_city)
            end_key = weather_location.get_key_on_city(end_city)

            # Получаем погодные данные для обоих городов
            start_weather = weather_location.get_weather_on_key(start_key)
            end_weather = weather_location.get_weather_on_key(end_key)


            # Проверяем, хорошие ли погодные условия
            start_weather_status = weather_location.check_bad_weather(
                start_weather["Температура (°C)"],
                start_weather["Скорость ветра (км/ч)"],
                start_weather["Вероятность осадков (%)"]
            )

            end_weather_status = weather_location.check_bad_weather(
                end_weather["Температура (°C)"],
                end_weather["Скорость ветра (км/ч)"],
                end_weather["Вероятность осадков (%)"]
            )

            # Отправляем результаты на страницу
            return render_template("result.html",
                                   start=start_city,
                                   end=end_city,
                                   start_weather=start_weather,
                                   end_weather=end_weather,
                                   start_weather_status=start_weather_status,
                                   end_weather_status=end_weather_status)

        except Exception as e:
            # Возвращаем ошибку
            return render_template("error.html", error_message=str(e))


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

    def get_weather_rain_on_key(self, locationKey):
        """
        Получение текущих погодных данных о вероятности осадков в течение часа по ключу местоположения, так как другая API не предоставляет таких данных.
        """
        url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/1hour/{locationKey}"
        params = {
            "apikey": self.api_key,  # API-ключ
            "details": "true",  # Полные данные
            "language": "ru-ru"  # Язык ответа
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            rain = response.json()[0].get("PrecipitationProbability", 0)  # Извлекаем вероятность дождя
            return rain
        # Проверяем статус ответа
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
            "Вероятность осадков (%)": self.get_weather_rain_on_key(locationKey)                                            # Вероятность осадков (может отсутствовать)
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

    def get_key_on_city(self, city):
        """
        Получение ключа местоположения по городу.
        """
        url = "http://dataservice.accuweather.com/locations/v1/cities/search"
        params = {
            "apikey": self.api_key,  # API-ключ
            "q": f"{city}",          # Город
            "language": "ru-ru"      # Язык ответа
        }
        # Выполняем GET-запрос к API
        response = requests.get(url, params=params)

        # Проверяем статус ответа и обрабатываем данные
        if response.status_code == 200:
            try:
                locationKey = response.json()[0]["Key"]
                return locationKey
            except IndexError:
                # Если API не возвращает город, выбрасываем ошибку
                raise Exception(f"Город '{city}' не найден.")
        else:
            error_message = self.handle_api_error(response)
            raise Exception(f"Ошибка при получении ключа для города '{city}': {error_message}")


    def check_bad_weather(self, temperature: float, wind_speed: float, precipitation_probability: float):
        """
            Функция для определения неблагоприятных погодных условий.

            Параметры:
            - temperature (float): Температура в градусах Цельсия.
            - wind_speed (float): Скорость ветра в км/ч.
            - precipitation_probability (float): Вероятность осадков в %.

            Условия:
            - температура ниже 20°C или выше 30°C,
            - скорость ветра выше 40 км/ч,
            -вероятность осадков выше 70%

            Возвращает:
            - "Хорошая погода" / "Плохая погода"
        """
        if (temperature < 20 or temperature > 30) or (wind_speed > 40) or (precipitation_probability > 70):
            return "Плохая погода"
        return  "Хорошая погода"

    def handle_api_error(self, response):
        """
        Обрабатывает ошибку API и возвращает точное сообщение.
        """
        if response.status_code == 401:
            return "Неверный API-ключ."
        elif response.status_code == 404:
            return "Город или ресурс не найден."
        elif response.status_code == 500:
            return "Ошибка сервера API."
        else:
            return f"Ошибка {response.status_code}: {response.text}"


if __name__ == '__main__':
    # Запускаем Flask приложение
    app.run(debug=True)



#
city = "Москва"

print(
    WeatherLocation(API_KEY).get_key_on_city(city),     # Получаем ключ местоположения
    WeatherLocation(API_KEY).get_weather_on_key(               # Получаем данные погоды по ключу
        WeatherLocation(API_KEY).get_key_on_city(city)  # Вызов метода получения ключа
   )
 )

# temperature = -9.0
# wind_speed = 35.0
# precipitation_probability = 50.0
# print(WeatherLocation(API_KEY).check_bad_weather(45, 70, 30))
#
# #Тестовые координаты
# lat = '37.7749'   # Широта
# lon = '-122.4194' # Долгота
# #
# Получение ключа местоположения и данных о погоде
# print(
#     WeatherLocation(API_KEY).get_key_on_lat_lon(lat, lon),     # Получаем ключ местоположения
#     WeatherLocation(API_KEY).get_weather_on_key(               # Получаем данные погоды по ключу
#         WeatherLocation(API_KEY).get_key_on_lat_lon(lat, lon)  # Вызов метода получения ключа
#     )
# )
