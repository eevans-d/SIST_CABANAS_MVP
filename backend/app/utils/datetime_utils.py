from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import pytz
from dateutil import parser

ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC"""
    if dt.tzinfo is None:
        dt = ARGENTINA_TZ.localize(dt)
    return dt.astimezone(pytz.UTC)

def from_utc(dt: datetime) -> datetime:
    """Convert UTC datetime to Argentina timezone"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(ARGENTINA_TZ)

def argentina_now() -> datetime:
    """Get current datetime in Argentina timezone"""
    return datetime.now(ARGENTINA_TZ)

def parse_argentine_date(date_str: str) -> Optional[date]:
    """Parse date string in Argentine format (DD/MM/YYYY)"""
    try:
        # Try DD/MM/YYYY format first
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = f"20{year}"
            return date(int(year), int(month), int(day))
        
        # Fallback to dateutil parser
        parsed = parser.parse(date_str, dayfirst=True)
        return parsed.date()
    except:
        return None

def format_date_spanish(dt: date) -> str:
    """Format date in Spanish (e.g., '15 de diciembre de 2024')"""
    months = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    return f"{dt.day} de {months[dt.month]} de {dt.year}"

def calculate_nights(check_in: date, check_out: date) -> int:
    """Calculate number of nights between dates"""
    return (check_out - check_in).days

def get_next_weekend() -> Tuple[date, date]:
    """Get next weekend dates (Saturday-Sunday)"""
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0 and datetime.now().hour > 18:
        days_until_saturday = 7
    
    saturday = today + timedelta(days=days_until_saturday)
    sunday = saturday + timedelta(days=1)
    
    return saturday, sunday