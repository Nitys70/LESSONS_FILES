

input_str = '10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	10	4	В	В	В	В	В	В \
В	В	В	В	В	В	В	В	В	В	В	В	В	В	В	В	В	В	В	В	В	4/2	11/7	11/7	11/7	11/7	11/7	11/7 \
    11/7	11/7	11/7	11/7	11/7	11/7	11/7	7/5	10	10	10	10	10	10	10	10	10	10	10	10	10	4	В	В	В	В	В	В	В	В	В'
 

hourly_rate = 305.48
north_rate = 0.6
benefit_rate = 0.4


#### Преобразование исходной введеной строки в строку, состояющую из чисел - часов, по которым будет произведен расчет зароботной платы 
hrs_list_init = input_str.split()
hrs_list = []
dbl_sallary_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 53, 66, 120, 128, 307]

for elem in hrs_list_init:
    if elem == 'В':
        hrs_list.append(0)
        
    elif len(elem) > 2:
        a = elem.split('/')
        b = float(a[0]) + float(int(a[1])*0.4)
        hrs_list.append(b)   
        
    else:
        hrs_list.append(int(elem)) 
        
jan = hrs_list[0:31]
feb = hrs_list[31:59]
mar = hrs_list[59:90]
apr = hrs_list[90:120]
may = hrs_list[120:151]
jun = hrs_list[151:181]
jul = hrs_list[181:212]
aug = hrs_list[212:243]
sept = hrs_list[243:273]
oct = hrs_list[273:304]
nov = hrs_list[304:334]
dec = hrs_list[334:365]


year = [jan, feb, mar, apr, may, jun, jul, aug, sept, oct, nov, dec]

#### Функция расчета зароботной платы 
def total_sallary(month):
    month = month
    
    sallary_full = 0
    pre_sall_total = 0
    
    def pre_sall(half_month):
        nonlocal pre_sall_total
        if len(half_month) < 30:
            total = 0
            for elem in half_month[0:15]:
                result = elem * hourly_rate * ( 0.8 + north_rate ) * 0.87
                pre_sall_total += result
            return total
        
        if len(half_month) >= 30:
            total = 0
            for elem in half_month[0:16]:
                result = elem * hourly_rate * ( 0.8 + north_rate ) * 0.87
                pre_sall_total += result
            return total
    
    pre_sall(month)
    
    def sallary(full_month):
        nonlocal sallary_full
        total = 0
        for elem in full_month:
            result = elem * hourly_rate * ( 0.8 + north_rate + benefit_rate ) * 0.87
            #print('This is RESULT: ', result)
            sallary_full += result
        return total
    sallary(month)
    
    sallary_remain = float(sallary_full - pre_sall_total)       
    # print('Аванс: ', pre_sall_total)
    # print('Зарплата:  ', sallary_remain)
    return pre_sall_total, sallary_remain

print_list = 1


#### Вывод на печать результатов, по датам, при помощи цикла перебора
for month in year: 
    if print_list < 10:
        print(f'Your presallary on 29.0{print_list} will be {round(total_sallary(month)[0], 2)} rub, Your sallary on 14.0{print_list+1} will be {round(total_sallary(month)[1], 2)} rub')
    elif print_list == 13:
        print(f'Your presallary on 29.{print_list-1} will be {round(total_sallary(month)[0], 2)} rub, Your sallary on 14.0{print_list-12} will be {round(total_sallary(month)[1], 2)} rub')
    else:
        print(f'Your presallary on 29.{print_list} will be {round(total_sallary(month)[0], 2)} rub, Your sallary on 14.{print_list} will be {round(total_sallary(month)[1], 2)} rub')
    
    print_list += 1
    
#print(f'Your presale will be {round(total_sallary(feb)[0], 2)}, Your sallary will be {round(total_sallary(feb)[1], 2)}')

    # if elem == '10':
    #     c.append(int(elem))
    # if elem == '10':
    #     c.append(int(elem))
    # if elem == '10':
    #     c.append(int(elem))
    # if elem == '10':
    #     c.append(int(elem))
    
# print(hrs_list)

