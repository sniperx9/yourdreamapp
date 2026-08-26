# ============================================================
#  YOUR DREAM - AI Financial Markets Analysis App (v8.4.1)
#  ✅ إصلاح جذري لمشكلة "الأخبار لا تعمل": المصدر الحقيقي لفوركس فاكتوري
#             يرجع حقل "date" واحد بصيغة ISO-8601 مع منطقة زمنية (لا يوجد
#             حقل "time" منفصل كما كان الكود القديم يفترض) → كل الأخبار كانت
#             تفشل بصمت. الآن يُحلَّل date بشكل صحيح ويُحوَّل لتوقيت الجهاز
#             المحلي، فتظهر الأخبار وتُحدَّث يوماً بيوم كما هي في الموقع.
#  ✅ برومبت SMC/ICT جديد كلياً بمستوى احترافي مؤسسي (Order Blocks, FVG,
#             BOS/CHoCH, Liquidity Pools, Confluence) + قراءة قناة
#             MA50-High / MA50-Low المرسومة على الجارت كفلتر اتجاه ودعم/
#             مقاومة ديناميكي ونقطة تلاقي إضافية لجودة الدخول
#  ✅ تبسيط النتيجة إلى هدف واحد (tp) فقط بدل هدفين (كان tp1/tp2) مع دخول
#             صفر انعكاس ووقف خسارة واحد، حسب طلب المستخدم
#  ✅ إصلاح: تعريف _fake() في AIEngine (كان مفقوداً بالكامل)
#  ✅ إصلاح: التقويم الاقتصادي كان يستخدم self._s غير المعرّف أبداً
#             → الأخبار كانت ثابتة/وهمية دائماً، الآن تُجلب فعلياً عبر urllib
#  ✅ إصلاح: إضافة سياق SSL (certifi) لحل CERTIFICATE_VERIFY_FAILED الشائع على أندرويد
#  ✅ إصلاح: تسجيل السبب الحقيقي دائماً بدل "غير معروف" (finishReason/API error/JSON parse)
#  ✅ إصلاح: رد Gemini كان يُقطع قبل اكتمال JSON (نفد maxOutputTokens=1200)
#             → رفع الحد إلى 3000 + طلب شرح موجز + إصلاح تلقائي للـ JSON المقطوع
#  ✅ حل مشكلة نصف الشاشة (Flet 0.86.1 compatible)
#  ✅ تسجيل دخول تلقائي (تذكر الجلسة)
#  ✅ التقاط صورة بالكاميرا أو رفع من المعرض
#  ✅ إزالة FilePicker من overlay (سبب الخطأ الأحمر)
#  ✅ منع تعدد الحسابات من نفس الجهاز
#  ✅ فترة تجريبية 3 أيام / 2 تحليل يومياً
#  ✅ لا خصم نقطة عند "لا توجد فرصة"
#  ✅ إلزام اختيار الزوج قبل رفع الصورة
#  ✅ إصلاح خطأ url غير معرّف
#  ✅ gemini-3.6-flash فقط
#  ✅ برومبت SMC/ICT احترافي مع فرق Scalping/Swing
#  ✅ تعليمات صفر انعكاس (Zero Reversal)
#  ✅ AI Engine يستخدم urllib فقط (بدون requests)
#  ✅ تحسين جلب الأخبار
#  ✅ أسعار وهمية محدثة
#  ✅ متوافق مع Flet 0.86.1 وأندرويد APK
# ============================================================

import flet as ft
import os, sqlite3, json, base64, re, uuid, hashlib
import datetime, random, threading, time, platform
from typing import Optional, Dict, List, Tuple

# ✅ urllib is built-in Python library, no pip install needed
import urllib.request
import urllib.error
import urllib.parse
import ssl

# ✅ إصلاح مشكلة CERTIFICATE_VERIFY_FAILED الشائعة جداً على أندرويد
# python-for-android لا يحتوي على متجر شهادات النظام، لذا urlopen()
# يفشل بصمت بخطأ SSL عند تنفيذه داخل APK حتى لو كان الاتصال بالإنترنت سليم.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    # إذا لم تتوفر certifi (لم تُضف كاعتمادية عند البناء) نستخدم سياق غير متحقق
    # كحل بديل مؤقت حتى لا يفشل كل طلب تماماً على الجهاز
    _SSL_CTX = ssl._create_unverified_context()

# ============================================================
#  HELPERS
# ============================================================
def _ic(*names):
    ns = getattr(ft, 'Icons', getattr(ft, 'icons', None))
    if not ns: return names[-1]
    for n in names:
        if hasattr(ns, n.upper()): return getattr(ns, n.upper())
        if hasattr(ns, n):        return getattr(ns, n)
    return names[-1]

def _op(color, opacity):  return f"{color},{opacity}"
def _border(w, color):
    for fn in [lambda: ft.Border.all(w, color), lambda: ft.border.all(w, color)]:
        try: return fn()
        except: pass
def _pad_sym(h, v):
    for fn in [lambda: ft.Padding.symmetric(horizontal=h,vertical=v),
               lambda: ft.padding.symmetric(horizontal=h,vertical=v),
               lambda: ft.Padding(left=h,right=h,top=v,bottom=v)]:
        try: return fn()
        except: pass
    return h
def _pad_only(l=0,t=0,r=0,b=0):
    for fn in [lambda: ft.Padding.only(left=l,top=t,right=r,bottom=b),
               lambda: ft.padding.only(left=l,top=t,right=r,bottom=b),
               lambda: ft.Padding(left=l,top=t,right=r,bottom=b)]:
        try: return fn()
        except: pass
    return l
def _marg_sym(h,v):
    for fn in [lambda: ft.Margin.symmetric(horizontal=h,vertical=v),
               lambda: ft.margin.symmetric(horizontal=h,vertical=v),
               lambda: ft.Margin(left=h,right=h,top=v,bottom=v)]:
        try: return fn()
        except: pass
    return h
def _align(name):
    coords = {"center":(0,0),"top_left":(-1,-1),"bottom_right":(1,1),"bottom_center":(0,1)}
    for src in [lambda: getattr(ft.alignment, name),
                lambda: getattr(ft.alignment, name.upper()),
                lambda: ft.Alignment(*coords.get(name,(0,0)))]:
        try: return src()
        except: pass
    return name
def _e(cls, attr, default):
    try:
        c = getattr(ft, cls)
        for a in [attr.upper(), attr.lower(), attr]:
            if hasattr(c, a): return getattr(c, a)
    except: pass
    return default

IC = {
    'sun':_ic('WB_SUNNY','BRIGHTNESS_5'),'moon':_ic('NIGHTS_STAY','DARK_MODE'),
    'info':_ic('INFO','INFO_OUTLINE'),'check':_ic('CHECK_CIRCLE','DONE_ALL'),
    'warn':_ic('WARNING_AMBER','WARNING'),'refresh':_ic('REFRESH','SYNC'),
    'logout':_ic('LOGOUT','EXIT_TO_APP'),'launch':_ic('OPEN_IN_NEW','LAUNCH'),
    'verified':_ic('VERIFIED','VERIFIED_USER'),'key':_ic('VPN_KEY','KEY','LOCK'),
    'store':_ic('SHOPPING_BAG','STORE'),'person':_ic('PERSON','ACCOUNT_CIRCLE'),
    'home':_ic('HOME','HOUSE'),'history':_ic('HISTORY','RESTORE'),
    'bolt':_ic('BOLT','FLASH_ON'),'clock':_ic('ACCESS_TIME','SCHEDULE'),
    'chart':_ic('SHOW_CHART','TRENDING_UP'),'email':_ic('EMAIL','MAIL'),
    'lock':_ic('LOCK','SECURITY'),'login':_ic('LOGIN','ARROW_FORWARD'),
    'add_usr':_ic('PERSON_ADD','GROUP_ADD'),'camera':_ic('CAMERA_ALT','CAMERA'),
    'tg':_ic('CHAT','FORUM'),'star':_ic('STAR','GRADE'),
    'deal':_ic('AUTO_AWESOME','FLASH_AUTO'),'news':_ic('NEWSPAPER','FEED'),
    'settings':_ic('MANAGE_ACCOUNTS','SETTINGS'),'upload':_ic('UPLOAD','CLOUD_UPLOAD'),
    'today':_ic('TODAY','CALENDAR_TODAY'),'bell':_ic('NOTIFICATIONS','NOTIFICATION_IMPORTANT'),
    'week':_ic('DATE_RANGE','CALENDAR_VIEW_WEEK'),'filter':_ic('FILTER_LIST','TUNE'),
    'delete':_ic('DELETE_FOREVER','DELETE'),'reset':_ic('RESTART_ALT','REFRESH'),
}

# ============================================================
#  LANGUAGE / i18n
# ============================================================
# ✅ حالة اللغة الحالية عالمية (يقرأها L() و PICK() من أي مكان بالكود، حتى
# داخل كلاسات مثل Calendar/TradingHours التي ليس لديها وصول مباشر لـ self.lang)
_LANG_STATE = {"v": "AR"}

def set_lang(lang: str):
    _LANG_STATE["v"] = "EN" if lang == "EN" else "AR"

def cur_lang() -> str:
    return _LANG_STATE["v"]

def PICK(ar, en):
    """اختيار مباشر بين نص عربي وإنكليزي جاهزين (يُستخدم للنصوص الديناميكية)"""
    return en if _LANG_STATE["v"] == "EN" else ar

# قاموس ترجمة لكل النصوص الثابتة الظاهرة بالواجهة (مفتاح=عربي، قيمة=إنكليزي)
AR_EN = {
    # -------- Auth / DB messages --------
    "البريد مسجل مسبقاً": "Email already registered",
    "هذا الجهاز مرتبط بحساب آخر، سجّل الدخول": "This device is linked to another account. Please log in",
    "تم إنشاء الحساب بنجاح ✅": "Account created successfully ✅",
    "البريد الإلكتروني غير مسجل": "Email not registered",
    "كلمة المرور غير صحيحة": "Incorrect password",
    "مرحباً Admin": "Welcome Admin",
    "الحساب مرتبط بجهاز آخر": "This account is linked to another device",
    "تم تسجيل الدخول ✅": "Logged in successfully ✅",
    "المفتاح غير صالح": "Invalid key",
    "المفتاح مستخدم مسبقاً": "Key already used",
    # -------- Tier labels --------
    "تجريبي": "Trial",
    "أساسية": "Basic",
    "متقدمة": "Advanced",
    "مخصص": "Custom",
    # -------- Currencies --------
    "🇺🇸 الدولار الأمريكي": "🇺🇸 US Dollar",
    "🇪🇺 اليورو": "🇪🇺 Euro",
    "🇬🇧 الجنيه الإسترليني": "🇬🇧 British Pound",
    "🇯🇵 الين الياباني": "🇯🇵 Japanese Yen",
    "🇨🇭 الفرنك السويسري": "🇨🇭 Swiss Franc",
    "🇨🇦 الدولار الكندي": "🇨🇦 Canadian Dollar",
    "🇦🇺 الدولار الأسترالي": "🇦🇺 Australian Dollar",
    "🇳🇿 الدولار النيوزيلندي": "🇳🇿 New Zealand Dollar",
    "🇨🇳 اليوان الصيني": "🇨🇳 Chinese Yuan",
    "🌍 جميع العملات": "🌍 All Currencies",
    # -------- Impact --------
    "🔴 عالي": "🔴 High",
    "🟡 متوسط": "🟡 Medium",
    "🟢 منخفض": "🟢 Low",
    # -------- Fallback event names --------
    "مؤشر مديري المشتريات (PMI) - منطقة اليورو": "Eurozone Manufacturing PMI",
    "مخزونات النفط الخام (EIA)": "Crude Oil Inventories (EIA)",
    "مؤشر ثقة المستهلك (Michigan)": "Michigan Consumer Sentiment Index",
    # -------- Trading sessions --------
    "سيدني": "Sydney", "طوكيو": "Tokyo", "لندن": "London", "نيويورك": "New York",
    "⭐ تداخل لندن-نيويورك": "⭐ London-New York Overlap",
    "✅ وقت جيد": "✅ Good Time",
    "⏳ وقت هادئ": "⏳ Quiet Time",
    # -------- Categories / trade types --------
    "فوركس": "Forex", "معادن": "Metals", "مؤشرات": "Indices", "كريبتو": "Crypto",
    "سكالبينج": "Scalping", "سويينج": "Swing",
    # -------- Image picking / camera --------
    "✅ تم": "✅ Done",
    "تم تحميل الصورة بنجاح": "Image uploaded successfully",
    "❌ خطأ": "❌ Error",
    "تعذر قراءة الملف - جرب طريقة أخرى": "Could not read the file - try another method",
    "⚠️ اختر الزوج أولاً": "⚠️ Select the pair first",
    "حدد الزوج ونوع التداول قبل رفع الصورة": "Select the pair and trading style before uploading an image",
    "اختر صورة الجارت": "Select chart image",
    "حدد الزوج ونوع التداول قبل التقاط الصورة": "Select the pair and trading style before capturing an image",
    "📷 التقاط صورة": "📷 Capture Image",
    "إلغاء": "Cancel",
    "التقاط": "Capture",
    "مكتبة الكاميرا غير مثبتة. استخدم رفع الصورة بدلاً.": "Camera library not installed. Use image upload instead.",
    "مسار الصورة": "Image path",
    "أدخل مسار صحيح": "Enter a valid path",
    "📁 اختر صورة": "📁 Select Image",
    "أدخل مسار الصورة:": "Enter the image path:",
    "تحميل": "Upload",
    # -------- Login / Register --------
    "البريد الإلكتروني": "Email",
    "كلمة المرور": "Password",
    "أدخل البريد وكلمة المرور": "Enter email and password",
    "استخدم Gmail/Hotmail/Outlook": "Use Gmail/Hotmail/Outlook",
    "✅ تم المسح": "✅ Cleared",
    "أنشئ حساباً جديداً الآن": "Create a new account now",
    "⚠️ مسح كامل البيانات؟": "⚠️ Erase all data?",
    "سيتم حذف جميع الحسابات والبيانات المحلية.\n": "All accounts and local data will be deleted.\n",
    "استخدم هذا فقط إذا نسيت بياناتك.": "Only use this if you forgot your details.",
    "مسح الكل": "Erase All",
    "الذكاء الاصطناعي للأسواق المالية": "AI for Financial Markets",
    "تسجيل الدخول": "Login",
    "ليس لديك حساب؟ سجل الآن": "Don't have an account? Register now",
    "⚠️ مشكلة في تسجيل الدخول؟ اضغط هنا": "⚠️ Trouble logging in? Tap here",
    "الاسم الكامل": "Full Name",
    "محمد أحمد": "John Smith",
    "جميع الحقول مطلوبة": "All fields are required",
    "Gmail/Hotmail/Outlook فقط": "Gmail/Hotmail/Outlook only",
    "كلمة المرور 6 أحرف على الأقل": "Password must be at least 6 characters",
    "إنشاء حساب": "Create Account",
    "إنشاء الحساب": "Create Account",
    "لديك حساب؟ تسجيل الدخول": "Already have an account? Login",
    # -------- Nav tabs --------
    "الرئيسية": "Home", "السجل": "History", "المتجر": "Store",
    "الأخبار": "News", "الحساب": "Account", "عن التطبيق": "About",
    # -------- Subscription / countdown --------
    "نشط": "Active", "منتهي": "Expired",
    "ينتهي الاشتراك": "Subscription ends in",
    "انتهى الاشتراك": "Subscription expired",
    "يوم": "Day", "ساعة": "Hour", "دقيقة": "Min",
    # -------- Home tab --------
    "الزوج المختار:": "Selected pair:",
    "اضغط لتغيير الصورة": "Tap to change image",
    "اختر الزوج أولاً\nثم ارفع صورة الجارت": "Select the pair first\nthen upload the chart image",
    "اضغط هنا لرفع صورة الجارت": "Tap here to upload the chart image",
    "رفع": "Upload",
    "❗ اختر الزوج أولاً": "❗ Select the pair first",
    "تجاوزت حصتك! قم بترقية باقتك.": "You've exceeded your quota! Upgrade your plan.",
    "اختر صورة الجارت أولاً": "Select the chart image first",
    "جارٍ تحليل الجارت بالذكاء الاصطناعي...": "Analyzing the chart with AI...",
    "⚠️ فشل الاتصال بـ AI - تحقق من الإنترنت": "⚠️ AI connection failed - check your internet",
    "انتظار": "Waiting",
    "تجاوزت حصتك!": "You've exceeded your quota!",
    "ℹ️ لا توجد فرصة مناسبة": "ℹ️ No suitable opportunity",
    "لم يتم خصم نقطة من حصتك": "No point was deducted from your quota",
    "تحليل بالذكاء الاصطناعي": "AI Analysis",
    "الفئة:": "Category:",
    "اختر الزوج:": "Select pair:",
    "نوع التداول:": "Trading style:",
    "📷 رفع صورة": "📷 Upload Image",
    "🤖 تحليل": "🤖 Analyze",
    # -------- Result card --------
    "اتصال AI فاشل": "AI connection failed",
    "لا توجد فرصة مناسبة الآن": "No suitable opportunity right now",
    "⚠️ تحليل وهمي - لا تعتمد عليه للتداول الحقيقي": "⚠️ Simulated analysis - do not rely on it for real trading",
    "السبب: فشل الاتصال بخادم الذكاء الاصطناعي.\n": "Reason: failed to connect to the AI server.\n",
    "• تأكد من الاتصال بالإنترنت\n": "• Check your internet connection\n",
    "• تأكد من صلاحية مفتاح API\n": "• Make sure the API key is valid\n",
    "• جرّب استخدام VPN": "• Try using a VPN",
    "تحليل ذكي": "Smart Analysis",
    "تحليل تجريبي": "Trial Analysis",
    "نقطة الدخول": "Entry Point",
    "وقف الخسارة": "Stop Loss",
    "الهدف": "Target",
    "صاعد 📈": "Bullish 📈", "هابط 📉": "Bearish 📉",
    "منطقة رئيسية": "Key Zone",
    "ملاحظة إضافية": "Additional Note",
    "موقع السعر": "Price Position",
    "نجاح": "Success",
    # -------- History tab --------
    "لا توجد توصيات سابقة": "No previous recommendations",
    "توصية سابقة": "previous recommendation(s)",
    # -------- Store tab --------
    "🔑 تنشيط بمفتاح": "🔑 Activate with Key",
    "✅ تم التفعيل!": "✅ Activated!",
    "مجاناً": "Free",
    "الباقة الحالية ✓": "Current Plan ✓",
    "اطلب عبر تليجرام": "Order via Telegram",
    "الباقات والتنشيط": "Plans & Activation",
    "تنشيط الآن": "Activate Now",
    "📱 تليجرام للدفع": "📱 Telegram for Payment",
    "شهر": "month", "تحليل/يوم": "analyses/day",
    "باقة": "Plan",
    # -------- News tab --------
    "اليوم": "Today", "غداً": "Tomorrow", "هذا الأسبوع": "This Week",
    "تحديث": "Refresh",
    "لا أخبار متاحة": "No news available",
    "الاثنين": "Monday", "الثلاثاء": "Tuesday", "الأربعاء": "Wednesday",
    "الخميس": "Thursday", "الجمعة": "Friday", "السبت": "Saturday", "الأحد": "Sunday",
    "الفعلي": "Actual", "التوقعات": "Forecast", "السابق": "Previous",
    "خبر عاجل! ابتعد عن السوق": "Urgent news! Stay away from the market",
    "الأخبار الاقتصادية": "Economic News",
    "ForexFactory • بيانات حية": "ForexFactory • Live Data",
    "الأخبار العالية الأثر قد تسبب تقلبات. كن حذراً.": "High-impact news may cause volatility. Be careful.",
    "هادئة": "quiet",
    # -------- Settings tab --------
    "🔄 تم": "🔄 Done",
    "بيانات محدثة": "Data updated",
    "مستخدم": "User",
    "حالة الاشتراك": "Subscription Status",
    "الباقة:": "Plan:",
    "المتبقي:": "Remaining:",
    "التحاليل:": "Analyses:",
    "المظهر": "Appearance",
    "الوضع الليلي": "Dark Mode",
    "الوضع النهاري": "Light Mode",
    "تسجيل الخروج": "Logout",
    "سياسة الخصوصية": "Privacy Policy",
    "الجهاز:": "Device:",
    "متبقي": "remaining",
    # -------- About tab --------
    "التطوير": "Development",
    "تمت البرمجة والتطوير بواسطة": "Programmed and developed by",
    "© 2025-2026 جميع الحقوق محفوظة": "© 2025-2026 All Rights Reserved",
}

def L(text):
    """ترجمة نص ثابت معروف حسب اللغة الحالية. النصوص غير الموجودة بالقاموس تُعاد كما هي."""
    if _LANG_STATE["v"] == "EN":
        return AR_EN.get(text, text)
    return text

# ============================================================
#  STORAGE
# ============================================================
def get_storage_dir() -> str:
    env = os.environ.get("FLET_APP_STORAGE_DATA","").strip()
    if env:
        os.makedirs(env, exist_ok=True); return env
    s = platform.system()
    if s == "Windows":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "YourDream")
    elif s == "Darwin":
        base = os.path.expanduser("~/Library/Application Support/YourDream")
    else:
        base = os.path.expanduser("~/.yourdream")
    os.makedirs(base, exist_ok=True); return base

# ============================================================
#  CONFIG
# ============================================================
class Cfg:
    APP = "Your Dream"
    VER = "8.3.5"
    DB  = os.path.join(get_storage_dir(), "yd_db.sqlite")

    _GK   = "QUl6YVN5REZJaEczd0twenRiS3kyc1haMnQ4Q3hQSThXZHEtMzJz"
    # Best models for chart analysis (ordered by accuracy)
    # Updated with Gemini 3.x models from ai.google.dev
    MODELS = [
        "gemini-3.6-flash",         # ✅ Latest - best balance speed/accuracy
    ]
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    # Build URLs for each model
    @classmethod
    def get_model_urls(cls):
        return [f"{cls.BASE_URL}/{model}:generateContent" for model in cls.MODELS]

    TG_USER = "Ah_alaa95"
    TG_URL  = "https://t.me/Ah_alaa95"

    TIERS = {
        'free_trial':      {'daily_signals':1,  'camera_quota':2,   'price':0,  'days':3,     'label':'تجريبي'},
        'basic':           {'daily_signals':3,  'camera_quota':3,   'price':10, 'days':30,    'label':'أساسية'},
        'advanced':        {'daily_signals':6,  'camera_quota':6,   'price':30, 'days':30,    'label':'متقدمة'},
        'vip':             {'daily_signals':12, 'camera_quota':12,  'price':75, 'days':30,    'label':'VIP'},
        'admin_unlimited': {'daily_signals':9999,'camera_quota':9999,'price':0, 'days':36500, 'label':'Admin'},
        'user30_special':  {'daily_signals':2,  'camera_quota':3,   'price':0,  'days':30,    'label':'مخصص'},
    }

    ADMIN_EMAIL = "ahmedalaa95"
    U30_EMAIL   = "user30"
    EMAIL_RE    = r'^[a-zA-Z0-9._%+-]+@(gmail\.com|hotmail\.com|outlook\.com)$'

    KEYS = {
        "yd10_650g2r10":"basic",  "yd10_a1b2c3d4":"basic",
        "yd30_x9k2m1":"advanced", "yd30_q1w2e3r4":"advanced",
        "yd75_v9p4z8":"vip",      "yd75_d3f4g5h6":"vip",
    }

    @classmethod
    def colors(cls, dark=True):
        if dark:
            return dict(
                bg="#08080e",card="#111118",accent="#d4a017",accent2="#f5c842",
                grad1="#1a2235",grad2="#0d1520",txt="#ffffff",txt2="#8a8d9f",txt3="#5a5d6f",
                chip_on="#d4a017",chip_on_txt="#000000",chip_off="#1a1a28",chip_off_txt="#666680",
                btn="#f0f0f0",btn_txt="#08080e",green="#00e676",red="#ff1744",
                divider="#1e1e2e",border="#2a2a3e",orange="#ff6d00",blue="#448aff")
        return dict(
            bg="#f2f4f8",card="#ffffff",accent="#b8860b",accent2="#d4a020",
            grad1="#e0e8f4",grad2="#ccd8ea",txt="#111120",txt2="#555570",txt3="#888898",
            chip_on="#b8860b",chip_on_txt="#ffffff",chip_off="#dde0ea",chip_off_txt="#555570",
            btn="#111120",btn_txt="#ffffff",green="#00897b",red="#c62828",
            divider="#d0d4e0",border="#c0c4d0",orange="#e65100",blue="#1565c0")

# ============================================================
#  SECURITY
# ============================================================
class Sec:
    _SEED = "YD_FIXED_SEED_DO_NOT_CHANGE_v1"

    def dev_id(self) -> str:
        dev_file = os.path.join(get_storage_dir(), "yd_device.id")
        try:
            if os.path.exists(dev_file):
                cached = open(dev_file).read().strip()
                if len(cached) >= 16: return cached
        except: pass
        new_id = hashlib.sha256(
            f"{uuid.getnode()}_{self._SEED}_{os.name}".encode()
        ).hexdigest()[:32]
        try: open(dev_file,"w").write(new_id)
        except: pass
        return new_id

    def hash(self, password: str) -> str:
        return hashlib.sha256(f"{password}{self._SEED}".encode()).hexdigest()

# ============================================================
#  FIREBASE (Auth + Firestore عبر REST فقط - urllib، بدون SDK ثقيل)
# ============================================================
class FbCfg:
    API_KEY    = "AIzaSyCcE7dUBQ9_aWsJdNVKG_gXCYoEgVZBWzY"
    PROJECT_ID = "yourdreamapp-da52d"
    AUTH_BASE  = "https://identitytoolkit.googleapis.com/v1/accounts"
    FS_BASE    = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

class Fb:
    # ✅ خريطة أسماء الباقات (غير حساسة لحالة الأحرف - المفتاح هنا بالأحرف الصغيرة
    # دائماً لأننا نطبّق .lower() على القيمة القادمة من Firestore قبل البحث)
    # بحيث تُستخدم مهما كُتبت بفايربيس: Gold أو gold أو GOLD كلها نفس النتيجة
    TIER_ALIAS = {
        "basic": "basic",
        "silver": "advanced",
        "advanced": "advanced",
        "gold": "vip",
        "vip": "vip",
    }
    """
    ✅ عميل Firebase خفيف يعتمد فقط على urllib (بدون pip install لأي SDK ثقيل
    قد لا يعمل عند تجميع APK). يغطي:
      - Firebase Auth: إنشاء حساب / تسجيل دخول (Email+Password)
      - Firestore: قراءة/كتابة مستندات (للمفاتيح Keys وربط الجهاز Devices)

    ⚠️ ملاحظة أمان مهمة (متوافقة مع اختيارك "Client SDK مباشر - أبسط لكن أقل
    أماناً"): هذا العميل لا يستخدم مفتاح Admin أبداً، ويعتمد بالكامل على
    Firestore Security Rules لمنع التلاعب. لازم تُفعّل هذه القواعد بالضبط
    بلوحة تحكم Firebase (Firestore Database → Rules) وإلا رح يرفض كل الطلبات:

        rules_version = '2';
        service cloud.firestore {
          match /databases/{database}/documents {
            match /Keys/{keyId} {
              allow read: if true;
              allow update: if request.resource.data.diff(resource.data)
                              .affectedKeys().hasOnly(['used','used_by','used_at'])
                            && resource.data.used == false;
              allow create, delete: if false;
            }
            match /Devices/{deviceId} {
              allow read: if true;
              allow create: if request.resource.data.keys().hasAll(['created_at','failed_attempts']);
              allow update: if true;
              allow delete: if false;
            }
          }
        }

    هاي القواعد تمنع: تعديل تِير المفتاح، إعادة تفعيل مفتاح مُستخدم، أو حذف
    أي مستند. ما تمنعه (بحكم اختيارك تجنّب Cloud Functions): مستخدم شاطر جداً
    قادر يقرأ كود APK ويرسل طلبات يدوية لتصفير عدّاد محاولاته الخاص بجهازه هو
    فقط - هذا سقف الأمان الممكن بدون سيرفر وسيط.
    """

    @staticmethod
    def _req(url, method="GET", body=None, timeout=15):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                      headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                raw = resp.read().decode()
                return True, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            try: err = json.loads(e.read().decode())
            except Exception: err = {"error": {"message": str(e)}}
            return False, err
        except Exception as e:
            return False, {"error": {"message": str(e)}}

    # -------- Auth --------
    @staticmethod
    def sign_up(email: str, password: str):
        ok, r = Fb._req(f"{FbCfg.AUTH_BASE}:signUp?key={FbCfg.API_KEY}", "POST",
                         {"email": email, "password": password, "returnSecureToken": True})
        if ok: return True, r.get("localId"), r.get("idToken")
        return False, r.get("error", {}).get("message", "UNKNOWN_ERROR"), None

    @staticmethod
    def sign_in(email: str, password: str):
        ok, r = Fb._req(f"{FbCfg.AUTH_BASE}:signInWithPassword?key={FbCfg.API_KEY}", "POST",
                         {"email": email, "password": password, "returnSecureToken": True})
        if ok: return True, r.get("localId"), r.get("idToken")
        return False, r.get("error", {}).get("message", "UNKNOWN_ERROR"), None

    # -------- Firestore (تنسيق REST الخاص بـ Firestore للقيم: {"stringValue":...} إلخ) --------
    @staticmethod
    def _to_fs(value):
        if isinstance(value, bool): return {"booleanValue": value}
        if isinstance(value, int): return {"integerValue": str(value)}
        if isinstance(value, float): return {"doubleValue": value}
        if isinstance(value, datetime.datetime):
            # ✅ Firestore Timestamp حقيقي (RFC3339 UTC) - مطلوب لتفعيل سياسة TTL
            # لاحقاً من لوحة تحكم Firebase (الحقل لازم يكون Timestamp وليس نص/رقم)
            v = value if value.tzinfo else value.replace(tzinfo=datetime.timezone.utc)
            v = v.astimezone(datetime.timezone.utc)
            return {"timestampValue": v.strftime("%Y-%m-%dT%H:%M:%S.") + f"{v.microsecond//1000:03d}Z"}
        if value is None: return {"nullValue": None}
        return {"stringValue": str(value)}

    @staticmethod
    def _from_fs(fields: dict) -> dict:
        out = {}
        for k, v in (fields or {}).items():
            if "stringValue" in v: out[k] = v["stringValue"]
            elif "integerValue" in v: out[k] = int(v["integerValue"])
            elif "doubleValue" in v: out[k] = v["doubleValue"]
            elif "booleanValue" in v: out[k] = v["booleanValue"]
            else: out[k] = None
        return out

    @staticmethod
    def get_doc(collection: str, doc_id: str):
        ok, r = Fb._req(f"{FbCfg.FS_BASE}/{collection}/{doc_id}?key={FbCfg.API_KEY}")
        if ok and "fields" in r:
            return True, Fb._from_fs(r["fields"])
        return False, None

    @staticmethod
    def set_doc(collection: str, doc_id: str, data: dict, update_mask=None):
        fields = {k: Fb._to_fs(v) for k, v in data.items()}
        mask_qs = ""
        if update_mask:
            mask_qs = "&" + "&".join(f"updateMask.fieldPaths={m}" for m in update_mask)
        url = f"{FbCfg.FS_BASE}/{collection}/{doc_id}?key={FbCfg.API_KEY}{mask_qs}"
        return Fb._req(url, "PATCH", {"fields": fields})

    # -------- منطق العمل (Business logic) --------
    @staticmethod
    def check_device_lock(device_id: str):
        """يرجع (locked: bool, seconds_remaining: int)"""
        ok, dev = Fb.get_doc("Devices", device_id)
        if not ok or not dev: return False, 0
        blocked_until = dev.get("blocked_until", 0)
        if blocked_until:
            remaining = blocked_until - time.time()
            if remaining > 0: return True, int(remaining)
        return False, 0

    @staticmethod
    def register_key_failure(device_id: str):
        """يزيد عدّاد المحاولات الفاشلة، وعند الوصول لـ3 يفعّل حظر 7 أيام (168 ساعة)"""
        ok, dev = Fb.get_doc("Devices", device_id)
        attempts = (dev.get("failed_attempts", 0) if ok and dev else 0) + 1
        data = {"failed_attempts": attempts, "created_at": int(time.time())}
        if attempts >= 3:
            data["blocked_until"] = int(time.time() + 7*24*3600)  # 168 ساعة بالتمام
        Fb.set_doc("Devices", device_id, data)
        return attempts

    @staticmethod
    def check_key(key: str):
        """يتحقق من صلاحية المفتاح بمجموعة Keys. غير حساس لحالة الأحرف بالكامل:
        Gold/gold/GOLD ⇐⇒ نفس النتيجة، وأيضاً غير حساس لاسم الحقل نفسه
        (tier/Tier/TIER كلها تُقرأ بشكل صحيح). يرجع (ok, tier_داخلي أو رسالة خطأ)"""
        ok, doc = Fb.get_doc("Keys", key)
        if not ok or not doc: return False, "المفتاح غير صالح"
        # ✅ فحص حقل "used" بشكل غير حساس لاسم الحقل أيضاً (used/Used/USED)
        used_val = None
        for k, v in doc.items():
            if k.strip().lower() == "used":
                used_val = v; break
        if used_val: return False, "المفتاح مستخدم مسبقاً"
        # ✅ البحث عن حقل التِير بغض النظر عن شكل اسمه بالضبط (tier/Tier/TIER/Type...)
        raw_tier = None
        for k, v in doc.items():
            if k.strip().lower() in ("tier", "type", "plan", "package"):
                raw_tier = v; break
        if raw_tier is None:
            print(f"[Fb] ⚠️ لم يُعثر على حقل التِير بمستند المفتاح '{key}' - تأكد من اسم الحقل بفايربيس. الحقول الموجودة: {list(doc.keys())}")
            raw_tier = "basic"
        raw_tier = str(raw_tier).strip().lower()
        # ✅ Basic → 3 تحاليل/يوم | Silver → 6 تحاليل/يوم | Gold → 12 تحليلاً/يوم
        # (تُطابق تلقائياً حصص الفئات الداخلية الموجودة أصلاً: basic/advanced/vip)
        tier = Fb.TIER_ALIAS.get(raw_tier, raw_tier)
        if tier not in Cfg.TIERS:
            print(f"[Fb] ⚠️ تِير غير معروف بالمفتاح: '{raw_tier}' - سيُستخدم 'basic' كقيمة احتياطية")
            tier = "basic"
        return True, tier

    @staticmethod
    def mark_key_used(key: str, uid: str, email: str = ""):
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        Fb.set_doc("Keys", key, {
            "used": True, "used_by": uid, "used_at": int(time.time()),
            # ✅ حفظ إيميل المستخدم بمستند المفتاح نفسه لتسهيل البحث اليدوي بلوحة التحكم
            "email": email,
            # ✅ حقلا Timestamp حقيقيان لتفعيل التنظيف التلقائي عبر Firestore TTL:
            # expire_at = بعد 30 يوم (نهاية صلاحية الباقة) | delete_at = بعد 37 يوم
            # (٧ أيام إضافية بعد الانتهاء) وهو الحقل الذي تُفعَّل عليه سياسة TTL
            "expire_at": now_utc + datetime.timedelta(days=30),
            "delete_at": now_utc + datetime.timedelta(days=37),
        }, update_mask=["used", "used_by", "used_at", "email", "expire_at", "delete_at"])

    @staticmethod
    def bind_device(device_id: str, uid: str):
        """يربط الجهاز بحساب، ويصفّر عدّاد المحاولات الفاشلة عند التفعيل الناجح"""
        Fb.set_doc("Devices", device_id, {
            "uid": uid, "failed_attempts": 0, "created_at": int(time.time())
        })

    @staticmethod
    def device_registered_to_other(device_id: str, uid: str) -> bool:
        """✅ يمنع إنشاء حساب جديد من جهاز مرتبط مسبقاً بحساب آخر (حتى بعد حذف
        التطبيق وإعادة تثبيته، طالما device_id نفسه ما زال يتولّد بنفس القيمة)"""
        ok, dev = Fb.get_doc("Devices", device_id)
        if ok and dev and dev.get("uid") and dev.get("uid") != uid:
            return True
        return False

    # -------- Users (نسخة سحابية من حالة الاشتراك تنجو من حذف التطبيق) --------
    @staticmethod
    def sync_user_state(uid: str, email: str, full_name: str, tier: str,
                         expiry_iso: str, camera_used: int, device_id: str):
        """✅ يحفظ حالة الاشتراك (الباقة/الانتهاء/الحصة) بمستند Users/{uid} على
        Firestore. هذا هو ما يسمح باستعادة الحساب بشكل صحيح بعد حذف التطبيق
        وإعادة تثبيته - لأن قاعدة البيانات المحلية (SQLite) تُمسح بالكامل عند
        الحذف، لكن Firestore يبقى كما هو."""
        Fb.set_doc("Users", uid, {
            "email": email, "full_name": full_name or "",
            "tier": tier, "expiry": expiry_iso,
            "camera_used": camera_used, "device_id": device_id,
            "updated_at": int(time.time()),
        })

    @staticmethod
    def get_user_state(uid: str):
        ok, doc = Fb.get_doc("Users", uid)
        if ok and doc: return doc
        return None


# ============================================================
#  DATABASE
# ============================================================
class DB:
    def __init__(self):
        self._lock = threading.RLock()
        self._init()

    def _cx(self):
        cx = sqlite3.connect(Cfg.DB, check_same_thread=False)
        cx.row_factory = sqlite3.Row
        return cx

    def _init(self):
        with self._lock:
            cx = self._cx(); c = cx.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                device_uuid TEXT,
                subscription_tier TEXT DEFAULT 'free_trial',
                subscription_expiry TEXT,
                daily_requests_used INTEGER DEFAULT 0,
                last_request_reset TEXT,
                camera_used INTEGER DEFAULT 0,
                last_camera_reset TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1)""")
            c.execute("""CREATE TABLE IF NOT EXISTS used_keys(
                id INTEGER PRIMARY KEY,
                key_value TEXT UNIQUE NOT NULL,
                user_id INTEGER, tier TEXT,
                activated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
            c.execute("""CREATE TABLE IF NOT EXISTS camera_requests(
                id INTEGER PRIMARY KEY,
                user_id INTEGER, pair TEXT, trade_type TEXT,
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
            c.execute("""CREATE TABLE IF NOT EXISTS session(
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                device_uuid TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
            for sql in [
                "ALTER TABLE users ADD COLUMN camera_used INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN last_camera_reset TEXT",
                "ALTER TABLE users ADD COLUMN firebase_uid TEXT",   # ✅ ربط الحساب المحلي بحساب Firebase Auth
            ]:
                try: c.execute(sql)
                except: pass
            cx.commit(); cx.close()

    def _row(self, r) -> Dict:
        if not r: return {}
        try:
            def _int(v, default=0):
                try: return int(v)
                except (TypeError, ValueError): return default
            return {
                "id":r["id"],"email":r["email"],"password_hash":r["password_hash"],
                "full_name":r["full_name"],"device_uuid":r["device_uuid"],
                "tier":r["subscription_tier"],"expiry":r["subscription_expiry"],
                "daily_used":_int(r["daily_requests_used"]),"last_reset":r["last_request_reset"],
                "camera_used":_int(r["camera_used"]),"last_camera_reset":r["last_camera_reset"],
                "created_at":r["created_at"],
                "firebase_uid": (r["firebase_uid"] if "firebase_uid" in r.keys() else None),
            }
        except Exception as ex:
            print(f"[_row] {ex}"); return {}

    def reset_all(self):
        with self._lock:
            try:
                cx = self._cx(); c = cx.cursor()
                c.execute("DELETE FROM camera_requests")
                c.execute("DELETE FROM used_keys")
                c.execute("DELETE FROM users")
                c.execute("DELETE FROM session")
                cx.commit(); cx.close()
            except: pass
        dev_file = os.path.join(get_storage_dir(), "yd_device.id")
        try: os.remove(dev_file)
        except: pass

    def device_has_account(self, dev: str) -> bool:
        with self._lock:
            cx = self._cx()
            r = cx.cursor().execute(
                "SELECT id FROM users WHERE device_uuid=? AND email NOT IN (?,?)",
                (dev, Cfg.ADMIN_EMAIL, Cfg.U30_EMAIL)).fetchone()
            cx.close(); return r is not None

    def create(self, email, pwd_hash, name, dev, password_plain=None) -> Tuple[bool, str]:
        email = email.lower().strip()
        is_special = email in (Cfg.ADMIN_EMAIL, Cfg.U30_EMAIL)

        # ✅ 1) فحص Firebase أولاً: هل هذا الجهاز مرتبط مسبقاً بحساب آخر؟
        # (يعتمد على dev_id الثابت قدر الإمكان، حتى بعد حذف التطبيق وإعادة تثبيته)
        if not is_special:
            if Fb.device_registered_to_other(dev, uid="__new__"):
                return False, "هذا الجهاز مرتبط بحساب آخر، سجّل الدخول"

        # ✅ 2) فحص التكرار محلياً أولاً (قبل لمس Firebase) لتفادي إنشاء حساب
        # Firebase "معلّق" بدون صف محلي مطابق إذا فشل أي فحص لاحق - هاي كانت
        # السبب الحقيقي لمشكلة "مسجل مسبقاً" عند التسجيل و"غير مسجل" عند الدخول
        # بنفس الوقت لنفس الإيميل.
        cx = self._cx(); c = cx.cursor()
        if c.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            cx.close(); return False, "البريد مسجل مسبقاً"
        if not is_special:
            if c.execute("SELECT id FROM users WHERE device_uuid=?", (dev,)).fetchone():
                cx.close(); return False, "هذا الجهاز مرتبط بحساب آخر، سجّل الدخول"
        cx.close()

        # ✅ 3) إنشاء الحساب فعلياً على Firebase Auth (Email/Password) إن وُجدت
        # كلمة مرور صريحة.
        fb_uid = None
        if password_plain:
            ok_fb, res_fb, _tok = Fb.sign_up(email, password_plain)
            if ok_fb:
                fb_uid = res_fb
            else:
                if res_fb == "EMAIL_EXISTS":
                    # ✅ إصلاح ذاتي (Self-heal): الإيميل موجود على Firebase لكن
                    # قد لا يوجد له صف محلي مطابق (حساب "معلّق" من محاولة سابقة
                    # فشلت بالمنتصف). نتحقق: إذا كلمة المرور صحيحة فعلاً لنفس
                    # الحساب، نُكمل إنشاء الصف المحلي بدل ما نرفض التسجيل نهائياً.
                    ok_signin, uid_or_err, _tok2 = Fb.sign_in(email, password_plain)
                    if ok_signin:
                        fb_uid = uid_or_err
                        print(f"[Firebase] ✅ تعافي تلقائي: حساب معلّق تم ربطه بصف محلي جديد ({email})")
                    else:
                        return False, "البريد مسجل مسبقاً"
                else:
                    print(f"[Firebase] sign_up warning: {res_fb} - سيُكمل التسجيل محلياً فقط")

        with self._lock:
            try:
                cx = self._cx(); c = cx.cursor()
                if c.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
                    cx.close(); return False, "البريد مسجل مسبقاً"
                if not is_special:
                    if c.execute("SELECT id FROM users WHERE device_uuid=?", (dev,)).fetchone():
                        cx.close(); return False, "هذا الجهاز مرتبط بحساب آخر، سجّل الدخول"
                if email == Cfg.ADMIN_EMAIL:
                    tier = "admin_unlimited"
                    expiry = datetime.datetime(2099,12,31).isoformat()
                elif email == Cfg.U30_EMAIL:
                    tier = "user30_special"
                    expiry = (datetime.datetime.now()+datetime.timedelta(days=30)).isoformat()
                else:
                    tier = "free_trial"
                    expiry = (datetime.datetime.now()+datetime.timedelta(days=3)).isoformat()
                now = datetime.datetime.now().isoformat()
                c.execute(
                    "INSERT INTO users(email,password_hash,full_name,device_uuid,"
                    "subscription_tier,subscription_expiry,daily_requests_used,"
                    "last_request_reset,camera_used,last_camera_reset,firebase_uid) "
                    "VALUES(?,?,?,?,?,?,0,?,0,?,?)",
                    (email, pwd_hash, name, dev, tier, expiry, now, now, fb_uid))
                cx.commit(); cx.close()
                # ✅ 3) ربط الجهاز بحساب Firebase (أو بمعرّف محلي إذا فشل Firebase)
                # هذا يمنع إنشاء حساب تجريبي ثانٍ من نفس الجهاز حتى بعد حذف التطبيق
                Fb.bind_device(dev, fb_uid or f"local_{email}")
                # ✅ حفظ حالة الاشتراك الأولية بـ Firestore (تنجو من حذف التطبيق)
                if fb_uid:
                    Fb.sync_user_state(fb_uid, email, name, tier, expiry, 0, dev)
                return True, "تم إنشاء الحساب بنجاح ✅"
            except Exception as e:
                return False, str(e)

    def auth(self, email, pwd_hash, dev, password_plain=None) -> Tuple[bool, Optional[Dict], str]:
        email = email.lower().strip()
        with self._lock:
            cx = self._cx(); c = cx.cursor()
            r_email = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if not r_email:
                cx.close()
                # ✅ تعافي تلقائي بعد حذف التطبيق وإعادة تثبيته: القاعدة المحلية
                # تُمسح بالكامل عند حذف التطبيق، لكن الحساب يبقى موجوداً فعلياً
                # على Firebase Auth + حالة اشتراكه محفوظة بـ Firestore (Users).
                # هون نتحقق من Firebase مباشرة ونعيد بناء الصف المحلي من هناك
                # بدل ما نرفض الدخول بالغلط رغم إن الحساب سليم فعلياً.
                if password_plain:
                    ok_signin, uid, _tok = Fb.sign_in(email, password_plain)
                    if ok_signin:
                        state = Fb.get_user_state(uid)
                        cx2 = self._cx(); c2 = cx2.cursor()
                        now_iso = datetime.datetime.now().isoformat()
                        if state:
                            tier = state.get("tier", "free_trial")
                            expiry = state.get("expiry", now_iso)
                            cam_used = int(state.get("camera_used", 0) or 0)
                            full_name = state.get("full_name", "")
                        else:
                            # لا توجد نسخة سحابية (حساب قديم من قبل هذا التحديث) -
                            # نعطيه تجربة مجانية جديدة كأفضل حل احتياطي متاح
                            tier, expiry, cam_used, full_name = "free_trial", \
                                (datetime.datetime.now()+datetime.timedelta(days=3)).isoformat(), 0, ""
                        c2.execute(
                            "INSERT INTO users(email,password_hash,full_name,device_uuid,"
                            "subscription_tier,subscription_expiry,daily_requests_used,"
                            "last_request_reset,camera_used,last_camera_reset,firebase_uid) "
                            "VALUES(?,?,?,?,?,?,0,?,?,?,?)",
                            (email, pwd_hash, full_name, dev, tier, expiry, now_iso, cam_used, now_iso, uid))
                        cx2.commit()
                        new_id = c2.lastrowid
                        c2.execute("DELETE FROM session")
                        c2.execute("INSERT INTO session(user_id, device_uuid) VALUES(?,?)", (new_id, dev))
                        cx2.commit(); cx2.close()
                        Fb.bind_device(dev, uid)
                        print(f"[Auth] ✅ تعافي تلقائي بعد إعادة التثبيت لـ {email} - الباقة المستعادة: {tier}")
                        u = self.get(new_id)
                        return True, u, "تم تسجيل الدخول ✅"
                return False, None, "البريد الإلكتروني غير مسجل"
            r = c.execute(
                "SELECT * FROM users WHERE email=? AND password_hash=?",
                (email, pwd_hash)).fetchone()
            if not r:
                cx.close(); return False, None, "كلمة المرور غير صحيحة"
            u = self._row(r)
            if u["email"] == Cfg.ADMIN_EMAIL:
                cx.close(); return True, u, "مرحباً Admin"
            # ✅ مطابقة إلزامية مع Firestore (المصدر الأساسي) بكل تسجيل دخول عادي
            # أيضاً، مو فقط بمسار التعافي بعد إعادة التثبيت. هذا يمنع نهائياً ظهور
            # باقة قديمة/تجريبية محلياً رغم إن فايربيس عنده الاشتراك الصحيح -
            # مهما كان سبب التضارب، فايربيس دائماً هو المرجع الصحيح.
            fb_uid = u.get("firebase_uid")
            if fb_uid:
                state = Fb.get_user_state(fb_uid)
                if state:
                    cloud_tier = state.get("tier", u["tier"])
                    cloud_expiry = state.get("expiry", u["expiry"])
                    cloud_cam = int(state.get("camera_used", u["camera_used"]) or 0)
                    if (cloud_tier != u["tier"] or cloud_expiry != u["expiry"]
                            or cloud_cam != u["camera_used"]):
                        c.execute(
                            "UPDATE users SET subscription_tier=?,subscription_expiry=?,"
                            "camera_used=? WHERE id=?",
                            (cloud_tier, cloud_expiry, cloud_cam, u["id"]))
                        cx.commit()
                        u["tier"] = cloud_tier; u["expiry"] = cloud_expiry; u["camera_used"] = cloud_cam
                        print(f"[Auth] 🔄 مزامنة باقة {email} مع فايربيس: {cloud_tier}")
            if not u.get("device_uuid"):
                c.execute("UPDATE users SET device_uuid=? WHERE id=?", (dev, u["id"]))
                cx.commit(); u["device_uuid"] = dev
            elif u["device_uuid"] != dev:
                cx.close(); return False, None, "الحساب مرتبط بجهاز آخر"
            c.execute("DELETE FROM session")
            c.execute("INSERT INTO session(user_id, device_uuid) VALUES(?,?)", (u["id"], dev))
            cx.commit()
            cx.close()
            # ✅ تحديث Firebase Auth أيضاً (best-effort، لا يوقف تسجيل الدخول المحلي لو فشل)
            if password_plain and u.get("firebase_uid"):
                try: Fb.sign_in(email, password_plain)
                except Exception: pass
            return True, u, "تم تسجيل الدخول ✅"

    def get_session(self, dev) -> Optional[Dict]:
        with self._lock:
            cx = self._cx(); c = cx.cursor()
            r = c.execute(
                "SELECT s.user_id, u.* FROM session s JOIN users u ON s.user_id = u.id "
                "WHERE s.device_uuid=?", (dev,)).fetchone()
            cx.close()
            if r:
                return self._row(r)
            return None

    def clear_session(self):
        with self._lock:
            cx = self._cx()
            cx.cursor().execute("DELETE FROM session")
            cx.commit(); cx.close()

    def get(self, uid) -> Optional[Dict]:
        with self._lock:
            cx = self._cx()
            r  = cx.cursor().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            cx.close(); return self._row(r)

    def reset_daily(self, uid):
        with self._lock:
            cx = self._cx(); c = cx.cursor()
            r = c.execute("SELECT last_request_reset FROM users WHERE id=?", (uid,)).fetchone()
            if r and r["last_request_reset"]:
                try:
                    if (datetime.datetime.now()-datetime.datetime.fromisoformat(
                            r["last_request_reset"])).total_seconds() >= 86400:
                        c.execute("UPDATE users SET daily_requests_used=0,last_request_reset=? WHERE id=?",
                                  (datetime.datetime.now().isoformat(), uid))
                        cx.commit()
                except: pass
            cx.close()

    def reset_camera(self, uid):
        with self._lock:
            cx = self._cx(); c = cx.cursor()
            r = c.execute("SELECT last_camera_reset FROM users WHERE id=?", (uid,)).fetchone()
            if r and r["last_camera_reset"]:
                try:
                    if (datetime.datetime.now()-datetime.datetime.fromisoformat(
                            r["last_camera_reset"])).total_seconds() >= 86400:
                        c.execute("UPDATE users SET camera_used=0,last_camera_reset=? WHERE id=?",
                                  (datetime.datetime.now().isoformat(), uid))
                        cx.commit()
                except: pass
            cx.close()

    def inc_camera(self, uid) -> bool:
        with self._lock:
            cx = self._cx(); c = cx.cursor()
            r = c.execute("SELECT camera_used,subscription_tier,subscription_expiry,"
                          "firebase_uid,email,full_name,device_uuid FROM users WHERE id=?", (uid,)).fetchone()
            if not r: cx.close(); return False
            # ✅ منع أي تحليل جديد فور انتهاء صلاحية الاشتراك، حتى لو الحصة
            # اليومية لم تُستهلك بالكامل بعد (كانت هذي الفحص مفقودة سابقاً)
            try:
                if r["subscription_expiry"]:
                    exp = datetime.datetime.fromisoformat(r["subscription_expiry"])
                    if exp <= datetime.datetime.now():
                        cx.close(); return False
            except Exception:
                pass
            used = r["camera_used"] or 0
            lim  = Cfg.TIERS.get(r["subscription_tier"],{}).get("camera_quota",0)
            if used >= lim: cx.close(); return False
            new_used = used + 1
            c.execute("UPDATE users SET camera_used=? WHERE id=?", (new_used, uid))
            cx.commit()
            fb_uid = r["firebase_uid"] if "firebase_uid" in r.keys() else None
            tier = r["subscription_tier"]; expiry = r["subscription_expiry"]
            email = r["email"]; full_name = r["full_name"]; dev = r["device_uuid"]
            cx.close()
            # ✅ مزامنة العداد الحقيقي مع Firestore بعد كل تحليل مباشرة (وليس فقط
            # عند التسجيل/التفعيل) - هذا يمنع استغلال الحصة عبر حذف التطبيق
            # وإعادة تثبيته، لأن العداد المُستعاد بعد إعادة التثبيت سيعكس آخر
            # استخدام فعلي بدل ما يرجع لآخر نقطة قديمة (كانت هذي فجوة حقيقية)
            if fb_uid:
                def _sync():
                    try: Fb.sync_user_state(fb_uid, email or "", full_name, tier, expiry, new_used, dev or "")
                    except Exception as ex: print(f"[Fb] sync after inc_camera failed: {ex}")
                threading.Thread(target=_sync, daemon=True).start()
            return True

    def activate(self, uid, key, dev=None, email=None) -> Tuple[bool, str, Optional[str]]:
        key = key.strip()

        # ✅ الحماية ضد التخمين (Anti-Brute-Force) عبر Firebase - مرتبطة بالجهاز
        # وليس محلياً بالتطبيق، فلا يمكن تجاوزها بحذف بيانات التطبيق فقط.
        if dev:
            locked, remaining = Fb.check_device_lock(dev)
            if locked:
                days = remaining // 86400; hours = (remaining % 86400) // 3600
                return False, PICK(f"⛔ محاولات كثيرة خاطئة. حاول بعد {days} يوم و {hours} ساعة",
                                    f"⛔ Too many failed attempts. Try again in {days}d {hours}h"), None

        # ✅ التحقق من المفتاح عبر Firestore أولاً (المصدر الأساسي)، وإن تعذّر
        # الوصول لـ Firebase نرجع للقائمة المحلية Cfg.KEYS كخطة احتياطية فقط.
        fb_ok, fb_result = Fb.check_key(key)
        if fb_ok:
            tier = fb_result
        elif key in Cfg.KEYS:
            tier = Cfg.KEYS[key]
        else:
            if dev: Fb.register_key_failure(dev)
            msg = fb_result if fb_result else "المفتاح غير صالح"
            return False, msg, None

        with self._lock:
            cx = self._cx(); c = cx.cursor()
            if c.execute("SELECT id FROM used_keys WHERE key_value=?", (key,)).fetchone():
                cx.close()
                if dev: Fb.register_key_failure(dev)
                return False, "المفتاح مستخدم مسبقاً", None
            expiry = (datetime.datetime.now()+datetime.timedelta(days=30)).isoformat()
            c.execute("UPDATE users SET subscription_tier=?,subscription_expiry=? WHERE id=?",
                      (tier, expiry, uid))
            c.execute("INSERT INTO used_keys(key_value,user_id,tier)VALUES(?,?,?)", (key,uid,tier))
            cx.commit()
            # ✅ جلب firebase_uid والحصة الحالية لمزامنة الحالة الجديدة مع Firestore
            row = c.execute("SELECT firebase_uid,full_name,camera_used FROM users WHERE id=?", (uid,)).fetchone()
            cx.close()
            # ✅ تحديث حالة المفتاح على Firebase لـ"مُستخدم" فوراً لمنع أي شخص آخر
            # من استخدامه، وتصفير عدّاد المحاولات الفاشلة لهذا الجهاز
            if fb_ok:
                Fb.mark_key_used(key, str(uid), email=email or "")
            if dev:
                Fb.set_doc("Devices", dev, {"failed_attempts": 0, "created_at": int(time.time())})
            # ✅ مزامنة الباقة الجديدة مع Firestore (Users/{uid}) فوراً حتى تنجو
            # من حذف التطبيق - هذا يضمن استعادة الباقة الصحيحة بعد إعادة التثبيت
            if row and row["firebase_uid"]:
                Fb.sync_user_state(row["firebase_uid"], email or "", row["full_name"],
                                    tier, expiry, row["camera_used"] or 0, dev or "")
            return True, PICK(f"تم تفعيل {tier.upper()} لمدة 30 يوماً ✅",
                               f"{tier.upper()} activated for 30 days ✅"), tier

    def log_camera(self, uid, pair, tt, result):
        with self._lock:
            cx = self._cx()
            cx.cursor().execute(
                "INSERT INTO camera_requests(user_id,pair,trade_type,result)VALUES(?,?,?,?)",
                (uid, pair, tt, result))
            cx.commit(); cx.close()

    def history(self, uid, n=30) -> List[Dict]:
        with self._lock:
            cx   = self._cx()
            rows = cx.cursor().execute(
                "SELECT pair,trade_type,result,created_at FROM camera_requests "
                "WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid,n)).fetchall()
            cx.close()
            return [{"pair":r["pair"],"tt":r["trade_type"],
                     "rec":r["result"],"at":r["created_at"]} for r in rows]


# ============================================================
#  AI ENGINE
# ============================================================
# ============================================================
#  AI ENGINE - urllib only (no external dependencies)
# ============================================================
class AIEngine:
    def __init__(self):
        try:
            self._k = base64.b64decode(Cfg._GK).decode()
        except Exception as e:
            print(f"[AIEngine] Key decode error: {e}")
            self._k = ""
        print(f"[AIEngine] Initialized. Key valid: {len(self._k) > 20}")

    def _call_gemini(self, url: str, img_b64: str, prompt: str) -> dict:
        """Call Gemini API using urllib (built-in, no pip install needed)"""
        payload = json.dumps({
            "contents": [{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                    {"text": prompt}
                ]
            }],
            "generationConfig": {
                "temperature": 0.05,
                "maxOutputTokens": 3000
            }
        }).encode('utf-8')

        req = urllib.request.Request(
            f"{url}?key={self._k}",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=45, context=_SSL_CTX) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            print(f"[AI] HTTP Error {e.code}: {error_body[:300]}")
            raise Exception(f"HTTP {e.code}: {error_body[:200]}")
        except urllib.error.URLError as e:
            print(f"[AI] URL Error: {e.reason}")
            raise Exception(f"Connection failed: {e.reason}")

    def _fake(self, pair: str, lang: str = "AR", error=None) -> Dict:
        """✅ نتيجة احتياطية عند فشل التحليل - يجب أن تكون واضحة أنها غير حقيقية.
        ⚠️ ملاحظة أمان: err_txt الحقيقي (قد يحتوي كلمة Gemini أو اسم الموديل) يُطبع
        فقط بالـ console للتشخيص، ولا يُدرَج أبداً داخل reason التي تظهر للمستخدم."""
        err_txt = str(error) if error else "غير معروف"
        print(f"[AI] Returning SIMULATED fallback. Reason: {err_txt}")
        if lang == "AR":
            reason = (
                f"⚠️ تعذّر إتمام التحليل الآن (نتيجة تجريبية وهمية).\n"
                f"لا تعتمد على هذه التوصية للتداول الحقيقي.\n"
                f"يرجى المحاولة مرة أخرى بعد قليل أو التأكد من اتصال الإنترنت."
            )
        else:
            reason = (
                f"⚠️ Could not complete the analysis right now (simulated fake result).\n"
                f"Do not rely on this recommendation for real trading.\n"
                f"Please try again shortly or check your internet connection."
            )
        return {
            "direction": "Buy",
            "entry": "0.00", "sl": "0.00", "tp": "0.00",
            "rr": "1:2.0",
            "reason": reason,
            "success_rate": "0%",
            "structure": "neutral",
            "ob_zone": "N/A", "liquidity": "N/A", "ma50_context": "N/A",
            "timeframe_used": "N/A",
            "source": "SIMULATED",   # ✅ يُستخدم فقط للتحقق الداخلي من كون النتيجة وهمية
            "_internal_model": f"اتصال AI فاشل ({err_txt[:80]})",
        }

    def analyze(self, img_b64: str, pair: str, tt: str = "Scalping", lang="AR") -> Dict:
        if not self._k or len(self._k) < 20:
            print("[AI] ❌ API key invalid")
            return self._fake(pair, lang, error="Invalid API key")

        if lang == "AR":
            prompt = (
                f"أنت محلل SMC/ICT مؤسسي محترف بخبرة عشرين عاماً في تداول العقود والفوركس والمعادن، "
                f"متخصص في قراءة نية 'المال الذكي' (Smart Money) بدقة جراحية. "
                f"حلّل الجارت المرفقة بعمق شديد للزوج/الأداة: {pair} | نمط التداول: {tt}.\n\n"

                "📈 مؤشرات على الجارت (مهم جداً - استخدمها):\n"
                "الجارت يحتوي على خطين متحركين (Moving Averages) مرسومين فوق الشموع:\n"
                "• MA50-High: متوسط متحرك فترة 50 مطبّق على أعلى سعر (High) لكل شمعة.\n"
                "• MA50-Low: متوسط متحرك فترة 50 مطبّق على أدنى سعر (Low) لكل شمعة.\n"
                "هذان الخطان يشكّلان 'قناة' ديناميكية (Dynamic Channel/Envelope). اقرأهما من الصورة "
                "بدقة واستخدمهما كالتالي:\n"
                "  - إذا كان السعر بالكامل فوق خط MA50-High → انحياز هيكلي صاعد قوي (الخط نفسه يعمل "
                "كدعم ديناميكي متحرك).\n"
                "  - إذا كان السعر بالكامل تحت خط MA50-Low → انحياز هيكلي هابط قوي (الخط نفسه يعمل "
                "كمقاومة ديناميكية متحركة).\n"
                "  - إذا كان السعر متذبذباً بين الخطين (داخل القناة) → السوق في تجميع/توازن "
                "(Equilibrium/Range) وتقل جودة أي دخول حتى يخرج السعر ويُغلق بوضوح خارج أحد الخطين.\n"
                "  - اختراق أحد الخطين مع إغلاق شمعة واضح خارجها + تزامن مع BOS/CHoCH يُعتبر تأكيداً "
                "إضافياً قوياً للدخول.\n"
                "  - ابحث عن تلاقي (Confluence) بين خط MA50 ومنطقة Order Block أو Fair Value Gap أو "
                "نقطة سيولة - هذا التلاقي يرفع جودة وثقة الإعداد بشكل كبير.\n\n"

                "🔹 إذا كان النمط 'Scalping': فرص قصيرة المدى (5-30 نقطة)، إطار M5/M15، التركيز على: "
                "آخر BOS/CHoCH، أقرب Order Block أو Fair Value Gap لم يُختبر، السيولة القريبة "
                "(Equal Highs/Lows)، وتفاعل السعر الفوري مع قناة MA50. وقف خسارة ضيق (5-15 نقطة).\n\n"
                "🔹 إذا كان النمط 'Swing': فرص متوسطة المدى (50-200 نقطة)، إطار H1/H4، التركيز على: "
                "الاتجاه الرئيسي وبنية السوق العليا (HH/HL أو LH/LL)، مناطق الطلب/العرض المؤسسية "
                "الكبرى، السيولة الخارجية (Buy-side/Sell-side Liquidity)، وموقع السعر من قناة MA50 "
                "على الإطار الأعلى. وقف خسارة أوسع (20-50 نقطة).\n\n"

                "📊 منهجية التحليل الإلزامية (بالترتيب):\n"
                "1. حدد بنية السوق (Market Structure): الاتجاه العام + آخر BOS أو CHoCH مؤكَّد.\n"
                "2. حدد موقع السعر بالنسبة لقناة MA50-High/MA50-Low وماذا يعني ذلك هيكلياً (كما فُصّل أعلاه).\n"
                "3. حدد أقوى Order Block (كتلة الأوامر) غير المُختبرة والمتوافقة مع اتجاه البنية.\n"
                "4. حدد أي Fair Value Gap (فجوة سيولة) في طريق السعر نحو نقطة الدخول.\n"
                "5. حدد مجمعات السيولة (Liquidity Pools / Equal Highs-Lows) المستهدفة كأهداف محتملة.\n"
                "6. تحقق من التلاقي (Confluence): هل تتقاطع منطقة الدخول مع خط MA50 + Order Block + "
                "FVG معاً؟ كلما زاد التلاقي، زادت جودة الإعداد.\n"
                "7. حدد نقطة الدخول الدقيقة بمبدأ 'صفر انعكاس' (Zero Reversal Entry): الدخول يجب أن "
                "يكون عند نقطة الرفض/التأكيد الفعلية مباشرة (مثل حافة OB أو منتصف FVG أو ملامسة خط "
                "MA50) وليس بانتظار ابتعاد السعر، بحيث يكون الدخول قريباً جداً من السعر الحالي بأقل "
                "احتمال لانعكاس إضافي ضد الصفقة قبل تفعيلها.\n"
                "8. حدد وقف خسارة منطقي خلف آخر نقطة سيولة/هيكلية محمية (وليس رقماً عشوائياً).\n"
                "9. حدد هدفاً واحداً فقط (Target واحد) عند أقرب مجمع سيولة منطقي بنسبة مخاطرة/عائد "
                "لا تقل عن 1:2.\n\n"

                "⚠️ قواعد صارمة غير قابلة للتفاوض:\n"
                "• لا تتسرّع أبداً باتخاذ القرار. خذ وقتك بالتحليل: افحص بنية السوق، قناة MA50، "
                "الـ Order Blocks، الـ FVG، ومجمعات السيولة كلها بعناية شديدة قبل أي استنتاج. "
                "التحليل السطحي أو المتسرّع مرفوض تماماً.\n"
                "• إذا لم يكن هناك إعداد SMC واضح وعالي الجودة ومؤكَّد بعدة عوامل تلاقي قوية جداً، اجعل "
                "direction = 'NoTrade' واشرح السبب بدقة - لا تجبر توصية أبداً تحت أي ظرف.\n"
                "• الجودة أهم من الكمية دائماً - النُدرة في التوصيات دليل جودة وليس نقصاً.\n"
                "• لا تُصدر توصية Buy أو Sell إطلاقاً إلا إذا كانت نسبة النجاح المقدَّرة بصدق "
                "(success_rate) 85% أو أعلى، بناءً على قوة التلاقي الفعلية بين جميع العوامل (بنية "
                "السوق + قناة MA50 + Order Block + FVG + السيولة) وليس رقماً متفائلاً بدون أساس حقيقي. "
                "إذا كانت ثقتك الحقيقية أقل من 85%، اجعل direction = 'NoTrade' بدل المجازفة بتوصية "
                "ضعيفة - هذا أهم قاعدة على الإطلاق.\n"
                "• الدخول يجب أن يكون قوياً جداً جداً: نقطة دخول واضحة عند تأكيد فعلي حقيقي (رفض سعري "
                "مؤكَّد، إغلاق شمعة واضح، أو ملامسة دقيقة لمنطقة تلاقي قوية) وليس تخميناً أو دخولاً "
                "مبكراً قبل التأكيد الكامل.\n"
                "• الدخول يجب أن يطبّق مبدأ صفر انعكاس فعلياً كما هو موضح أعلاه.\n"
                "• هدف واحد فقط (tp) - لا تُرجع هدفين.\n"
                "• نسبة المخاطرة/العائد يجب أن تكون 1:2 على الأقل وإلا فالإعداد مرفوض.\n"
                "• لا توصي بصفقة تعاكس بنية السوق الواضحة أو تعاكس اتجاه قناة MA50 دون اختراق مؤكَّد.\n"
                "• حقل reason يجب أن يكون قصيراً جداً (سطر أو سطرين فقط)، بلغة عربية مبسّطة يفهمها "
                "أي متداول عادي غير محترف. ممنوع منعاً باتاً استخدام أي مصطلحات أو اختصارات تقنية "
                "إنكليزية في هذا الحقل مثل: SMC, ICT, OB, Order Block, FVG, BOS, CHoCH, Liquidity, "
                "Smart Money. اشرح السبب بكلمات بسيطة (مثال: 'السعر ارتد من منطقة دعم قوية مع تأكيد "
                "الاتجاه الصاعد') بدل ذكر اسم الأداة الفنية نفسها.\n\n"

                "رد بـJSON فقط بدون أي نص إضافي:\n"
                '{"direction":"Buy|Sell|NoTrade","entry":"السعر الدقيق","sl":"السعر الدقيق",'
                '"tp":"السعر الدقيق","rr":"1:X",'
                '"reason":"شرح موجز جداً بالعربي البسيط بدون أي مصطلحات تقنية (سطر أو سطرين كحد أقصى)",'
                '"success_rate":"X%",'
                '"structure":"bullish|bearish|neutral","ob_zone":"وصف المنطقة بلغة بسيطة بدون مصطلحات",'
                '"liquidity":"وصف بلغة بسيطة بدون مصطلحات","ma50_context":"وصف موقع السعر بلغة بسيطة",'
                '"timeframe_used":"M5/M15 أو H1/H4","source":"AI-Vision"}'
            )
        else:
            prompt = (
                f"You are a professional institutional SMC/ICT analyst with 20 years of experience "
                f"trading forex, metals and futures, specialized in reading Smart Money intent with "
                f"surgical precision. Deeply analyze the attached chart for: {pair} | "
                f"Trading style: {tt}.\n\n"

                "📈 Chart overlays (very important - use these):\n"
                "The chart has two moving averages plotted on it:\n"
                "• MA50-High: a 50-period moving average applied to each candle's High.\n"
                "• MA50-Low: a 50-period moving average applied to each candle's Low.\n"
                "Together they form a dynamic channel/envelope. Read them from the image and use them as:\n"
                "  - Price fully above MA50-High → strong bullish structural bias (the line itself acts "
                "as dynamic support).\n"
                "  - Price fully below MA50-Low → strong bearish structural bias (the line itself acts "
                "as dynamic resistance).\n"
                "  - Price oscillating between the two lines → range/equilibrium, lower setup quality "
                "until price closes clearly outside one of the lines.\n"
                "  - A clear candle close breaking one of the lines, combined with BOS/CHoCH, is a "
                "strong additional confirmation.\n"
                "  - Look for confluence between the MA50 lines and an Order Block or Fair Value Gap or "
                "liquidity point - this materially raises setup quality and confidence.\n\n"

                "🔹 If 'Scalping': short-term opportunities (5-30 pips), M5/M15 timeframe, focus on: "
                "latest BOS/CHoCH, nearest untested Order Block or Fair Value Gap, nearby liquidity "
                "(Equal Highs/Lows), and immediate price reaction to the MA50 channel. Tight stop loss "
                "(5-15 pips).\n\n"
                "🔹 If 'Swing': medium-term opportunities (50-200 pips), H1/H4 timeframe, focus on: "
                "major trend and higher-timeframe structure (HH/HL or LH/LL), major institutional "
                "demand/supply zones, external liquidity (buy-side/sell-side), and price position "
                "relative to the MA50 channel on the higher timeframe. Wider stop loss (20-50 pips).\n\n"

                "Mandatory analysis methodology (in order):\n"
                "1. Determine market structure: overall trend + latest confirmed BOS or CHoCH.\n"
                "2. Determine price position relative to the MA50-High/MA50-Low channel and its "
                "structural meaning (as detailed above).\n"
                "3. Identify the strongest untested Order Block aligned with structure.\n"
                "4. Identify any Fair Value Gap in price's path toward the entry.\n"
                "5. Identify targeted liquidity pools / equal highs-lows as potential targets.\n"
                "6. Check confluence: does the entry zone overlap the MA50 line + Order Block + FVG "
                "together? More confluence = higher setup quality.\n"
                "7. Pinpoint the exact entry using the 'Zero Reversal Entry' principle: entry must be "
                "right at the actual rejection/confirmation point (e.g. OB edge, FVG midpoint, or MA50 "
                "touch), not after price has already moved away, so entry sits as close as possible to "
                "current price with minimal further adverse movement before activation.\n"
                "8. Set a logical stop loss behind the last protected liquidity/structural point (never "
                "an arbitrary number).\n"
                "9. Set exactly ONE realistic target at the nearest logical liquidity pool, with a "
                "risk/reward of at least 1:2.\n\n"

                "⚠️ Strict, non-negotiable rules:\n"
                "• Never rush the decision. Take your time analyzing: carefully examine market "
                "structure, the MA50 channel, Order Blocks, FVGs, and liquidity pools all in depth "
                "before reaching any conclusion. Shallow or hasty analysis is completely rejected.\n"
                "• If no clear, high-quality SMC setup confirmed by multiple very strong confluence "
                "factors exists, set direction='NoTrade' and explain precisely why - never force a "
                "trade under any circumstance.\n"
                "• Quality always beats quantity - rare recommendations are a sign of quality, not a "
                "shortfall.\n"
                "• Never output Buy or Sell unless your honestly estimated success_rate is 85% or "
                "higher, based on the real strength of confluence across ALL factors (market structure "
                "+ MA50 channel + Order Block + FVG + liquidity) - not an optimistic number with no "
                "real basis. If your genuine confidence is below 85%, set direction='NoTrade' instead "
                "of risking a weak call - this is the single most important rule.\n"
                "• The entry must be very, very strong: a clear entry only at a real, confirmed trigger "
                "(a confirmed price rejection, a clear candle close, or a precise touch of a strong "
                "confluence zone) - never a guess or an early entry before full confirmation.\n"
                "• Entry must genuinely apply the zero-reversal principle described above.\n"
                "• Exactly one target (tp) - never return two targets.\n"
                "• Risk/Reward must be at least 1:2 or the setup is rejected.\n"
                "• Never recommend a trade against clear market structure or against the MA50 channel "
                "direction without a confirmed break.\n"
                "• The 'reason' field must be in plain simple English any casual trader can understand. "
                "NEVER use technical jargon or acronyms such as: SMC, ICT, OB, Order Block, FVG, BOS, "
                "CHoCH, Liquidity, Smart Money. Explain the reason in plain words (e.g. 'price bounced "
                "off a strong support area confirming the uptrend') instead of naming the technical tool.\n\n"

                "Respond with JSON only, no extra text:\n"
                '{"direction":"Buy|Sell|NoTrade","entry":"exact price","sl":"exact price",'
                '"tp":"exact price","rr":"1:X",'
                '"reason":"very brief plain-language explanation with NO technical jargon (max 2 short '
                'sentences)","success_rate":"X%",'
                '"structure":"bullish|bearish|neutral","ob_zone":"plain-language zone description, no jargon",'
                '"liquidity":"plain-language description, no jargon","ma50_context":"plain-language price position",'
                '"timeframe_used":"M5/M15 or H1/H4","source":"AI-Vision"}'
            )

        # ✅ Try each model URL using urllib only (built-in)
        last_error = None
        urls = Cfg.get_model_urls()
        print(f"[AI] Starting analysis with {len(urls)} model(s)...")

        for url in urls:
            model_name = url.split('/')[-2]
            try:
                print(f"[AI] Trying model: {model_name}")
                data = self._call_gemini(url, img_b64, prompt)

                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        txt = candidate["content"]["parts"][0]["text"]
                        txt = re.sub(r'```json|```','',txt).strip()
                        m = re.search(r'\{.*\}', txt, re.DOTALL)
                        parsed_ok = False
                        if m:
                            try:
                                res = json.loads(m.group())
                                parsed_ok = True
                            except json.JSONDecodeError:
                                # ✅ الرد كان مقطوعاً (نفد maxOutputTokens) - نحاول إصلاحه تلقائياً
                                # بإغلاق آخر قيمة نصية مفتوحة وإضافة قوس الإغلاق
                                repaired = m.group()
                                repaired = re.sub(r',\s*"[a-zA-Z_]*"?:?\s*"?[^"}]*$', '', repaired)
                                if not repaired.rstrip().endswith('}'):
                                    repaired = repaired.rstrip().rstrip(',') + '}'
                                try:
                                    res = json.loads(repaired)
                                    parsed_ok = True
                                    print(f"[AI] ⚠️ Repaired truncated JSON from {model_name}")
                                except Exception:
                                    last_error = f"رد Gemini من {model_name} كان مقطوعاً ولم يُصلَح (نفد maxOutputTokens على الأرجح): {txt[:150]}"
                        if parsed_ok:
                            # ✅ شبكة أمان برمجية إلزامية: حتى لو النموذج ما التزم بالتعليمات،
                            # لا نسمح بأي توصية Buy/Sell بنسبة نجاح أقل من 85% مهما كان - تتحول
                            # تلقائياً لـ NoTrade بدل ما تنعرض للمستخدم كتوصية ضعيفة.
                            try:
                                sr_txt = str(res.get("success_rate", "0")).replace("%", "").strip()
                                sr_val = float(sr_txt) if sr_txt else 0
                            except (ValueError, TypeError):
                                sr_val = 0
                            if res.get("direction") in ("Buy", "Sell") and sr_val < 85:
                                print(f"[AI] ⚠️ توصية بنسبة {sr_val}% أقل من 85% - تحويلها لـ NoTrade إلزامياً")
                                res["direction"] = "NoTrade"
                            # ✅ لا نكشف اسم مزوّد الذكاء الاصطناعي أو اسم الموديل للمستخدم أبداً.
                            # نحتفظ بالاسم الحقيقي فقط لغرض السجلات الداخلية (console) تحت مفتاح
                            # منفصل لا يُعرض بواجهة المستخدم إطلاقاً.
                            res["_internal_model"] = model_name   # للسجلات الداخلية فقط
                            res["source"] = "AI-Vision"            # ما يظهر للمستخدم (عام غير محدد)
                            print(f"[AI] ✅ Success with {model_name}")
                            return res
                        elif not m:
                            last_error = f"لم يُرجع Gemini نص JSON صالح: {txt[:150]}"
                            print(f"[AI] No JSON found in response")
                    else:
                        # ✅ finishReason غالباً يوضح السبب الحقيقي (SAFETY, MAX_TOKENS...)
                        finish = candidate.get("finishReason", "?")
                        last_error = f"استجابة غير مكتملة من {model_name} (finishReason={finish})"
                        print(f"[AI] Invalid response structure: {candidate.keys()} | finishReason={finish}")
                else:
                    if "error" in data:
                        last_error = f"خطأ Gemini API: {data['error']}"
                        print(f"[AI] API Error: {data['error']}")
                    else:
                        last_error = f"لا توجد نتائج (candidates) في رد {model_name}: {data}"
                        print(f"[AI] No candidates in response: {data.keys()}")

            except Exception as ex:
                print(f"[AI] ❌ API error with {model_name}: {ex}")
                last_error = ex
                continue

        # All models failed
        print(f"[AI] ❌ All models failed, returning simulated response")
        return self._fake(pair, lang, error=last_error)

    def check_good_time(self, session_info: dict, upcoming_news: list, lang: str = "AR") -> Optional[Dict]:
        """
        ✅ تحليل نصي بسيط (بدون صورة) عبر Gemini لتحديد هل الوقت الحالي جيد
        للتداول أم لا، اعتماداً على الجلسات النشطة والأخبار القريبة. يُستخدم
        بالخلفية كل 4 ساعات فقط عند فتح التطبيق (بدون إشعارات بعد إغلاقه).
        """
        active = ", ".join(session_info.get("active", [])) or "لا توجد جلسة رئيسية نشطة"
        news_txt = "لا توجد أخبار عالية الأثر خلال الساعات القادمة"
        if upcoming_news:
            items = [f"{n.get('event_en', n.get('event','?'))} خلال {int(n.get('minutes_until',0))} دقيقة"
                     for n in upcoming_news[:3]]
            news_txt = "؛ ".join(items)

        if lang == "AR":
            prompt = (
                "أنت مساعد يقيّم بإيجاز شديد جودة اللحظة الحالية للتداول اليومي على الفوركس/المعادن، "
                "بناءً فقط على معلومتين: الجلسات النشطة حالياً، وأقرب الأخبار الاقتصادية عالية الأثر.\n"
                f"الجلسات النشطة الآن: {active}\n"
                f"الأخبار القادمة: {news_txt}\n\n"
                "قيّم: هل الوضع الحالي عموماً مناسب للتداول (سيولة جيدة، لا أخبار خطيرة جداً قريبة جداً) "
                "أم لا (سيولة ضعيفة جداً أو خبر عالي الأثر خلال أقل من 15 دقيقة)؟\n"
                "ممنوع ذكر أي مصطلحات تقنية معقدة. جاوب بلغة عربية بسيطة وموجزة جداً.\n\n"
                "رد بـJSON فقط:\n"
                '{"good_time": true|false, "reason": "سبب موجز جداً بالعربي البسيط (جملة واحدة قصيرة)"}'
            )
        else:
            prompt = (
                "You are an assistant briefly judging whether right now is a generally good moment for "
                "day trading forex/metals, based only on two facts: currently active trading sessions, "
                "and the nearest high-impact economic news.\n"
                f"Active sessions now: {active}\n"
                f"Upcoming news: {news_txt}\n\n"
                "Judge: is the current moment generally favorable for trading (good liquidity, no very "
                "risky news too close) or not (very low liquidity, or high-impact news within 15 minutes)?\n"
                "Never mention complex technical jargon. Answer in simple, very brief plain English.\n\n"
                "Respond with JSON only:\n"
                '{"good_time": true|false, "reason": "very brief plain-language reason (one short sentence)"}'
            )

        payload = json.dumps({
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
        }).encode('utf-8')

        try:
            url = Cfg.get_model_urls()[0]
            req = urllib.request.Request(
                f"{url}?key={self._k}", data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=20, context=_SSL_CTX) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            txt = data["candidates"][0]["content"]["parts"][0]["text"]
            txt = re.sub(r'```json|```', '', txt).strip()
            m = re.search(r'\{.*\}', txt, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception as ex:
            print(f"[AI] check_good_time failed: {ex}")
        return None


#  CALENDAR - Economic Calendar with Arabic Support
# ============================================================
class Calendar:
    """تقويم اقتصادي مع ترجمة عربية"""

    # ترجمة العملات للعربية
    CURRENCY_AR = {
        "USD": "🇺🇸 الدولار الأمريكي",
        "EUR": "🇪🇺 اليورو",
        "GBP": "🇬🇧 الجنيه الإسترليني",
        "JPY": "🇯🇵 الين الياباني",
        "CHF": "🇨🇭 الفرنك السويسري",
        "CAD": "🇨🇦 الدولار الكندي",
        "AUD": "🇦🇺 الدولار الأسترالي",
        "NZD": "🇳🇿 الدولار النيوزيلندي",
        "CNY": "🇨🇳 اليوان الصيني",
        "ALL": "🌍 جميع العملات",
    }

    # ترجمة الأثر
    IMPACT_AR = {
        "High": "🔴 عالي",
        "Medium": "🟡 متوسط",
        "Low": "🟢 منخفض",
    }

    # ترجمة أسماء الأحداث
    EVENT_TRANSLATIONS = {
        "Non-Farm Payrolls": "التغير في الوظائف غير الزراعية (NFP)",
        "Unemployment Rate": "معدل البطالة",
        "Federal Funds Rate": "معدل الفائدة الفيدرالي",
        "FOMC": "اجتماع اللجنة الفيدرالية (FOMC)",
        "CPI": "مؤشر أسعار المستهلكين (CPI)",
        "Core CPI": "مؤشر أسعار المستهلكين الأساسي",
        "PPI": "مؤشر أسعار المنتجين (PPI)",
        "GDP": "الناتج المحلي الإجمالي (GDP)",
        "Retail Sales": "مبيعات التجزئة",
        "Industrial Production": "الإنتاج الصناعي",
        "ISM Manufacturing": "مؤشر ISM للتصنيع",
        "ISM Services": "مؤشر ISM للخدمات",
        "Consumer Confidence": "ثقة المستهلك",
        "Durable Goods Orders": "طلبات السلع المعمرة",
        "Initial Jobless Claims": "طلبات إعانة البطالة الأولية",
        "Building Permits": "تراخيص البناء",
        "Housing Starts": "بدء بناء المساكن",
        "Existing Home Sales": "مبيعات المنازل القائمة",
        "New Home Sales": "مبيعات المنازل الجديدة",
        "Trade Balance": "الميزان التجاري",
        "Current Account": "الحساب الجاري",
        "ECB": "البنك المركزي الأوروبي (ECB)",
        "BoE": "بنك إنجلترا (BoE)",
        "BoJ": "بنك اليابان (BoJ)",
        "SNB": "البنك الوطني السويسري",
        "RBA": "البنك الاحتياطي الأسترالي",
        "RBNZ": "البنك الاحتياطي النيوزيلندي",
        "BoC": "بنك كندا",
        "Interest Rate Decision": "قرار معدل الفائدة",
        "Monetary Policy Statement": "بيان السياسة النقدية",
        "Press Conference": "المؤتمر الصحفي",
        "PMI": "مؤشر مديري المشتريات (PMI)",
        "Services PMI": "مؤشر PMI للخدمات",
        "Manufacturing PMI": "مؤشر PMI للتصنيع",
        "Composite PMI": "مؤشر PMI المركب",
        "ZEW Economic Sentiment": "مؤشر ZEW للمعنويات",
        "IFO Business Climate": "مؤشر IFO المناخي",
        "GfK Consumer Confidence": "مؤشر GfK لثقة المستهلك",
        "Employment Change": "التغير في التوظيف",
        "Average Hourly Earnings": "متوسط الأجور بالساعة",
        "ADP Non-Farm Employment": "تقرير ADP للوظائف",
        "JOLTS Job Openings": "فرص العمل الشاغرة",
        "Factory Orders": "طلبات المصانع",
        "Business Inventories": "مخزونات الأعمال",
        "Wholesale Inventories": "مخزونات الجملة",
        "Michigan Consumer Sentiment": "معنويات المستهلكين",
        "Personal Income": "الدخل الشخصي",
        "Personal Spending": "الإنفاق الشخصي",
        "Core PCE Price Index": "مؤشر أسعار PCE الأساسي",
        "Crude Oil Inventories": "مخزونات النفط الخام",
        "Natural Gas Storage": "مخزونات الغاز الطبيعي",
        "API Crude Oil": "مخزونات API للنفط",
        "Flash Manufacturing PMI": "مؤشر PMI التصنيعي الأولي",
        "Flash Services PMI": "مؤشر PMI للخدمات الأولي",
        "Employment Report": "تقرير التوظيف",
        "Trade Deficit": "عجز الميزان التجاري",
        "Budget Balance": "ميزانية الميزان",
        "Consumer Price Index": "مؤشر أسعار المستهلكين",
        "Producer Price Index": "مؤشر أسعار المنتجين",
        "Retail Sales m/m": "مبيعات التجزئة شهرياً",
        "Core Retail Sales m/m": "مبيعات التجزئة الأساسية شهرياً",
        "Unemployment Claims": "طلبات إعانة البطالة",
        "Philadelphia Fed Manufacturing Index": "مؤشر فيلادلفيا للتصنيع",
        "CB Consumer Confidence": "ثقة المستهلك (CB)",
        "Pending Home Sales": "مبيعات المنازل المعلقة",
        "Chicago PMI": "مؤشر شيكاغو PMI",
        "Dallas Fed Manufacturing Business Index": "مؤشر دالاس للتصنيع",
        "Richmond Fed Manufacturing Index": "مؤشر ريتشموند للتصنيع",
        "Kansas Fed Manufacturing Index": "مؤشر كانساس للتصنيع",
        "Empire State Manufacturing Index": "مؤشر إمباير ستيت للتصنيع",
        "NFIB Small Business Index": "مؤشر NFIB للأعمال الصغيرة",
        "Redbook": "مؤشر ريدبوك",
        "MBA Mortgage Applications": "طلبات الرهن العقاري (MBA)",
        "FHFA House Price Index": "مؤشر أسعار المنازل (FHFA)",
        "S&P/CS Composite HPI": "مؤشر أسعار المنازل S&P/CS",
        "New Zealand": "نيوزيلندا",
        "Australia": "أستراليا",
        "United States": "الولايات المتحدة",
        "United Kingdom": "المملكة المتحدة",
        "Euro Zone": "منطقة اليورو",
        "Germany": "ألمانيا",
        "France": "فرنسا",
        "Italy": "إيطاليا",
        "Spain": "إسبانيا",
        "Switzerland": "سويسرا",
        "Japan": "اليابان",
        "Canada": "كندا",
        "China": "الصين",
    }

    def __init__(self):
        self._cache: List[Dict] = []
        self._last = None

    def _fetch_url(self, url: str, timeout: int = 15) -> Optional[dict]:
        """Fetch JSON from URL using urllib (built-in)"""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except Exception as ex:
            print(f"[Calendar fetch error] {ex}")
        return None

    def _translate(self, text: str) -> str:
        """ترجمة نص للعربية"""
        if not text:
            return text
        # Check exact match
        if text in self.EVENT_TRANSLATIONS:
            return self.EVENT_TRANSLATIONS[text]
        # Check partial match
        for eng, ar in self.EVENT_TRANSLATIONS.items():
            if eng.lower() in text.lower():
                return ar
        return text

    def fetch(self, days=7) -> List[Dict]:
        now = datetime.datetime.now()
        if self._last and (now - self._last).seconds < 300:
            return self._filter(self._cache, days)

        evts = []

        # ✅ Try multiple real sources using urllib (built-in, يعمل على أندرويد)
        sources = [
            {
                "url": "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
                "parser": self._parse_forexfactory,
            },
            {
                "url": "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json",
                "parser": self._parse_forexfactory,
            },
            {
                "url": "https://nfs.faireconomy.media/ff_calendar_nextweek.json",
                "parser": self._parse_forexfactory,
            },
        ]

        for source in sources:
            try:
                data = self._fetch_url(source["url"], timeout=15)
                if data and len(data) > 0:
                    parsed = source["parser"](data, now)
                    if parsed and len(parsed) > 0:
                        evts.extend(parsed)
                        print(f"[Calendar] ✅ Loaded {len(parsed)} events from {source['url']}")
            except Exception as ex:
                print(f"[Calendar Source] {ex}")
                continue

        if evts and len(evts) > 3:
            # ✅ إزالة التكرار: نعتمد على العملة + الوقت (مقرَّب للدقيقة) بدل النص
            # المُترجم فقط، لأن الترجمة الجزئية (partial match) في _translate()
            # ممكن تخلي عنوانين مختلفين يتطابقوا نصياً، أو العكس تختلف صياغة
            # العنوان قليلاً بين مصدرين (nfs/cdn-nfs) لنفس الخبر بالضبط.
            seen = set()
            unique_evts = []
            for e in evts:
                key = f"{e['currency']}_{e['datetime'].strftime('%Y-%m-%d %H:%M')}_{e['event'].strip().lower()}"
                if key not in seen:
                    seen.add(key)
                    unique_evts.append(e)

            self._cache = sorted(unique_evts, key=lambda x: x["datetime"])
            self._last = now
            print(f"[Calendar] ✅ Total unique events: {len(self._cache)}")
        else:
            print("[Calendar] ⚠️ No real data available, using fallback")
            self._cache = self._fallback()

        return self._filter(self._cache, days)

    def _parse_forexfactory(self, data, now):
        """Parse ForexFactory JSON format.
        ✅ الحقل الحقيقي القادم من نيوز فوركس فاكتوري هو "date" فقط، وهو
        نص ISO-8601 كامل مع منطقة زمنية مضمّنة، مثال:
        "2026-08-10T12:30:00-04:00"
        (لا يوجد حقل "time" منفصل إطلاقاً - هذا كان سبب فشل تحليل كل الأخبار
        سابقاً لأن strptime كان يفشل بصمت بسبب try/except: continue)
        """
        evts = []
        for it in data:
            try:
                raw = it.get("date", "")
                if not raw:
                    continue
                # ISO-8601 مع إزاحة زمنية، مثال: 2026-08-10T12:30:00-04:00
                raw_norm = raw.replace("Z", "+00:00")
                try:
                    dt_aware = datetime.datetime.fromisoformat(raw_norm)
                except ValueError:
                    # fallback: بعض التنسيقات القديمة "YYYY-MM-DD HH:MM:SS"
                    dt_aware = datetime.datetime.strptime(raw_norm[:19], "%Y-%m-%dT%H:%M:%S")
                if dt_aware.tzinfo is not None:
                    # تحويل من UTC/إزاحة المصدر إلى التوقيت المحلي للجهاز
                    dt = dt_aware.astimezone().replace(tzinfo=None)
                else:
                    dt = dt_aware
                imp = it.get("impact", "Low")

                if imp in ("High", "Medium"):
                    raw_title = it.get("title", "?")
                    event_ar = self._translate(raw_title)
                    currency = it.get("country", "ALL")

                    evts.append({
                        "datetime": dt,
                        "currency": currency,
                        "event": event_ar,          # عربي (افتراضي، متوافق مع الكود القديم)
                        "event_en": raw_title,       # ✅ الاسم الأصلي بالإنكليزي لعرضه عند اختيار EN
                        "impact": imp,
                        "forecast": it.get("forecast") or "N/A",
                        "previous": it.get("previous") or "N/A",
                        "actual": it.get("actual") or "N/A",
                        "minutes_until": (dt - now).total_seconds() / 60,
                    })
            except:
                continue
        return evts

    def _filter(self, evts, days):
        now = datetime.datetime.now()
        cut = now + datetime.timedelta(days=days)
        # ✅ إصلاح: كان الفلتر يستبعد أي خبر صار قبل أكثر من ساعة وحدة من الآن،
        # حتى لو صدر بنفس اليوم (مثال: خبر الساعة 9 صباحاً يختفي بعد الساعة 10
        # رغم إنه لسا "اليوم")! الصحيح: نعرض كل أخبار اليوم من منتصف الليل،
        # مو بس آخر ساعة، تماماً متل ForexFactory وInvesting.com.
        start_of_today = datetime.datetime.combine(now.date(), datetime.time.min)
        res = []
        for e in evts:
            e["minutes_until"] = (e["datetime"] - now).total_seconds() / 60
            if e["datetime"] >= start_of_today and e["datetime"] <= cut:
                res.append(e)
        return res

    def _fallback(self):
        """⚠️ بيانات احتياطية - تُستخدم فقط عند فشل جميع المصادر"""
        now = datetime.datetime.now()
        # Generate realistic fallback events based on current time
        fallback_events = [
            {
                "datetime": now + datetime.timedelta(hours=4),
                "currency": "USD",
                "event": "مؤشر ISM للتصنيع",
                "impact": "High",
                "forecast": "49.2",
                "previous": "48.7",
                "actual": "N/A",
                "minutes_until": 240,
            },
            {
                "datetime": now + datetime.timedelta(hours=8),
                "currency": "USD",
                "event": "طلبات إعانة البطالة الأولية",
                "impact": "Medium",
                "forecast": "215K",
                "previous": "218K",
                "actual": "N/A",
                "minutes_until": 480,
            },
            {
                "datetime": now + datetime.timedelta(hours=12),
                "currency": "EUR",
                "event": "مؤشر مديري المشتريات (PMI) - منطقة اليورو",
                "impact": "Medium",
                "forecast": "46.8",
                "previous": "46.2",
                "actual": "N/A",
                "minutes_until": 720,
            },
            {
                "datetime": now + datetime.timedelta(hours=20),
                "currency": "USD",
                "event": "مخزونات النفط الخام (EIA)",
                "impact": "Medium",
                "forecast": "-1.2M",
                "previous": "-0.8M",
                "actual": "N/A",
                "minutes_until": 1200,
            },
            {
                "datetime": now + datetime.timedelta(hours=28),
                "currency": "USD",
                "event": "مؤشر ثقة المستهلك (Michigan)",
                "impact": "Medium",
                "forecast": "68.5",
                "previous": "66.8",
                "actual": "N/A",
                "minutes_until": 1680,
            },
        ]
        # ✅ إضافة الاسم الإنكليزي تلقائياً من قاموس الترجمة العام لكل خبر احتياطي
        for _fe in fallback_events:
            _fe["event_en"] = AR_EN.get(_fe["event"], _fe["event"])
        return fallback_events

# ✅ دمج كل ترجمات أسماء الأحداث/الدول (EVENT_TRANSLATIONS) داخل قاموس اللغة
# العام AR_EN تلقائياً (بدل كتابتها يدوياً مرتين) - المفتاح بالقاموس الأصلي
# إنكليزي والقيمة عربية، فنعكسها هنا لنحصل على عربي->إنكليزي.
for _en, _ar in Calendar.EVENT_TRANSLATIONS.items():
    AR_EN.setdefault(_ar, _en)
for _ar in Calendar.CURRENCY_AR.values():
    pass  # مضافة يدوياً أعلاه بالفعل مع الأعلام
for _en, _ar in {"High":"عالي","Medium":"متوسط","Low":"منخفض"}.items():
    pass  # الأثر (Impact) مضاف يدوياً أعلاه بالإيموجي المطابق

# ============================================================
#  TRADING HOURS
# ============================================================
class TradingHours:
    SESS = {"سيدني":(22,7),"طوكيو":(0,9),"لندن":(8,17),"نيويورك":(13,22)}
    def info(self):
        h = datetime.datetime.now().hour
        act = [n for n,(o,cl) in self.SESS.items()
               if (o>cl and (h>=o or h<cl)) or (o<=cl and o<=h<cl)]
        rec = ("⭐ تداخل لندن-نيويورك" if "لندن" in act and "نيويورك" in act
               else "✅ وقت جيد" if ("لندن" in act or "نيويورك" in act)
               else "⏳ وقت هادئ")
        return {"time":datetime.datetime.now().strftime("%H:%M"),"active":act,"rec":rec}

# ============================================================
#  NOTIFIER
# ============================================================
class Notifier:
    def __init__(self, page):
        self.page = page
        self._col = ft.Column([], spacing=6)
        self._ctr = ft.Container(content=self._col, right=8, top=56, width=300)
        page.overlay.append(self._ctr)

    def show(self, title, body, icon=None, color="#448aff", secs=5):
        if not icon: icon = IC['info']
        c = Cfg.colors(self.page.theme_mode == _e("ThemeMode","DARK","dark"))
        toast = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon,color=color,size=16),
                        ft.Text(title,size=10,weight=_e("FontWeight","BOLD","bold"),
                                color=c["txt"],expand=True)],spacing=5),
                ft.Text(body,size=9,color=c["txt2"])],spacing=2),
            padding=_pad_sym(8,8),bgcolor=c["card"],border_radius=8,
            border=_border(1.5,color),
            shadow=ft.BoxShadow(blur_radius=6,color=_op("#000000",.4)))
        self._col.controls.insert(0,toast)
        try: self.page.update()
        except: pass
        def _rm():
            time.sleep(secs)
            try:
                if toast in self._col.controls:
                    self._col.controls.remove(toast); self.page.update()
            except: pass
        threading.Thread(target=_rm,daemon=True).start()

# ============================================================
#  HELPERS
# ============================================================
def calc_countdown(expiry_iso):
    if not expiry_iso: return {"days":0,"hours":0,"mins":0,"expired":True,"pct":0.0}
    try:
        diff = datetime.datetime.fromisoformat(expiry_iso) - datetime.datetime.now()
        if diff.total_seconds()<=0: return {"days":0,"hours":0,"mins":0,"expired":True,"pct":0.0}
        s=diff.total_seconds()
        return {"days":int(s//86400),"hours":int((s%86400)//3600),
                "mins":int((s%3600)//60),"expired":False,"pct":min(1.0,s/(30*86400))}
    except: return {"days":0,"hours":0,"mins":0,"expired":True,"pct":0.0}

def _stat_col(label, value, color, c):
    return ft.Container(
        content=ft.Column([
            ft.Text(label,size=8,color=c["txt2"]),
            ft.Text(str(value) if value else "N/A",size=11,
                weight=_e("FontWeight","BOLD","bold"),color=color)],
            horizontal_alignment=_e("CrossAxisAlignment","CENTER","center"),spacing=1),
        expand=True,padding=_pad_sym(4,4),bgcolor=_op(color,.07),
        border_radius=6,margin=_marg_sym(2,0))


# ============================================================
#  APP
# ============================================================
class App:
    CATS = {
        "فوركس":  ["EUR/USD","GBP/USD","USD/JPY","USD/CHF","USD/CAD","AUD/USD","NZD/USD",
                   "EUR/GBP","EUR/JPY","EUR/CHF","EUR/AUD","EUR/CAD","GBP/JPY","GBP/CHF",
                   "GBP/AUD","AUD/JPY","CAD/JPY","NZD/JPY"],
        "معادن":  ["XAU/USD","XAG/USD"],
        "مؤشرات":["US30","NAS100"],
        "كريبتو":["BTC/USD"],
    }
    PM = {"EUR/USD":"EURUSD","GBP/USD":"GBPUSD","USD/JPY":"USDJPY","USD/CHF":"USDCHF",
          "USD/CAD":"USDCAD","AUD/USD":"AUDUSD","NZD/USD":"NZDUSD","EUR/GBP":"EURGBP",
          "EUR/JPY":"EURJPY","EUR/CHF":"EURCHF","EUR/AUD":"EURAUD","EUR/CAD":"EURCAD",
          "GBP/JPY":"GBPJPY","GBP/CHF":"GBPCHF","GBP/AUD":"GBPAUD","AUD/JPY":"AUDJPY",
          "CAD/JPY":"CADJPY","NZD/JPY":"NZDJPY","XAU/USD":"XAUUSD","XAG/USD":"XAGUSD",
          "US30":"US30","NAS100":"NAS100","BTC/USD":"BTCUSD"}
    TT = {"سكالبينج":"Scalping","سويينج":"Swing"}

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = Cfg.APP
        self.page.padding = 0
        self.page.theme_mode = _e("ThemeMode","DARK","dark")
        self.page.bgcolor = Cfg.colors(True)["bg"]

        # ✅ حل مشكلة نصف الشاشة - لا نحدد حجم النافذة على Android
        try:
            if platform.system() in ["Windows", "Darwin", "Linux"]:
                self.page.window_width = 390
                self.page.window_height = 844
        except Exception:
            pass

        # Initialize core components first
        self.sec = Sec()
        self.db = DB()
        self.ai = AIEngine()
        self.cal = Calendar()
        self.trd = TradingHours()

        # Initialize state variables
        self.user: Optional[Dict] = None
        self.dev_id = self.sec.dev_id()
        self.is_dark = True
        self.lang = "AR"
        self.nav_idx = 0
        self.sel_cat = "معادن"
        self.sel_pair = "XAUUSD"
        self.sel_tt = "Scalping"
        self._alerted: set = set()
        self._bg = False
        self._cam_b64: Optional[str] = None
        self._pair_selected = False
        self.news_filter = 1

        # Create theme button (uses self.C property)
        self.theme_btn = ft.IconButton(
            icon=IC['moon'], 
            icon_color=self.C["accent"], 
            on_click=self._toggle_theme
        )

        # ✅ حالة التطبيق
        self._cam_b64 = None
        self._pair_selected = False

        # ✅ Notifier - تهيئة لاحقة لتجنب مشاكل overlay
        self.notifier = None

        # ✅ تسجيل دخول تلقائي (بعد تهيئة كل المكونات)
        self._auto_login()

    def _auto_login(self):
        """تسجيل دخول تلقائي إذا كانت الجلسة موجودة"""
        session_user = self.db.get_session(self.dev_id)
        if session_user:
            self.user = session_user
            self.db.reset_daily(self.user["id"])
            self._show_main()
        else:
            self._show_login()

    @property
    def C(self): return Cfg.colors(self.is_dark)

    # -------- UI HELPERS --------
    def _chip(self, txt, active, cb, small=False, color=None):
        c=self.C; acc=color or c["chip_on"]
        return ft.Container(
            content=ft.Text(L(txt),size=10 if small else 12,
                weight=_e("FontWeight","BOLD","bold") if active else _e("FontWeight","W_400","w400"),
                color=c["chip_on_txt"] if active else c["chip_off_txt"]),
            padding=_pad_sym(10 if small else 14, 7 if small else 9),
            border_radius=25, bgcolor=acc if active else c["chip_off"],
            on_click=cb, border=_border(1, acc if active else "transparent"))

    def _glass(self, content, pad=16):
        c=self.C
        return ft.Container(content=content,padding=_pad_sym(pad,pad),border_radius=16,
            bgcolor=_op("#ffffff",.07) if self.is_dark else _op("#ffffff",.8),
            border=_border(1.5, _op("#ffffff",.16) if self.is_dark else _op("#000000",.1)))

    def _bigbtn(self, text, cb, icon=None, color=None):
        c=self.C; color=color or c["accent"]
        items=[]
        if icon: items.append(ft.Icon(icon,color="#000" if self.is_dark else "#fff",size=18))
        items.append(ft.Text(text,weight=_e("FontWeight","BOLD","bold"),size=14,
                             color="#000" if self.is_dark else "#fff"))
        return ft.ElevatedButton(
            content=ft.Row(items,alignment=_e("MainAxisAlignment","CENTER","center"),spacing=8),
            style=ft.ButtonStyle(bgcolor=color,padding=_pad_sym(20,14),
                shape=ft.RoundedRectangleBorder(radius=24),elevation=4),
            on_click=cb)

    def _inp(self, label, hint, pwd=False, icon=None):
        c=self.C
        return ft.TextField(label=label,hint_text=hint,password=pwd,can_reveal_password=pwd,
            prefix_icon=icon,border_radius=12,filled=True,
            border_color=_op("#ffffff" if self.is_dark else "#000000",.22),
            focused_border_color=c["accent"],text_size=13,
            label_style=ft.TextStyle(size=12,color=c["txt2"]))

    def _toggle_theme(self, e=None):
        self.is_dark = not self.is_dark
        self.page.theme_mode = _e("ThemeMode","DARK","dark") if self.is_dark else _e("ThemeMode","LIGHT","light")
        self.page.bgcolor = self.C["bg"]
        self.theme_btn.icon = IC['moon'] if self.is_dark else IC['sun']
        self.theme_btn.icon_color = self.C["accent"]
        if self.user: self._show_main()
        else: self._show_login()

    def _toggle_lang(self, e=None):
        """تبديل اللغة بين العربية والإنجليزية"""
        try:
            self.lang = "EN" if self.lang=="AR" else "AR"
            set_lang(self.lang)   # ✅ مزامنة الحالة العالمية التي تقرأها L()/PICK()
            # ✅ لا نمسح الصورة عند تبديل اللغة
            if self.user: 
                self._show_main()
            else: 
                self._show_login()
        except Exception as ex:
            print(f"[TOGGLE_LANG ERROR] {ex}")
            import traceback
            traceback.print_exc()

    async def _handle_picked_image(self, files):
        """معالجة الصور المختارة من FilePicker"""
        if files and len(files) > 0:
            try:
                f = files[0]
                print(f"[DEBUG] File picked: name={getattr(f, 'name', '?')}, "
                      f"path={getattr(f, 'path', '?')}, "
                      f"has_bytes={hasattr(f, 'bytes') and f.bytes is not None}, "
                      f"size={getattr(f, 'size', '?')}")

                # Try multiple methods to get image data
                image_bytes = None

                # Method 1: Direct bytes (with_data=True on mobile/web)
                if hasattr(f, 'bytes') and f.bytes is not None:
                    print("[DEBUG] Using f.bytes")
                    image_bytes = f.bytes

                # Method 2: Read from path (desktop)
                elif hasattr(f, 'path') and f.path:
                    p = f.path
                    print(f"[DEBUG] Trying path: {p}")
                    if os.path.exists(p):
                        with open(p, "rb") as img_file:
                            image_bytes = img_file.read()
                    else:
                        # On Android, path might be a content URI
                        print(f"[DEBUG] Path not found, trying content URI: {p}")
                        # Try reading as content URI
                        try:
                            import urllib.request
                            with urllib.request.urlopen(p) as response:
                                image_bytes = response.read()
                        except Exception as uri_ex:
                            print(f"[DEBUG] URI read failed: {uri_ex}")

                # Method 3: Try reading from upload_url (for web uploads)
                elif hasattr(f, 'upload_url') and f.upload_url:
                    print(f"[DEBUG] Trying upload_url: {f.upload_url}")
                    try:
                        req = urllib.request.Request(f.upload_url)
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            image_bytes = resp.read()
                    except Exception as url_ex:
                        print(f"[DEBUG] URL read failed: {url_ex}")

                # Convert to base64
                if image_bytes:
                    self._cam_b64 = base64.b64encode(image_bytes).decode()
                    print(f"[DEBUG] Image loaded successfully, size: {len(image_bytes)} bytes")
                    if self.nav_idx == 0:
                        self._update_tab(0)
                        self.page.update()
                    if self.notifier:
                        self.notifier.show(L("✅ تم"), L("تم تحميل الصورة بنجاح"), IC['check'], self.C["green"], 3)
                else:
                    print("[DEBUG] Could not get image bytes")
                    if self.notifier:
                        self.notifier.show(L("❌ خطأ"), L("تعذر قراءة الملف - جرب طريقة أخرى"), IC['warn'], self.C["red"], 5)

            except Exception as ex:
                print(f"[FILE ERROR] {ex}")
                import traceback
                traceback.print_exc()
                if self.notifier:
                    self.notifier.show(L("❌ خطأ"), PICK(f"تعذر قراءة الملف: {str(ex)}", f"Could not read the file: {str(ex)}"), IC['warn'], self.C["red"], 5)

    async def _pick_file_dialog(self, e):
        """فتح نافذة اختيار الملف - Flet 0.86+ async"""
        if not self._pair_selected:
            if self.notifier:
                self.notifier.show(L("⚠️ اختر الزوج أولاً"), L("حدد الزوج ونوع التداول قبل رفع الصورة"), IC['warn'], self.C["orange"], 4)
            return

        try:
            # ✅ Flet 0.86+ - FilePicker is a Service, use async/await
            # Create picker instance
            picker = ft.FilePicker()

            # Pick files with data
            files = await picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE,
                allowed_extensions=["jpg", "jpeg", "png", "bmp", "webp"],
                dialog_title=L("اختر صورة الجارت"),
                with_data=True,  # Read file contents directly on mobile
            )

            print(f"[DEBUG] Picked files: {files}")
            if files:
                await self._handle_picked_image(files)
            else:
                print("[DEBUG] No files selected")
        except Exception as ex:
            print(f"[FilePicker Error] {ex}")
            import traceback
            traceback.print_exc()
            # Fallback: use manual path input
            self._show_manual_path_dialog()

    async def _capture_camera(self, e):
        """فتح الكاميرا - Flet 0.81+ Camera control"""
        if not self._pair_selected:
            if self.notifier:
                self.notifier.show(L("⚠️ اختر الزوج أولاً"), L("حدد الزوج ونوع التداول قبل التقاط الصورة"), IC['warn'], self.C["orange"], 4)
            return

        try:
            # Try to use flet_camera if available
            import flet_camera as fc

            camera = fc.Camera(
                expand=True,
                preview_enabled=True,
                on_capture=self._on_camera_capture,
            )

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(L("📷 التقاط صورة"), color=self.C["txt"]),
                content=camera,
                actions=[
                    ft.TextButton(L("إلغاء"), on_click=lambda e: setattr(dlg, "open", False) or self.page.update()),
                    ft.ElevatedButton(L("التقاط"), on_click=lambda e: camera.capture()),
                ],
                bgcolor=self.C["card"],
            )
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()
        except ImportError:
            # flet_camera not installed, use fallback
            self.notifier.show("ℹ️", L("مكتبة الكاميرا غير مثبتة. استخدم رفع الصورة بدلاً."), IC['info'], self.C["blue"], 5)
            await self._pick_file_dialog(e)

    def _on_camera_capture(self, e):
        """معالجة الصورة الملتقطة من الكاميرا"""
        try:
            if hasattr(e, 'image') and e.image:
                self._cam_b64 = e.image
                if self.nav_idx == 0:
                    self._update_tab(0)
                    self.page.update()
        except Exception as ex:
            print(f"[Camera] {ex}")

    def _show_manual_path_dialog(self):
        """حوار إدخال مسار يدوي (بديل)"""
        path_field = ft.TextField(
            label=L("مسار الصورة"),
            hint_text="/storage/emulated/0/DCIM/image.jpg",
            prefix_icon=IC['upload'],
            border_radius=12,
            filled=True,
            text_size=13,
        )

        def on_confirm(e):
            path = path_field.value.strip()
            if path and os.path.exists(path):
                try:
                    self._cam_b64 = base64.b64encode(open(path, "rb").read()).decode()
                    if self.nav_idx == 0:
                        self._update_tab(0)
                        self.page.update()
                    dlg.open = False
                    self.page.update()
                except Exception as ex:
                    if self.notifier:
                        self.notifier.show(L("❌ خطأ"), str(ex), IC['warn'], self.C["red"], 4)
            else:
                if self.notifier:
                    self.notifier.show("⚠️", L("أدخل مسار صحيح"), IC['warn'], self.C["orange"], 3)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(L("📁 اختر صورة"), color=self.C["txt"]),
            content=ft.Column([
                ft.Text(L("أدخل مسار الصورة:"), color=self.C["txt2"], size=12),
                path_field,
            ], spacing=4, tight=True),
            actions=[
                ft.TextButton(L("إلغاء"), on_click=lambda e: setattr(dlg, "open", False) or self.page.update()),
                ft.ElevatedButton(L("تحميل"), style=ft.ButtonStyle(bgcolor=self.C["accent"], color="#000"), on_click=on_confirm),
            ],
            bgcolor=self.C["card"],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # -------- VIEWS --------
    def _show_login(self):
        # Ensure overlay is initialized
        self._init_overlay()
        c=self.C
        ef=self._inp(L("البريد الإلكتروني"),"example@gmail.com",icon=IC['email'])
        pf=self._inp(L("كلمة المرور"),"••••••••",pwd=True,icon=IC['lock'])
        st=ft.Text("",size=11,text_align=_e("TextAlign","CENTER","center"))
        ring=ft.ProgressRing(color=c["accent"],width=20,height=20,stroke_width=2.5,visible=False)
        login_btn = self._bigbtn(L("تسجيل الدخول"),None,IC['login'],c["accent"])

        def _do(e):
            em=ef.value.strip().lower(); pw=pf.value.strip()
            if not em or not pw:
                st.value=L("أدخل البريد وكلمة المرور"); st.color=c["red"]; self.page.update(); return
            if em not in (Cfg.ADMIN_EMAIL, Cfg.U30_EMAIL):
                if not re.match(Cfg.EMAIL_RE, em):
                    st.value=L("استخدم Gmail/Hotmail/Outlook"); st.color=c["red"]; self.page.update(); return
            # ✅ عملية الدخول (فحص محلي + اتصال شبكة مع Firebase) كانت تشتغل
            # مباشرة على خيط الواجهة فتجمّد التطبيق بدون أي مؤشر تحميل لحد ١٥
            # ثانية - الآن تشتغل بخيط منفصل مع دائرة تحميل واضحة، والزر يتعطّل
            # أثناء المحاولة لمنع الضغط المتكرر.
            ring.visible=True; login_btn.disabled=True
            st.value=""; self.page.update()
            def _work():
                try:
                    ok, u, msg = self.db.auth(em, self.sec.hash(pw), self.dev_id, password_plain=pw)
                except Exception as ex:
                    ok, u, msg = False, None, PICK(f"خطأ: {ex}", f"Error: {ex}")
                ring.visible=False; login_btn.disabled=False
                st.color = c["green"] if ok else c["red"]
                st.value = L(msg)
                self.page.update()
                if ok:
                    self.user=u; self.db.reset_daily(u["id"])
                    threading.Timer(0.5, self._show_main).start()
            threading.Thread(target=_work,daemon=True).start()
        login_btn.on_click = _do

        def _reset_confirm(e):
            def _do_reset(e2):
                self.db.reset_all()
                self.dev_id = self.sec.dev_id()
                dlg.open = False; self.page.update()
                self.notifier.show(L("✅ تم المسح"),L("أنشئ حساباً جديداً الآن"),IC['check'],c["green"],5)
                threading.Timer(1, self._show_register).start()
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(L("⚠️ مسح كامل البيانات؟"),color=c["red"]),
                content=ft.Text(L("سيتم حذف جميع الحسابات والبيانات المحلية.\n")+
                                L("استخدم هذا فقط إذا نسيت بياناتك."),color=c["txt2"],size=12),
                actions=[
                    ft.TextButton(L("إلغاء"),on_click=lambda e: setattr(dlg,"open",False) or self.page.update()),
                    ft.ElevatedButton(L("مسح الكل"),
                        style=ft.ButtonStyle(bgcolor=c["red"],color="#fff"),
                        on_click=_do_reset)],
                actions_alignment=_e("MainAxisAlignment","END","end"))
            self.page.dialog=dlg; dlg.open=True; self.page.update()

        v=ft.View(route="/",bgcolor=c["bg"],controls=[
            ft.Container(expand=True,alignment=_align("center"),padding=_pad_sym(28,20),
                content=ft.Column([
                    ft.Icon(IC['camera'],size=64,color=c["accent"]),
                    ft.Text(Cfg.APP,size=26,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                    ft.Text(L("الذكاء الاصطناعي للأسواق المالية"),size=11,color=c["txt2"]),
                    ft.Container(height=10),
                    self._glass(ft.Column([
                        ef,pf,ft.Container(height=4),
                        ft.Row([login_btn,ring],alignment=_e("MainAxisAlignment","CENTER","center"),spacing=10),
                        st],spacing=10),pad=20),
                    ft.TextButton(L("ليس لديك حساب؟ سجل الآن"),
                        on_click=lambda e: self._show_register(),
                        style=ft.ButtonStyle(color=c["accent"])),
                    ft.TextButton(L("⚠️ مشكلة في تسجيل الدخول؟ اضغط هنا"),
                        on_click=_reset_confirm,
                        style=ft.ButtonStyle(color=c["txt3"])),
                ],horizontal_alignment=_e("CrossAxisAlignment","CENTER","center"),
                spacing=10,scroll=_e("ScrollMode","AUTO","auto")))])
        self.page.views.clear(); self.page.views.append(v); self.page.update()

    def _show_register(self):
        c=self.C
        nf=self._inp(L("الاسم الكامل"),L("محمد أحمد"),icon=IC['person'])
        ef=self._inp(L("البريد الإلكتروني"),"example@gmail.com",icon=IC['email'])
        pf=self._inp(L("كلمة المرور"),"••••••••",pwd=True,icon=IC['lock'])
        st=ft.Text("",size=11,text_align=_e("TextAlign","CENTER","center"))
        ring=ft.ProgressRing(color=c["accent"],width=20,height=20,stroke_width=2.5,visible=False)
        reg_btn = self._bigbtn(L("إنشاء الحساب"),None,IC['add_usr'],c["accent"])

        def _do(e):
            nm=nf.value.strip(); em=ef.value.strip().lower(); pw=pf.value.strip()
            if not nm or not em or not pw:
                st.value=L("جميع الحقول مطلوبة"); st.color=c["red"]; self.page.update(); return
            if em not in (Cfg.ADMIN_EMAIL,Cfg.U30_EMAIL):
                if not re.match(Cfg.EMAIL_RE,em):
                    st.value=L("Gmail/Hotmail/Outlook فقط"); st.color=c["red"]; self.page.update(); return
            if len(pw)<6:
                st.value=L("كلمة المرور 6 أحرف على الأقل"); st.color=c["red"]; self.page.update(); return
            ring.visible=True; reg_btn.disabled=True; st.value=""; self.page.update()
            def _work():
                try:
                    ok, msg = self.db.create(em, self.sec.hash(pw), nm, self.dev_id, password_plain=pw)
                except Exception as ex:
                    ok, msg = False, PICK(f"خطأ: {ex}", f"Error: {ex}")
                ring.visible=False; reg_btn.disabled=False
                st.value=L(msg); st.color=c["green"] if ok else c["red"]; self.page.update()
                if ok: threading.Timer(1.5, self._show_login).start()
            threading.Thread(target=_work,daemon=True).start()
        reg_btn.on_click = _do

        v=ft.View(route="/register",bgcolor=c["bg"],controls=[
            ft.Container(expand=True,alignment=_align("center"),padding=_pad_sym(28,20),
                content=ft.Column([
                    ft.Text(L("إنشاء حساب"),size=22,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                    ft.Container(height=8),
                    self._glass(ft.Column([nf,ef,pf,ft.Container(height=4),
                        ft.Row([reg_btn,ring],alignment=_e("MainAxisAlignment","CENTER","center"),spacing=10),st],
                        spacing=10),pad=20),
                    ft.TextButton(L("لديك حساب؟ تسجيل الدخول"),
                        on_click=lambda e: self._show_login(),
                        style=ft.ButtonStyle(color=c["accent"]))],
                horizontal_alignment=_e("CrossAxisAlignment","CENTER","center"),
                spacing=12,scroll=_e("ScrollMode","AUTO","auto")))])
        self.page.views.clear(); self.page.views.append(v); self.page.update()


    def _init_overlay(self):
        """تهيئة المكونات التي تحتاج overlay (تُستدعى مرة واحدة)"""
        if self.notifier is None:
            self.notifier = Notifier(self.page)

    def _show_main(self):
        c=self.C; self.page.bgcolor=c["bg"]

        # Initialize overlay components
        self._init_overlay()

        self.nav=ft.NavigationBar(selected_index=self.nav_idx,on_change=self._on_nav,
            destinations=[
                ft.NavigationBarDestination(icon=IC['home'],label=L("الرئيسية")),
                ft.NavigationBarDestination(icon=IC['history'],label=L("السجل")),
                ft.NavigationBarDestination(icon=IC['store'],label=L("المتجر")),
                ft.NavigationBarDestination(icon=IC['news'],label=L("الأخبار")),
                ft.NavigationBarDestination(icon=IC['settings'],label=L("الحساب")),
                ft.NavigationBarDestination(icon=IC['info'],label=L("عن التطبيق"))],
            bgcolor=c["bg"],indicator_color=c["accent"])
        self.content=ft.Container(expand=True,bgcolor=c["bg"])
        hdr=ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(content=self.theme_btn,border_radius=8,
                        bgcolor=c["chip_off"],border=_border(1,_op(c["txt2"],.3)),padding=_pad_sym(2,2)),
                    ft.Container(content=ft.Text(self.lang,size=11,
                        weight=_e("FontWeight","BOLD","bold"),color=c["accent"]),
                        padding=_pad_sym(10,7),border_radius=8,bgcolor=c["chip_off"],
                        border=_border(1,c["accent"]),on_click=self._toggle_lang)],spacing=6),
                ft.Column([ft.Text("Your Dream",size=15,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                           ft.Text("AI CHART ANALYST",size=8,color=c["txt2"])],
                    horizontal_alignment=_e("CrossAxisAlignment","CENTER","center"),spacing=0),
                ft.CircleAvatar(
                    content=ft.Text((self.user.get("full_name") or "U")[0].upper(),
                        size=13,weight=_e("FontWeight","BOLD","bold"),color=c["bg"]),
                    bgcolor=c["accent"],radius=16)],
                alignment=_e("MainAxisAlignment","SPACE_BETWEEN","spaceBetween")),
            padding=_pad_sym(14,9),bgcolor=c["bg"])
        layout=ft.Column([hdr,self.content,self.nav],spacing=0,expand=True)
        self.page.views.clear()
        self.page.views.append(ft.View(route="/",bgcolor=c["bg"],controls=[layout],padding=_pad_sym(0,0)))
        self._update_tab(self.nav_idx); self.page.update(); self._start_bg()

    def _on_nav(self,e):
        self.nav_idx=e.control.selected_index; self._update_tab(self.nav_idx)

    def _update_tab(self,idx):
        tabs=[self._tab_home,self._tab_history,self._tab_store,self._tab_news,self._tab_settings,self._tab_about]
        if 0<=idx<len(tabs): self.content.content=tabs[idx]()
        self.page.update()

    def _start_bg(self):
        if self._bg: return
        self._bg=True
        if not hasattr(self,'_last_trade_check'): self._last_trade_check=0
        def _run():
            while self._bg:
                try:
                    if self.user:
                        for a in self.cal.fetch(7):
                            mins=a.get("minutes_until",-1)
                            if a["impact"]=="High" and 0<mins<=30:
                                k=f"{a['event']}_{a['datetime'].isoformat()}"
                                if k not in self._alerted:
                                    ev_disp = PICK(a["event"], a.get("event_en", a["event"]))
                                    self.notifier.show(
                                        PICK("⚠️ خبر مهم بعد 30 دقيقة","⚠️ Important news in 30 min"),
                                        PICK(f"{ev_disp} ({a['currency']}) بعد {int(mins)} د",
                                             f"{ev_disp} ({a['currency']}) in {int(mins)} min"),
                                        IC['bell'],"#ef5350",12)
                                    self._alerted.add(k)

                        # ✅ تحليل "هل الوقت الآن جيد للتداول؟" عبر Gemini كل 4 ساعات
                        # (فقط طالما التطبيق مفتوح - بدون إشعارات بعد إغلاقه، كما طُلب)
                        now_ts = time.time()
                        if now_ts - self._last_trade_check >= 4*3600:
                            self._last_trade_check = now_ts
                            def _check_time():
                                try:
                                    sess = self.trd.info()
                                    upcoming = [e for e in self.cal.fetch(1) if 0 < e.get("minutes_until",-1) <= 240]
                                    res = self.ai.check_good_time(sess, upcoming, self.lang)
                                    if res and res.get("good_time"):
                                        self.notifier.show(
                                            PICK("✅ الوقت الآن جيد جداً للتداول","✅ Now is a great time to trade"),
                                            PICK(res.get("reason","سيولة جيدة الآن"),
                                                 res.get("reason","Good liquidity right now")),
                                            IC['bolt'],"#69f0ae",10)
                                except Exception as ex:
                                    print(f"[BG] good-time check failed: {ex}")
                            threading.Thread(target=_check_time,daemon=True).start()
                except: pass
                time.sleep(60)
        threading.Thread(target=_run,daemon=True).start()

    # -------- COUNTDOWN CARD --------
    def _countdown_card(self, user):
        c=self.C; tier=user.get("tier","free_trial")
        tn=Cfg.TIERS.get(tier,{}).get("label","?"); cd=calc_countdown(user.get("expiry"))
        bc=(c["red"] if cd["expired"] or cd["days"]<=3 else
            c["orange"] if cd["days"]<=7 else c["accent"])
        cam_used=int(user.get("camera_used",0) or 0)
        cam_lim=Cfg.TIERS.get(tier,{}).get("camera_quota",0)
        def _box(val,lbl):
            return ft.Container(
                content=ft.Column([
                    ft.Text(str(val),size=22,weight=_e("FontWeight","BOLD","bold"),color=bc),
                    ft.Text(lbl,size=8,color=c["txt2"])],
                    horizontal_alignment=_e("CrossAxisAlignment","CENTER","center"),spacing=0),
                padding=_pad_sym(12,6),border_radius=10,
                bgcolor=_op(bc,.12),border=_border(1,_op(bc,.3)))
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(L("نشط") if not cd["expired"] else L("منتهي"),
                        size=9,weight=_e("FontWeight","BOLD","bold"),color="#000"),
                        bgcolor=bc,padding=_pad_sym(8,2),border_radius=8),
                    ft.Text(L(tn),size=18,weight=_e("FontWeight","BOLD","bold"),color=c["txt"])],
                    alignment=_e("MainAxisAlignment","SPACE_BETWEEN","spaceBetween")),
                ft.Column([
                    ft.Text(L("ينتهي الاشتراك") if not cd["expired"] else L("انتهى الاشتراك"),
                        size=9,color=c["txt2"]),
                    ft.Row([_box(cd["days"],L("يوم")),ft.Text(":",size=16,color=c["txt2"]),
                            _box(cd["hours"],L("ساعة")),ft.Text(":",size=16,color=c["txt2"]),
                            _box(cd["mins"],L("دقيقة"))],
                        alignment=_e("MainAxisAlignment","CENTER","center"),spacing=6)],
                    spacing=4,horizontal_alignment=_e("CrossAxisAlignment","CENTER","center")),
                ft.ProgressBar(value=cd["pct"],color=bc,bgcolor=_op("#ffffff",.1),height=4,border_radius=2),
                ft.Row([
                    ft.Row([ft.Icon(IC['camera'],size=12,color=c["accent"]),
                            ft.Text(PICK(f"تحاليل: {cam_used}/{cam_lim}",f"Analyses: {cam_used}/{cam_lim}"),size=10,color=c["txt2"])],spacing=3),
                    ft.Text(PICK(f"{max(0,cam_lim-cam_used)} متبقي",f"{max(0,cam_lim-cam_used)} left"),size=10,color=c["accent"],
                        weight=_e("FontWeight","BOLD","bold"))],
                    alignment=_e("MainAxisAlignment","SPACE_BETWEEN","spaceBetween"))],
                spacing=8),
            padding=_pad_sym(16,16),border_radius=20,
            gradient=ft.LinearGradient(begin=_align("top_left"),end=_align("bottom_right"),
                colors=[self.C["grad1"],self.C["grad2"]]),
            border=_border(1.5,_op(bc,.4)))

    # -------- TAB HOME --------
    def _tab_home(self):
        c=self.C; user=self.db.get(self.user["id"])
        self.db.reset_camera(user["id"]); user=self.db.get(self.user["id"])
        tier=user.get("tier","free_trial")
        lim=Cfg.TIERS.get(tier,{}).get("camera_quota",0)
        cam_used=int(user.get("camera_used",0) or 0); cam_rem=max(0,lim-cam_used)
        tr=self.trd.info()

        def _sc(cat):
            def h(e): self.sel_cat=cat; self.sel_pair=self.PM[self.CATS[cat][0]]; self._pair_selected=True; self._update_tab(0)
            return h
        def _sp(pd):
            def h(e): self.sel_pair=self.PM[pd]; self._pair_selected=True; self._update_tab(0)
            return h
        def _st(a):
            def h(e): self.sel_tt=self.TT[a]; self._update_tab(0)
            return h

        ci={"فوركس":"💱","معادن":"⚡","مؤشرات":"📊","كريبتو":"₿"}
        cat_row=ft.Row([ft.Container(
            content=ft.Row([ft.Text(ci.get(cat,""),size=14),
                ft.Text(L(cat),size=11,
                    weight=_e("FontWeight","BOLD","bold") if cat==self.sel_cat else _e("FontWeight","W_400","w400"),
                    color=c["chip_on_txt"] if cat==self.sel_cat else c["chip_off_txt"])],spacing=4),
            padding=_pad_sym(12,9),border_radius=25,
            bgcolor=c["chip_on"] if cat==self.sel_cat else c["chip_off"],
            on_click=_sc(cat),
            border=_border(1,c["accent"] if cat==self.sel_cat else "transparent"))
            for cat in self.CATS],scroll=_e("ScrollMode","AUTO","auto"),spacing=6)

        pair_row=ft.Row([self._chip(p,self.PM[p]==self.sel_pair,_sp(p),small=True)
            for p in self.CATS[self.sel_cat]],scroll=_e("ScrollMode","AUTO","auto"),spacing=4)
        type_row=ft.Row([self._chip(tp,self.TT[tp]==self.sel_tt,_st(tp)) for tp in self.TT],spacing=8)

        pn=[k for k,v in self.PM.items() if v==self.sel_pair]
        pair_name=pn[0] if pn else self.sel_pair

        badge=ft.Container(
            content=ft.Row([ft.Icon(IC['chart'],size=16,color=c["accent"]),
                ft.Text(L("الزوج المختار:"),size=11,color=c["txt2"]),
                ft.Container(content=ft.Text(pair_name,size=13,
                    weight=_e("FontWeight","BOLD","bold"),color="#000"),
                    bgcolor=c["accent"],padding=_pad_sym(10,3),border_radius=12),
                ft.Text(f"| {self.sel_tt}",size=11,color=c["txt2"])],spacing=6),
            padding=_pad_sym(12,8),border_radius=12,bgcolor=c["card"],
            border=_border(1,_op(c["accent"],.5)))

        if self._cam_b64:
            img_inner=ft.Stack([
                ft.Image(src=f"data:image/jpeg;base64,{self._cam_b64}",fit=_e("ImageFit","CONTAIN","contain"),
                    border_radius=12,expand=True),
                ft.Container(content=ft.Row([ft.Icon(IC['camera'],size=12,color="#fff"),
                    ft.Text(L("اضغط لتغيير الصورة"),size=9,color="#fff")],spacing=4),
                    alignment=_align("bottom_center"),padding=_pad_only(b=8))])
        else:
            hc=c["orange"] if not self._pair_selected else c["accent"]
            hi=IC['warn'] if not self._pair_selected else IC['camera']
            ht=(L("اختر الزوج أولاً\nثم ارفع صورة الجارت") if not self._pair_selected
                else L("اضغط هنا لرفع صورة الجارت"))
            img_inner=ft.Column([ft.Icon(hi,size=52,color=_op(hc,.5)),
                ft.Text(ht,size=12,color=c["txt2"],text_align=_e("TextAlign","CENTER","center"))],
                alignment=_e("MainAxisAlignment","CENTER","center"),
                horizontal_alignment=_e("CrossAxisAlignment","CENTER","center"))

        # ✅ Camera + Gallery buttons
        cam_btn = ft.ElevatedButton(
            content=ft.Row([ft.Icon(IC['camera'],size=16),ft.Text(L("التقاط"),size=12)],spacing=4),
            style=ft.ButtonStyle(bgcolor=c["accent"],color="#000",padding=_pad_sym(12,8)),
            on_click=lambda e: self.page.run_task(self._capture_camera, e),
            disabled=not self._pair_selected,
        )

        gal_btn = ft.ElevatedButton(
            content=ft.Row([ft.Icon(IC['upload'],size=16),ft.Text(L("رفع"),size=12)],spacing=4),
            style=ft.ButtonStyle(bgcolor=_op(c["accent"],.7),color="#000",padding=_pad_sym(12,8)),
            on_click=lambda e: self.page.run_task(self._pick_file_dialog, e),
            disabled=not self._pair_selected,
        )

        img_box=ft.Container(width=float("inf"),height=200,border_radius=14,bgcolor=c["card"],
            border=_border(2, _op(c["accent"],.6) if self._cam_b64 else
                _op(c["orange"],.5) if not self._pair_selected else _op(c["accent"],.4)),
            content=img_inner,
            on_click=lambda e: self.page.run_task(self._pick_file_dialog, e) if self._pair_selected else None)

        ring=ft.ProgressRing(color=c["accent"],width=28,height=28,stroke_width=3,visible=False)
        stxt=ft.Text("",size=11,color=c["txt2"],text_align=_e("TextAlign","CENTER","center"))
        rcol=ft.Column([],spacing=8)

        def _analyze(e):
            if not self._pair_selected: stxt.value=L("❗ اختر الزوج أولاً"); self.page.update(); return
            if cam_rem<=0: stxt.value=L("تجاوزت حصتك! قم بترقية باقتك."); self.page.update(); return
            if not self._cam_b64: stxt.value=L("اختر صورة الجارت أولاً"); self.page.update(); return
            ring.visible=True; stxt.value=L("جارٍ تحليل الجارت بالذكاء الاصطناعي..."); rcol.controls.clear(); self.page.update()
            def _work():
                try:
                    res=self.ai.analyze(self._cam_b64, self.sel_pair, self.sel_tt, self.lang)
                    # Handle None response (all models failed)
                    if res is None:
                        stxt.value=L("⚠️ فشل الاتصال بـ AI - تحقق من الإنترنت")
                        ring.visible=False
                        self.page.update()
                        return
                    dir_raw=str(res.get("direction","")).strip().lower()
                    no_trade=dir_raw in {"","none","no","no trade","notrade","n/a","wait","neutral","لا توجد فرصة","انتظار","-"}
                    if not no_trade:
                        if not self.db.inc_camera(user["id"]):
                            stxt.value=L("تجاوزت حصتك!"); ring.visible=False; self.page.update(); return
                        self.db.log_camera(user["id"],self.sel_pair,self.sel_tt,json.dumps(res,ensure_ascii=False))
                        fresh=self.db.get(user["id"])
                        if fresh: self.user=fresh
                    else:
                        self.notifier.show(L("ℹ️ لا توجد فرصة مناسبة"),
                            L("لم يتم خصم نقطة من حصتك"),IC['info'],"#448aff",5)
                    rcol.controls.clear(); rcol.controls.append(self._result_card(res, no_trade))
                    stxt.value=""
                except Exception as ex: 
                    rcol.controls.append(ft.Text(PICK(f"خطأ: {ex}",f"Error: {ex}"),color=c["red"]))
                    stxt.value=""
                finally: ring.visible=False
                try: self.page.update()
                except: pass
            threading.Thread(target=_work,daemon=True).start()

        tr_card=ft.Container(
            content=ft.Row([ft.Icon(IC['clock'],color=c["accent"],size=14),
                ft.Column([ft.Text(PICK(tr["rec"],AR_EN.get(tr["rec"],tr["rec"])),size=11,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                    ft.Text(PICK(f"الجلسات: {', '.join(tr['active']) or 'هادئة'}",
                                 f"Sessions: {', '.join(AR_EN.get(s,s) for s in tr['active']) or 'quiet'}"),size=9,color=c["txt2"])],
                    spacing=1,expand=True),
                ft.Text(tr["time"],size=14,color=c["accent"],weight=_e("FontWeight","BOLD","bold"))],spacing=8),
            padding=_pad_sym(10,10),border_radius=12,bgcolor=c["card"],
            border=_border(1,_op("#ffffff" if self.is_dark else "#000000",.1)))

        quota_bar=ft.Container(
            content=ft.Row([
                ft.Icon(IC['camera'],size=13,color=c["green"] if cam_rem>0 else c["red"]),
                ft.Text(PICK(f"حصة التحاليل اليومية: {cam_used}/{lim}",f"Daily analysis quota: {cam_used}/{lim}"),size=11,
                    color=c["green"] if cam_rem>0 else c["red"]),
                ft.Container(content=ft.Text(PICK(f"{cam_rem} متبقي",f"{cam_rem} left"),size=9,color="#000"),
                    bgcolor=c["green"] if cam_rem>0 else c["red"],padding=_pad_sym(7,2),border_radius=8)
            ],spacing=6),
            padding=_pad_sym(8,8),border_radius=10,bgcolor=c["card"],
            border=_border(1,_op(c["green"] if cam_rem>0 else c["red"],.3)))

        return ft.Container(expand=True,padding=_pad_sym(14,8),bgcolor=c["bg"],
            content=ft.Column([
                self._countdown_card(user),ft.Container(height=6),tr_card,ft.Container(height=8),
                ft.Text(L("تحليل بالذكاء الاصطناعي"),size=14,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                ft.Container(height=2),
                ft.Row([ft.Icon(IC['filter'],size=14,color=c["txt2"]),ft.Text(L("الفئة:"),size=10,color=c["txt2"])],spacing=4),
                cat_row,ft.Container(height=4),
                ft.Row([ft.Icon(IC['chart'],size=14,color=c["txt2"]),ft.Text(L("اختر الزوج:"),size=10,color=c["txt2"])],spacing=4),
                pair_row,ft.Container(height=4),
                ft.Row([ft.Icon(IC['bolt'],size=14,color=c["txt2"]),ft.Text(L("نوع التداول:"),size=10,color=c["txt2"])],spacing=4),
                type_row,ft.Container(height=6),badge,ft.Container(height=6),img_box,ft.Container(height=6),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([ft.Icon(IC['upload'],color=c["btn_txt"],size=16),
                            ft.Text(L("📷 رفع صورة"),size=11,weight=_e("FontWeight","BOLD","bold"),color=c["btn_txt"])],
                            spacing=5,alignment=_e("MainAxisAlignment","CENTER","center")),
                        style=ft.ButtonStyle(bgcolor=c["btn"],shape=ft.RoundedRectangleBorder(radius=20),padding=_pad_sym(10,12)),
                        on_click=lambda e: self.page.run_task(self._pick_file_dialog, e),expand=True),
                    ft.ElevatedButton(
                        content=ft.Row([ft.Icon(IC['deal'],color="#000",size=16),
                            ft.Text(L("🤖 تحليل"),size=11,weight=_e("FontWeight","BOLD","bold"),color="#000")],
                            spacing=5,alignment=_e("MainAxisAlignment","CENTER","center")),
                        style=ft.ButtonStyle(bgcolor=c["accent"],shape=ft.RoundedRectangleBorder(radius=20),padding=_pad_sym(10,12)),
                        on_click=_analyze,expand=True)],spacing=8),
                quota_bar,
                ft.Row([ring,stxt],spacing=8,alignment=_e("MainAxisAlignment","CENTER","center")),
                rcol],
                spacing=0,scroll=_e("ScrollMode","AUTO","auto"),expand=True))


    def _result_card(self, res, no_trade=False):
        c=self.C; pn=[k for k,v in self.PM.items() if v==self.sel_pair]; pname=pn[0] if pn else self.sel_pair

        # Check if this is a simulated/fake result
        is_simulated = "SIMULATED" in str(res.get("source","")) or "اتصال AI فاشل" in str(res.get("source",""))

        if no_trade:
            return self._glass(ft.Column([
                ft.Row([ft.Icon(IC['info'],color="#448aff",size=16),
                    ft.Text(PICK(f"تحليل {pname} - {self.sel_tt}",f"{pname} Analysis - {self.sel_tt}"),size=12,
                        weight=_e("FontWeight","BOLD","bold"),color=c["txt"])],spacing=6),
                ft.Divider(height=1,color=_op("#ffffff",.12)),
                ft.Container(content=ft.Row([ft.Icon(IC['warn'],size=18,color="#ffd740"),
                    ft.Text(L("لا توجد فرصة مناسبة الآن"),size=14,
                        weight=_e("FontWeight","BOLD","bold"),color="#ffd740",expand=True)],spacing=6),
                    padding=_pad_sym(10,10),bgcolor=_op("#ffd740",.1),border_radius=8),
                ft.Container(content=ft.Row([ft.Icon(IC['check'],size=12,color=c["green"]),
                    ft.Text(L("لم يتم خصم نقطة من حصتك"),size=10,color=c["green"],expand=True)],spacing=5),
                    padding=_pad_sym(8,5),bgcolor=_op(c["green"],.08),border_radius=7)],spacing=8),pad=12)

        d=res.get("direction","?"); is_buy=d=="Buy"
        dc=c["green"] if is_buy else c["red"]; arr="▲" if is_buy else "▼"

        # If simulated, show warning color
        if is_simulated:
            dc = c["orange"]

        def ch(l,v,cl):
            return ft.Container(content=ft.Column([ft.Text(l,size=8,color=c["txt2"]),
                ft.Text(str(v),size=12,weight=_e("FontWeight","BOLD","bold"),color=cl)],
                horizontal_alignment=_e("CrossAxisAlignment","CENTER","center"),spacing=1),
                padding=_pad_sym(10,7),bgcolor=_op("#ffffff" if self.is_dark else "#000000",.06),
                border_radius=8,expand=True)
        def tag(t,bg): return ft.Container(content=ft.Text(t,size=9,color="#000" if self.is_dark else "#fff",
            weight=_e("FontWeight","BOLD","bold")),bgcolor=bg,padding=_pad_sym(7,3),border_radius=8)

        extra=[]

        # ⚠️ SIMULATED warning banner
        if is_simulated:
            extra.append(ft.Container(
                content=ft.Row([
                    ft.Icon(IC['warn'],size=16,color=c["orange"]),
                    ft.Text(L("⚠️ تحليل وهمي - لا تعتمد عليه للتداول الحقيقي"),size=11,
                        color=c["orange"],weight=_e("FontWeight","BOLD","bold"),expand=True)
                ],spacing=6),
                padding=_pad_sym(10,8),bgcolor=_op(c["orange"],.12),
                border=_border(1.5,c["orange"]),border_radius=10
            ))
            extra.append(ft.Container(
                content=ft.Text(
                    PICK("السبب: فشل الاتصال بخادم الذكاء الاصطناعي.\n"
                    "• تأكد من الاتصال بالإنترنت\n"
                    "• تأكد من صلاحية مفتاح API\n"
                    "• جرّب استخدام VPN",
                    "Reason: failed to connect to the AI server.\n"
                    "• Check your internet connection\n"
                    "• Make sure the API key is valid\n"
                    "• Try using a VPN"),
                    size=10,color=c["txt2"],text_align=_e("TextAlign","RIGHT","right")
                ),
                padding=_pad_sym(10,8),bgcolor=_op("#ffffff",.04),border_radius=8
            ))

        # ✅ لا نعرض أي شرح أو تحليل نصي للصفقة للمستخدم إطلاقاً (منطقة رئيسية/
        # ملاحظة إضافية/موقع السعر/السبب) - فقط الأرقام الأساسية للصفقة
        source_text = L("تحليل ذكي") if not is_simulated else L("تحليل تجريبي")
        source_bg = _op(c["orange"],.3) if is_simulated else _op("#448aff",.3)

        return self._glass(ft.Column([
            ft.Row([ft.Icon(IC['deal'],color=c["accent"],size=16),
                ft.Text(PICK(f"تحليل {pname} - {self.sel_tt}",f"{pname} Analysis - {self.sel_tt}"),size=12,
                    weight=_e("FontWeight","BOLD","bold"),color=c["txt"])],spacing=6),
            ft.Divider(height=1,color=_op("#ffffff",.12)),
            ft.Row([ft.Text(f"{arr} {d}",size=20,weight=_e("FontWeight","BOLD","bold"),color=dc),
                ft.Row([tag(PICK(f"نجاح: {res.get('success_rate','?')}",f"Success: {res.get('success_rate','?')}"),_op(dc,.4)),
                    tag(source_text,source_bg)],spacing=5)],
                alignment=_e("MainAxisAlignment","SPACE_BETWEEN","spaceBetween")),
            ft.Row([tag(PICK('صاعد 📈' if res.get('structure')=='bullish' else 'هابط 📉',
                             'Bullish 📈' if res.get('structure')=='bullish' else 'Bearish 📉'),
                _op("#64ffda" if res.get("structure")=="bullish" else "#ff5252",.2)),
                tag(f"RR: {res.get('rr','?')}",_op("#ffd740",.2))],spacing=6),
            ft.Divider(height=1,color=_op("#ffffff",.08)),
            ft.Row([ch(L("نقطة الدخول"),res.get("entry","?"),"#448aff"),ch(L("وقف الخسارة"),res.get("sl","?"),c["red"])],spacing=5),
            ft.Row([ch(L("الهدف"),res.get("tp",res.get("tp1","?")),c["green"])],spacing=5),
            *extra],spacing=7),pad=12)

    # -------- TAB HISTORY --------
    def _tab_history(self):
        c=self.C; hist=self.db.history(self.user["id"]); items=[]
        for h in hist:
            try:
                rec=json.loads(h["rec"]); d=rec.get("direction","?")
                is_buy=d=="Buy"; dc=c["green"] if is_buy else c["red"]; arr="▲" if is_buy else "▼"
                items.append(ft.Container(
                    content=ft.Row([
                        ft.Container(content=ft.Text(arr,size=14,color=dc,
                            weight=_e("FontWeight","BOLD","bold")),width=24),
                        ft.Column([
                            ft.Text(f"{h['pair']} | {h.get('tt','')}",size=12,
                                weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                            ft.Text(PICK(f"دخول:{rec.get('entry','?')} SL:{rec.get('sl','?')}",
                                         f"Entry:{rec.get('entry','?')} SL:{rec.get('sl','?')}"),size=10,color=c["txt2"]),
                            ft.Text((h["at"] or "")[:16],size=9,color=c["txt3"])],expand=True,spacing=2),
                        ft.Container(content=ft.Text(rec.get("rr",""),size=10,color="#ffd740"),
                            padding=_pad_sym(6,3),bgcolor=_op("#ffd740",.1),border_radius=6)],spacing=8),
                    padding=_pad_sym(10,10),border_radius=10,bgcolor=c["card"],
                    border=_border(1,_op("#ffffff" if self.is_dark else "#000000",.08))))
            except: continue
        return ft.Container(expand=True,padding=_pad_sym(14,10),bgcolor=c["bg"],
            content=ft.Column([
                ft.Text(L("السجل"),size=18,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                ft.Text(PICK(f"{len(items)} توصية سابقة",f"{len(items)} previous recommendation(s)"),size=11,color=c["txt2"]),
                ft.Divider(color=c["divider"]),
                *(items if items else [ft.Text(L("لا توجد توصيات سابقة"),color=c["txt2"],
                    text_align=_e("TextAlign","CENTER","center"))])],
                spacing=6,scroll=_e("ScrollMode","AUTO","auto"),expand=True))

    # -------- TAB STORE --------
    def _tab_store(self):
        c=self.C; user=self.db.get(self.user["id"])
        kf=ft.TextField(label=L("🔑 تنشيط بمفتاح"),hint_text="yd10_xxxx / yd30_xxxx / yd75_xxxx",
            border_radius=10,filled=True,prefix_icon=IC['key'],
            border_color=_op("#ffffff",.18),focused_border_color=c["accent"],text_size=13)
        kst=ft.Text("",size=11)
        def _act(e):
            ok,msg,tier=self.db.activate(user["id"],kf.value,dev=self.dev_id,email=user.get("email",""))
            kst.value=L(msg); kst.color=c["green"] if ok else c["red"]
            if ok:
                self.user=self.db.get(user["id"])
                self.notifier.show(L("✅ تم التفعيل!"),PICK(f"باقة {tier.upper()}",f"{tier.upper()} Plan"),IC['check'],"#69f0ae",5)
                self._update_tab(2)
            self.page.update()
        def _tg(e): self.page.launch_url(Cfg.TG_URL)
        cm={"free_trial":"#9e9e9e","basic":"#448aff","advanced":"#64ffda","vip":"#e040fb"}
        cards=[]
        for tk,ti in Cfg.TIERS.items():
            if tk in ("admin_unlimited","user30_special"): continue
            tc=cm.get(tk,"#888"); is_cur=user.get("tier")==tk
            cards.append(ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text(L(ti["label"]),size=14,weight=_e("FontWeight","BOLD","bold"),color=tc),
                        ft.Text(f"${ti['price']}/{L('شهر')}" if ti["price"]>0 else L("مجاناً"),size=13,color=c["txt"])],
                        alignment=_e("MainAxisAlignment","SPACE_BETWEEN","spaceBetween")),
                    ft.Row([ft.Row([ft.Icon(IC['camera'],size=12,color=tc),
                        ft.Text(PICK(f"{ti['camera_quota']} تحليل/يوم",f"{ti['camera_quota']} analyses/day"),size=11,color=c["txt2"])],spacing=3),
                        ft.Row([ft.Icon(IC['clock'],size=12,color=tc),
                        ft.Text(PICK(f"{ti['days']} يوم",f"{ti['days']} days"),size=11,color=c["txt2"])],spacing=3)],spacing=14),
                    ft.ElevatedButton(L("الباقة الحالية ✓") if is_cur else L("اطلب عبر تليجرام"),
                        style=ft.ButtonStyle(bgcolor=_op(tc,.2) if is_cur else tc,
                            color=c["txt"] if is_cur else "#000",
                            shape=ft.RoundedRectangleBorder(radius=12),padding=_pad_sym(12,8)),
                        on_click=(lambda e:None) if is_cur else _tg,width=float("inf"))],spacing=7),
                padding=_pad_sym(14,14),border_radius=12,bgcolor=c["card"],
                border=_border(1.5,_op(tc,.5) if is_cur else _op(tc,.25))))
        return ft.Container(expand=True,padding=_pad_sym(14,10),bgcolor=c["bg"],
            content=ft.Column([
                ft.Text(L("الباقات والتنشيط"),size=18,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                ft.Text(PICK(f"الباقة الحالية: {Cfg.TIERS.get(user.get('tier','free_trial'),{}).get('label','')}",
                             f"Current plan: {L(Cfg.TIERS.get(user.get('tier','free_trial'),{}).get('label',''))}"),
                    size=11,color=c["accent"]),
                ft.Divider(color=c["divider"]),*cards,
                self._glass(ft.Column([
                    ft.Text(L("🔑 تنشيط بمفتاح"),size=13,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                    kf,ft.ElevatedButton(L("تنشيط الآن"),icon=IC['verified'],
                        style=ft.ButtonStyle(bgcolor=c["accent"],color=c["bg"],
                            shape=ft.RoundedRectangleBorder(radius=12),padding=_pad_sym(14,10)),
                        on_click=_act,width=float("inf")),kst],spacing=8),pad=14),
                self._glass(ft.Column([
                    ft.Text(L("📱 تليجرام للدفع"),size=13,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                    ft.Row([ft.Icon(IC['tg'],color=c["accent"]),
                        ft.Text(f"@{Cfg.TG_USER}",size=12,color=c["txt"],expand=True),
                        ft.IconButton(IC['launch'],icon_color=c["accent"],on_click=_tg)],spacing=6)],spacing=6),pad=14)],
                spacing=10,scroll=_e("ScrollMode","AUTO","auto"),expand=True))

    # -------- TAB NEWS --------
    def _tab_news(self):
        c=self.C
        nc=ft.Column([],spacing=6,scroll=_e("ScrollMode","AUTO","auto"),expand=True)
        loading=ft.Row([ft.ProgressRing(color=c["accent"],width=24,height=24)],
            alignment=_e("MainAxisAlignment","CENTER","center"))
        fm={0:L("اليوم"),1:L("غداً"),7:L("هذا الأسبوع")}; fdm={0:0.9,1:2,7:7}

        # Currency name mapping for display
        curr_names = Calendar.CURRENCY_AR
        # ✅ قفل يمنع تشغيل أكثر من عملية تحميل بنفس الوقت (كان سبب تكرار
        # الأخبار الفعلي: الضغط على "تحديث" أثناء تحميل أول يخلي الاثنين
        # يضيفوا عناصر لنفس القائمة nc.controls بدون ما يمسحوا بعض)
        if not hasattr(self,'_news_loading'): self._news_loading=False
        def _build_fr():
            return ft.Row([ft.Container(
                content=ft.Row([
                    ft.Icon(IC['today'] if k==0 else IC['bell'] if k==1 else IC['week'],size=13,
                        color="#000" if self.news_filter==k else c["txt2"]),
                    ft.Text(v,size=11,
                        weight=_e("FontWeight","BOLD","bold") if self.news_filter==k else _e("FontWeight","W_400","w400"),
                        color="#000" if self.news_filter==k else c["txt2"])],spacing=4),
                padding=_pad_sym(12,8),border_radius=20,
                bgcolor=c["accent"] if self.news_filter==k else c["chip_off"],
                border=_border(1,c["accent"] if self.news_filter==k else "transparent"),
                on_click=self._make_nf(k,nc,loading)) for k,v in fm.items()],spacing=6)
        def _load(days=None):
            if self._news_loading: return   # ✅ يمنع تشغيل تحميل ثانٍ فوق الأول
            self._news_loading=True
            try:
                dtf=fdm.get(self.news_filter,2)
                nc.controls.clear(); nc.controls.append(loading)
                try: self.page.update()
                except: pass
                try: items=self.cal.fetch(int(dtf))
                except: items=[]
                nc.controls.clear(); now=datetime.datetime.now()
                _render_news(items, nc, c, curr_names, now)
            finally:
                self._news_loading=False
                try: self.page.update()
                except: pass

        def _render_news(items, nc, c, curr_names, now):
            if self.news_filter==0: filtered=[i for i in items if i["datetime"].date()==now.date()]
            elif self.news_filter==1:
                tmr=(now+datetime.timedelta(days=1)).date()
                filtered=[i for i in items if i["datetime"].date() in (now.date(),tmr)]
            else: filtered=items
            if not filtered:
                nc.controls.append(ft.Text(L("لا أخبار متاحة"),color=c["txt2"],
                    text_align=_e("TextAlign","CENTER","center"),size=13))
            else:
                by_d={}
                for it in filtered:
                    dk=it["datetime"].strftime("%Y-%m-%d"); by_d.setdefault(dk,[]).append(it)
                dn={1:L("الاثنين"),2:L("الثلاثاء"),3:L("الأربعاء"),4:L("الخميس"),5:L("الجمعة"),6:L("السبت"),0:L("الأحد")}
                for dk in sorted(by_d.keys()):
                    dto=datetime.datetime.strptime(dk,"%Y-%m-%d")
                    if dto.date()==now.date(): dl=f"📅 {L('اليوم')} - {dto.strftime('%d %b')}"
                    elif dto.date()==(now+datetime.timedelta(days=1)).date(): dl=f"📅 {L('غداً')} - {dto.strftime('%d %b')}"
                    else: dl=f"📅 {dn.get(dto.weekday(),'')} - {dto.strftime('%d %b')}"
                    nc.controls.append(ft.Container(content=ft.Row([
                        ft.Container(width=3,height=18,bgcolor=c["accent"],border_radius=2),
                        ft.Text(dl,size=12,weight=_e("FontWeight","BOLD","bold"),color=c["accent"])],spacing=8),
                        padding=_pad_only(t=8,b=4)))
                    for it in by_d[dk]:
                        imp=it["impact"]; ic="#ef5350" if imp=="High" else "#ffca28"
                        mins=it.get("minutes_until",0)
                        if mins>0:
                            if mins<=30: tc="#ef5350"; tl=PICK(f"⚠️ بعد {int(mins)} دقيقة", f"⚠️ in {int(mins)} min")
                            elif mins<=60: tc="#ffca28"; tl=PICK(f"⏳ بعد {int(mins)} دقيقة", f"⏳ in {int(mins)} min")
                            elif mins<1440: tc="#66bb6a"; tl=PICK(f"⏳ بعد {int(mins//60)}س {int(mins%60)}د", f"⏳ in {int(mins//60)}h {int(mins%60)}m")
                            else: tc="#9e9e9e"; tl=PICK(f"📅 بعد {int(mins//1440)} يوم", f"📅 in {int(mins//1440)}d")
                        else: tc="#9e9e9e"; tl=PICK("✅ انتهى", "✅ Ended")
                        urgent=(0<mins<=30 and imp=="High")
                        nc.controls.append(ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(content=ft.Text(L(Calendar.IMPACT_AR.get(imp, imp)),size=8,weight=_e("FontWeight","BOLD","bold"),color="#000"),
                                        bgcolor=ic,padding=_pad_sym(5,1),border_radius=4),
                                    ft.Container(content=ft.Text(L(curr_names.get(it["currency"], it["currency"])),size=9,weight=_e("FontWeight","BOLD","bold"),color="#000"),
                                        bgcolor=c["accent"],padding=_pad_sym(6,1),border_radius=4),
                                    ft.Text(it["datetime"].strftime("%H:%M"),size=10,color=c["txt2"]),
                                    ft.Container(expand=True),
                                    ft.Text(tl,size=9,color=tc,weight=_e("FontWeight","BOLD","bold"))],spacing=5),
                                ft.Text(PICK(it["event"], it.get("event_en", it["event"])),size=12,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                                ft.Row([_stat_col(L("الفعلي"),it.get("actual","N/A"),"#81c784",c),
                                    _stat_col(L("التوقعات"),it.get("forecast","N/A"),"#64b5f6",c),
                                    _stat_col(L("السابق"),it.get("previous","N/A"),"#ffd54f",c)],spacing=0),
                                *([ft.Container(content=ft.Row([ft.Icon(IC['bell'],size=12,color="#ef5350"),
                                    ft.Text(L("خبر عاجل! ابتعد عن السوق"),size=9,color="#ef5350",
                                        weight=_e("FontWeight","BOLD","bold"))],spacing=4),
                                    padding=_pad_sym(6,3),bgcolor=_op("#ef5350",.1),border_radius=6)] if urgent else [])],spacing=5),
                            padding=_pad_sym(10,10),border_radius=10,
                            bgcolor=_op("#ef5350",.06) if urgent else c["card"],
                            border=_border(1.5 if urgent else 1,
                                "#ef5350" if urgent else _op("#ffffff" if self.is_dark else "#000000",.08))))
            try: self.page.update()
            except: pass
        threading.Thread(target=_load,daemon=True).start(); self._news_load=_load
        return ft.Container(expand=True,padding=_pad_sym(14,8),bgcolor=c["bg"],
            content=ft.Column([
                ft.Row([ft.Column([
                    ft.Text(L("الأخبار الاقتصادية"),size=17,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                    ft.Text(PICK("ForexFactory • بيانات حية","ForexFactory • Live Data"),size=9,color=c["txt2"])],spacing=1,expand=True),
                    ft.IconButton(IC['refresh'],icon_color=c["accent"],tooltip=L("تحديث"),
                        on_click=lambda e:threading.Thread(target=_load,daemon=True).start())],
                    alignment=_e("MainAxisAlignment","SPACE_BETWEEN","spaceBetween")),
                ft.Container(content=_build_fr()),
                ft.Container(content=ft.Row([ft.Icon(IC['warn'],color="#ef5350",size=13),
                    ft.Text(L("الأخبار العالية الأثر قد تسبب تقلبات. كن حذراً."),size=9,color=c["txt2"],expand=True)],spacing=5),
                    padding=_pad_sym(8,5),bgcolor=_op("#ef5350",.07),border_radius=7),
                ft.Divider(height=1,color=c["divider"]),
                ft.Container(content=nc,expand=True)],spacing=6,expand=True))

    def _make_nf(self, k, nc, loading):
        def h(e):
            self.news_filter=k
            if hasattr(self,'_news_load'): threading.Thread(target=self._news_load,daemon=True).start()
            self._update_tab(3)
        return h

    # -------- TAB SETTINGS --------
    def _tab_settings(self):
        c=self.C; user=self.db.get(self.user["id"])
        lim=Cfg.TIERS.get(user.get("tier","free_trial"),{}).get("camera_quota",0)
        cam_used=int(user.get("camera_used",0) or 0); cd=calc_countdown(user.get("expiry"))
        bc=(c["red"] if cd["days"]<=3 else c["orange"] if cd["days"]<=7 else c["accent"])
        def _ref(e):
            self.user=self.db.get(self.user["id"]); self._update_tab(4)
            self.notifier.show(L("🔄 تم"),L("بيانات محدثة"),IC['info'],"#448aff",3)
        return ft.Container(expand=True,padding=_pad_sym(14,10),bgcolor=c["bg"],
            content=ft.Column([
                ft.Text(L("الحساب"),size=18,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                self._glass(ft.Column([
                    ft.Row([ft.CircleAvatar(content=ft.Text((user.get("full_name") or "U")[0].upper(),
                        size=18,weight=_e("FontWeight","BOLD","bold"),color=c["bg"]),
                        bgcolor=c["accent"],radius=24),
                        ft.Column([ft.Text(user.get("full_name") or L("مستخدم"),size=15,
                            weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                            ft.Text(user.get("email",""),size=10,color=c["txt2"])],spacing=2,expand=True)],spacing=10),
                    ft.Text(PICK(f"🔐 الجهاز: {self.dev_id[:18]}...",f"🔐 Device: {self.dev_id[:18]}..."),size=10,color=c["accent"])],spacing=7)),
                self._glass(ft.Column([
                    ft.Text(L("حالة الاشتراك"),size=13,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                    ft.Row([ft.Text(L("الباقة:"),size=12,color=c["txt2"]),
                        ft.Text(L(Cfg.TIERS.get(user.get("tier",""),{}).get("label",user.get("tier",""))),
                            color=c["accent"],weight=_e("FontWeight","BOLD","bold"))],spacing=6),
                    ft.Row([ft.Text(L("المتبقي:"),size=12,color=c["txt2"]),
                        ft.Text(PICK(f"{cd['days']}د {cd['hours']}س {cd['mins']}ق",f"{cd['days']}d {cd['hours']}h {cd['mins']}m") if not cd["expired"] else L("منتهي"),
                            color=bc,weight=_e("FontWeight","BOLD","bold"))],spacing=6),
                    ft.ProgressBar(value=cd["pct"],color=bc,bgcolor=_op("#ffffff",.1),height=4,border_radius=2),
                    ft.Row([ft.Text(L("التحاليل:"),size=12,color=c["txt2"]),
                        ft.Text(PICK(f"{cam_used}/{lim} ({lim-cam_used} متبقي)",f"{cam_used}/{lim} ({lim-cam_used} left)"),
                            color=c["accent"],weight=_e("FontWeight","BOLD","bold"))],spacing=6)],spacing=6)),
                self._glass(ft.Column([
                    ft.Text(L("المظهر"),size=13,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                    ft.Row([ft.Text(L("الوضع الليلي") if self.is_dark else L("الوضع النهاري"),size=12,color=c["txt2"]),
                        ft.Switch(value=self.is_dark,on_change=self._toggle_theme,active_color=c["accent"])],
                        alignment=_e("MainAxisAlignment","SPACE_BETWEEN","spaceBetween"))],spacing=5)),
                ft.ElevatedButton(L("تحديث"),icon=IC['refresh'],
                    style=ft.ButtonStyle(bgcolor=c["accent"],color=c["bg"],
                        shape=ft.RoundedRectangleBorder(radius=10),padding=_pad_sym(0,12)),
                    on_click=_ref,width=float("inf")),
                ft.ElevatedButton(L("تسجيل الخروج"),icon=IC['logout'],
                    style=ft.ButtonStyle(bgcolor=c["red"],color="#fff",
                        shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e:self._logout()),
                ft.Text(f"{Cfg.APP} v{Cfg.VER}",size=9,color=c["txt3"],
                    text_align=_e("TextAlign","CENTER","center"))],
                spacing=10,scroll=_e("ScrollMode","AUTO","auto"),expand=True))

    # -------- TAB ABOUT (سياسة الخصوصية + التطوير) --------
    def _tab_about(self):
        c=self.C
        privacy_txt = PICK(
            """• يتم تخزين بياناتك الشخصية (البريد الإلكتروني، كلمة المرور) بشكل مشفر وآمن في قاعدة بيانات محلية على جهازك فقط.

• لا نقوم بمشاركة بياناتك مع أي طرف ثالث.

• يتم استخدام بيانات التحليل (صور الجارت) فقط لإرسالها إلى خدمة الذكاء الاصطناعي لإنتاج التحليل، ولا يتم حفظها على خوادمنا.

• يتم تخزين سجل التحاليل محلياً على جهازك فقط.

• التطبيق لا يجمع أي بيانات شخصية إضافية عن المستخدم.

• يمكنك حذف جميع بياناتك في أي وقت من خلال زر "مسح الكل" في شاشة تسجيل الدخول.""",
            """• Your personal data (email, password) is stored encrypted and securely in a local database on your device only.

• We do not share your data with any third party.

• Analysis data (chart images) is only used to send to the AI service to produce the analysis, and is not saved on our servers.

• Your analysis history is stored locally on your device only.

• The app does not collect any additional personal data about the user.

• You can delete all your data at any time via the "Erase All" button on the login screen.""")
        return ft.Container(expand=True,padding=_pad_sym(14,10),bgcolor=c["bg"],
            content=ft.Column([
                ft.Text(L("عن التطبيق"),size=18,weight=_e("FontWeight","BOLD","bold"),color=c["txt"]),
                ft.Divider(color=c["divider"]),
                self._glass(ft.Column([
                    ft.Row([ft.Icon(IC['info'],size=20,color=c["accent"]),
                        ft.Text(L("سياسة الخصوصية"),size=16,weight=_e("FontWeight","BOLD","bold"),color=c["txt"])],spacing=8),
                    ft.Container(height=6),
                    ft.Text(privacy_txt,
                        size=11,color=c["txt2"],text_align=_e("TextAlign","LEFT" if cur_lang()=="EN" else "RIGHT","left" if cur_lang()=="EN" else "right")),
                ],spacing=6),pad=16),
                ft.Container(height=10),
                self._glass(ft.Column([
                    ft.Row([ft.Icon(IC['star'],size=20,color=c["accent"]),
                        ft.Text(L("التطوير"),size=16,weight=_e("FontWeight","BOLD","bold"),color=c["txt"])],spacing=8),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(L("تمت البرمجة والتطوير بواسطة"),size=12,color=c["txt2"],
                                text_align=_e("TextAlign","CENTER","center")),
                            ft.Text("أحمد علاء",size=24,weight=_e("FontWeight","BOLD","bold"),color=c["accent"],
                                text_align=_e("TextAlign","CENTER","center")),
                            ft.Container(height=4),
                            ft.Text(f"{Cfg.APP} v{Cfg.VER}",size=11,color=c["txt3"],
                                text_align=_e("TextAlign","CENTER","center")),
                        ],horizontal_alignment=_e("CrossAxisAlignment","CENTER","center"),spacing=4),
                        padding=_pad_sym(20,16),border_radius=16,
                        bgcolor=_op(c["accent"],.08),
                        border=_border(1.5,_op(c["accent"],.3)),
                        alignment=_align("center"),
                        width=float("inf")
                    ),
                ],spacing=6),pad=16),
                ft.Container(height=10),
                ft.Text(L("© 2025-2026 جميع الحقوق محفوظة"),size=9,color=c["txt3"],
                    text_align=_e("TextAlign","CENTER","center"),width=float("inf")),
            ],spacing=0,scroll=_e("ScrollMode","AUTO","auto"),expand=True))

    def _logout(self):
        self._bg=False; self.user=None; self._cam_b64=None; self._pair_selected=False
        self.db.clear_session()
        self._show_login()


def main(page: ft.Page):
    try:
        App(page)
    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        # Show error on page
        page.add(ft.Text(f"Application startup error: {e}", color="red", size=16))
        page.update()

ft.app(target=main)
