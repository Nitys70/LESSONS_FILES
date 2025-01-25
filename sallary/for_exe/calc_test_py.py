import os
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

print('Программа для расчета доходов. \n \
Разместите файл в формате .xlsx в ту же папку, где находится файл .exe \n \
Ответьте на вопросы программы. \n \
Результат будет загружен в папку results (создастся автоматически) \n \
Для продолжения нажмите ENTER')

stopping_for_reading = input('')

dir_name = os.getcwd()

dir_name = dir_name.replace('\\', '/')
dir_name = dir_name + '/'
file_list = os.listdir(dir_name)
print('DIR NAME:', dir_name)
print('#   File name')
print('_________________')
for ind, name in enumerate(file_list):
    print(ind, ' ', name)
    
file_num = int(input('Введите номер файла, который будет обрабатываться: \n'))

file_path = dir_name + '/' + str(file_list[file_num])

df = pd.read_excel(f"{file_path}")

#####################################################
# Создаем DF из исходного графика сменности
# = df_new 

# Список месяцев в году - понадобится в преобразованиях
month_list = ['Январь', 'Февраль', 'Март', 'Апрель', 
              'Май', 'Июнь', 'Июль', 'Август', 
              'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# Переименуем признак в конечный, на данном этапе в нем много 
# лишнего, по итогу будут месяцы.
df = df.rename(columns={'СОГЛАСОВАНО': 'month'})

def white_space_del(month):
    """Удаление начальных или конечных пробелов значений
    Введен обработчик исключений, т.к. все данные в DF нас 
    не инетересуют, нужны только названия месяцев - они точно 
    обрабатываются функцией

    Args:
        month (str): Значение признака столбца "месяц"

    Returns:
        str : очищенные от пробелов значения 
    """
    
    try:
        return month.strip()
    except:
        return month
    
df['month'] = df['month'].apply(white_space_del)

# Создаем новый DF, где значениях признака месяц только месяцы
df_new = df[df.month.isin(month_list)]

# n - счетчик итераций цикла
# Переименуем колонки (начиная со второй в цифровом порядке - 
# будет соответствие чилам месяца).
n = 1
for i in range(1,96):
    df_new = df_new.rename(columns={df_new.columns[i]: f'{n}'})
    n+=1

# Удалим признаки выше 32 по названию включительно    
df_new.drop(df_new.columns[list(range(32,96))], axis=1, inplace=True)

# Сбрасываем индекс и удаляем старый
df_new = df_new.reset_index()

df_new.drop(df_new.columns[0], axis=1, inplace=True)
# Здесь на выходе получили и индексы по порядку, в соответствии 
# 0 - январь, 11 - декабрь. 
# Колонка 0 (1) - название месяца, далее - числа месяца
df_new



#####################################################
# Создаем копию DF и удаляем признак месяца, 
# Итого, будет DF с посчитанными часами для расчета
# = df_hours

df_hours = df_new.copy()
df_hours = df_hours.drop('month', axis=1)

def hours_convert(hour):
    """Преобрузование текстовых значений часов в текстовые
    Конвертируются ночные часы в суммарные к расчету, 
    отсутствием часов заменяется нулевым значением

    Args:
        hour (str): строкове значение из графика
    Returns:
        float : числовые значения для дальнейших расчетов 
    """

    if '/' in hour:
        day = int(hour.rsplit('/', 1)[0])
        night = int(hour.rsplit('/', 1)[1])
        total = day + 0.4*night
        return total
    
    if str(hour).isdigit():
        return float(hour)
    
    else:
        return 0

df_hours = df_hours.map(hours_convert)


#####################################################
# Создание ДФ с указанием отработанных часов в 
# праздничные дни, подлежащие дополнительной оплате
# = df_holidays_hours

# ДФ оригинального графика
df_schedule = df_new.copy()
df_schedule = df_schedule.drop('month', axis=1)

# Создаем ДФ с часами в праздничные дни, значения - нули, 
# потом будем его заполнять данными
df_holidays_hours = df_new.copy()
df_holidays_hours = df_holidays_hours.drop('month', axis=1)
df_holidays_hours = df_holidays_hours.map(lambda x: 0)

# Список праздничных дней, элементы списка - кортежи, где 
# первый индекс - месяц, второй индекс - число
holidays_list = [(0,0), (0,1), (0,2), (0,3), 
                 (0,4), (0,5), (0,6), (0,7), 
                 (1,22), (2,7), (4,0), (4,8), 
                 (5,11), (10,3)
                 ]

# Функция заполнения праздничными часами при их наличии
def holidays(day):
    if '/' in day:
        result = int(list(day.split('/'))[0])
        return result
    else:
        try:
            result = int(day)
            return result
        except:
            return 0

# Заполнение ДФ df_holidays_hours отработанными часами в 
# праздничные дни при помощи функции выше        
for elem in holidays_list:
    df_holidays_hours.iat[elem[0], elem[1]] = \
        holidays(df_schedule.loc[elem[0]][elem[1]])
        
#####################################################
# Создание ДФ с суммарным количеством часов
# = df_hours_total

df_hours_total = df_hours + df_holidays_hours


#####################################################
# Создаем ДФ со значениями ЧТС 
# = df_chts / chts_df_summary (- справочный с изм)
 
# Списки ЧТС и их дат, на основе создадим справочный DF
chts_list = list()
date_chts_list = list()

# Создание копии DF для заполнения значениями ЧТС
df_chts = df_hours.copy()

# Запрос значения ЧТС
chts = input('Введите часовую тарифную ставку на 1 января (~210,32): \n')

chts = chts.replace(',', '.')
chts = float(chts)

# Добавим данные в списки
chts_list.append(chts)
date_chts_list.append('01-01')

# Заполнение значений DF значениями ЧТС
df_chts = df_chts.map(lambda x: chts)

# Функция для внесения изменений ЧТС в DF 
def chts_changes():
    """Функция для корректировки DF с ЧТС, 
    позволяет вносить данные, по датам
    """
    
    # Запрос данных об изменениях
    date_of_change = input('Напишите дату изменения и ее размер в формате ДД-ММ-ЧТС (~11-12-234,45): \n')
    
    # Создание переменных дня, месяца изменений, и нового значения
    day, month, chts = date_of_change.split('-')
    
    # Приведением к расчетным типам данных
    day = int(day) 
    month = int(month)
    chts = chts.replace(',', '.')
    chts = float(chts)
    
    # Значения для подбивки с индексами
    current_month = month - 1
    current_day = day - 1
    
    # Обновление значений DF новыми
    df_chts.loc[month:12] = df_chts.loc[month:12].map(lambda x: chts)
    df_chts.loc[current_month][current_day:31] = df_chts.loc[current_month][current_day:31].map(lambda x: chts)
    
    # Добавим данные в списки
    chts_list.append(chts)
    date_chts_list.append(f'{day}-{month}')
    
    # Запрос на наличией дополнительных изменений
    more_changes = int(input('Менялась ли еще ЧТС? Да - 1, нет - 0: \n'))
    
    # В случае дополнительных изменений - повторный вызов функции 
    if more_changes == 1:
        chts_changes()
    
# Запрос о наличии изменений в ЧТС    
if_not_one_chts = int(input('Менялась ли ЧТС в течении года? 1- да, 0 - нет: \n'))

# Если ЧТС менялся - вызов функции на внесение изменений
if if_not_one_chts != 0:
    chts_changes()

# Справочный (архивный) DF с данными по изменениям    
chts_df_summary = pd.DataFrame({'ЧТС': chts_list, 'Дата': date_chts_list})


#####################################################
# Создаем ДФ с северными надбавками (полярки)
# = df_north_ratio / north_ratio_df_summary (- справочный с изм)

# Списки северных надбавок и их дат, на основе создадим справочный DF
north_ratio_list = list()
date_chts_list = list()

# Создание копии DF для заполнения значениями ЧТС
df_north_ratio = df_hours.copy()

# Запрос значения ЧТС
north_ratio = input('Введите северную надбавку (Полярку) на 1 января в процентах (~50): \n')

north_ratio = int(north_ratio)/100

# Добавим данные в списки
north_ratio_list.append(north_ratio)
date_chts_list.append('01-01')

# Заполнение значений DF значениями ЧТС
df_north_ratio = df_north_ratio.map(lambda x: north_ratio)

# Функция для внесения изменений ЧТС в DF 
def north_ratio_changes():
    """Функция для корректировки DF с Поляркой, 
    позволяет вносить данные, по датам
    """
    
    # Запрос данных об изменениях
    date_of_change = input('Напишите дату изменения и размер в формате ДД-ММ-Полярка (~11-12-70): \n')
    
    # Создание переменных дня, месяца изменений, и нового значения
    day, month, north_ratio = date_of_change.split('-')
    
    # Приведением к расчетным типам данных
    day = int(day) 
    month = int(month)
    north_ratio = north_ratio.replace(',', '.')
    north_ratio = int(north_ratio)/100
    
    # Значения для подбивки с индексами
    current_month = month - 1
    current_day = day - 1
    
    # Обновление значений DF новыми
    df_north_ratio.loc[month:12] = df_north_ratio.loc[month:12].map(lambda x: north_ratio)
    df_north_ratio.loc[current_month][current_day:31] = df_north_ratio.loc[current_month][current_day:31].map(lambda x: north_ratio)
    
    # Добавим данные в списки
    north_ratio_list.append(north_ratio)
    date_chts_list.append(f'{day}-{month}')
    
    # Запрос на наличией дополнительных изменений
    more_changes = int(input('Менялась ли еще Полярка? Да - 1, нет - 0: \n'))
    
    # В случае дополнительных изменений - повторный вызов функции 
    if more_changes == 1:
        north_ratio_changes()
    
# Запрос о наличии изменений в ЧТС    
if_not_one_chts = int(input('Менялась ли Полярка в течении года? 1- да, 0 - нет: \n'))

# Если ЧТС менялся - вызов функции на внесение изменений
if if_not_one_chts != 0:
    north_ratio_changes()

# Справочный (архивный) DF с данными по изменениям    
north_ratio_df_summary = pd.DataFrame({'Полярка': north_ratio_list, 'Дата': date_chts_list})


#####################################################
# Создаем ДФ с районными коэфициентами (80 процентов)
# = df_region_coef 

df_region_coef = df_hours.copy()
df_region_coef = df_region_coef.map(lambda x: 0.8)

#####################################################
# Создаем ДФ с премиями (ежемесячными)
# df_benefits / benefits_perc_df_summary (- справочный с изм)

# Создаем ДФ с размером ежемесячной премии (стандарт - 40 %)
df_benefits = df_hours.copy()

df_benefits = df_benefits.map(lambda x: 0.4)

# Создаем списки для фиксации данных (сформируем далее ДФ на них)
benefits_perc_list = ['40']
benefits_date_list = ['01.01-31.12']

# Функция внесения изменений в ДФ с размерами премиальной части
def benefits_changes():
    """Функция для корректировки DF с размером ежемесячной премии, 
    позволяет вносить данные, по датам
    """
    
    # Запрос данных об изменениях
    date_of_change = input('Напишите даты изменений и ее размер в формате ДД-ММ-ДД-ММ-Процент (~01-12-31-12-20): \n')
    
    # Создание переменных дня, месяца изменений, и нового значения
    day_1, month_1, day_2, month_2, benefit = date_of_change.split('-')
    
    # Приведением к расчетным типам данных
    day_1 = int(day_1) 
    month_1 = int(month_1)
    day_2 = int(day_2) 
    month_2 = int(month_2)
    benefit = benefit.replace(',', '.')
    benefit = int(benefit)/100
    
    # Значения для подбивки с индексами
    current_month_1 = month_1 - 1
    current_day_1 = day_1 - 1
    current_month_2 = month_2 - 1
    current_day_2 = day_2
    
    # Количество месяцев в течении которых премия была отличной от стандартной
    month_qnt = current_month_2 - current_month_1 + 1

    # Цикл обработки и внесения изменений (настроен исходя из количества 
    # месяцев, в которых были изменения, при помощи условий)
    for n in range(month_qnt):
                
        if n == 0 and month_qnt == 1:

            df_benefits.loc[(current_month_1 + n)][current_day_1:current_day_2] = \
                df_benefits.loc[(current_month_1 + n)][current_day_1:current_day_2]\
                .map(lambda x: benefit)

            continue
            
        if (n == 0) and (month_qnt != 1):
            
            df_benefits.loc[current_month_1][current_day_1:31] = \
                df_benefits.loc[current_month_1][current_day_1:31].apply(lambda x: benefit)

            continue
        
        if n == (len(range(month_qnt)) - 1):
            
            df_benefits.loc[(current_month_1 + n)][0:current_day_2] = \
        df_benefits.loc[(current_month_1 + n)][0:current_day_2]\
            .map(lambda x: benefit)

            continue

        else:
            
            row_index = current_month_1 + n
            df_benefits.loc[row_index] = \
                df_benefits.loc[row_index].map(lambda x: benefit)
            
            continue
            

    # Добавим данные в списки
    benefits_perc_list.append(int(benefit*100))
    benefits_date_list.append(f'{day_1}.{month_1} - {day_2}.{month_2}')
    
    # Запрос на наличией дополнительных изменений
    more_changes = int(input('Менялась ли еще Премия? Да - 1, нет - 0: \n'))
    
    # В случае дополнительных изменений - повторный вызов функции 
    if more_changes == 1:
        benefits_changes()

# Запрос на наличие изменений от стандартного размера премии
is_benefits_changed = int(input('Ежемесячная премия менялась? 1 - да, 0 - нет: \n'))

# Вызов функции внесения изменений, если таковые имеются
if is_benefits_changed != 0:
    benefits_changes()

# Создание справочного (архивного) ДФ с изменениями        
benefits_perc_df_summary = \
    pd.DataFrame({'Процент премии': benefits_perc_list, 'Даты': benefits_date_list})


#########
# !!!!!!!!!!
# Расчет северной надбавке и районного коэфициента 
# по премии будет произведен ниже, после расчетов ДФ в 
# денежной форме 

#####################################################
# Создание ДФ с отметкой рабочий день или нет (вспомогательный ДФ)
# = df_shift_on

df_shift_on = df_hours.copy()
df_shift_on = df_shift_on.map(lambda x: 1 if x != 0 else 0)


#####################################################
# Создание ДФ с компенсациями вахтового метода работы
# = df_day_compensation

# Запрос суммы суточной компенсации 
day_compensation = int(input('Введите сумму суточной компенсации вахтового метода работы: \n'))

# Создание ДФ с суточными коменсациями
df_day_compensation = df_shift_on.copy()
df_day_compensation = df_day_compensation.map(lambda x: day_compensation if x == 1 else 0)

#####################################################
# Создание ДФ с выплатами компенсаций за дни межвахтового отдыха (МО)
# = df_dayoff_compensation


# Создание списка рабочих/выходных дней на основе ДФ df_shift_on
line_days = []
df_shift_on.T.map(lambda x: line_days.append(x))

# Паттерн поиска периода окончания выхты
shift_off_pattern = [1, 0, 0, 0, 0]

# Список индексов, куда будут занесены дни окончания вахты (добавил 
# первый элемент 0 для дальнейшего корректного расчета - потом удалим)
indexes_list = [0]

# Цикл для поиска дней окончания вахт и внесение индекса дня в список
for i in range(len(line_days)):
    if line_days[i:(i+len(shift_off_pattern))] == shift_off_pattern:
        indexes_list.append(i+1)

# Подсчет количества дней вахты (продолжнительность вахты)        
work_days = []

for m in range(len(indexes_list)-1):
    index_1 = indexes_list[m]
    index_2 = indexes_list[m+1]
    work_days.append(line_days[index_1:index_2].count(1))

# Список с количество целых недель на вахте (за одну неделю - 
# один компенсационный выходной)    
work_weeks = [x//7 for x in work_days]

# Уточнение о наличии переходящей вахты, если да, добавляем неделю
if_newyear_on = int(input('Есть ли переходящая вахта с прошлого года? 1 - да, 0 - нет: \n'))

if if_newyear_on == 1:
    work_weeks[0] = work_weeks[0] + 1

# Удаляем первый элемент списка (писал об этом выше)    
indexes_list = indexes_list[1:]

# Замена значений списка на сумму компенсации за выходной
n = 0
for days in work_weeks:
    
    for day in range(days):
        line_days[(indexes_list[n]+day)] = 8
    n += 1   
    
# Приступаем к этапу формирования ДФ из созданного списка
# Задаем будующие индексы 
cols_list = list(range(1,32))

# Создаем новый список, разделив существующий список на куски по 31 элементу
line_days_to_df = []

while len(line_days) != 0:
    line_days_to_df.append(line_days[:31])
    line_days = line_days[31:]

# Создаем ДФ
df_dayoff_compensation = pd.DataFrame(line_days_to_df, columns=cols_list)

df_dayoff_compensation = \
    df_dayoff_compensation.map(lambda x: 0 if x == 1 else x)

# Перенесем значения, попавшие на 31 число в тех месяцах, где нет 31 дня:
short_months = [3, 5, 8, 10]

for month in short_months:
    if df_dayoff_compensation.loc[month][30] != 0:
        df_dayoff_compensation.iat[month, 30] = 0
        df_dayoff_compensation.iat[(month+1), 13] = 8 

# Перенесем значения с несуществующих дней февраля, уточним, високосный ли год
if_lip_year = int(input('Год високосный? 1 - да, 0 - нет: \n'))

# Корректировки по расчету, связанные с високосностью года
if if_lip_year == 0:
    
    start_date = 13
    k = 30
    while k != 27:
        if df_dayoff_compensation.loc[1][k] != 0:
           df_dayoff_compensation.iat[1, k] = 0
           df_dayoff_compensation.iat[2, start_date] = 8
        start_date -= 1
        k -= 1

if if_lip_year == 1:
    
    start_date = 13
    k = 30
    while k != 28:
        if df_dayoff_compensation.loc[1][k] != 0:
           df_dayoff_compensation.iat[1, k] = 0
           df_dayoff_compensation.iat[2, start_date] = 8
        start_date -= 1
        k -= 1

# Создадим ДФ с итоговыми суммами компенсаций исходя из ЧТС
df_dayoff_compensation = \
    pd.DataFrame(df_dayoff_compensation.values * df_chts.values)

# Переименуем колонки в диапаназон 1-31
dict_to_rename = dict(zip(list(range(31)), list(range(1,32))))
df_dayoff_compensation = df_dayoff_compensation.rename(columns=dict_to_rename)

#####################################################
# Создание ДФ с выплатами за время в пути
# = df_trip_hours

# Создание списка рабочих/выходных дней на основе ДФ df_shift_on
line_days_trip = []
df_shift_on.T.map(lambda x: line_days_trip.append(x))

# Паттерн поиска периода окончания выхты
shift_off_pattern = [1, 0, 0, 0, 0]
shift_on_pattern = [0, 0, 0, 0, 1]


# Список индексов, куда будут занесены дни окончания вахты (добавил 
# первый элемент 0 для дальнейшего корректного расчета - потом удалим)
indexes_list_trip = []

# Цикл для поиска дней окончания вахт и внесение индекса дня в список
for i in range(len(line_days_trip)):
    if line_days_trip[i:(i+len(shift_off_pattern))] == shift_off_pattern:
        indexes_list_trip.append(i)
    if line_days_trip[i:(i+len(shift_off_pattern))] == shift_on_pattern:
        indexes_list_trip.append(i+4)

# Создание копии "линейного" списка дней со значениями ноль (его будем заполнять)
rotation_date_list = [0 for x in line_days_trip]

# Создание "линейного" списка из исходного графика - его значения будем 
# анализировать, чтобы проставить значение часов в пути
line_days_schedule = []
df_schedule.T.map(lambda x: line_days_schedule.append(x))

# Функция для проверки значения и проставки часов в пути
def trip_hours_count(hour):
    if hour == 'ДП' or hour == 'дп':
        return 8
    else:
        return 5

# Циклом заполним значения часов в пути при помощи функции
for date in indexes_list_trip:
    rotation_date_list[date] = trip_hours_count(line_days_schedule[date])
    
# Приступаем к этапу формирования ДФ из созданного списка
# Задаем будующие индексы 
cols_list = list(range(1,32))

# Создаем новый список, разделив существующий список на куски по 31 элементу
rotation_date_hours = []

while len(rotation_date_list) != 0:
    rotation_date_hours.append(rotation_date_list[:31])
    rotation_date_list = rotation_date_list[31:]

# Создание ДФ из списка
df_trip_hours = pd.DataFrame(rotation_date_hours, columns=cols_list)

# Конвертация часов в пути в денежную форму по ЧТС
df_trip_hours = pd.DataFrame((df_trip_hours.values * df_chts.values), columns=cols_list)


#####################################################
# Создание ДФ с тратами на питание
# = df_food

# Создаем копию ДФ для заполнения, запрашиваем данные, заполняем
df_food = df_shift_on.copy()

bill = int(input('Введите средний чек по питанию в день: \n'))

df_food = df_food.map(lambda x: bill if x == 1 else 0)

# Функция для внесения изменений в траты на питание    
def more_bills():
    """Функция для внесения изменений в созданный ДФ с тратами на питание
    У пользолвателя запрашиваются данные на внесение изменений,
    внутри функции, при необходимости дополнительных изменений происходит вызов функции
    """
    user_input = input('Введите данные в формате ДД-ММ-ДД-ММ-Средний чек (~01-06-31-12-750): \n')
    
    input_list = list(user_input.split('-'))
    
    day_1 = int(input_list[0]) - 1
    month_1 = int(input_list[1]) - 1
    day_2 = int(input_list[2])
    month_2 = int(input_list[3]) - 1
    bill_current = int(input_list[4])
    
    diff_month = month_2 - month_1
    
    if diff_month == 0:
        df_food.loc[month_1][day_1:day_2] = \
            df_food.loc[month_1][day_1:day_2].map(lambda x: bill_current if x != 0 else 0)       
    
    else:    
        df_food.loc[month_1][day_1:] = \
            df_food.loc[month_1][day_1:].map(lambda x: bill_current if x != 0 else 0)
            
        df_food.loc[month_2][:day_2] = \
            df_food.loc[month_2][:day_2].map(lambda x: bill_current if x != 0 else 0)
            
        for n in range(1, diff_month):
            df_food.loc[month_1 + n][:32] = \
                df_food.loc[month_1 + n][:32].map(lambda x: bill_current if x != 0 else 0)
    
    user_input_2 = input('Хотите еще внести изменения в средний чек? 1 - Да, 0 - Нет: \n')
    
    if int(user_input_2) == 1:
        more_bills()

# Запрос о необходимости указать дополнительные данные по тратам
diff_bill = int(input('Хотите задать размер среднего чек за конкретный период? 1 - Да, 0 - Нет: \n'))

# В случае неоходимости внесения изменений - вызов функции внесения изменений
if diff_bill == 1:
    more_bills()

# Список сумм трат на питание   
food_payment_list = []

# Заполняем первый элемент списка (трата за 1-24 января)
food_payment_list.append(df_food.loc[0][:25].sum())

# Заполняем остальные элемент списка за год
for n in range(11):
    result = df_food.loc[n][25:].sum() + df_food.loc[n+1][:25].sum()
    food_payment_list.append(result)
    
#####################################################
# Создание ДФ с начислениями
# = df_hours_payment - оплата по часовому тарифу
# = df_north_ratio_payment - оплата северной надбавки
# = df_region_coef_payment - оплата районного коэфциента
# = df_benefits_payment - оплата премиальной части


df_hours_payment = df_hours_total * df_chts
df_north_ratio_payment = df_hours_payment * df_north_ratio
df_region_coef_payment = df_hours_payment * df_region_coef


#####################################################
# Расчет полной суммы по месячным премиям в ДФ
# = df_benefits_payment_all

df_benefits_payment = df_hours_payment * df_benefits

df_benefits_north_ratio = df_benefits_payment * df_north_ratio
df_benefits_region_coef = df_benefits_payment * df_region_coef

df_benefits_payment_all = df_benefits_payment + df_benefits_north_ratio + df_benefits_region_coef


#####################################################
# Расчет полугодовых премий

half_year_bonus_1 = df_hours_payment.loc[:6].sum().sum()*0.2
bonus_1_nort_ratio = df_north_ratio.loc[7][30]
half_year_bonus_1 = half_year_bonus_1 * (0.8+bonus_1_nort_ratio+1)

half_year_bonus_2 = df_hours_payment.loc[6:].sum().sum()*0.25
bonus_2_nort_ratio = df_north_ratio.loc[11][30]
half_year_bonus_2 = half_year_bonus_2 * (0.8+bonus_2_nort_ratio+1)


#####################################################
# Расчет отпускных

# Создание ДФ с доходами, участвующими в расчете отпускных
cols_list = list(range(1,32))

day_payment_all = pd.DataFrame(
    df_hours_payment.values + df_north_ratio_payment.values + 
    df_region_coef_payment.values + df_benefits_payment_all.values + 
    df_trip_hours.values + df_dayoff_compensation.values + 
    df_day_compensation.values, 
    columns=cols_list
    )

# Суммирование дохода
total_money = day_payment_all.sum().sum()

# Суммирование дохода с премиями
total_money_with_bonus = total_money + half_year_bonus_1 + half_year_bonus_2

# Вычисление "стоимости" дня отпуска
# Так же взять поправочный коэфциент 0.95, эмпирически
vacation_day = total_money_with_bonus / 27.3 / 12 * 0.95


#####################################################
# Создание ДФ с отпусками
# = df_vacation

df_vacation = df_schedule.copy()

df_vacation = df_vacation.map(
    lambda x: vacation_day if x == 'ОТ' or x == 'от' else 0
    )

#####################################################
# Создание ДФ с начислениями для расчета налоговой базы
# = df_for_taxes

# Создание ДФ с доходами, участвующими в расчете налоговой ставки
cols_list = list(range(1,32))

df_for_taxes = pd.DataFrame(
    df_hours_payment.values + df_north_ratio_payment.values + 
    df_region_coef_payment.values + df_benefits_payment_all.values + 
    df_trip_hours.values + df_dayoff_compensation.values + 
    df_vacation.values, 
    columns=cols_list
    )

# Запроса размера ЕДВ
edv = int(input('Введите размер ЕДВ к отпуску: \n'))

# Добавление сумм, полученных в качестве полугодвых премий
df_for_taxes.loc[3][30] = df_for_taxes.loc[3][30] + half_year_bonus_2*0.9

df_for_taxes.loc[7][30] = df_for_taxes.loc[7][30] + half_year_bonus_1

# Добавление выплаты по ЕДВ
vacation_list = []

df_vacation.map(lambda x: vacation_list.append(x))

vacation_additional_payment_index = vacation_list.index(vacation_day)

vacation_add_pay_row = vacation_additional_payment_index // 31
vacation_add_pay_col = vacation_additional_payment_index % 31

df_for_taxes.loc[vacation_add_pay_row][vacation_add_pay_col] = \
    df_for_taxes.loc[vacation_add_pay_row][vacation_add_pay_col] + edv


#####################################################
# Создание ДФ с коэфициентами НДФЛ
# = df_for_taxes
    
cols_list = list(range(1,32))

# Создание ДФ с НДФЛ-кэфами стандартными 0,87
df_taxes = df_hours.copy()
df_taxes = df_taxes.map(lambda x: 0.87)

list_for_taxes = []

df_for_taxes.map(lambda x: list_for_taxes.append(x))

index_list_1 = []
index_list_2 = []
index_list_3 = []

# Корректировка НДФЛ кэфов исходя из доходов 
# (внесение прогрессивной шкалы по 2,4, 5, 20 млн)
index_counter = 0
income_counter = 0

# Расчет суммарного дохода в цикле набегающим итогом, 
# взятие индексов, когда доход преодолел налоговый рубеж, 
# внесение по этим индексам корректировок в ДФ с НДФЛ кэфами
for elem in list_for_taxes:
    income_counter += elem
    
    if income_counter > 2400000:
        index_list_1.append(index_counter)
    if income_counter > 5000000:
        index_list_2.append(index_counter)
    if income_counter > 20000000:
        index_list_3.append(index_counter)

    index_counter += 1

if index_list_1:
    row = index_list_1[0] // 31
    col = index_list_1[0] % 31
    df_taxes.loc[row][col:] = df_taxes.loc[row][col:].map(lambda x: 0.85)
    df_taxes.loc[(row+1):] = df_taxes.loc[(row+1):].map(lambda x: 0.85)
    
if index_list_2:
    row = index_list_2[0] // 31
    col = index_list_2[0] % 31
    df_taxes.loc[row][col:] = df_taxes.loc[row][col:].map(lambda x: 0.82)
    df_taxes.loc[(row+1):] = df_taxes.loc[(row+1):].map(lambda x: 0.82)

if index_list_3:
    row = index_list_3[0] // 31
    col = index_list_3[0] % 31
    df_taxes.loc[row][col:] = df_taxes.loc[row][col:].map(lambda x: 0.8)
    df_taxes.loc[(row+1):] = df_taxes.loc[(row+1):].map(lambda x: 0.8)


#####################################################
# Создание ДФ с выплатами с учетом НДФЛ, 
# отдельно считаем доходы без премий df_payment_no_benefits 
# и с премиями df_payment_benefits
# По итогу получаем списки авансов pre_salary_list 
# и зарплат salary_list, на основе которых формируем ДФ с выплатами
# Итоги округляем 
# = pre_salary_list_rounded, = salary_list_rounded

cols_list = list(range(1,32))

df_payment_no_benefits = pd.DataFrame(
    df_hours_payment.values + df_north_ratio_payment.values + 
    df_region_coef_payment.values +
    df_trip_hours.values + df_dayoff_compensation.values + 
    df_day_compensation.values, 
    columns=cols_list
    )

df_payment_no_benefits = pd.DataFrame(
    df_payment_no_benefits.values * df_taxes.values, 
    columns=cols_list
    )

df_payment_benefits = df_benefits_payment_all.copy()

df_payment_benefits = pd.DataFrame(
    df_payment_benefits.values * df_taxes.values, 
    columns=cols_list
    )

# Задаем нулевые значения, в которые будет прибавлять итоги
pre_salary_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

salary_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# В цикле считаем и заносим суммы по выплатам
for n in range(12):
    if n == 1:
        pre_salary_list[n] = \
            pre_salary_list[n] + df_payment_no_benefits.loc[n][:14].sum()
        salary_list[n] = \
            salary_list[n] + df_payment_no_benefits.loc[n][14:].sum()    
    else:
        pre_salary_list[n] = \
            pre_salary_list[n] + df_payment_no_benefits.loc[n][:15].sum()
        salary_list[n] = \
            salary_list[n] + df_payment_no_benefits.loc[n][15:].sum()

# В зарплатный список добавляем суммы по месячным премиям
for n in range(12):
    salary_list[n] = salary_list[n] + df_payment_benefits.loc[n].sum()

# Из зарплатного списка вычитаем расходы на питание
for n in range(12):
    salary_list[n] = salary_list[n] - food_payment_list[n]

# Создаем списки с округленными значениями
pre_salary_list_rounded = ['%.2f' % x for x in pre_salary_list]
salary_list_rounded = ['%.2f' % x for x in salary_list]


#####################################################
# Создание ДФ с итоговыми начислениями по авансу / ЗП
# = df_summary_payment

df_summary_payment = pd.DataFrame({
    'Месяц работы': month_list, 
    'Аванс за период': pre_salary_list_rounded, 
    'Зарплата за период': salary_list_rounded
    })

#####################################################
# Создание ДФ с итоговыми выплатами отпускных
# = df_vacation_payment

# Создаем копию ДФ с отпускными
df_vacation_tax = df_vacation.copy()

# Уменьшаем выплаты на величину НДФЛ
df_vacation_tax = pd.DataFrame(
    df_vacation.values * df_taxes.values, 
    columns = cols_list
    )

# Нам надо разбить отпуска на периоды

# "Линейный" список с выплатами из ДФ df_vacation_tax
df_vacation_tax_list = []

# Список индексов отпускных дней
df_vacation_tax_ind = []

df_vacation_tax.T.map(lambda x: df_vacation_tax_list.append(x))

for n in range(len(df_vacation_tax_list)):
    if df_vacation_tax_list[n] != 0:
        df_vacation_tax_ind.append(n)

# Список индексов - разделителей, когда период отпуска закончился
separation_list = []

# Находим индексы границы отпусков
for n in range(len(df_vacation_tax_ind)-1):
    if (df_vacation_tax_ind[n+1] - df_vacation_tax_ind[n]) > 3:
        separation_list.append(df_vacation_tax_ind[n+1])
        
# Добавляем первый и последний элемент как граничные
separation_list.insert(0,0)
separation_list = separation_list + [800]

# Список с выплатами за период
vacation_payment_list = []
# Список с названиями периодов
vacation_periods_list = []

# Цикл по подсчету суммы выплат за период отпуска
for n in range(len(separation_list) - 1):
    start_index = separation_list[n]
    end_index = separation_list[n+1]
    vacation_payment_list.append(round(
        sum(df_vacation_tax_list[start_index:end_index]), 2)
        )

# Цикл по наименованию периодов отпусков
for n in range(len(separation_list) - 1):
    if n in [0, 3, 4, 8, 9]:
        ending = '-ый'
    elif n in [1, 5, 6, 7]:
        ending = '-ой'
    elif n in [2]:
        ending = '-ий'
    else:
        ending = ''

    vacation_periods_list.append(
        f'Оплата за {n + 1}{ending} период отпуска'
    )

# Создание итогового ДФ с выплатами за отпуск    
df_vacation_payment = pd.DataFrame({
    'Период': vacation_periods_list, 
    'Размер выплаты, руб.' : vacation_payment_list
    })


#####################################################
# Создание ДФ с итоговыми выплатами полугодовых премий
# = df_half_year_bonus

# Обновляем данные с учетом НДФЛ и округляем
half_year_bonus_1_tax = round(
    (half_year_bonus_1 * df_taxes.loc[7][30]), 2
    )
half_year_bonus_2_tax = round(
    (half_year_bonus_2 * df_taxes.loc[11][30]), 2
    )

# Создаем ДФ
df_half_year_bonus = pd.DataFrame({
    'Название': ['Премия за 1-ое полугодие', 
                 'Премия за 2-ое полугодие'],
    'Размер выплаты': [half_year_bonus_1_tax,
                       half_year_bonus_2_tax]
    })


#####################################################
# Создание ЭКСЕЛЬ файла с результатами

# Создадим новую директорию с результатами
newpath = str(f'{dir_name}' + '/results/')

if not os.path.exists(newpath):
    os.makedirs(newpath)

# Проверка на наличие файла с идентичным названием в директории

# Список файлов директории
file_list_results = os.listdir(newpath)

# Предполагаемое имя файла для сохранения
file_name_to_save = str('calculation_' +  f'{str(file_list[file_num])}')

# Список, в которых будут заносится варианты названия версии, 
# последний - верный будет 
file_name_to_save_list = []

# Номер версии документа
version = 2

# Рекурсивная функция переименования документа, если он уже существует
def file_name_checking():
    global version
    global file_name_to_save
    global file_list_results
    
    # Услование остановки рекурсии - отсутствие названия-претендента 
    # в списке файлов директории 
    while file_name_to_save in file_list_results:

        ind_to_cut = file_name_to_save.find('_ver')
        
        if ind_to_cut > 0:
            file_name_to_save = file_name_to_save[:ind_to_cut] + '.xlsx'

        file_name_to_save = file_name_to_save.replace('.xlsx', f'_ver_{version}.xlsx')
        
         
        file_name_to_save_list.append(file_name_to_save)
        version += 1
        
        file_name_checking()

# Проверка наличия файла в директории с таким-же именем, 
# в случае если да - вызов функции для переименования      
if file_name_to_save in file_list_results:
    file_name_checking()
else:
    file_name_to_save_list.append(file_name_to_save)

# Выбор имени файла 
file_name_to_save = file_name_to_save_list[-1]

# Директория для сохранения файла и имя файла
dir_to_save = str(
    f'{dir_name}' + '/results/' + f'{file_name_to_save}'
    )

# Сохранение ДФ-ов в эксель, с ручной настройкой ширины столбцов
# и созданием листов внутри документа 
with pd.ExcelWriter(dir_to_save, engine='xlsxwriter') as writer:  

    df_summary_payment.to_excel(
        writer, sheet_name='Аванс_и_Зарплата', index=False
        )
    writer.sheets['Аванс_и_Зарплата'].set_column(0, 0, 15)
    writer.sheets['Аванс_и_Зарплата'].set_column(1, 2, 20)

    df_vacation_payment.to_excel(
        writer, sheet_name='Отпускные', index=False
        )
    writer.sheets['Отпускные'].set_column(0, 1, 30)
    
    df_half_year_bonus.to_excel(
        writer, sheet_name='Полугодовые премии', index=False
        )
    writer.sheets['Полугодовые премии'].set_column(0, 1, 25)
    
    chts_df_summary.to_excel(
        writer, sheet_name='Введенные данные', index=False,
        startrow=0
        )
    writer.sheets['Введенные данные'].set_column(0, 1, 15)
    
    north_ratio_df_summary.to_excel(
        writer, sheet_name='Введенные данные', index=False,
        startrow=5
        )
    
    benefits_perc_df_summary.to_excel(
        writer, sheet_name='Введенные данные', index=False,
        startrow=10
        )
    
