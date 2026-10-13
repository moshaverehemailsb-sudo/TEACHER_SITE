import re
from datetime import datetime, timezone

from sqlalchemy import func, select, text

from app import baf_data as data
from app.database import SessionLocal
from app.models import (
    Course,
    PopularComparison,
    Review,
    ReviewAnswer,
    ReviewQuestion,
    Subject,
    Tag,
    Teacher,
    TeacherBio,
    TeacherTag,
)
from app.text import normalize_search

SUBJECT_OF = {teacher_id: subject for teacher_id, _, subject in data.TEACHERS}


def tag_slug(name: str) -> str:
    return re.sub(r"\s+", "-", name.strip())


def import_teachers(db, subjects: dict[str, Subject]) -> dict[int, Teacher]:
    teachers = {t.id: t for t in db.scalars(select(Teacher))}
    for teacher_id, name, subject_name in data.TEACHERS:
        bio = data.BIOS.get(teacher_id)
        style = bio["style"] if bio else None
        tags = bio["tags"] if bio else []

        teacher = teachers.get(teacher_id)
        if teacher is None:
            teacher = Teacher(id=teacher_id, slug=f"t-{teacher_id}")
            db.add(teacher)
            teachers[teacher_id] = teacher

        teacher.full_name = name
        teacher.profile_image_url = data.PHOTOS.get(teacher_id)
        teacher.teaching_style = style
        teacher.suitable_level = data.BIO_SUITABLE_LEVEL if bio else None
        teacher.is_active = True
        teacher.subjects = [subjects[subject_name]]
        teacher.normalized_search = normalize_search(
            " ".join([name, subject_name, style or "", *tags])
        )
    db.flush()

    # آیدی‌ها را دستی گذاشتیم، پس شمارنده‌ی جدول را جلو می‌بریم
    db.execute(
        text(
            "SELECT setval(pg_get_serial_sequence('teachers', 'id'), "
            "(SELECT MAX(id) FROM teachers))"
        )
    )
    return teachers


def import_bios(teachers: dict[int, Teacher]) -> None:
    for teacher_id, bio in data.BIOS.items():
        teacher = teachers[teacher_id]
        detail = teacher.detail or TeacherBio()
        detail.class_style = bio["class_style"]
        detail.method = bio["method"]
        detail.level_text = bio["level_text"]
        detail.problem_solving = bio["problem_solving"]
        detail.education = bio["education"]
        detail.experience = bio["experience"]
        detail.note = bio["note"]
        teacher.detail = detail


def import_tags(db) -> None:
    tags = {t.name: t for t in db.scalars(select(Tag))}
    links = {
        (link.teacher_id, link.tag_id, link.source)
        for link in db.scalars(select(TeacherTag))
    }
    for teacher_id, bio in data.BIOS.items():
        for name in bio["tags"]:
            tag = tags.get(name)
            if tag is None:
                tag = Tag(name=name, slug=tag_slug(name))
                db.add(tag)
                db.flush()
                tags[name] = tag
            key = (teacher_id, tag.id, "verified")
            if key not in links:
                db.add(
                    TeacherTag(
                        teacher_id=teacher_id, tag_id=tag.id, source="verified"
                    )
                )
                links.add(key)


def import_courses(db, teachers: dict[int, Teacher], subjects: dict[str, Subject]) -> None:
    courses = {c.slug: c for c in db.scalars(select(Course))}
    for teacher_id, items in data.COURSES.items():
        teacher = teachers[teacher_id]
        subject = subjects[SUBJECT_OF[teacher_id]]
        for order, (title, description) in enumerate(items, start=1):
            slug = f"c-{teacher_id}-{order}"
            course = courses.get(slug)
            if course is None:
                course = Course(slug=slug)
                db.add(course)
                courses[slug] = course
            course.title = title
            course.description = description
            course.subject = subject
            course.status = "published"
            course.sort_order = order
            course.teachers = [teacher]


def import_reviews(db) -> None:
    question = db.scalar(
        select(ReviewQuestion).where(ReviewQuestion.key == "would_recommend")
    )
    if question is None:
        raise SystemExit("Run `python -m app.seed` first.")

    existing = {
        (r.teacher_id, r.body)
        for r in db.scalars(select(Review).where(Review.is_imported.is_(True)))
    }
    now = datetime.now(timezone.utc)
    for teacher_id, items in data.REVIEWS.items():
        for label, stars, body in items:
            if (teacher_id, body) in existing:
                continue
            review = Review(
                teacher_id=teacher_id,
                user_id=None,
                overall_rating=stars,
                body=body,
                educational_stage=label,
                status="approved",
                is_imported=True,
                moderated_at=now,
            )
            # قرارداد: ۴ و ۵ ستاره یعنی «توصیه می‌کنم»
            review.answers.append(
                ReviewAnswer(question_id=question.id, value=1 if stars >= 4 else 0)
            )
            db.add(review)


def import_pairs(db) -> None:
    pairs = {
        (p.teacher_a_id, p.teacher_b_id): p
        for p in db.scalars(select(PopularComparison))
    }
    for order, (a, b, label) in enumerate(data.PAIRS, start=1):
        if SUBJECT_OF[a] != SUBJECT_OF[b]:
            raise ValueError(f"Pair {a}-{b} is not the same subject")
        pair = pairs.get((a, b))
        if pair is None:
            pair = PopularComparison(teacher_a_id=a, teacher_b_id=b, label=label)
            db.add(pair)
        pair.label = label
        pair.sort_order = order


def count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def main() -> None:
    with SessionLocal() as db:
        subjects = {s.name: s for s in db.scalars(select(Subject))}
        if not subjects:
            raise SystemExit("Run `python -m app.seed` first.")

        teachers = import_teachers(db, subjects)
        import_bios(teachers)
        import_tags(db)
        db.flush()
        import_courses(db, teachers, subjects)
        import_reviews(db)
        import_pairs(db)
        db.commit()

        print(
            "teachers =", count(db, Teacher),
            "| bios =", count(db, TeacherBio),
            "| tags =", count(db, Tag),
            "| teacher_tags =", count(db, TeacherTag),
            "| courses =", count(db, Course),
            "| reviews =", count(db, Review),
            "| pairs =", count(db, PopularComparison),
        )


if __name__ == "__main__":
    main()