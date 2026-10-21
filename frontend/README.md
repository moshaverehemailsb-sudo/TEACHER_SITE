# Baf (باف) — Frontend

سایت ایستا (بدون build). همه‌ی داده از API بک‌اند می‌آید.

```
index.html
css/style.css
js/  api.js, utils.js, state.js, store.js, profile.js, carousel.js, home.js, compare.js, auth.js, app.js
assets/teachers/   <teacher-id>.jpg
```

اسکریپت‌ها ماژول نیستند و به ترتیب `index.html` بارگذاری می‌شوند؛ ترتیب را عوض نکن.

## اجرا

1. بک‌اند را اجرا کن (`uvicorn app.main:app --reload`).
2. فرانت را با یک سرور محلی روی پورت ۵۵۰۰ باز کن (مثلاً Live Server در VS Code). باز کردن مستقیم `index.html` با دابل‌کلیک کار نمی‌کند.
3. آدرس بک‌اند فقط در بالای `js/api.js` (`API_BASE`) نوشته شده است.

آدرس فرانت باید در `CORS_ORIGINS` بک‌اند باشد (پیش‌فرض: `http://localhost:5500` و `http://127.0.0.1:5500`).

## نکات

- هر متنی که از API می‌آید قبل از گذاشتن در `innerHTML` با `esc()` (در `utils.js`) امن می‌شود. هر جای جدیدی هم که متن API را نشان می‌دهی همین کار را بکن.
- توکن ورود در `localStorage` ذخیره می‌شود (کلید `baf_token`).
- عکس استادها مسیر نسبی `assets/teachers/<id>.jpg` است و از همین پروژه باز می‌شود.


cd C:\Users\ASUS\Desktop\TECHERS_SITE
mkdir frontend
Copy-Item -Recurse "C:\Users\ASUS\Desktop\TECHERS_SITE\baf\*" frontend\ -Exclude .git
dir frontend