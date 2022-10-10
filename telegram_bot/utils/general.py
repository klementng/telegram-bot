import datetime as dt
from datetime import datetime

def round_datetime(tm, delta) -> datetime:
    tm = tm - dt.timedelta(
        minutes=tm.minute % delta,
        seconds=tm.second,
        microseconds=tm.microsecond
    )
    
    return tm