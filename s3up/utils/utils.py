"""
© AVA, 2025
"""
from datetime import datetime
import pytz


class Timestamp:
    timezone = 'UTC'

    @classmethod
    def set_timezone(cls, tzone='UTC'):
        cls.timezone = tzone if tzone is not None else 'UTC'
        return f'Timezone is set to {tzone}'

    @classmethod
    def now(cls, timestamp=True, timespec='seconds', sep='T'):
        if timestamp:
            return datetime.now(pytz.timezone(cls.timezone)).timestamp()
        else:
            return datetime.now(pytz.timezone(cls.timezone)).isoformat(timespec=timespec, sep=sep)

    @classmethod
    def to_isotime(cls, ts, timespec='milliseconds'):
        return datetime.fromtimestamp(ts).isoformat(timespec=timespec)

    @classmethod
    def to_date(cls, ts):
        return datetime.fromtimestamp(ts).date().isoformat()

    @classmethod
    def to_time(cls, ts, timespec='seconds'):
        return datetime.fromtimestamp(ts).time().isoformat(timespec=timespec)

    @classmethod
    def to_weekday(cls, ts):
        # Monday is 1 and Sunday is 7
        return datetime.fromtimestamp(ts).weekday()

    @staticmethod
    def time_to_ts(time_str, format_str='%Y-%m-%dT%H:%M:%S'):
        time_str = datetime.today().strftime('%Y-%m-%d') + 'T' + time_str
        ts = datetime.strptime(time_str, format_str).timestamp()
        return ts

    @staticmethod
    def get_unique_id():
        return int(datetime.now().timestamp() * 100000000)
