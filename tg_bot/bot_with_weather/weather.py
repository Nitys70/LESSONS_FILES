import requests
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime
from internal_data import weather_api
import pandas as pd

import requests
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime
import pandas as pd

async def generate_weather_plot(lat: float, lon: float, api_key: str) -> BytesIO:
    """Генерирует график погоды"""
    url = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&appid={weather_api}&lang=ru'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        forecast_df = pd.DataFrame(data['hourly'])

        feats_to_convert = ['dt']

        def ts_convert(ts):
            return datetime.fromtimestamp(ts).strftime('%d-%m-%Y %H:%M:%S')

        for feat in feats_to_convert:
            forecast_df[feat] = forecast_df[feat].apply(ts_convert)
        
        def description_extract(data):
            return f"{data[0]['main']} : {data[0]['description']}"
            
        forecast_df['info'] = forecast_df['weather'].apply(description_extract)
        forecast_df = forecast_df.drop('weather', axis=1)
        
        plt.figure(figsize=(14,6))
        line_graph = sns.lineplot(
            data=forecast_df,
            x='dt',
            y='temp'
        )

        line_graph.grid()
        line_graph.set_ylabel('Температура воздуха', fontsize=16)
        line_graph.set_xlabel('')
        plt.tick_params(axis='x', labelrotation=90)

        line_title_name = f'Прогноз температуры за период {forecast_df.iloc[0]["dt"]} - {forecast_df.iloc[47]["dt"]}'
        line_graph.set_title(line_title_name, fontsize=16)
        
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
        
    except Exception as e:
        print(f"Error generating weather plot: {e}")
        raise