import asyncio
from typing import Literal
import math

import requests
from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import aiohttp
import accuweather


# API-ключ для доступа к AccuWeather API
API_KEY = "9BgIFbYQz6Ma2gJe3iSmZd8SWVmadiKm"


class WeatherLocation():
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_key_on_city(self, city: str) -> str:
        url = "http://dataservice.accuweather.com/locations/v1/cities/search"
        params = {
            "apikey": self.api_key,
            "q": f"{city}",
            "language": "ru-ru"
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            try:
                locationKey = response.json()[0]["Key"]
                return locationKey
            except IndexError:
                raise ValueError(f"Город '{city}' не найден.")
        else:
            error_message = self.handle_api_error(response)
            raise RuntimeError(f"Ошибка при получении ключа для города '{city}': {error_message}")

    def get_weather_on_key(self, location_key: str) -> dict:
        return asyncio.run(self._get_weather_on_key(location_key))

    async def _get_weather_on_key(self, location_key: str) -> dict:
        async with aiohttp.ClientSession() as session:
            accu = accuweather.AccuWeather(
                api_key=self.api_key,
                session=session,
                location_key=location_key,
                language="ru-ru",
            )

            try:
                weather_data = await accu.async_get_current_conditions()
            except accuweather.exceptions.RequestsExceededError:
                raise RuntimeError("Закончилась квота на ключе")
            except accuweather.exceptions.InvalidApiKeyError:
                raise RuntimeError("Неправильный ключ апи")
            except accuweather.exceptions.InvalidCoordinatesError:
                raise ValueError("Неправильные координаты")
            except accuweather.exceptions.ApiError:
                raise RuntimeError("Произошла ошибка на стороне AccuWeather")
            except Exception as e:
                raise RuntimeError(f"Произошла неизвлестная ошибка: {e}")

            result = {
                "Температура (°C)": weather_data["Temperature"]["Metric"]["Value"],
                "Скорость ветра (км/ч)": weather_data["Wind"]["Speed"]["Metric"]["Value"],
                "Вероятность осадков (%)": self.get_weather_rain_on_key(location_key),
                "Влажность (%)": weather_data["RelativeHumidity"],
            }
            return result

    def get_weather_on_key_period(self, location_key: str, days: int) -> list[dict]:
        return asyncio.run(self._get_weather_on_key_period(location_key, days))

    async def _get_weather_on_key_period(self, location_key: str, days: int) -> list[dict]:
        if days == 1:
            return [await self._get_weather_on_key(location_key)]
        
        async with aiohttp.ClientSession() as session:
            accu = accuweather.AccuWeather(
                api_key=self.api_key,
                session=session,
                location_key=location_key,
                language="ru-ru",
            )

            try:
                weather_data_daily = (await accu.async_get_daily_forecast(days=5))[:days]
            except accuweather.exceptions.RequestsExceededError:
                raise RuntimeError("Закончилась квота на ключе")
            except accuweather.exceptions.InvalidApiKeyError:
                raise RuntimeError("Неправильный ключ апи")
            except accuweather.exceptions.InvalidCoordinatesError:
                raise ValueError("Неправильные координаты")
            except accuweather.exceptions.ApiError:
                raise RuntimeError("Произошла ошибка на стороне AccuWeather")
            except Exception as e:
                raise RuntimeError(f"Произошла неизвлестная ошибка: {e}")
            
            weather_data_days = []
            for weather_data in weather_data_daily:
                weather_data_days += [{
                    "Температура (°C)": round((weather_data["TemperatureMax"]["Value"] + weather_data["TemperatureMin"]["Value"]) / 2, 2),
                    "Скорость ветра (км/ч)": weather_data["WindDay"]["Speed"]["Value"],
                    "Вероятность осадков (%)": self.get_weather_rain_on_key(location_key),
                    "Влажность (%)": weather_data["RelativeHumidityDay"]["Average"],
                }]
            
            return weather_data_days

    def get_weather_rain_on_key(self, locationKey: str):
        url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/1hour/{locationKey}"
        params = {
            "apikey": self.api_key,
            "details": "true",
            "language": "ru-ru"
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            rain = response.json()[0].get("PrecipitationProbability", 0)
            return rain
        else:
            error_message = self.handle_api_error(response)
            raise Exception(f"Ошибка при получении данных о вероятности дождя: {error_message}")

    def get_report(self, **keys) -> html.Ul:
        report = []
        for key, value in keys.items():
            report += [html.Li(f"{key}: {value}")]
        return html.Ul(report)

    def check_bad_weather(self, temperature: float, wind_speed: float, precipitation_probability: float, *other):
        """
            Функция для определения неблагоприятных погодных условий.

            Параметры:
            - temperature (float): Температура в градусах Цельсия.
            - wind_speed (float): Скорость ветра в км/ч.
            - precipitation_probability (float): Вероятность осадков в %.

            Условия:
            - температура ниже 20°C или выше 30°C,
            - скорость ветра выше 40 км/ч,
            - вероятность осадков выше 70%

            Возвращает:
            - "Хорошая погода" / "Плохая погода"
        """
        if (temperature < 20 or temperature > 30) or (wind_speed > 40) or (precipitation_probability > 70):
            return "Плохая погода"
        return "Хорошая погода"

    def handle_api_error(self, response: requests.Response) -> str:
        if response.status_code == 401:
            return "Неверный API-ключ."
        elif response.status_code == 404:
            return "Город или ресурс не найден."
        elif response.status_code == 500:
            return "Ошибка сервера API."
        elif response.status_code == 503:
            return "Квота закончилась на API ключе"
        else:
            return f"Ошибка {response.status_code}: {response.text}"

weather_api = WeatherLocation(API_KEY)

# Инициализация Dash-приложения с темой DARKLY
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Параметры для отображения
parameters = ["Температура (°C)", "Скорость ветра (км/ч)", "Вероятность осадков (%)", "Влажность (%)"]

# Основной layout приложения
app.layout = html.Div([
    html.H1("Проверка погоды для вашего путешествия", className='text-center mb-4', style={'color': '#7FDBFF'}),
    dbc.Col([
        dbc.Row([
            dbc.Card([
                dbc.CardBody([
                    dcc.Input(id="start-city", placeholder="Введите первый город (например, Москва)", debounce=True, className="form-control mb-2")
                ])
            ], className="mb-3")
        ]),
        dbc.Row([
            dbc.Card([
                dbc.CardBody([
                    dcc.Input(id="between-cities", placeholder="Введите промежуточные города через разделитель в виде \",\" (Новгород, Петрозаводск)", debounce=True, className="form-control mb-2")
                ])
            ], className="mb-3")
        ]),
        dbc.Row([
            dbc.Card([
                dbc.CardBody([
                    dcc.Input(id="end-city", placeholder="Введите конечный город (например, Санкт-Петербург)", debounce=True, className="form-control mb-2")
                ])
            ], className="mb-3")
        ]),
    ], align="center"),
    dbc.Row([
        dbc.Col([
            dbc.Button('Найти', id='find-btn', color='primary', className="mt-3 mx-auto", style={"width": "200px"})
        ], width=12, className="text-center")
    ], className="mb-4"),
    html.Div(id="error-message", style={"color": "red", "text-align": "center", "margin-bottom": "20px"}),
    html.Div([
        html.Label("Период (дни)"),
        dcc.Slider(id="period-slider", min=1, max=5, step=1, value=1, marks={i: f"{i} день" for i in range(1, 7+1)})
    ], style={"margin-bottom": "20px"}),
    html.Div([
        html.Label("Выберите параметр для отображения:"),
        dcc.Dropdown(
            id='parameter-dropdown',
            options=[{"label": param, "value": param} for param in parameters],
            value="Температура (°C)",
            clearable=False,
            style={"color": "black"},
        ),
    ], style={"width": "90%", "margin": "20px auto"}),
    dcc.Graph(id='weather-graph', config={'displayModeBar': False}),
    html.H3(id="weather-status", className="mt-4"),
])

# Callback для обновления данных о погоде
@app.callback(
    [Output('weather-status', 'children'),
     Output('weather-graph', 'figure'),
     Output('error-message', 'children')],
    [Input('find-btn', 'n_clicks')],
    [State('start-city', 'value'),
     State('between-cities', 'value'),
     State('end-city', 'value'),
     State('parameter-dropdown', 'value'),
     State('period-slider', 'value')]
)
def update_weather(n_clicks, start_city: str, _between_cities: str, end_city: str, selected_param: str, period: int):
    try:
        # Проверка ввода городов
        if not start_city or not start_city.strip():
            raise Exception("Введите название начального города.")
        if not end_city or not end_city.strip():
            raise Exception("Введите название конечного города.")

        start_city_key = weather_api.get_key_on_city(start_city.strip())
        end_city_key = weather_api.get_key_on_city(end_city.strip())
        
        between_city_keys = {}
        _between_cities = _between_cities or ""
        for city in _between_cities.strip().split(","):
            if city == "":
                continue

            city = city.strip()
            between_city_keys[city] = weather_api.get_key_on_city(city)

        start_weather = weather_api.get_weather_on_key_period(start_city_key, days=period)
        end_weather = weather_api.get_weather_on_key_period(end_city_key, days=period)
        between_weather = {}
        for city, city_key in between_city_keys.items():
            between_weather[city] = weather_api.get_weather_on_key_period(city_key, days=period)
        weathers = [start_weather, *between_weather.values(), end_weather]

        start_weather_status = [weather_api.check_bad_weather(*item.values()) for item in start_weather]
        end_weather_status = [weather_api.check_bad_weather(*item.values()) for item in end_weather]
        between_weather_status = {}
        for city in between_city_keys.keys():
            between_weather_status[city] = [weather_api.check_bad_weather(*item.values()) for item in between_weather[city]]
        _weather_s = [start_weather_status, *between_weather_status.values(), end_weather_status]

        weather_status = []
        cities = [start_city, *between_city_keys.keys(), end_city]
        for i, weather_vals in enumerate([start_weather, *between_weather.values(), end_weather]):
            city_weather: list = [
                html.H3(f"Погода в {cities[i]}"),
            ]
            for day, weather in enumerate(weather_vals, start=1):
                city_weather.append(
                    html.Li([
                        html.P(f"День {day}: {_weather_s[i][day-1]}"),
                        weather_api.get_report(**weather)
                    ])
                )
            weather_status.append(html.Div(city_weather))

        x_values = [f"Начальный город - {start_city}", *list(between_weather.keys()), f"Конечный город - {end_city}"]
        
        figure = go.Figure()
        for i, city_weather in enumerate(weathers):
            city_name = x_values[i]
            y_values = [item[selected_param] for item in city_weather]
            figure.add_trace(go.Scatter(
                x=list(range(1, period + 1)),
                y=y_values,
                mode="lines+markers",
                name=f"{city_name}",
            ))
        
        figure.update_layout(
            title=f"Данные погоды: {selected_param}",
            xaxis_title="Дни",
            yaxis_title=selected_param,
            template="plotly_white",
            xaxis=dict(
                tickmode="array",
                tickvals=list(range(1, period + 1)),
            ),
        )
        
        # y_values = [item[selected_param] for item in [start_weather[0], *between_weather.values(), end_weather[0]]]

        # figure.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines+markers', name=selected_param))
        # figure.update_layout(
        #     title=f"График: {selected_param}",
        #     xaxis_title="Города",
        #     yaxis_title=selected_param,
        #     template="plotly_dark",
        # )

        return weather_status, figure, None

    except Exception as e:
        # В случае ошибки
        error_message = html.Div([
            html.H4("Ошибка", style={'color': 'red'}),
            html.P(str(e))
        ])

        # raise e

        return "", go.Figure(), error_message


if __name__ == '__main__':
    app.run(use_reloader=True)
