import schedule

def task():
    print('Hello! I am a task!')
    return


schedule.every(10).seconds.do(task)
