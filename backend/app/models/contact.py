import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class EmailStatus(str, enum.Enum):
    unknown = "unknown"
    valid = "valid"
    invalid = "invalid"
    risky = "risky"


class Company(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "companies"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="company")


class Contact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contacts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped[Company | None] = relationship("Company", back_populates="contacts")
    emails: Mapped[list["ContactEmail"]] = relationship(
        "ContactEmail", back_populates="contact", lazy="selectin"
    )
    tags: Mapped[list["ContactTag"]] = relationship("ContactTag", back_populates="contact")

    @property
    def primary_email(self) -> str | None:
        valid = [e for e in self.emails if e.status == EmailStatus.valid]
        if valid:
            return valid[0].email
        return self.emails[0].email if self.emails else None


class ContactEmail(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contact_emails"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus), nullable=False, default=EmailStatus.unknown
    )
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)

    contact: Mapped[Contact] = relationship("Contact", back_populates="emails")


class Tag(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tags"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6366f1")


class ContactTag(Base):
    __tablename__ = "contact_tags"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    contact: Mapped[Contact] = relationship("Contact", back_populates="tags")
    tag: Mapped[Tag] = relationship("Tag")


class List_(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lists"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    list_contacts: Mapped[list["ListContact"]] = relationship(
        "ListContact", back_populates="list_"
    )


class ListContact(Base):
    __tablename__ = "list_contacts"

    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lists.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )

    list_: Mapped[List_] = relationship("List_", back_populates="list_contacts")
    contact: Mapped[Contact] = relationship("Contact")
