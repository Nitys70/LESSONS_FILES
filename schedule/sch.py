import pandas as pd

pd.set_option('display.max_columns', None)

# chts = input('Введите свою часовую тарифную ставку')
# north_ratio = input('Введите размер своей северно надбавки, в процентах')
# bonus = input('Введите размер премиальной части в процентах')
# alms = input('Введите размер надбавки за вахтовый метод работы')
# canteen = input('Введите средний чек в столовой за 1 день')

# chts = chts.replace(',','.')
# chts = float(chts)
# north_ratio = float(north_ratio)
# bonus = float(bonus)
# alms = float(alms)
# canteen = float(canteen)

chts = 505.58
north_ratio = 60
bonus = 40
alms = 363
canteen = 1150

# Создание DF из исходного графика в формате эксель
scd_df = pd.read_excel(
    'D:/IDE_folder/LESSONS_FILES/schedule/data/myself_2024.xlsx'
    )

# Вспомогательный список с номера строк и месяцами исходного DF
date_keys = [(13, 'jan'), (15, 'feb'), (17, 'mar'), 
             (20, 'apr'), (22, 'may'), (24, 'jun'), 
             (28, 'july'), (30, 'aug'), (32, 'sep'), 
             (35, 'oct'), (37, 'nov'), (39, 'dec')
             ]


year_schdl_df = pd.DataFrame(columns=[list(range(1, 32))])

### Цикл, создание DF, дублирующего оригинальный эксель график

for elem in date_keys:
    mnth_arr_orig = (pd.DataFrame(scd_df.iloc[elem[0]]))[1:32].values
    mnth_arr = mnth_arr_orig.reshape((1, 31))
    mnth_arr_df = pd.DataFrame(
    data = mnth_arr, 
    columns = [list(range(1, 32))], 
    index = [elem[1]]  
    ) 
    year_schdl_df = pd.concat( [year_schdl_df, mnth_arr_df] )


###
### Фнукция для конвертации значений в часовые значения
###

def data_conv(elem):

    try:
        elem = int(elem)
        return elem

    except:
        if '/' in elem:
            elem = elem.replace(' ', '')
            elem = elem.replace('/', ' ')
            elem = elem.split(' ')
            d = int(elem[0]) + int(elem[1])*0.4
            return d
        if elem == 'В' or elem == 'в':
            return 0
        if elem == 'ОТ' or elem == 'от':
            return 'ОТ'
        else:
            return 0


### Преобразование DF в DF, где в ячейках часы

for n in range(year_schdl_df.shape[0]):
    year_schdl_df.iloc[n] = year_schdl_df.iloc[n].apply(data_conv)

### Список праздничных дней

holidays = [(0,1), (0,2), (0,3), (0,4), 
            (0,5), (0,6), (0,7), (0,8),
            (1,23), (2,8), (4,1), (4,9),
            (5,12), (10,4)]

### Преобразование часов в year_schdl_df с учетом прздничных дней (умножаем на 2)
for elem in holidays:
    year_schdl_df.iloc[elem[0]][elem[1]] = year_schdl_df.iloc[elem[0]][elem[1]]*2

###
### Фнукция для конвертации часовых значений в денежные. На выходе кортеж
###    
def money_convert(elem):
    try:
        pre_sallary = elem*chts*(1.8 + north_ratio/100)
        sallary = pre_sallary*(bonus/100)
        return pre_sallary, sallary
    except:
        return elem
    


### Создание нового DF, где значения ячеек - кортежи (аванс, зарплата)
year_schdl_money = year_schdl_df.copy()

for n in range(year_schdl_money.shape[0]):
    year_schdl_money.iloc[n] = year_schdl_money.iloc[n].apply(money_convert)
###



###
### Фнукция для создание итогового DF с приходом ДС на карту (на руки)
###   
def summary_tab(elem):
    summary = pd.DataFrame(
        columns=['14ое', '29ое'], 
        index= ['Январь', 'Февраль', 'Март', 'Апрель', 'Май',
            'Июнь', 'Июль', 'Август', 'Сентябрь',
            'Октябрь', 'Ноябрь', 'Декабрь', 'Январь' ] )

    df = elem.copy()
    for month in range(12):
        df.iloc[month] = df.iloc[month].apply(
            lambda x: x if type(x) is tuple else (0,0) 
            )

    m=0
    count_above_25 = 0

    for m in range(12):
        # print('there is',elem, 'end of elem')
        presallary = 0
        sallary = 0
        count_upto_25 = 0
        
        
        for day in range(1,26):
            if (df.iloc[m][day][0] + df.iloc[m][day][1]) > 0:
                count_upto_25 += 1
        
        for day in range(26,31):
            if (df.iloc[m][day][0] + df.iloc[m][day][1]) > 0:
                count_above_25 += 1 
        
        for n in range(1,16):
            presallary += (df.iloc[m][n][0] + alms)
            
        for n in range(1,(df.shape[1]+1)):
            if n <= 15:
                sallary += df.iloc[m][n][1]
                
            if n>15:
                sallary += (df.iloc[m][n][0] + df.iloc[m][n][1] + alms)
        
       
        
        summary.iloc[m][1] = round(presallary*0.87, 2)
        summary.iloc[m+1][0] = round((sallary-canteen*(count_upto_25+count_above_25))*0.87,2)
        count_above_25 = 0        
        m+=1


    return summary    



###
### Фнукция для расчета премии за 1 полугодие
###

def bonus_1(elem):

    year_schdl_df_bonus = elem.copy()

    for n in range(0, 6):
        year_schdl_df_bonus.iloc[n] = year_schdl_df_bonus.iloc[n].apply(
            lambda x: x if (type(x) is int or type(x) is float) else 0
            )

    # type(year_schdl_df_bonus.iloc[8][1])

    hrs_sum = 0

    for n in range(0, 6):
        hrs_sum += year_schdl_df_bonus.iloc[n].sum()

    year_schdl_df_bonus
    hrs_sum
    bonus = hrs_sum*chts*(1.8 + north_ratio/100)*0.87*0.2
    return bonus


print('Премия за 1 полугодие', round(bonus_1(year_schdl_df), 2))

###
### Фнукция для расчета премии за 2 полугодие
###


def bonus_2(elem):

    year_schdl_df_bonus = elem.copy()

    for n in range (6,12):
        year_schdl_df_bonus.iloc[n] = year_schdl_df_bonus.iloc[n].apply(
            lambda x: x if (type(x)==int or type(x)==float) else 0 
            )

    # type(year_schdl_df_bonus.iloc[8][1])

    hrs_sum = 0

    for n in range(6, 12):
        hrs_sum += year_schdl_df_bonus.iloc[n].sum()

    year_schdl_df_bonus
    hrs_sum
    bonus = hrs_sum*chts*(1.8 + north_ratio/100)*0.87*0.25
    return bonus


print('Премия за 2 полугодие', round(bonus_2(year_schdl_df), 2))



# print(year_schdl_money.apply(summary_tab))


summary_df = summary_tab(year_schdl_money)

print(summary_df)
# summary_df.to_excel('data\sallary_2024.xlsx')

# !pip freeze > requirements.txt
