import time
import datetime
from loguru import logger

class RPM:

    def __init__(self, rpm: int = 30):
        self.rpm = rpm
        self.record = {'slot': self.get_minute_slot(), 'counter': 0}

    def get_minute_slot(self):
        current_time = time.time()
        dt_object = datetime.fromtimestamp(current_time)
        total_minutes_since_midnight = dt_object.hour * 60 + dt_object.minute
        return total_minutes_since_midnight

    def wait(self):
        current = time.time()
        dt_object = datetime.fromtimestamp(current)
        minute_slot = self.get_minute_slot()

        if self.record['slot'] == minute_slot:
            # check RPM exceed
            if self.record['counter'] >= self.rpm:
                # wait until next minute
                next_minute = dt_object.replace(
                    second=0, microsecond=0) + timedelta(minutes=1)
                _next = next_minute.timestamp()
                sleep_time = abs(_next - current)
                time.sleep(sleep_time)

                self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        else:
            self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        self.record['counter'] += 1
        logger.debug(self.record)
