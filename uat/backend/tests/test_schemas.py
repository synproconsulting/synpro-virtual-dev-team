"""Tests for all Pydantic schemas."""

import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from schemas import (
    MessageBase, MessageCreate, MessageResponse,
    ConversationBase, ConversationCreate, ConversationUpdate,
    ConversationResponse, ConversationWithMessages, ConversationListResponse,
    ProductBase, ProductCreate, ProductUpdate, ProductResponse,
)


# ?? Conversation / Message schema tests ???????????????????????????????????????

class TestMessageSchemas:

    def test_valid(self):
        m = MessageBase(role="user", content="hello")
        assert m.content == "hello"

    def test_empty_content_invalid(self):
        with pytest.raises(ValidationError):
            MessageBase(role="user", content="")

    def test_message_create_invalid_id(self):
        with pytest.raises(ValidationError):
            MessageCreate(conversation_id=0, role="user", content="x")


class TestConversationSchemas:

    def test_base_valid(self):
        assert ConversationBase(title="My Chat").title == "My Chat"

    def test_empty_title_invalid(self):
        with pytest.raises(ValidationError):
            ConversationBase(title="")

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            ConversationBase(title="x" * 256)

    def test_update_all_optional(self):
        assert ConversationUpdate().title is None

    def test_list_response_negative_total(self):
        with pytest.raises(ValidationError):
            ConversationListResponse(conversations=[], total=-1, page=1, page_size=10)

    def test_list_response_invalid_page(self):
        with pytest.raises(ValidationError):
            ConversationListResponse(conversations=[], total=0, page=0, page_size=10)


# ?? Product schema tests ???????????????????????????????????????????????????????

class TestProductSchemas:

    def test_create_valid(self):
        p = ProductCreate(
            name="synpro-vdt",
            jira_project_key="SDT1",
            github_repo="synproconsulting/synpro-virtual-dev-team",
        )
        assert p.jira_project_key == "SDT1"
        assert p.railway_service_id is None
        assert p.sonarcloud_key is None

    def test_create_with_optional(self):
        p = ProductCreate(
            name="full",
            jira_project_key="FULL",
            github_repo="org/full",
            railway_service_id="svc-abc",
            sonarcloud_key="org_full",
        )
        assert p.railway_service_id == "svc-abc"
        assert p.sonarcloud_key == "org_full"

    def test_name_required(self):
        with pytest.raises(ValidationError):
            ProductCreate(jira_project_key="K", github_repo="o/r")

    def test_jira_key_required(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="p", github_repo="o/r")

    def test_github_repo_required(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="p", jira_project_key="K")

    def test_name_empty_invalid(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="", jira_project_key="K", github_repo="o/r")

    def test_jira_key_too_long(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="p", jira_project_key="K" * 51, github_repo="o/r")

    def test_update_all_optional(self):
        u = ProductUpdate()
        assert u.name is None
        assert u.jira_project_key is None
        assert u.github_repo is None

    def test_update_partial(self):
        u = ProductUpdate(sonarcloud_key="org_new")
        assert u.sonarcloud_key == "org_new"
        assert u.name is None

    def test_response_has_uuid_id(self):
        now = datetime.utcnow()
        r = ProductResponse(
            id=uuid4(),
            name="p",
            jira_project_key="K",
            github_repo="o/r",
            created_at=now,
            updated_at=now,
        )
        assert r.id is not None

    def test_no_price_or_currency_fields(self):
        with pytest.raises((ValidationError, TypeError)):
            ProductCreate(name="p", jira_project_key="K", github_repo="o/r", price=9.99, currency="USD")