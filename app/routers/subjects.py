from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db
from app.models import Subject, SubjectFilterOption, SubjectGroup
from app.schemas.catalog import (
    FilterGroupOut,
    FilterOptionOut,
    SubjectListOut,
    SubjectOut,
)

router = APIRouter(tags=["subjects"])


@router.get("/subjects", response_model=SubjectListOut)
def list_subjects(db: Session = Depends(get_db)):
    subjects = db.scalars(select(Subject).order_by(Subject.sort_order)).all()
    groups = db.scalars(
        select(SubjectGroup)
        .options(
            selectinload(SubjectGroup.options).selectinload(SubjectFilterOption.subject)
        )
        .order_by(SubjectGroup.sort_order)
    ).all()

    return SubjectListOut(
        top=[s.name for s in subjects if s.is_featured],
        subjects=[SubjectOut(key=s.name, slug=s.slug) for s in subjects],
        groups=[
            FilterGroupOut(
                name=g.name,
                options=[
                    FilterOptionOut(label=o.label, subject=o.subject.name)
                    for o in g.options
                ],
            )
            for g in groups
        ],
    )