from uuid import uuid4

from fastapi import APIRouter, Depends, Response
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db
from app.errors import ApiError
from app.models import Course, PopularComparison, Teacher, TeacherBio
from app.schemas.admin import (
    AdminCourseOut,
    AdminTeacherOut,
    BioIn,
    CourseCreateIn,
    CourseUpdateIn,
    PairIn,
    PairOut,
    TeacherCreateIn,
    TeacherUpdateIn,
)
from app.schemas.teachers import BioOut
from app.security import require_admin
from app.services.teacher_admin import (
    clean,
    find_subjects,
    refresh_search,
    set_verified_tags,
    to_admin_out,
)

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


def get_teacher_or_404(db: Session, teacher_id: int, *options) -> Teacher:
    """مثل جست‌وجوی عمومی، ولی استاد غیرفعال را هم برمی‌گرداند."""
    teacher = db.scalar(
        select(Teacher).where(Teacher.id == teacher_id).options(*options)
    )
    if teacher is None:
        raise ApiError(404, "TEACHER_NOT_FOUND", "استاد پیدا نشد.")
    return teacher


# ---------------- استادها ----------------
@router.post("/teachers", response_model=AdminTeacherOut, status_code=201)
def create_teacher(body: TeacherCreateIn, db: Session = Depends(get_db)):
    subjects = find_subjects(db, body.subjects)
    teacher = Teacher(
        slug=f"new-{uuid4().hex}",
        full_name=body.name,
        teaching_style=clean(body.style),
        suitable_level=clean(body.level),
        profile_image_url=body.photo_url,
        is_active=True,
    )
    teacher.subjects = subjects
    db.add(teacher)
    db.flush()
    teacher.slug = f"t-{teacher.id}"
    set_verified_tags(db, teacher, body.tags)
    refresh_search(db, teacher)
    db.commit()
    return to_admin_out(db, teacher)


@router.patch("/teachers/{teacher_id}", response_model=AdminTeacherOut)
def update_teacher(
    teacher_id: int, body: TeacherUpdateIn, db: Session = Depends(get_db)
):
    teacher = get_teacher_or_404(db, teacher_id, selectinload(Teacher.subjects))
    fields = body.model_dump(exclude_unset=True)

    if fields.get("name") is not None:
        teacher.full_name = fields["name"]
    if fields.get("subjects") is not None:
        teacher.subjects = find_subjects(db, fields["subjects"])
    if "style" in fields:
        teacher.teaching_style = clean(fields["style"])
    if "level" in fields:
        teacher.suitable_level = clean(fields["level"])
    if "photo_url" in fields:
        teacher.profile_image_url = fields["photo_url"]
    if fields.get("is_active") is not None:
        teacher.is_active = fields["is_active"]
    db.flush()

    if fields.get("tags") is not None:
        set_verified_tags(db, teacher, fields["tags"])
    refresh_search(db, teacher)
    db.commit()
    return to_admin_out(db, teacher)


@router.put("/teachers/{teacher_id}/bio", response_model=BioOut)
def put_bio(teacher_id: int, body: BioIn, db: Session = Depends(get_db)):
    """جایگزین کامل: فیلدی که نفرستی خالی می‌شود."""
    teacher = get_teacher_or_404(db, teacher_id, selectinload(Teacher.detail))
    bio = teacher.detail or TeacherBio()
    bio.class_style = clean(body.class_style)
    bio.method = clean(body.method)
    bio.level_text = clean(body.level_text)
    bio.problem_solving = clean(body.problem_solving)
    bio.education = clean(body.education)
    bio.experience = clean(body.experience)
    bio.note = clean(body.note)
    teacher.detail = bio
    db.commit()
    return BioOut(
        class_style=bio.class_style,
        method=bio.method,
        level_text=bio.level_text,
        problem_solving=bio.problem_solving,
        education=bio.education,
        experience=bio.experience,
        note=bio.note,
    )


# ---------------- دوره‌ها ----------------
def to_course_out(course: Course) -> AdminCourseOut:
    return AdminCourseOut(
        id=course.id,
        title=course.title,
        description=course.description,
        course_type=course.course_type,
        status=course.status,
        sort_order=course.sort_order,
        teacher_ids=sorted(t.id for t in course.teachers),
    )


@router.post(
    "/teachers/{teacher_id}/courses", response_model=AdminCourseOut, status_code=201
)
def create_course(
    teacher_id: int, body: CourseCreateIn, db: Session = Depends(get_db)
):
    teacher = get_teacher_or_404(
        db, teacher_id, selectinload(Teacher.subjects), selectinload(Teacher.courses)
    )
    if not teacher.subjects:
        raise ApiError(400, "TEACHER_HAS_NO_SUBJECT", "ابتدا برای استاد درس تعیین کن.")
    subject = min(teacher.subjects, key=lambda s: s.sort_order)
    next_order = max((c.sort_order for c in teacher.courses), default=0) + 1

    course = Course(
        slug=f"new-{uuid4().hex}",
        title=body.title,
        description=clean(body.description),
        subject_id=subject.id,
        course_type=body.course_type,
        status=body.status,
        sort_order=next_order,
    )
    course.teachers = [teacher]
    db.add(course)
    db.flush()
    course.slug = f"course-{course.id}"
    db.commit()
    return to_course_out(course)


@router.patch("/courses/{course_id}", response_model=AdminCourseOut)
def update_course(
    course_id: int, body: CourseUpdateIn, db: Session = Depends(get_db)
):
    course = db.scalar(
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.teachers))
    )
    if course is None:
        raise ApiError(404, "COURSE_NOT_FOUND", "دوره پیدا نشد.")

    fields = body.model_dump(exclude_unset=True)
    for name in ("title", "status", "sort_order"):
        if fields.get(name) is not None:
            setattr(course, name, fields[name])
    if "description" in fields:
        course.description = clean(fields["description"])
    if "course_type" in fields:
        course.course_type = fields["course_type"]
    db.commit()
    return to_course_out(course)


# ---------------- مقایسه‌های پرطرفدار ----------------
def to_pair_out(pair: PopularComparison) -> PairOut:
    return PairOut(
        id=pair.id,
        teacher_a_id=pair.teacher_a_id,
        teacher_b_id=pair.teacher_b_id,
        label=pair.label,
        sort_order=pair.sort_order,
    )


@router.post("/popular-comparisons", response_model=PairOut, status_code=201)
def create_pair(body: PairIn, db: Session = Depends(get_db)):
    if body.teacher_a_id == body.teacher_b_id:
        raise ApiError(400, "COMPARE_SAME_TEACHER", "دو استاد باید متفاوت باشند.")

    a = get_teacher_or_404(db, body.teacher_a_id, selectinload(Teacher.subjects))
    b = get_teacher_or_404(db, body.teacher_b_id, selectinload(Teacher.subjects))
    if not {s.id for s in a.subjects} & {s.id for s in b.subjects}:
        raise ApiError(
            400,
            "COMPARE_DIFFERENT_SUBJECT",
            "فقط استادهای هم‌درس را می‌توان مقایسه کرد.",
        )

    exists = db.scalar(
        select(PopularComparison.id).where(
            or_(
                and_(
                    PopularComparison.teacher_a_id == a.id,
                    PopularComparison.teacher_b_id == b.id,
                ),
                and_(
                    PopularComparison.teacher_a_id == b.id,
                    PopularComparison.teacher_b_id == a.id,
                ),
            )
        )
    )
    if exists is not None:
        raise ApiError(409, "PAIR_EXISTS", "این مقایسه قبلاً ثبت شده است.")

    sort_order = body.sort_order
    if sort_order is None:
        sort_order = (db.scalar(select(func.max(PopularComparison.sort_order))) or 0) + 1

    pair = PopularComparison(
        teacher_a_id=a.id,
        teacher_b_id=b.id,
        label=body.label,
        sort_order=sort_order,
    )
    db.add(pair)
    db.commit()
    return to_pair_out(pair)


@router.delete("/popular-comparisons/{pair_id}", status_code=204)
def delete_pair(pair_id: int, db: Session = Depends(get_db)):
    pair = db.get(PopularComparison, pair_id)
    if pair is None:
        raise ApiError(404, "PAIR_NOT_FOUND", "مقایسه پیدا نشد.")
    db.delete(pair)
    db.commit()
    return Response(status_code=204)