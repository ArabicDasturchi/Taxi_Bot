from sqlalchemy import BigInteger, Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True) # telegramga ulangan raqam
    contact_number = Column(String(50), nullable=True) # telefon qilish uchun aloqa raqami
    car_model = Column(String(100), nullable=True)
    role = Column(String(50), default='driver') # user, driver, admin
    status = Column(String(50), default='pending') # pending, active, banned
    bot_enabled = Column(Boolean, default=False) # Whether auto-forwarding is ON
    session_string = Column(String(500), nullable=True) # User's own pyrogram session
    available_seats = Column(Integer, default=4) # Available seats
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    routes = relationship("Route", back_populates="driver")
    payments = relationship("Payment", back_populates="user")


class Route(Base):
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    from_city = Column(String(100), nullable=False)
    to_city = Column(String(100), nullable=False)
    
    driver = relationship("User", back_populates="routes")


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default='pending') # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="payments")
