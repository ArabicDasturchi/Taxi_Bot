from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from .models import User, Route, Payment

class CRUD:
    @staticmethod
    async def get_user(session: AsyncSession, telegram_id: int):
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int):
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def create_user(session: AsyncSession, telegram_id: int, full_name: str, phone_number: str, contact_number: str, car_model: str, role: str = 'driver'):
        new_user = User(telegram_id=telegram_id, full_name=full_name, phone_number=phone_number, contact_number=contact_number, car_model=car_model, role=role)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    @staticmethod
    async def get_all_users(session: AsyncSession):
        result = await session.execute(select(User))
        return result.scalars().all()

    @staticmethod
    async def update_user_status(session: AsyncSession, user_id: int, status: str):
        await session.execute(update(User).where(User.id == user_id).values(status=status))
        await session.commit()

    @staticmethod
    async def update_bot_toggle(session: AsyncSession, user_id: int, enabled: bool):
        await session.execute(update(User).where(User.id == user_id).values(bot_enabled=enabled))
        await session.commit()

    @staticmethod
    async def update_available_seats(session: AsyncSession, user_id: int, seats: int):
        await session.execute(update(User).where(User.id == user_id).values(available_seats=seats))
        await session.commit()

    @staticmethod
    async def update_session_string(session: AsyncSession, user_id: int, session_str: str):
        await session.execute(update(User).where(User.id == user_id).values(session_string=session_str))
        await session.commit()

    @staticmethod
    async def increment_ads_sent(session: AsyncSession, user_id: int):
        user = await session.execute(select(User).where(User.id == user_id))
        user_obj = user.scalars().first()
        if user_obj:
            await session.execute(update(User).where(User.id == user_id).values(ads_sent=user_obj.ads_sent + 1))
            await session.commit()

    @staticmethod
    async def increment_clients_found(session: AsyncSession, user_id: int):
        user = await session.execute(select(User).where(User.id == user_id))
        user_obj = user.scalars().first()
        if user_obj:
            await session.execute(update(User).where(User.id == user_id).values(clients_found=user_obj.clients_found + 1))
            await session.commit()

    @staticmethod
    async def add_passenger_route(session: AsyncSession, driver_id: int, from_city: str, to_city: str):
        new_route = Route(driver_id=driver_id, from_city=from_city, to_city=to_city)
        session.add(new_route)
        await session.commit()

    @staticmethod
    async def get_routes_by_driver(session: AsyncSession, driver_id: int):
        result = await session.execute(select(Route).where(Route.driver_id == driver_id))
        return result.scalars().all()

    @staticmethod
    async def delete_route(session: AsyncSession, route_id: int):
        route = await session.get(Route, route_id)
        if route:
            await session.delete(route)
            await session.commit()
