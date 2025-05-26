from sqlmodel import Session
from app.crud import create_group
from app.models import GroupPublic, GroupRegister
from app.tests.utils.core import random_string
from app.tests.utils.user import create_random_user

def create_random_group(database: Session) -> GroupPublic:
    title = random_string()
    description = random_string()
    group_in = GroupRegister(title=title, description=description)
    new_group = create_group(session=database, group_register=group_in)
    return new_group
    