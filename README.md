# Baf API (بک‌اند سایت باف)

بک‌اند سایت «باف»، برای پیدا کردن و مقایسه‌ی اساتید کنکور و خواندن و ثبت نظر دانش‌آموزان.
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
4. فایل `.env.example` را کپی کن به اسم `.env` و مقدارها را پر کن (جدول زیر). رمزها را هرگز در گیت نگذار.
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
| `ADMIN_TOKEN` | توکن بخش مدیریت. اگر خالی باشد بخش مدیریت غیرفعال است (`ADMIN_DISABLED`) |
| `SECRET_KEY` | کلید امضای توکن ورود کاربر. اگر عوض شود همه‌ی توکن‌ها بی‌اعتبار می‌شوند |
| `PHONE_HASH_KEY` | کلید هش شماره‌ی موبایل. **هرگز عوضش نکن**، وگرنه همه‌ی کاربران قبلی «جدید» حساب می‌شوند |
| `SMS_PROVIDER` | روش ارسال پیامک. `console` فقط برای توسعه است (کد در ترمینال چاپ می‌شود). خالی یعنی ارسال پیامک غیرفعال (`SMS_DISABLED`) |

رمزهای `ADMIN_TOKEN` و `SECRET_KEY` و `PHONE_HASH_KEY` را با این دستور بساز:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

فرانت را با یک سرور محلی روی پورت ۵۵۰۰ باز کن (مثلاً Live Server در VS Code). باز کردن مستقیم فایل `index.html` با دابل‌کلیک از CORS رد می‌شود.

## تست‌ها

```powershell
pytest -v
```

تست‌ها روی همان `DATABASE_URL` اجرا می‌شوند. تست‌های دیتابیس داخل تراکنشی اجرا می‌شوند که در پایان برگردانده می‌شود، پس داده‌ای باقی نمی‌ماند (فقط شمارنده‌ی آیدی‌ها جلو می‌رود). تست‌های API داده‌ی واقعی فرانت را می‌خوانند، پس قبل از `pytest` باید `app.seed` و `app.import_baf` را اجرا کرده باشی.

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

برای استاد بدون نظر، `rating` و `recommendPercent` برابر `null` و `reviewCount` برابر `0` است. `style` و `level` و `photoUrl` هم ممکن است `null` باشند.

### Endpointهای عمومی

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

شکل `bio`: `{ classStyle, method, levelText, problemSolving, education, experience, note }`. اگر استاد بیوگرافی ندارد `bio` برابر `null` است. `education` ممکن است چند خط باشد که با `\n` جدا شده‌اند.

### ورود با شماره موبایل

| متد و آدرس | توضیح |
|---|---|
| `POST /auth/request-code` | بدنه: `{ phone }`. شماره با فرمت‌های `09...`، `+98...`، `0098...` و ارقام فارسی پذیرفته می‌شود. پاسخ: `{ message, expiresIn: 120, retryAfter: 60 }` |
| `POST /auth/verify-code` | بدنه: `{ phone, code }` (کد ۶ رقمی، ارقام فارسی هم مجاز). پاسخ: `{ accessToken, tokenType: "bearer", expiresIn, user: { id, displayName } }` |
| `GET /auth/me` | کاربر واردشده. نیاز به هدر `Authorization: Bearer <accessToken>` |

کد ۲ دقیقه اعتبار دارد، یک‌بار مصرف است و حداکثر ۵ بار می‌شود امتحانش کرد. هر شماره هر ۶۰ ثانیه یک کد و حداکثر ۵ کد در ساعت می‌گیرد. شماره‌ی موبایل به‌صورت خام ذخیره نمی‌شود، فقط یک هش. توکن ۳۰ روز اعتبار دارد.

### ثبت نظر

`POST /teachers/{id}/reviews` با هدر `Authorization: Bearer <accessToken>`.

```json
{
  "reviewerLabel": "دانش‌آموز پایه دوازدهم",
  "stars": 5,
  "recommends": true,
  "body": "متن نظر، حداکثر ۱۰۰۰ کاراکتر"
}
```

مقدارهای مجاز `reviewerLabel`: «دانش‌آموز پایه دهم»، «دانش‌آموز پایه یازدهم»، «دانش‌آموز پایه دوازدهم»، «فارغ‌التحصیل». `stars` بین ۱ تا ۵ است. پاسخ `201`: `{ id, status: "pending", message }`. نظر بعد از تأیید ادمین نمایش داده می‌شود. هر کاربر برای هر استاد یک نظر دارد و حداکثر ۵ نظر در ساعت می‌تواند ثبت کند. تگ‌های HTML از متن نظر حذف می‌شوند، ولی فرانت هم باید هر متنی را که از API می‌گیرد escape کند.

### Endpointهای مدیریت

همه با هدر `Authorization: Bearer <ADMIN_TOKEN>` و زیر `/api/v1/admin` هستند.

| متد و آدرس | توضیح |
|---|---|
| `GET /admin/reviews?status=` | صف نظرها (`pending` پیش‌فرض، یا `approved`/`rejected`/`hidden`/`all`) |
| `PATCH /admin/reviews/{id}` | `{ "status": "approved", "note": "..." }` تأیید، رد یا مخفی کردن |
| `POST /admin/teachers` | ساخت استاد: `name`، `subject`، `style`، `level`، `tags`، `photoUrl`، `bio`، `isActive` |
| `GET /admin/teachers/{id}` | استاد را حتی اگر غیرفعال باشد برمی‌گرداند |
| `PATCH /admin/teachers/{id}` | ویرایش فیلدهای ارسال‌شده. `tags` کل تگ‌های تأییدشده را جایگزین می‌کند. `bio` فقط فیلدهای ارسال‌شده را عوض می‌کند. `null` برای `style` و `level` و `photoUrl` مقدار را پاک می‌کند |
| `POST /admin/teachers/{id}/courses` | ساخت دوره: `title`، `description` |
| `PATCH /admin/courses/{id}` | `title`، `description`، `status` (`draft`/`published`/`archived`)، `sortOrder` |
| `POST /admin/popular-comparisons` | `{ teacherAId, teacherBId, label }` (باید هم‌درس باشند) |
| `DELETE /admin/popular-comparisons/{id}` | حذف مقایسه‌ی پرطرفدار |

استاد و دوره حذف نمی‌شوند: استاد با `isActive: false` غیرفعال و دوره با `status: archived` آرشیو می‌شود تا نظرها و تاریخچه حفظ شوند. `photoUrl` فقط مسیری که با `assets/` شروع شود یا آدرس `https://` را می‌پذیرد.

## خطاها

همه‌ی خطاها این قالب را دارند:

```json
{ "error": { "code": "TEACHER_NOT_FOUND", "message": "استاد پیدا نشد." } }
```

خطای اعتبارسنجی (`VALIDATION_ERROR`) یک فیلد `details` هم دارد: `[{ field, message }]`.

| کد | وضعیت | معنی |
|---|---|---|
| `VALIDATION_ERROR` | 422 | داده‌ی ارسالی معتبر نیست |
| `INVALID_PHONE` | 422 | شماره‌ی موبایل معتبر نیست |
| `COMPARE_MISSING_IDS` | 400 | یکی از `a` یا `b` ارسال نشده |
| `COMPARE_SAME_TEACHER` | 400 | دو آیدی برابرند |
| `COMPARE_DIFFERENT_SUBJECT` | 400 | دو استاد درس مشترک ندارند |
| `SUBJECT_NOT_FOUND` | 400 | درس وجود ندارد |
| `TEACHER_HAS_NO_SUBJECT` | 400 | استاد درسی ندارد |
| `CODE_INVALID` | 400 | کد ورود نادرست، منقضی یا مصرف‌شده است |
| `UNAUTHORIZED` | 401 | توکن نیست یا نامعتبر است |
| `ACCOUNT_DISABLED` | 403 | حساب غیرفعال شده است |
| `NOT_FOUND` / `TEACHER_NOT_FOUND` / `COURSE_NOT_FOUND` / `REVIEW_NOT_FOUND` / `PAIR_NOT_FOUND` | 404 | مورد پیدا نشد |
| `METHOD_NOT_ALLOWED` | 405 | متد مجاز نیست |
| `REVIEW_EXISTS` / `PAIR_EXISTS` | 409 | تکراری است |
| `PAYLOAD_TOO_LARGE` | 413 | حجم درخواست بیش از ۶۴ کیلوبایت |
| `RATE_LIMITED` / `CODE_RECENTLY_SENT` / `TOO_MANY_ATTEMPTS` | 429 | تعداد درخواست یا تلاش بیش از حد مجاز |
| `SETUP_INCOMPLETE` | 500 | داده‌ی اولیه کامل نیست (`app.seed` اجرا نشده) |
| `SMS_FAILED` | 502 | ارسال پیامک ناموفق بود |
| `ADMIN_DISABLED` / `AUTH_DISABLED` / `SMS_DISABLED` | 503 | بخش مربوطه تنظیم نشده است |

## تصمیم‌ها و فرض‌ها

- نمره و تعداد نظر و درصد توصیه همیشه از نظرهای `approved` حساب می‌شوند و جایی ذخیره نمی‌شوند.
- درصد توصیه از سؤال `would_recommend` می‌آید. نظرهای واردشده از فرانت قدیمی با ۴ یا ۵ ستاره «توصیه می‌کنم» ثبت شده‌اند.
- دو استاد «هم‌درس» هستند اگر حداقل یک درس مشترک داشته باشند.
- ترتیب پیش‌فرض لیست استادها: اول ترتیب درس (`sort_order`)، بعد آیدی.
- نظر جدید باید کاربر داشته باشد؛ فقط نظرهای واردشده (`is_imported`) بدون کاربر مجازند.
- `photoUrl` همان مسیر نسبی فرانت (`assets/teachers/{id}.jpg`) است و فرانت آن را باز می‌کند.
- محدودیت تعداد درخواست فعلاً در حافظه‌ی همان پردازش است. برای چند سرور باید به Redis منتقل شود.

## هنوز ساخته نشده

ارسال واقعی پیامک (فعلاً فقط حالت `console`)، آپلود عکس، کپچا روی درخواست کد، Dockerfile و انتشار.