from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from sqlalchemy import select, or_

from app.core.deps import CurrentUser, DB
from app.models.contact import Company, Contact, ContactEmail, EmailStatus
from app.schemas.contact import ContactCreate, ContactFilter, ContactOut

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactOut])
async def list_contacts(db: DB, current_user: CurrentUser, filters: ContactFilter = ContactFilter()):
    stmt = (
        select(Contact)
        .where(Contact.organization_id == current_user.memberships[0].organization_id)
        .offset((filters.page - 1) * filters.per_page)
        .limit(filters.per_page)
    )
    if filters.search:
        term = f"%{filters.search}%"
        stmt = stmt.where(
            or_(
                Contact.first_name.ilike(term),
                Contact.last_name.ilike(term),
            )
        )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactCreate, db: DB, current_user: CurrentUser):
    org_id = current_user.memberships[0].organization_id

    company = None
    if body.company_name:
        result = await db.execute(
            select(Company).where(
                Company.organization_id == org_id,
                Company.name == body.company_name,
            )
        )
        company = result.scalar_one_or_none()
        if not company:
            company = Company(
                organization_id=org_id,
                name=body.company_name,
                domain=body.company_domain,
            )
            db.add(company)
            await db.flush()

    contact = Contact(
        organization_id=org_id,
        first_name=body.first_name,
        last_name=body.last_name,
        title=body.title,
        phone=body.phone,
        linkedin_url=body.linkedin_url,
        company_id=company.id if company else None,
    )
    db.add(contact)
    await db.flush()

    if body.email:
        email_obj = ContactEmail(
            contact_id=contact.id,
            email=body.email.lower(),
            is_primary=True,
            status=EmailStatus.unknown,
        )
        db.add(email_obj)
        await db.flush()

    await db.refresh(contact)
    return contact


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(contact_id: UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: UUID, db: DB, current_user: CurrentUser):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    await db.delete(contact)
