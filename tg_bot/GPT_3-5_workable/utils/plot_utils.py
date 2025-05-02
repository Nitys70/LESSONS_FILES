import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO

def fig_to_bytes(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

def plot_temperature(timestamps, temps):
    fig, ax = plt.subplots()
    ax.plot(timestamps, temps, marker="o", color="tomato", label="Температура (°C)")
    ax.set_title("Прогноз температуры")
    ax.set_xlabel("Время")
    ax.set_ylabel("Температура, °C")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    ax.grid(True)
    fig.autofmt_xdate()
    return fig_to_bytes(fig)

def plot_wind(timestamps, speed, gusts):
    fig, ax = plt.subplots()
    ax.plot(timestamps, speed, marker="o", label="Скорость ветра", color="skyblue")
    ax.plot(timestamps, gusts, marker="x", label="Порывы ветра", color="steelblue")
    ax.set_title("Прогноз ветра")
    ax.set_xlabel("Время")
    ax.set_ylabel("Скорость, м/с")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    ax.grid(True)
    fig.autofmt_xdate()
    return fig_to_bytes(fig)

def plot_precipitation(timestamps, values):
    fig, ax = plt.subplots()
    ax.bar(timestamps, values, width=0.03, color="deepskyblue")
    ax.set_title("Прогноз осадков")
    ax.set_xlabel("Время")
    ax.set_ylabel("Осадки, мм")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    ax.grid(True)
    fig.autofmt_xdate()
    return fig_to_bytes(fig)

def plot_conditions(timestamps, conditions):
    fig, ax = plt.subplots()
    condition_codes = {cond: i for i, cond in enumerate(sorted(set(conditions)))}
    y = [condition_codes[c] for c in conditions]
    ax.plot(timestamps, y, marker="o", linestyle="None", color="orchid")
    ax.set_yticks(list(condition_codes.values()))
    ax.set_yticklabels(list(condition_codes.keys()))
    ax.set_title("Прогноз погодных условий")
    ax.set_xlabel("Время")
    ax.set_ylabel("Состояние")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %H:%M'))
    ax.grid(True)
    fig.autofmt_xdate()
    return fig_to_bytes(fig)
