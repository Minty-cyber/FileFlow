from sqlmodel import Session
from app.core.database import engine, initiate_database


def init() -> None:
    with Session(engine) as session:
        initiate_database(session)


def main() -> None:
    init()
    
def run_initializer():
    main()

if __name__ == "__main__":
    main()
