# Baf API (بک‌اند سایت باف)

بک‌اند سایت «باف»، برای پیدا کردن و مقایسه‌ی اساتید کنکور و خواندن نظر دانش‌آموزان.
FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL.

## راه‌اندازی روی کامپیوتر خودت

1. ریپو را clone کن و وارد پوشه‌اش شو.
2. محیط مجازی بساز و فعال کن:

```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
```

3. یک دیتابیس PostgreSQL جدا برای خودت بساز (مثلاً یک پروژه یا branch جدید در Neon). دیتابیس اصلی را استفاده نکن.
4. فایل `.env.example` را کپی کن به اسم `.env` و `DATABASE_URL` را با آدرس دیتابیس خودت پر کن.
   ابتدای آدرس باید `postgresql+psycopg://` باشد. رمز را هرگز در گیت نگذار.
5. جدول‌ها را بساز و داده‌ی اولیه را وارد کن:

```powershell
   alembic upgrade head
   python -m app.seed
   python -m app.import_baf
```

   هر دو اسکریپت بی‌خطر تکرار می‌شوند.
6. سرور را اجرا کن:

```powershell
   uvicorn app.main:app --reload
```

   - سرور: http://127.0.0.1:8000
   - مستندات زنده و تست endpointها: http://127.0.0.1:8000/docs

## متغیرهای محیطی

| نام | توضیح |
|---|---|
| `DATABASE_URL` | آدرس دیتابیس، شروع با `postgresql+psycopg://` |
| `CORS_ORIGINS` | آدرس‌های مجاز فرانت، با کاما جدا می‌شوند. پیش‌فرض: `http://localhost:5500,http://127.0.0.1:5500` |

فرانت را با یک سرور محلی روی پورت ۵۵۰۰ باز کن (مثلاً Live Server در VS Code). باز کردن مستقیم فایل `index.html` با دابل‌کلیک از CORS رد می‌شود.

## تست‌ها

```powershell
pytest -v
```

تست‌ها روی همان `DATABASE_URL` اجرا می‌شوند. تست‌های دیتابیس داخل تراکنشی اجرا می‌شوند که در پایان برگردانده می‌شود، پس چیزی در دیتابیس باقی نمی‌ماند. تست‌های API داده‌ی واقعی فرانت را می‌خوانند، پس قبل از `pytest` باید `app.seed` و `app.import_baf` را اجرا کرده باشی.

## مرجع API

همه‌ی آدرس‌ها زیر `/api/v1` هستند، به‌جز `/health`. نام فیلدهای JSON به‌صورت camelCase است.

### کارت استاد

```json
{
  "id": 1,
  "name": "امید مصلایی",
  "subject": "شیمی",
  "style": "کامل و تکنیکی",
  "level": "همه‌ی سطح‌ها",
  "tags": ["رسمی", "تست زیاد"],
  "photoUrl": "assets/teachers/1.jpg",
  "rating": 4.7,
  "reviewCount": 3,
  "recommendPercent": 100
}
```

برای استاد بدون نظر، `rating` و `recommendPercent` برابر `null` و `reviewCount` برابر `0` است. فیلدهای `style` و `level` و `photoUrl` هم ممکن است `null` باشند.

### Endpointها

| متد و آدرس | توضیح |
|---|---|
| `GET /health` | بررسی سلامت سرور و دیتابیس |
| `GET /subjects` | `{ top, subjects: [{key, slug}], groups: [{name, options: [{label, subject}]}] }` |
| `GET /teachers` | پارامترها: `subject`، `q`، `sort` (`popular`/`reviews`/`default`)، `scratch`، `page`، `pageSize` (حداکثر ۵۰). پاسخ: `{ items: [کارت], total, page, pageSize }` |
| `GET /teachers/{id}` | کارت استاد به‌همراه `bio` و `courses` |
| `GET /teachers/{id}/reviews` | نظرهای تأییدشده، تازه‌ترین اول. پارامترها: `page`، `pageSize`. هر نظر: `{ id, reviewerLabel, stars, recommends, body, createdAt }` |
| `GET /teachers/{id}/rivals` | استادهای هم‌درس، مرتب بر اساس نمره. پارامتر: `limit` |
| `GET /compare?a=&b=` | مقایسه‌ی دو استاد هم‌درس: `{ subject, a, b }` (کارت به‌علاوه‌ی `education` و `experience`) |
| `GET /popular-comparisons` | `{ items: [{ id, label, a: کارت, b: کارت }] }` |

شکل `bio`: `{ classStyle, method, levelText, problemSolving, education, experience, note }`. اگر استاد بیوگرافی ندارد `bio` برابر `null` است. مقدار `education` ممکن است چند خط باشد که با `\n` جدا شده‌اند.

### خطاها

```json
{ "error": { "code": "TEACHER_NOT_FOUND", "message": "استاد پیدا نشد." } }
```

| کد | وضعیت | معنی |
|---|---|---|
| `TEACHER_NOT_FOUND` | 404 | استاد وجود ندارد یا غیرفعال است |
| `COMPARE_MISSING_IDS` | 400 | یکی از `a` یا `b` ارسال نشده |
| `COMPARE_SAME_TEACHER` | 400 | دو آیدی برابرند |
| `COMPARE_DIFFERENT_SUBJECT` | 400 | دو استاد درس مشترک ندارند |

## تصمیم‌ها و فرض‌ها

- نمره و تعداد نظر و درصد توصیه همیشه از نظرهای `approved` حساب می‌شوند و جایی ذخیره نمی‌شوند.
- درصد توصیه از سؤال `would_recommend` می‌آید. نظرهای واردشده از فرانت قدیمی با ۴ یا ۵ ستاره «توصیه می‌کنم» ثبت شده‌اند.
- دو استاد «هم‌درس» هستند اگر حداقل یک درس مشترک داشته باشند.
- ترتیب پیش‌فرض لیست استادها: اول ترتیب درس (`sort_order`)، بعد آیدی.
- نظر جدید باید کاربر داشته باشد؛ فقط نظرهای واردشده (`is_imported`) بدون کاربر مجازند.
- `photoUrl` همان مسیر نسبی فرانت (`assets/teachers/{id}.jpg`) است و فرانت آن را باز می‌کند.

## هنوز ساخته نشده

ورود کاربر، ثبت نظر جدید (`POST`)، پنل ادمین و تأیید نظرها، آپلود عکس، محدودیت تعداد درخواست (rate limit)، و یکدست‌سازی پاسخ خطای اعتبارسنجی (۴۲۲) با قالب بالا.