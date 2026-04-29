"""Tests for all database models."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Conversation, Message, MessageRole, Product


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


# ?? Conversation / Message model tests ???????????????????????????????????????

class TestConversationModel:

    def test_create_conversation(self, db_session):
        conv = Conversation(title="Test", user_id="user1")
        db_session.add(conv)
        db_session.commit()
        assert conv.id is not None
        assert conv.title == "Test"
        assert conv.user_id == "user1"
        assert isinstance(conv.created_at, datetime)

    def test_conversation_repr(self, db_session):
        conv = Conversation(title="My Conv", user_id="user1")
        db_session.add(conv); db_session.commit()
        assert "My Conv" in repr(conv)

    def test_conversation_cascade_delete(self, db_session):
        conv = Conversation(title="Test", user_id="user1")
        db_session.add(conv); db_session.commit()
        msg = Message(conversation_id=conv.id, role=MessageRole.USER, content="hi")
        db_session.add(msg); db_session.commit()
        conv_id = conv.id
        db_session.delete(conv); db_session.commit()
        assert db_session.query(Message).filter(Message.conversation_id == conv_id).count() == 0

    def test_message_roles(self, db_session):
        conv = Conversation(title="Test", user_id="u1")
        db_session.add(conv); db_session.commit()
        for role in [MessageRole.USER, MessageRole.ASSISTANT, MessageRole.SYSTEM]:
            msg = Message(conversation_id=conv.id, role=role, content="x")
            db_session.add(msg)
        db_session.commit()
        assert db_session.query(Message).filter(Message.conversation_id == conv.id).count() == 3


# ?? Product model tests ???????????????????????????????????????????????????????

class TestProductModel:

    def test_create_product_required_fields(self, db_session):
        product = Product(
            name="synpro-vdt",
            jira_project_key="SDT1",
            github_repo="synproconsulting/synpro-virtual-dev-team",
        )
        db_session.add(product)
        db_session.commit()
        assert product.id is not None
        assert product.name == "synpro-vdt"
        assert product.jira_project_key == "SDT1"
        assert product.github_repo == "synproconsulting/synpro-virtual-dev-team"

    def test_product_optional_fields_default_none(self, db_session):
        product = Product(name="p1", jira_project_key="KEY1", github_repo="org/repo")
        db_session.add(product); db_session.commit()
        assert product.railway_service_id is None
        assert product.sonarcloud_key is None

    def test_product_with_all_fields(self, db_session):
        product = Product(
            name="full-product",
            jira_project_key="FP1",
            github_repo="org/full-product",
            railway_service_id="railway-uuid-123",
            sonarcloud_key="org_full-product",
        )
        db_session.add(product); db_session.commit()
        assert product.railway_service_id == "railway-uuid-123"
        assert product.sonarcloud_key == "org_full-product"

    def test_product_name_unique(self, db_session):
        from sqlalchemy.exc import IntegrityError
        db_session.add(Product(name="unique", jira_project_key="K1", github_repo="o/r"))
        db_session.commit()
        db_session.add(Product(name="unique", jira_project_key="K2", github_repo="o/r2"))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_product_repr(self, db_session):
        product = Product(name="my-product", jira_project_key="MP1", github_repo="org/mp")
        db_session.add(product); db_session.commit()
        assert "my-product" in repr(product)
        assert "MP1" in repr(product)

    def test_product_has_no_price_or_currency(self, db_session):
        product = Product(name="vdt-product", jira_project_key="VDT", github_repo="org/vdt")
        db_session.add(product); db_session.commit()
        assert not hasattr(product, "price")
        assert not hasattr(product, "currency")
        assert not hasattr(product, "display_name")
        assert not hasattr(product, "is_active")