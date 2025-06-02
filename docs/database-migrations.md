# Database Migrations with Alembic

This project uses **Alembic** for managing database schema migrations. Alembic is a lightweight database migration tool for SQLAlchemy, which is compatible with SQLModel.

## Creating a New Migration

1. **Update Your Models**

   Make changes to your SQLModel models in the models.py file or wherever your models are defined.

2. **Generate a Migration Script**

   Use Alembic’s `autogenerate` feature to create a new migration script:
   ```
   alembic revision --autogenerate -m "Describe your migration"
   ```
   This will create a new migration file in the versions directory.

3. **Review the Migration Script**

   Open the generated migration script and review the changes. Make sure Alembic has correctly detected all intended schema changes.

4. **Apply the Migration**

   Run the migration to update your database schema:
   ```
   alembic upgrade head
   ```

## Common Alembic Commands

- **Create a new migration:**  
  ```
  alembic revision --autogenerate -m "your message"
  ```
- **Apply migrations:**  
  ```
  alembic upgrade head
  ```
- **Downgrade (undo) last migration:**  
  ```
  alembic downgrade -1
  ```
- **View current migration:**  
  ```
  alembic current
  ```

## Troubleshooting

- If Alembic does not detect changes, ensure your models are imported in the `env.py` file inside the alembic directory.
- For manual changes, edit the migration script directly.

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [SQLModel + Alembic Guide](https://sqlmodel.tiangolo.com/tutorial/migrations/)

---

**Note:** Always backup your database before running migrations on production systems.