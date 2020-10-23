from datetime import datetime

def getDuration(time2):
    datetimeFormat = '%d.%m.%Y %H:%M:%S'
    time1 = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    time_dif = datetime.strptime(time1, datetimeFormat) - datetime.strptime(time2, datetimeFormat)
    if time_dif.total_seconds() < 0:
        return("0:00:00")
    return (time_dif)