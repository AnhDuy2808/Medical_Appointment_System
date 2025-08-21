from datetime import date, datetime

def str_to_datetime(date_str: str) -> datetime:
    try:
        if not date_str:
            raise ValueError
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return datetime.now()