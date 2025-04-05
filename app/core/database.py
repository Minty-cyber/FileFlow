from sqlmodel import Session, create_engine, select
from app.crud import create_user
from app.core.config import settings
from app.models import User, UserRegister


engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI),pool_pre_ping=True)


def initiate_database(session: Session) -> None:
    user = session.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserRegister(
            email = settings.FIRST_SUPERUSER,
            password = settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser = True
        )
        user = create_user(session=session, user_register=user_in)