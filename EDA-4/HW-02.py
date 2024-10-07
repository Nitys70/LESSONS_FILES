# Произведем чтение данных и выведем первые 5 строк для изучения

print(123)
# Произведем чтение данных и выведем первые 5 строк для изучения

import pandas as pd

data = pd.read_csv('data/ds_salaries_SF.csv', index_col = 'Unnamed: 0')

display(data.head())
