# PM Agent Chat History Module

A robust Python module for managing conversations and messages in the PM Agent chat system. This module provides database models, validation schemas, and repository patterns for storing and retrieving chat history.

## Features

- **SQLAlchemy ORM Models**: Database models for conversations and messages
- **Pydantic Schemas**: Request/response validation and serialization
- **Repository Pattern**: Clean separation of database operations
- **Type Safety**: Full type hints throughout the codebase
- **Comprehensive Testing**: Unit tests for all major components
- **Database Agnostic**: Works with PostgreSQL, SQLite, and other SQLAlchemy-supported databases

## Architecture

### Models (`src/chat/models.py`)

Defines the database schema:

- **Conversation**: Represents a chat conversation thread
  - `id`: Primary key
  - `title`: Conversation title
  - `user_id`: Owner of the conversation
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp
  - `messages`: One-to-many relationship with messages

- **Message**: Represents individual messages in a conversation
  - `id`: Primary key
  - `conversation_id`: Foreign key to conversation
  - `role`: Message sender role (user/assistant/system)
  - `content`: Message text content
  - `created_at`: Creation timestamp

### Schemas (`src/chat/schemas.py`)

Pydantic models for validation and serialization:

- `MessageCreate`: Creating new messages
- `MessageResponse`: Message API responses
- `ConversationCreate`: Creating new conversations
- `ConversationUpdate`: Updating conversation details
- `ConversationResponse`: Conversation API responses
- `ConversationWithMessages`: Full conversation with message history
- `ConversationListResponse`: Paginated conversation lists

### Repository (`src/chat/repository.py`)

Database access layer with clean interfaces:

- **ConversationRepository**: CRUD operations for conversations
  - `create_conversation()`
  - `get_conversation_by_id()`
  - `get_user_conversations()` (with pagination)
  - `update_conversation()`
  - `delete_conversation()`

- **MessageRepository**: CRUD operations for messages
  - `create_message()`
  - `get_conversation_messages()` (with pagination)
  - `get_message_by_id()`
  - `delete_message()`

### Database (`src/chat/database.py`)

Configuration and session management:

- Engine creation
- Session factory setup
- Table creation utilities
- Database URL from environment variables

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
# or for SQLite:
export DATABASE_URL="sqlite:///./chat.db"
```

## Usage

### Initialize Database

```python
from src.chat import create_database_engine, create_tables, get_session_factory

# Create engine and tables
engine = create_database_engine()
create_tables(engine)

# Create session factory
SessionLocal = get_session_factory(engine)
```

### Create a Conversation

```python
from src.chat import ConversationRepository

# Get a database session
db = SessionLocal()

# Create repository
conv_repo = ConversationRepository(db)

# Create a conversation
conversation = conv_repo.create_conversation(
    title="Project Discussion",
    user_id="user123"
)

print(f"Created conversation: {conversation.id}")
db.close()
```

### Add Messages to Conversation

```python
from src.chat import MessageRepository

db = SessionLocal()
msg_repo = MessageRepository(db)

# Add a user message
user_msg = msg_repo.create_message(
    conversation_id=conversation.id,
    role="user",
    content="What tasks do we have today?"
)

# Add an assistant response
assistant_msg = msg_repo.create_message(
    conversation_id=conversation.id,
    role="assistant",
    content="Here are today's tasks: 1. Code review 2. Deploy feature 3. Update docs"
)

db.close()
```

### Retrieve Conversation with Messages

```python
db = SessionLocal()
conv_repo = ConversationRepository(db)
msg_repo = MessageRepository(db)

# Get conversation
conversation = conv_repo.get_conversation_by_id(1)

# Get all messages
messages = msg_repo.get_conversation_messages(conversation.id)

for msg in messages:
    print(f"{msg.role.value}: {msg.content}")

db.close()
```

### List User Conversations

```python
db = SessionLocal()
conv_repo = ConversationRepository(db)

# Get user's conversations with pagination
conversations = conv_repo.get_user_conversations(
    user_id="user123",
    skip=0,
    limit=10
)

total = conv_repo.count_user_conversations("user123")

for conv in conversations:
    print(f"{conv.title} - Last updated: {conv.updated_at}")

db.close()
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/chat tests/

# Run specific test file
pytest tests/test_models.py
pytest tests/test_repository.py
pytest tests/test_schemas.py
```

### Test Coverage

The module includes comprehensive tests for:

- Model creation and relationships
- Cascade deletion behavior
- Repository CRUD operations
- Pagination functionality
- Schema validation
- Edge cases and error handling

## Database Schema

### Conversations Table

| Column     | Type         | Constraints                    |
|------------|--------------|--------------------------------|
| id         | INTEGER      | PRIMARY KEY, AUTOINCREMENT     |
| title      | VARCHAR(255) | NOT NULL                       |
| user_id    | VARCHAR(100) | NOT NULL, INDEXED              |
| created_at | DATETIME     | NOT NULL, DEFAULT utcnow       |
| updated_at | DATETIME     | NOT NULL, DEFAULT utcnow       |

### Messages Table

| Column          | Type    | Constraints                              |
|-----------------|---------|------------------------------------------|
| id              | INTEGER | PRIMARY KEY, AUTOINCREMENT               |
| conversation_id | INTEGER | FOREIGN KEY (conversations.id), INDEXED  |
| role            | ENUM    | NOT NULL (user/assistant/system)         |
| content         | TEXT    | NOT NULL                                 |
| created_at      | DATETIME| NOT NULL, DEFAULT utcnow                 |

## Environment Variables

- `DATABASE_URL`: Database connection string (required)
  - PostgreSQL: `postgresql://user:password@host:port/database`
  - SQLite: `sqlite:///path/to/database.db`
  - MySQL: `mysql://user:password@host:port/database`

## Best Practices

1. **Always use context managers or try/finally for sessions**:
   ```python
   db = SessionLocal()
   try:
       # Your database operations
       pass
   finally:
       db.close()
   ```

2. **Use repositories for database access**: Don't query models directly in business logic

3. **Validate with schemas**: Use Pydantic schemas for all API inputs/outputs

4. **Handle exceptions**: Wrap database operations in try/except blocks

5. **Use transactions**: Commit changes explicitly and handle rollbacks

## Contributing

When contributing to this module:

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for classes and public methods
4. Add tests for new functionality
5. Keep functions under 30 lines where possible
6. No hardcoded secrets or credentials

## License

This module is part of the PM Agent system.
