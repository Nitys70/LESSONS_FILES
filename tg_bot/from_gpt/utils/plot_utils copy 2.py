import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime

PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)

def save_plot(fig, name):
    path = os.path.join(PLOT_DIR, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path

def plot_temperature(timestamps, temps):
    fig, ax = plt.subplots()
    ax.plot(timestamps, temps, marker="o", label="Температура (°C)", color="tomato")
    ax.set_title("Прогноз температуры")
    ax.set_xlabel("Время")
    ax.set_ylabel("Температура, °C")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    ax.grid(True)
    fig.autofmt_xdate()
    return save_plot(fig, "temperature.png")

def plot_wind(timestamps, speed, gusts):
    fig, ax = plt.subplots()
    ax.plot(timestamps, speed, marker="o", label="Скорость ветра", color="skyblue")
    ax.plot(timestamps, gusts, marker="x", label="Порывы ветра", color="steelblue")
    ax.set_title("Прогноз ветра")
    ax.set_xlabel("Время")
    ax.set_ylabel("Скорость, м/с")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    return save_plot(fig, "wind.png")

def plot_precipitation(timestamps, values):
    fig, ax = plt.subplots()
    ax.bar(timestamps, values, width=0.03, color="deepskyblue")
    ax.set_title("Прогноз осадков")
    ax.set_xlabel("Время")
    ax.set_ylabel("Осадки, мм")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    ax.grid(True)
    fig.autofmt_xdate()
    return save_plot(fig, "precipitation.png")

def plot_conditions(timestamps, conditions):
    fig, ax = plt.subplots()
    condition_codes = {cond: i for i, cond in enumerate(sorted(set(conditions)))}
    y = [condition_codes[c] for c in conditions]
    ax.plot(timestamps, y, marker="o", linestyle="dashed", color="orchid")
    ax.set_yticks(list(condition_codes.values()))
    ax.set_yticklabels(list(condition_codes.keys()))
    ax.set_title("Прогноз погодных условий")
    ax.set_xlabel("Время")
    ax.set_ylabel("Состояние")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    ax.grid(True)
    fig.autofmt_xdate()
    return save_plot(fig, "conditions.png")