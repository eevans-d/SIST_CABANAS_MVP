from enum import Enum


class ReservationStatus(str, Enum):
    PRE_RESERVED = "pre_reserved"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class AccommodationType(str, Enum):
    CABIN = "cabin"
    APARTMENT = "apartment"
    HOUSE = "house"
    ROOM = "room"


class MessageType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    LOCATION = "location"
    INTERACTIVE = "interactive"


class ChannelSource(str, Enum):
    WHATSAPP = "whatsapp"
    AIRBNB = "airbnb"
    BOOKING = "booking"
    DIRECT = "direct"
    MERCADOLIBRE = "mercadolibre"
    OTHER = "other"
