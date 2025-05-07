from sqlmodel import Session
from app.core.database import engine, populate_database_users, create_normal_user

def init() -> None:
    with Session(engine) as session:
        populate_database_users(session)
        create_normal_user(session)


def main() -> None:
    init()


def run_initializer():
    main()


if __name__ == "__main__":
    main()
