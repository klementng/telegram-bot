import datetime as dt
from datetime import datetime

def round_datetime(tm:datetime, delta:int) -> datetime:
    """
    Round down Datatime object to the nearest delta mins

    Args:
        tm: datetime object
        delta: mins to round to

    Return:
        Rounded down datetime object
    """

    tm = tm - dt.timedelta(
        minutes=tm.minute % delta,
        seconds=tm.second,
        microseconds=tm.microsecond
    )
    
    return tm