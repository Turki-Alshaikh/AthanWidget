<div align="center">
  <img src="icon.ico" alt="AthanWidget Logo" width="100"/>
  <h1>🕌 AthanWidget</h1>
  <p><strong>A Sleek, Minimalist Windows Desktop Widget for Prayer Times</strong></p>
  <p><strong>ويدجت احترافي وعائم لمواقيت الصلاة على سطح المكتب (Windows)</strong></p>

  [![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)](https://github.com/Turki-Alshaikh/AthanWidget/releases/latest)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](#)
  [![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](#)
</div>

<br>

<div align="center">
  <a href="#-arabic-عربي">عربي 🇸🇦</a> &nbsp; | &nbsp; <a href="#-english">English 🇺🇸</a>
</div>

---

## 🇸🇦 Arabic (عربي)

### 🌟 نبذة عن التطبيق
**AthanWidget** هو أداة ذكية وأنيقة لسطح المكتب تتيح لك متابعة الوقت المتبقي للصلاة القادمة بكل سهولة. يتميز التطبيق بتصميم عصري (Minimalist & Dark Mode) مستوحى من أدوات Apple (Widgets). يعمل التطبيق بهدوء في الخلفية دون أن يزعجك، مع نظام ذكي للتنبيهات والتحديثات.

### ✨ المميزات الأساسية (تحديث v1.1.0)
- 📍 **تحديد ذكي للموقع:** يجلب مواقيت الصلاة ويعرض اسم مدينتك الحالية تلقائياً بدقة بناءً على عنوان IP.
- 💾 **حفظ نظيف (Registry):** لا حاجة لملفات خارجية (مثل JSON). يحفظ التطبيق إعداداته وموقعه بهدوء وأمان داخل سجل الويندوز (Windows Registry).
- 🎨 **تخصيص حر وشفافية:** واجهة أنيقة بزوايا دائرية. يمكنك إخفاء الخلفية تماماً، أو إخفاء الحدود، أو تغيير الألوان للحصول على نصوص عائمة نقية على الشاشة.
- 🕰️ **ذكاء زمني (مضى على الصلاة):** بعد الأذان، سيتحول العداد ليعرض "مضى على الصلاة" لمدة 30 دقيقة كحد أقصى قبل الانتقال تلقائياً للصلاة القادمة.
- 🔔 **نظام الإشعارات (التنبيهات):** إشعارات منبثقة ذكية في شريط المهام (يمكنك تحديد تنبيه قبل الأذان بـ 5 دقائق مثلاً، وتنبيه وقت الأذان الفعلي).
- 🔄 **تحديث تلقائي (Auto-Updater):** نظام ذكي للتحقق من التحديثات من GitHub وتحميلها واستبدالها بنقرة واحدة وفي الخلفية.
- ⚙️ **إعدادات متقدمة (Modern UI):** لوحة تحكم بتصميم أبل تتيح لك التبديل بين الأرقام العربية/الإنجليزية، والتشغيل التلقائي مع بدء الويندوز.

### 🚀 طريقة الاستخدام (للمستخدمين)
لا حاجة لتثبيت بايثون أو أي برامج أخرى! 
1. اذهب إلى قسم [Releases](../../releases/latest).
2. قم بتحميل أحدث إصدار من ملف `AthanWidget.exe`.
3. ضع الملف في أي مجلد تفضله، شغله، واستمتع! (يمكنك النقر على الزاوية اليمنى السفلية لتغيير حجمه متى شئت).

### 🛠️ للمطورين (تشغيل الكود المصدري)
إذا كنت مطوراً وترغب في التعديل على المشروع:

1. تثبيت المكتبات المطلوبة:
```bash
pip install PyQt6 requests
```
2. تشغيل السكربت:
```bash
python AthanWidget.py
```
3. تحويله إلى ملف تنفيذي `.exe` للتوزيع:
```bash
pyinstaller --noconsole --onefile --icon=icon.ico --add-data "icon.ico;." AthanWidget.py
```

---

## 🇺🇸 English

### 🌟 About The App
**AthanWidget** is a smart, elegant desktop widget that helps you track the remaining time for the next Islamic prayer. Featuring a minimalist, Apple-inspired Dark Mode design, it runs silently in the background without cluttering your workspace, providing smart notifications and seamless updates.

### ✨ Key Features (v1.1.0 Update)
- 📍 **Smart Location Detection:** Automatically fetches prayer times and displays your current city name based on your IP address.
- 💾 **Clean Registry Save:** No more messy external files (like JSON). The app securely saves your preferences and widget position directly in the Windows Registry.
- 🎨 **Ultimate Customization:** Adjust background transparency, hide the background completely, hide borders, or change colors to get pure floating text on your desktop.
- 🕰️ **Smart Time Tracking:** After the Athan, the timer intelligently switches to "Time elapsed since prayer" for up to 30 minutes before transitioning to the next prayer.
- 🔔 **Smart Notifications:** Customizable system tray pop-up alerts (e.g., notify 5 minutes before Athan, and exactly at Athan time).
- 🔄 **Seamless Auto-Updater:** Built-in mechanism to check for updates via GitHub API, download, and replace the old version automatically with one click.
- ⚙️ **Modern UI Settings:** An iOS-like control panel allowing you to toggle Arabic/English numerals and enable "Run at Windows startup".

### 🚀 How to Use (For Users)
No need to install Python or any dependencies!
1. Go to the [Releases](../../releases/latest) section.
2. Download the latest `AthanWidget.exe` file.
3. Place it anywhere you like, run it, and enjoy! (You can drag the bottom-right corner to resize the widget).

### 🛠️ For Developers (Running from Source)
If you want to tweak the code:

1. Install requirements:
```bash
pip install PyQt6 requests
```
2. Run the script:
```bash
python AthanWidget.py
```
3. Build the executable (`.exe`):
```bash
pyinstaller --noconsole --onefile --icon=icon.ico --add-data "icon.ico;." AthanWidget.py
```

<br>

---

<div align="center">
  <strong>Developed by <a href="https://github.com/Turki-Alshaikh">Turki Alshaikh</a></strong>
  <br>
  <sub>صُنع بكل 💙 لخدمة المسلمين | Made with 💙 to serve Muslims</sub>
</div>
