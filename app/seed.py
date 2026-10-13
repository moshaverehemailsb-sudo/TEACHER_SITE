from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import (
    ReviewQuestion,
    Subject,
    SubjectFilterOption,
    SubjectGroup,
)

# (کلید درس، slug انگلیسی، نمایش در چیپ‌های بالا) به ترتیب نمایش
SUBJECTS = [
    ("ریاضی", "math", True),
    ("زیست", "biology", True),
    ("شیمی", "chemistry", True),
    ("فیزیک", "physics", False),
    ("زمین‌شناسی", "geology", False),
    ("ادبیات", "literature", False),
    ("عربی", "arabic", False),
    ("جامعه‌شناسی", "sociology", False),
    ("تاریخ", "history", False),
    ("جغرافیا", "geography", False),
    ("فلسفه", "philosophy", False),
    ("اقتصاد", "economics", False),
    ("زبان", "english", False),
    ("دین و زندگی", "religion", False),
    ("سلامت", "health", False),
    ("هویت", "identity", False),
]

# هر گزینه: (برچسب نمایشی، کلید درس)
GROUPS = [
    (
        "رشته ریاضی",
        [
            ("ریاضی", "ریاضی"),
            ("حسابان", "ریاضی"),
            ("هندسه", "ریاضی"),
            ("گسسته", "ریاضی"),
            ("آمار و احتمال", "ریاضی"),
            ("فیزیک", "فیزیک"),
            ("شیمی", "شیمی"),
        ],
    ),
    (
        "رشته تجربی",
        [
            ("زیست‌شناسی", "زیست"),
            ("فیزیک", "فیزیک"),
            ("شیمی", "شیمی"),
            ("ریاضی", "ریاضی"),
            ("زمین‌شناسی", "زمین‌شناسی"),
        ],
    ),
    (
        "رشته انسانی",
        [
            ("ادبیات تخصصی", "ادبیات"),
            ("عربی تخصصی", "عربی"),
            ("جامعه‌شناسی", "جامعه‌شناسی"),
            ("تاریخ", "تاریخ"),
            ("جغرافیا", "جغرافیا"),
            ("فلسفه و منطق", "فلسفه"),
            ("اقتصاد", "اقتصاد"),
            ("ریاضی و آمار", "ریاضی"),
        ],
    ),
    (
        "دروس عمومی",
        [
            ("فارسی", "ادبیات"),
            ("عربی", "عربی"),
            ("زبان انگلیسی", "زبان"),
            ("دین و زندگی", "دین و زندگی"),
            ("سلامت و بهداشت", "سلامت"),
            ("هویت اجتماعی", "هویت"),
        ],
    ),
]


def seed_subjects(db) -> dict[str, Subject]:
    by_name = {s.name: s for s in db.scalars(select(Subject))}
    for order, (name, slug, featured) in enumerate(SUBJECTS, start=1):
        subject = by_name.get(name)
        if subject is None:
            subject = Subject(name=name, slug=slug)
            db.add(subject)
            by_name[name] = subject
        subject.sort_order = order
        subject.is_featured = featured
    db.flush()
    return by_name


def seed_filter_groups(db, subjects: dict[str, Subject]) -> None:
    groups = {g.name: g for g in db.scalars(select(SubjectGroup))}
    for group_order, (group_name, options) in enumerate(GROUPS, start=1):
        group = groups.get(group_name) or SubjectGroup(name=group_name)
        group.sort_order = group_order
        db.add(group)
        existing = {o.label: o for o in group.options}
        for option_order, (label, subject_name) in enumerate(options, start=1):
            option = existing.get(label)
            if option is None:
                option = SubjectFilterOption(label=label)
                group.options.append(option)
            option.subject_id = subjects[subject_name].id
            option.sort_order = option_order


def seed_questions(db) -> None:
    question = db.scalar(
        select(ReviewQuestion).where(ReviewQuestion.key == "would_recommend")
    )
    if question is None:
        db.add(
            ReviewQuestion(
                key="would_recommend",
                question_text="آیا این استاد را به دیگران توصیه می‌کنی؟",
                question_type="yes_no",
                display_order=1,
            )
        )


def count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def main() -> None:
    with SessionLocal() as db:
        subjects = seed_subjects(db)
        seed_filter_groups(db, subjects)
        seed_questions(db)
        db.commit()

        print(
            "subjects =", count(db, Subject),
            "| groups =", count(db, SubjectGroup),
            "| options =", count(db, SubjectFilterOption),
            "| questions =", count(db, ReviewQuestion),
        )


if __name__ == "__main__":
    main()