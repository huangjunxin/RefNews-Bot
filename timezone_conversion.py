import pytz
from datetime import datetime


async def convert_to_hongkong_time(timestamp_str):
    # Convert the timestamp to a datetime object
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S%z')

    # Set the original timezone to GMT
    timestamp = timestamp.replace(tzinfo=pytz.timezone('GMT'))

    # Set the Hong Kong timezone
    hong_kong_tz = pytz.timezone('Asia/Hong_Kong')
    # Convert the timestamp to Hong Kong time
    hong_kong_time = timestamp.astimezone(hong_kong_tz)

    # Format the converted time in the desired string representation
    converted_time = hong_kong_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    return converted_time


async def get_hongkong_time():
    # Get the current UTC time, with UTC timezone information
    server_time_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    # Convert server time to Hong Kong time
    hong_kong = pytz.timezone('Asia/Hong_Kong')
    hong_kong_time = server_time_utc.astimezone(hong_kong)

    # Format the time string as requested
    formatted_time = hong_kong_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")

    return formatted_time
