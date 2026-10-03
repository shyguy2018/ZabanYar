<p align="center">
  <img src="assets/icon.png" width="128" alt="ZabanYar icon">
</p>

<h1 align="center">ZabanYar · زبان‌یار</h1>

<p align="center">
  Fixes words typed with the wrong keyboard language — English ⇄ Persian — on Windows.<br>
  <b>Made by Behrooz Shayestepoor</b>
</p>

<p align="center">
  <a href="../../releases/latest"><b>⬇ Download ZabanYar.exe</b></a> ·
  <a href="#how-to-use-it">How to use</a> ·
  <a href="#راهنمای-فارسی">راهنمای فارسی</a>
</p>

---

## What it does

You meant to write **سلام** but the keyboard was on English, so you got `sghl`.
Or you meant **did you mean** but the keyboard was on Persian, so you got `did غخع ئثشد`.
ZabanYar notices this and fixes it for you.

| You typed | Keyboard was | ZabanYar turns it into |
|---|---|---|
| `sghl` | English | **سلام** |
| `ldo,hl` | English | **میخوام** |
| `غخع ئثشد` | Persian | **you mean** |
| `حقهزث` | Persian | **price** |

Real English and Persian words — and brand names like *Fluke* or *Testo* — are left alone.

## How to use it

### 1. Install
1. Go to the [latest release](../../releases/latest) and download **ZabanYar.exe**.
2. Double-click it. A notice *“ZabanYar is running”* appears in the bottom-right corner for a few seconds.
3. Its icon (blue square with **A** and **ف**) sits near the clock. If you don't see it, click the **^** arrow next to the clock.
   Tip: drag the icon out of the **^** menu onto the taskbar so it is always visible.

Both **English** and **Persian** keyboards must be installed in Windows
(Settings → Time & language → Language & region).

### 2. Just type
Type normally in any program — Word, Chrome, WhatsApp, Notepad… Each time you press <kbd>Space</kbd>, ZabanYar checks the word you just typed:

- **When it is sure** the word was typed with the wrong keyboard, it replaces the word automatically and switches the keyboard language for you, so you can keep typing.
- **When it is not sure**, a small bubble appears next to your text: *«منظورتون این بود؟»* (*Did you mean?*) with the suggested word.
  - Click the bubble or **تبدیل کن ✓** (or press the hotkey) → the text is converted.
  - Click **✕**, press <kbd>Esc</kbd>, or just keep typing → nothing changes. The bubble disappears by itself after a few seconds.
- If several words in a row were wrong, they are all fixed together.

### 3. Fix a word manually
If ZabanYar didn't catch a word, press the **hotkey** (<kbd>Pause</kbd> by default) right after typing it.
The last word (and anything typed after it) is converted to the other language.
Laptop without a <kbd>Pause</kbd> key? Choose <kbd>F8</kbd>, <kbd>F9</kbd> or <kbd>F10</kbd> in the tray menu → **Hotkey**.

### 4. Start automatically
Right-click the tray icon → **Start with Windows**.

### 5. Turn it off or close it
Right-click the tray icon → **Off (hotkey only)** to pause automatic fixing, or **Exit** to close it.

### Good to know
- Automatic fixing happens only on <kbd>Space</kbd> — never on <kbd>Enter</kbd>, so a chat message is never changed after it's sent.
- Clicking somewhere else or switching windows makes ZabanYar forget what you typed.
- It doesn't work inside programs that run *as administrator*, unless you also run ZabanYar as administrator (right-click → **Run as administrator**).

## Settings (tray menu)

| Menu item | What it does |
|---|---|
| **Smart: auto-fix when sure, ask when unsure** | Default mode |
| **Bubble only: always ask first** | Never changes text by itself |
| **Off (hotkey only)** | Only the manual hotkey works |
| **Hotkey** | Pause / F8 / F9 / F10 / Scroll Lock / Insert |
| **Switch keyboard language after fixing** | Also changes the active keyboard |
| **Start with Windows** | Run automatically at login |

Settings are saved in `%APPDATA%\ZabanYar\config.json`; errors (if any) in `error.log` next to it.

## Privacy

ZabanYar reads keystrokes only to recognise the current word. It keeps the last few words in memory,
forgets them when you click or switch windows, and **never saves or sends anything** — there is no
network code at all. Because it reads the keyboard, some antivirus programs may warn about it;
the full source is right here.

## How it works

- `app.py` — Windows part: a low-level keyboard hook, asks Windows what each key would produce in
  your **own** English and Persian layouts (`ToUnicodeEx`), replaces text with `SendInput`, the bubble (Tk)
  and the tray icon (pystray).
- `core.py` — platform-independent decision logic: word-frequency dictionaries for both languages
  (from [wordfreq](https://github.com/rspeer/wordfreq)) plus a character-bigram model for unknown words.
- `tests/` — unit tests for the decision logic (`python -m pytest tests`).

## Build from source

```bat
git clone https://github.com/<you>/ZabanYar.git
cd ZabanYar
build.bat
```

Needs Python 3.10+ ("Add python.exe to PATH" ticked). `build.bat` downloads the word lists (via wordfreq),
creates the icon and builds the program; `ZabanYar.exe` appears in the folder.
To run without building: `run.bat`.

Every push is built automatically by GitHub Actions; pushing a tag like `v1.1` publishes a release with the exe.

---

<div dir="rtl">

## راهنمای فارسی

**زبان‌یار** کلماتی را که با زبان اشتباه کیبورد تایپ شده‌اند خودکار درست می‌کند.
مثلاً اگر کیبورد انگلیسی باشد و بخواهید «سلام» بنویسید، حروف نامفهوم تایپ می‌شود؛ زبان‌یار آن را به «سلام» تبدیل می‌کند.
برعکسش هم کار می‌کند: اگر کیبورد فارسی باشد و انگلیسی تایپ کنید، کلمهٔ انگلیسی درست را می‌نویسد.
کلمه‌های درست فارسی و انگلیسی و اسم برندها دست نمی‌خورند.

### ۱. نصب
۱. به صفحهٔ آخرین نسخه بروید و فایل برنامه را دانلود کنید ([Releases → ZabanYar.exe](../../releases/latest)).
۲. روی فایل دوبار کلیک کنید. چند ثانیه پیامی در گوشهٔ پایین صفحه می‌آید که می‌گوید «زبان‌یار روشن است».
۳. آیکون برنامه (مربع آبی با حروف A و ف) کنار ساعت ویندوز است. اگر نمی‌بینید، روی فلش کوچک ^ کنار ساعت بزنید.
   پیشنهاد: آیکون را از آن منو بکشید و روی نوار وظیفه رها کنید تا همیشه دیده شود.

دقت کنید هر دو کیبورد فارسی و انگلیسی در تنظیمات زبان ویندوز نصب باشند.

### ۲. فقط تایپ کنید
در هر برنامه‌ای مثل ورد، کروم یا واتس‌اپ عادی تایپ کنید. هر بار که کلید فاصله را می‌زنید، زبان‌یار کلمهٔ قبلی را بررسی می‌کند:

- **اگر مطمئن باشد** کلمه با زبان اشتباه تایپ شده، خودش آن را درست می‌کند و زبان کیبورد را هم عوض می‌کند تا بقیه را درست تایپ کنید.
- **اگر مطمئن نباشد**، یک حباب کوچک کنار متن باز می‌شود و می‌پرسد «منظورتون این بود؟» و کلمهٔ پیشنهادی را نشان می‌دهد.
  - روی حباب یا دکمهٔ «تبدیل کن ✓» کلیک کنید یا کلید میانبر را بزنید تا متن تبدیل شود.
  - اگر نمی‌خواهید، روی ✕ بزنید یا به تایپ ادامه دهید؛ حباب بعد از چند ثانیه خودش بسته می‌شود.
- اگر چند کلمه پشت سر هم اشتباه تایپ شده باشد، همه با هم درست می‌شوند.

### ۳. تبدیل دستی
اگر برنامه کلمه‌ای را تشخیص نداد، بلافاصله بعد از تایپ آن کلید میانبر را بزنید تا آخرین کلمه به زبان دیگر تبدیل شود.
کلید میانبر پیش‌فرض کلید توقف است (Pause).
اگر لپ‌تاپتان این کلید را ندارد، روی آیکون راست‌کلیک کنید و از منوی کلید میانبر یکی دیگر را انتخاب کنید (Hotkey → F8 / F9 / F10).

### ۴. اجرای خودکار با روشن شدن ویندوز
روی آیکون راست‌کلیک کنید و این گزینه را بزنید (Start with Windows).

### ۵. تنظیمات منوی آیکون
روی آیکون کنار ساعت راست‌کلیک کنید. گزینه‌ها:

| گزینه در منو | کارش |
|---|---|
| Smart: auto-fix when sure, ask when unsure | حالت پیش‌فرض: وقتی مطمئن است خودش درست می‌کند، وقتی نه، می‌پرسد |
| Bubble only: always ask first | هیچ‌وقت خودش تغییر نمی‌دهد، همیشه اول می‌پرسد |
| Off (hotkey only) | تشخیص خودکار خاموش؛ فقط کلید میانبر کار می‌کند |
| Hotkey | انتخاب کلید میانبر |
| Switch keyboard language after fixing | بعد از تبدیل، زبان کیبورد هم عوض شود |
| Start with Windows | اجرای خودکار با ویندوز |
| About | دربارهٔ برنامه |
| Exit | بستن برنامه |

### نکته‌ها
- تبدیل خودکار فقط با کلید فاصله انجام می‌شود، نه با اینتر؛ پس پیامی که فرستاده‌اید عوض نمی‌شود.
- با کلیک در جای دیگر یا رفتن به پنجرهٔ دیگر، برنامه کلمه‌های قبلی را فراموش می‌کند.
- در برنامه‌هایی که با دسترسی مدیر اجرا شده‌اند کار نمی‌کند، مگر اینکه زبان‌یار را هم با راست‌کلیک و این گزینه اجرا کنید (Run as administrator).
- **حریم خصوصی:** برنامه هیچ چیزی را ذخیره یا به اینترنت ارسال نمی‌کند.
- ممکن است آنتی‌ویروس هشدار بدهد، چون برنامه کیبورد را می‌خواند؛ کد کامل برنامه همین‌جاست.

**ساخته شده توسط بهروز شایسته‌پور**

</div>

## License

[MIT](LICENSE) © 2026 Behrooz Shayestepoor — word lists in `data/` are CC BY-SA 4.0 (from wordfreq, see [data/SOURCES.md](data/SOURCES.md)).
