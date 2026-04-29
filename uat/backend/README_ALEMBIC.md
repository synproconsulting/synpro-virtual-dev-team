# Alembic Database Migrations

This backend now uses Alembic for managing database schema changes.

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Set the DATABASE_URL environment variable:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
   ```

## Common Commands

### Apply all pending migrations
```bash
alembic upgrade head
```

### View migration history
```bash
alembic history --verbose
```

### Check current database version
```bash
alembic current
```

### Downgrade one migration
```bash
alembic downgrade -1
```

### Downgrade to a specific revision
```bash
alembic downgrade <revision_id>
```

### Create a new migration (after modifying models.py)
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Create an empty migration
```bash
alembic revision -m "Description of changes"
```

## Migration Files

- **alembic.ini**: Main configuration file
- **alembic/env.py**: Environment configuration that connects to your database
- **alembic/versions/**: Directory containing all migration files
- **models.py**: SQLAlchemy models (source of truth for schema)

## Initial Migration

The initial migration (`001_initial_schema.py`) creates:

- **users** table: User accounts with email, username, password hash, and metadata
- **password_reset_tokens** table: Tokens for password reset functionality

## Workflow

1. Modify `models.py` to add/change database schema
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review the generated migration file in `alembic/versions/`
4. Apply migration: `alembic upgrade head`
5. Commit both `models.py` and the migration file to version control

## Notes

- Always review auto-generated migrations before applying them
- The `init_db()` function in `main.py` is now deprecated in favor of Alembic
- Alembic tracks applied migrations in the `alembic_version` table
- Never edit migrations that have been applied to production
