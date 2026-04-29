"""Tests for all repository classes."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, MessageRole
from repository import ConversationRepository, MessageRepository, ProductRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()

@pytest.fixture
def conv_repo(db_session): return ConversationRepository(db_session)
@pytest.fixture
def msg_repo(db_session): return MessageRepository(db_session)
@pytest.fixture
def product_repo(db_session): return ProductRepository(db_session)


# ?? ConversationRepository tests ??????????????????????????????????????????????

class TestConversationRepository:

    def test_create_and_get(self, conv_repo):
        conv = conv_repo.create_conversation("Title", "user1")
        assert conv.id is not None
        fetched = conv_repo.get_conversation_by_id(conv.id)
        assert fetched.title == "Title"

    def test_get_not_found(self, conv_repo):
        assert conv_repo.get_conversation_by_id(99999) is None

    def test_get_user_conversations(self, conv_repo):
        conv_repo.create_conversation("A", "user1")
        conv_repo.create_conversation("B", "user1")
        conv_repo.create_conversation("C", "user2")
        assert len(conv_repo.get_user_conversations("user1")) == 2
        assert len(conv_repo.get_user_conversations("user2")) == 1

    def test_count(self, conv_repo):
        conv_repo.create_conversation("X", "u1")
        conv_repo.create_conversation("Y", "u1")
        assert conv_repo.count_user_conversations("u1") == 2

    def test_update(self, conv_repo):
        conv = conv_repo.create_conversation("Old", "u1")
        updated = conv_repo.update_conversation(conv.id, "New")
        assert updated.title == "New"

    def test_update_not_found(self, conv_repo):
        assert conv_repo.update_conversation(99999, "X") is None

    def test_delete(self, conv_repo):
        conv = conv_repo.create_conversation("Del", "u1")
        assert conv_repo.delete_conversation(conv.id) is True
        assert conv_repo.get_conversation_by_id(conv.id) is None

    def test_delete_not_found(self, conv_repo):
        assert conv_repo.delete_conversation(99999) is False


# ?? MessageRepository tests ???????????????????????????????????????????????????

class TestMessageRepository:

    def test_create_and_get(self, conv_repo, msg_repo):
        conv = conv_repo.create_conversation("T", "u1")
        msg = msg_repo.create_message(conv.id, "user", "hello")
        assert msg.id is not None
        assert msg.role == MessageRole.USER
        fetched = msg_repo.get_message_by_id(msg.id)
        assert fetched.content == "hello"

    def test_get_conversation_messages(self, conv_repo, msg_repo):
        conv = conv_repo.create_conversation("T", "u1")
        msg_repo.create_message(conv.id, "user", "a")
        msg_repo.create_message(conv.id, "assistant", "b")
        msgs = msg_repo.get_conversation_messages(conv.id)
        assert len(msgs) == 2

    def test_delete_message(self, conv_repo, msg_repo):
        conv = conv_repo.create_conversation("T", "u1")
        msg = msg_repo.create_message(conv.id, "user", "bye")
        assert msg_repo.delete_message(msg.id) is True
        assert msg_repo.get_message_by_id(msg.id) is None

    def test_delete_not_found(self, msg_repo):
        assert msg_repo.delete_message(99999) is False


# ?? ProductRepository tests ???????????????????????????????????????????????????

class TestProductRepository:

    def test_create_required_fields(self, product_repo):
        p = product_repo.create_product(
            name="vdt",
            jira_project_key="SDT1",
            github_repo="synproconsulting/synpro-virtual-dev-team",
        )
        assert p.id is not None
        assert p.name == "vdt"
        assert p.jira_project_key == "SDT1"
        assert p.github_repo == "synproconsulting/synpro-virtual-dev-team"
        assert p.railway_service_id is None
        assert p.sonarcloud_key is None

    def test_create_with_optional_fields(self, product_repo):
        p = product_repo.create_product(
            name="full",
            jira_project_key="FULL",
            github_repo="org/full",
            railway_service_id="svc-123",
            sonarcloud_key="org_full",
        )
        assert p.railway_service_id == "svc-123"
        assert p.sonarcloud_key == "org_full"

    def test_get_by_name(self, product_repo):
        product_repo.create_product("named", "N1", "org/named")
        p = product_repo.get_by_name("named")
        assert p is not None
        assert p.jira_project_key == "N1"

    def test_get_by_name_not_found(self, product_repo):
        assert product_repo.get_by_name("nonexistent") is None

    def test_list_products(self, product_repo):
        product_repo.create_product("alpha", "A1", "org/a")
        product_repo.create_product("beta", "B1", "org/b")
        products = product_repo.list_products()
        assert len(products) == 2
        assert products[0].name == "alpha"  # ordered by name

    def test_list_pagination(self, product_repo):
        for i in range(5):
            product_repo.create_product(f"prod{i}", f"P{i}", f"org/p{i}")
        assert len(product_repo.list_products(skip=0, limit=3)) == 3
        assert len(product_repo.list_products(skip=3, limit=3)) == 2

    def test_update(self, product_repo):
        p = product_repo.create_product("upd", "U1", "org/upd")
        updated = product_repo.update_product(p.id, sonarcloud_key="org_upd", github_repo="org/updated")
        assert updated.sonarcloud_key == "org_upd"
        assert updated.github_repo == "org/updated"

    def test_update_not_found(self, product_repo):
        import uuid
        assert product_repo.update_product(uuid.uuid4(), name="x") is None

    def test_delete(self, product_repo):
        p = product_repo.create_product("del", "D1", "org/del")
        assert product_repo.delete_product(p.id) is True
        assert product_repo.get_by_id(p.id) is None

    def test_delete_not_found(self, product_repo):
        import uuid
        assert product_repo.delete_product(uuid.uuid4()) is False

    def test_count(self, product_repo):
        product_repo.create_product("c1", "C1", "org/c1")
        product_repo.create_product("c2", "C2", "org/c2")
        assert product_repo.count_products() == 2