# 🎌 Anime News Bot (ربات ارسال خودکار اخبار انیمه، مانگا و مانهوا)

<div align="center">

![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated%20Workflow-green?logo=githubactions)
![License](https://img.shields.io/badge/License-MIT-purple)
![Platform](https://img.shields.io/badge/Platform-Bale%20Messenger-orange)

ربات هوشمند پایتونی برای دریافت لحظه‌ای آخرین اخبار، رویدادها، تریلرها و به‌روزرسانی‌های **انیمه، مانگا و مانهوا** از معتبرترین مراجع جهانی، ترجمه خودکار به فارسی و ارسال شکیل به کانال پیام‌رسان بله.

</div>

---

## 🌟 قابلیت‌ها و ویژگی‌ها (Features)

- 📡 **پایش خودکار مراجع معتبر خبری:**
  - **Anime News Network (ANN)** - بزرگ‌ترین مرجع اخبار صنعت انیمه
  - **MyAnimeList (MAL) News** - آخرین اطلاعیه‌ها، فیلم‌ها و رتبه‌بندی‌ها
  - **Anime Corner** - تریلرها، فصل‌های جدید و اخبار اختصاصی
  - **Otaku USA Magazine** - بررسی و اخبار مانگا و انیمه
  - **MangaDex API** - جدیدترین مانهواها و مانگاهای کره‌ای و ژاپنی به همراه کاور رسمی
- 🌐 **ترجمه خودکار به زبان فارسی:** ترجمه روان عناوین و خلاصه‌های خبری با حفظ واژگان تخصصی انیمه‌ای.
- ⚡ **ترجمه تنبل و هوشمند (Lazy Translation):** ترجمه صرفاً برای اخباری که جدید هستند و در صف ارسال قرار می‌گیرند انجام می‌شود تا سهمیه روزانه API هدر نرود و از بلاک شدن IP جلوگیری گردد.
- 🛡️ **سیستم امن و بهینه HTML Formatting:** استفاده از `html.escape` و `html.unescape` برای جلوگیری از خطاهای Parse Mode و کاراکترهای نامعتبر در پیام‌رسان بله.
- 🖼️ **پشتیبانی کامل از تصاویر:** ارسال اخبار همراه با عکس و پوستر به صورت کپشن‌دار (و بازگشت خودکار به پیام متنی در صورت در دسترس نبودن تصویر).
- 🎯 **فیلترینگ هوشمند:** جداسازی اخبار اصلی انیمه و مانگا از اخبار نامربوط (گیمینگ، لایواکشن، سریال‌های تلویزیونی).
- 🕒 **اتوماسیون کامل با GitHub Actions:** اجرای خودکار در فواصل ۱ ساعته بدون نیاز به سرور شخصی یا هزینه نگهداری (Serverless).
- 💾 **جلوگیری از ارسال اخبار تکراری:** ذخیره‌سازی تاریخچه هش شناسه‌های ارسال‌شده (`posted_news.json`) با حفظ ترتیب زمانی.

---

## 🛠️ پیش‌نیازها و وابستگی‌ها

- پایتون نسخه 3.10 یا بالاتر
- پکیج‌های پایتون در `requirements.txt`:
  - `requests`
  - `feedparser`
  - `beautifulsoup4`

---

## ⚙️ راه‌اندازی و اجرای محلی (Local Setup)

### ۱. کلون کردن مخزن
```bash
git clone https://github.com/misamahmoodi190-jpg/anime-news-bot.git
cd anime-news-bot
```

### ۲. ساخت محیط مجازی و نصب وابستگی‌ها
```bash
python -m venv venv
# در لینوکس / مک:
source venv/bin/activate
# در ویندوز:
venv\Scripts\activate

pip install -r requirements.txt
```

### ۳. تنظیم متغیرهای محیطی (Environment Variables)
متغیرهای زیر را در سیستم یا ترمینال خود تنظیم کنید:

| نام متغیر | توضیحات |
| :--- | :--- |
| `BALE_BOT_TOKEN` | توکن ربات ایجاد شده در بات‌فا (BotFather) بله |
| `BALE_CHANNEL_ID` | شناسه عددی یا چت‌آیدی کانال بله مقصد (ربات باید ادمین کانال باشد) |

**در لینوکس / مک:**
```bash
export BALE_BOT_TOKEN="your_bot_token_here"
export BALE_CHANNEL_ID="your_channel_id_here"
```

**در ویندوز (PowerShell):**
```powershell
$env:BALE_BOT_TOKEN="your_bot_token_here"
$env:BALE_CHANNEL_ID="your_channel_id_here"
```

**در ویندوز (CMD):**
```cmd
set BALE_BOT_TOKEN=your_bot_token_here
set BALE_CHANNEL_ID=your_channel_id_here
```

### ۴. اجرای ربات
```bash
python news_bot.py
```

---

## 🚀 راه‌اندازی خودکار با GitHub Actions

این پروژه طوری طراحی شده که به صورت کاملاً رایگان روی **GitHub Actions** اجرا شود:

1. وارد مخزن فورک‌شده‌ی خود در گیت‌هاب شوید.
2. به بخش **Settings > Secrets and variables > Actions** بروید.
3. دو Secret با نام‌های زیر اضافه کنید:
   - `BALE_BOT_TOKEN`: توکن بات بله
   - `BALE_CHANNEL_ID`: شناسه چت کانال بله
4. دسترسی نوشتن Workflow را فعال کنید:
   - از مسیر **Settings > Actions > General > Workflow permissions** گزینه **Read and write permissions** را انتخاب و ذخیره کنید.
5. ورک‌فلو به‌طور خودکار هر ۱ ساعت یک‌بار اجرا می‌شود؛ همچنین از تب **Actions** می‌توانید دکمه **Run workflow** را برای اجرای دستی بزنید.

---

## 📁 ساختار فایل‌های پروژه

```text
anime-news-bot/
├── .github/
│   └── workflows/
│       └── news.yml         # ورک‌فلو اجرای خودکار گیت‌هاب اکشنز
├── news_bot.py              # کد اصلی ربات (دریافت، فیلتر، ترجمه و ارسال)
├── posted_news.json         # فایل تاریخچه شناسه‌های ارسال شده
├── requirements.txt         # لیست پکیج‌ها و پیش‌نیازهای پایتون
└── README.md                # مستندات و راهنمای کامل پروژه
```

---

## 🤝 مشارکت و بهبود (Contributing)

پیشنهادات، گزارش باگ‌ها و Pull Request‌ها با کمال میل استقبال می‌شوند!
اگر منبع خبری جدیدی مدنظر دارید یا ویژگی خاصی می‌خواهید اضافه کنید، کافیست یک Issue یا PR باز کنید.

---

## 📄 مجوز (License)

این پروژه تحت مجوز [MIT License](LICENSE) منتشر شده است.
