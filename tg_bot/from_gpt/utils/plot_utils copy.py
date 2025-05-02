import matplotlib.pyplot as plt
from datetime import datetime
import os
import random

# Для сохранения графиков
def _save_plot(fig, name_prefix="weather_plot"):
    os.makedirs("data/plots", exist_ok=True)
    filename = f"data/plots/{name_prefix}_{random.randint(1000,9999)}.png"
    fig.savefig(filename, bbox_inches="tight")
    plt.close(fig)
    return filename

# Температура
def plot_forecast(forecast):
    hours = [datetime.fromtimestamp(f["dt"]).strftime("%d %H:%M") for f in forecast]
    temp = [f["temp"] for f in forecast]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(hours, temp, marker="o", color="tab:red", label="Температура")
    ax.set_xticks(hours[::6])
    ax.set_xticklabels(hours[::6], rotation=45, ha="right")
    ax.set_title("🌡️ Температура на 2 суток")
    ax.set_ylabel("°C")
    ax.grid(True)
    ax.legend()

    return _save_plot(fig, "temp")

# Ветер и порывы
def plot_wind(forecast):
    hours = [datetime.fromtimestamp(f["dt"]).strftime("%d %H:%M") for f in forecast]
    wind_speed = [f["wind_speed"] for f in forecast]
    gusts = [f.get("wind_gust", 0) for f in forecast]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(hours, wind_speed, marker="o", label="Ветер (м/с)", color="tab:blue")
    ax.plot(hours, gusts, marker="x", label="Порывы", color="tab:orange")
    ax.set_xticks(hours[::6])
    ax.set_xticklabels(hours[::6], rotation=45, ha="right")
    ax.set_title("💨 Ветер и порывы")
    ax.set_ylabel("м/с")
    ax.grid(True)
    ax.legend()

    return _save_plot(fig, "wind")

# Осадки
def plot_precipitation(forecast):
    hours = [datetime.fromtimestamp(f["dt"]).strftime("%d %H:%M") for f in forecast]
    precipitation = [f.get("pop", 0) * 100 for f in forecast]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(hours, precipitation, color="tab:purple")
    ax.set_xticks(hours[::6])
    ax.set_xticklabels(hours[::6], rotation=45, ha="right")
    ax.set_title("🌧️ Вероятность осадков")
    ax.set_ylabel("%")
    ax.grid(True)

    return _save_plot(fig, "precip")

# Погодные явления (облачность и описание)
def plot_weather_description(forecast):
    hours = [datetime.fromtimestamp(f["dt"]).strftime("%d %H:%M") for f in forecast]
    clouds = [f["clouds"] for f in forecast]
    descriptions = [f["weather"][0]["description"].capitalize() for f in forecast]

    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(hours, clouds, color="gray", marker="o", label="Облачность (%)")
    ax1.set_xticks(hours[::6])
    ax1.set_xticklabels(hours[::6], rotation=45, ha="right")
    ax1.set_ylabel("Облачность (%)")
    ax1.set_title("⛅ Погодные условия")
    ax1.grid(True)

    # Описание погоды как подписи
    for i in range(0, len(hours), 6):
        ax1.text(i, clouds[i] + 5, descriptions[i], fontsize=7, ha="center", rotation=45)

    return _save_plot(fig, "description")
