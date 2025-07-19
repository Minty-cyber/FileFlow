from typing import Generic, TypeVar, Optional, Any
from sqlmodel import SQLModel, select, Session

T = TypeVar('T', bound=SQLModel)


class CRUDRepository(Generic[T]):
    def __init__(self, model: type[T]):
        self.model = model
      
    def create(
        self,
        *,
        session: Session,
        data: SQLModel,
        extra_data: dict = None
    ) -> T:
        model_data = data.model_dump()
        if extra_data:
            model_data.update(extra_data)
        new_instance = self.model.model_validate(model_data)
        session.add(new_instance)
        session.commit()
        session.refresh(new_instance)
        return new_instance
    
    def get_by_field(
        self,
        *,
        session: Session,
        field: str,
        value: Any
    ) -> Optional[T]:
        if hasattr(self.model, field):
            statement = select(self.model).where(
                getattr(self.model, field) == value
            )
            return session.exec(statement).first()
        return None
        
    def update(
        self,
        *,
        session: Session,
        db_instance: T,
        update_data: SQLModel,
        extra_data: dict = None
    ) -> T:
        data = update_data.model_dump(exclude_unset=True)
        if extra_data:
            data.update(extra_data)
        db_instance.sqlmodel_update(data)
        session.add(db_instance)
        session.commit()
        session.refresh(db_instance)
        return db_instance
