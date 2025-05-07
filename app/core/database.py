from sqlmodel import Session, create_engine, select
from app.crud import create_user
from app.core.config import settings
from app.models import User, UserRegister
import logfire


engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI),pool_pre_ping=True)

logfire.instrument_sqlalchemy(engine)
# logfire.info("Logfire Initialised for FastAPI")

def populate_database_users(session: Session) -> None:
    user = session.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserRegister(
            email = settings.FIRST_SUPERUSER,
            password = settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser = True,
            
        )
        user = create_user(session=session, user_register=user_in)
        
        
def create_normal_user(session: Session) -> None:
    user = session.exec(select(User). where(User.email == settings.EMAIL_TEST_USER)).first()
    if not user:
        user_in = UserRegister(
            email=settings.EMAIL_TEST_USER, 
            password=settings.EMAIL_TEST_USER_PASSWORD
            )
        user = create_user(session=session, user_register=user_in)
    