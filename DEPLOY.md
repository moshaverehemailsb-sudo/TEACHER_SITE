# راهنمای انتشار روی سرور (Ubuntu)

ساختار: nginx فایل‌های فرانت را می‌دهد و درخواست‌های `/api/` را به بک‌اند (uvicorn) می‌فرستد. دیتابیس همان Neon است. فرانت و API روی یک آدرس‌اند، پس CORS لازم نیست.

## ۱. پیش‌نیازها

```bash
sudo apt update
sudo apt install -y python3 python3-venv nginx git ufw
sudo adduser --system --group --home /srv/baf baf
```

نسخه‌ی پایتون سرور را هم‌نسخه‌ی کامپیوتر خودت بگیر (۳.۱۴). اگر نبود، با نسخه‌ی پایین‌تر امتحان کن و ببین `pip install -r requirements.txt` خطا می‌دهد یا نه.

## ۲. بک‌اند

```bash
sudo -u baf git clone <آدرس ریپوی بک‌اند> /srv/baf/backend
cd /srv/baf/backend
sudo -u baf python3 -m venv .venv
sudo -u baf .venv/bin/pip install -r requirements.txt
sudo -u baf cp .env.example .env
sudo chmod 600 .env
sudo -u baf nano .env
```

مقدارهای `.env` سرور (همه‌ی رمزها را **تازه** بساز، نه همان‌های کامپیوتر خودت):

```
DATABASE_URL=postgresql+psycopg://...
APP_ENV=production
SECRET_KEY=<token_urlsafe(48)>
PHONE_HASH_KEY=<token_urlsafe(48)>
ADMIN_TOKEN=<token_urlsafe(48)>
SMS_PROVIDER=<اسم سرویس پیامک، بعد از وصل شدن>
SMS_DAILY_LIMIT=500
FORWARDED_ALLOW_IPS=127.0.0.1
```

`FRONTEND_DIR` و `CORS_ORIGINS` را خالی بگذار (nginx فرانت را می‌دهد).

دیتابیس:

```bash
sudo -u baf .venv/bin/alembic upgrade head
sudo -u baf .venv/bin/python -m app.seed
sudo -u baf .venv/bin/python -m app.import_baf
```

`import_baf` فقط یک‌بار و برای داده‌ی اولیه است. دیتابیس production را جدا از دیتابیس توسعه بساز.

## ۳. اجرای همیشگی بک‌اند (systemd)

فایل `/etc/systemd/system/baf-api.service`:

```ini
[Unit]
Description=Baf API
After=network.target

[Service]
User=baf
Group=baf
WorkingDirectory=/srv/baf/backend
EnvironmentFile=/srv/baf/backend/.env
ExecStart=/srv/baf/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --workers 1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

محدودیت تعداد درخواست در حافظه‌ی هر پردازش است، پس فعلاً `--workers 1` بماند.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now baf-api
curl http://127.0.0.1:8000/health
```

باید `{"status":"ok"}` ببینی.

## ۴. فرانت

از کامپیوتر خودت (PowerShell، داخل پوشه‌ی فرانت؛ `.git` را نفرست):

```powershell
scp -r index.html admin.html css js assets USER@SERVER_IP:/tmp/baf-frontend/
```

روی سرور:

```bash
sudo mkdir -p /srv/baf/frontend
sudo cp -r /tmp/baf-frontend/* /srv/baf/frontend/
```

## ۵. nginx

فایل `/etc/nginx/sites-available/baf`:

```nginx
proxy_cache_path /var/cache/nginx/baf levels=1:2 keys_zone=baf:10m max_size=200m inactive=10m use_temp_path=off;

server {
    listen 80;
    server_name _;          # بعد از خرید دامنه: server_name example.ir www.example.ir;

    root /srv/baf/frontend;
    index index.html;
    client_max_body_size 64k;

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    location ~ /\. { deny all; }

    # خواندن‌های عمومی: ۶۰ ثانیه کش (بار روی بک‌اند را خیلی کم می‌کند)
    location ~ ^/api/v1/(subjects|popular-comparisons|teachers) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache baf;
        proxy_cache_methods GET HEAD;
        proxy_cache_valid 200 60s;
        proxy_cache_bypass $http_authorization;
        proxy_no_cache $http_authorization;
        add_header X-Cache $upstream_cache_status;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health { proxy_pass http://127.0.0.1:8000; }

    location /assets/ { expires 7d; }

    location / { try_files $uri $uri/ /index.html; }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/baf /etc/nginx/sites-enabled/baf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

نتیجه‌ی کش: نظر تأییدشده‌ی جدید تا ۶۰ ثانیه دیرتر در سایت دیده می‌شود. درخواست‌های ورود، ثبت نظر و مدیریت هرگز کش نمی‌شوند.

## ۶. فایروال

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

پورت ۸۰۰۰ بیرون باز نیست؛ فقط nginx به آن وصل می‌شود.

## ۷. بررسی

- `http://SERVER_IP/` سایت را نشان بدهد.
- `curl -I http://SERVER_IP/api/v1/subjects` دو بار پشت سر هم: بار اول `X-Cache: MISS`، بار دوم `HIT`.
- `http://SERVER_IP/admin.html` صفحه‌ی مدیریت (با `ADMIN_TOKEN` سرور).

## ۸. پاکسازی کدهای ورود قدیمی

```bash
sudo -u baf crontab -e
```

```
0 4 * * * cd /srv/baf/backend && .venv/bin/python -m app.cleanup
```

## به‌روزرسانی بک‌اند

```bash
cd /srv/baf/backend
sudo -u baf git pull
sudo -u baf .venv/bin/pip install -r requirements.txt
sudo -u baf .venv/bin/alembic upgrade head
sudo systemctl restart baf-api
```

برای فرانت، فایل‌های تغییرکرده را دوباره با `scp` و `cp` به `/srv/baf/frontend` بفرست.

## بعد از خرید دامنه

1. رکورد DNS دامنه را به IP سرور بزن.
2. در nginx مقدار `server_name` را به دامنه عوض کن و `sudo systemctl reload nginx`.
3. گواهی HTTPS بگیر (معمولاً `certbot`) و آدرس `http` را به `https` هدایت کن.

## بعد از انتخاب سرویس پیامک

کلاس ارسال اضافه می‌شود، `SMS_PROVIDER` و کلید سرویس در `.env` سرور تنظیم می‌شود و `sudo systemctl restart baf-api` می‌زنی.