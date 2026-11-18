# -*- coding: utf-8 -*-
"""
سامانه ثبت‌نام کارگاه‌های مرکز تحقیقات پزشکی ورزشی
اجرا:  pip install -r requirements.txt  سپس  python app.py
"""
import io
import os
import re
import sqlite3
from datetime import datetime

from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, send_file, send_from_directory, session, url_for)
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "registrations.db"))
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))

# ─── تنظیمات مدیریت ──────────────────────────────────────────────
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "sportmed1405")  # ← این رمز را حتماً تغییر دهید
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret")    # ← این هم تغییر دهید

DEGREES = ["کاردانی", "کارشناسی", "کارشناسی ارشد", "دکتری حرفه‌ای",
           "دکتری تخصصی (PhD)", "فوق‌دکتری", "سایر"]

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
TERMS = [f"ترم {i}".translate(FA_DIGITS) for i in range(1, 15)] + ["سایر"]

# ─── فایل رزومه ──────────────────────────────────────────────────
ALLOWED_CV_EXT = {"pdf", "jpg", "jpeg", "png", "doc", "docx", "zip"}
MAX_CV_SIZE = 5 * 1024 * 1024  # ۵ مگابایت

# ستون‌های مشترک فرم / جدول مدیریت / خروجی اکسل
FIELDS = [
    ("full_name",  "نام و نام خانوادگی"),
    ("student_id", "شماره دانشجویی"),
    ("mobile",     "شماره موبایل"),
    ("email",      "ایمیل"),
    ("degree",     "مقطع"),
    ("major",      "رشته تحصیلی"),
    ("term",       "ترم تحصیلی"),
    ("interest",   "حوزه علاقه‌مندی"),
    ("cv_file",    "فایل رزومه"),
]

# ─── تعریف کارگاه‌ها ─────────────────────────────────────────────
# برای افزودن کارگاه جدید، یک دیکشنری مثل نمونه‌های زیر اضافه کنید.
#   open: True یعنی ثبت‌نام فعال است
#   poster: نام فایل پوستر داخل پوشه static/posters (خالی باشد طرح گرافیکی نمایش داده می‌شود)
WORKSHOPS = [
    {
        "id": "sysrev-1405",
        "title": "دوره جامع مرور سیستماتیک(Systematic Review)",
        "subtitle": "مرکز تحقیقات پزشکی ورزشی",
        "level": "از تدوین پروتکل تا نگارش مقاله علمی",
        "description": "ویژه‌ی فصل زمستان — بر اساس استانداردهای Cochrane و PRISMA 2020",
        "highlight": "در این دوره، علاوه بر یادگیری گام‌به‌گام تمام مراحل مرور سیستماتیک، به‌عنوان عضو تیم پژوهشی وارد یک «مقاله‌ی حقیقی» می‌شوید: مقاله در طول همان دوره به‌صورت عملی تکمیل می‌شود و با راهنمایی مدرسان، برای انتشار در مجلات علمی آماده خواهد شد. یعنی در پایان دوره، به‌جای صرفاً یک گواهی شرکت، یک مقاله‌ی واقعی در رزومه‌ی علمی شما ثبت می‌شود.",
        "topics": [
            "پروتکل نویسی و ثبت در PROSPERO",
            "استراتژی جستجو در PubMed و Scopus",
            "غربالگری با نرم‌افزار و استخراج داده",
            "ارزیابی سوگیری",
            "سنتز یافته‌ها و نگارش مقاله",
        ],
        "deadline": "۳۰ آذر ۱۴۰۵",
        "contact": "sportmed@tums.ac.ir",
        "poster": "systematic-review.jpg",
        "open": True,
    },
    {
        "id": "ai-med-1405",
        "title": "کارگاه هوش مصنوعی در پزشکی",
        "subtitle": "مرکز تحقیقات پزشکی ورزشی",
        "level": "کاربرد عملی هوش مصنوعی در آموزش، مطالعه و پژوهش",
        "description": "ویژه‌ی فصل زمستان — بدون نیاز به دانش برنامه‌نویسی؛ برای درس، مطالعه و پژوهش",
        "highlight": "در این کارگاه، ابزارهای هوش مصنوعی را نه به‌صورت تئوری، بلکه به‌صورت زنده و عملی روی مطالعات، متون درسی و مقالات خودتان به‌کار می‌گیرید؛ از نوشتن پرامپت حرفه‌ای تا خلاصه‌سازی مقالات و کتب درسی، جستجوی هوشمند در پایگاه‌های علمی و ساختن یک دستیار مطالعاتی شخصی. در پایان دوره، یک جعبه‌ابزار کامل از هوش مصنوعی برای پیشبرد آموزش و پژوهش خود خواهید داشت.",
        "topics": [
            "پرامپت‌نویسی (Prompt Engineering) برای کاربردهای پزشکی",
            "خلاصه‌نویسی مقالات و کتب درسی با هوش مصنوعی",
            "شخصی‌سازی مطالعه با هوش مصنوعی",
            "کار عملی با NotebookLM",
            "استخراج داده و ساخت جدول‌های پژوهشی با هوش مصنوعی",
            "جستجوی هوشمند در پایگاه‌های علمی (Elicit و Semantic Scholar)",
            "اخلاق و محدودیت‌های استفاده از AI در آموزش و پژوهش",
        ],
        "deadline": "۳۰ آذر ۱۴۰۵",
        "contact": "sportmed@tums.ac.ir",
        "poster": "",
        "open": True,
    },
    {
        "id": "spss-1405",
        "title": "کارگاه آمار با SPSS",
        "subtitle": "مرکز تحقیقات پزشکی ورزشی",
        "level": "از مبانی آمار تا تحلیل داده‌های پژوهش",
        "description": "کاربردی و مبتنی بر تمرین با داده‌های واقعی",
        "topics": [
            "آمار توصیفی و آزمون‌های نرمال بودن",
            "t-test، ANOVA و آزمون‌های غیرپارامتریک",
            "ضریب همبستگی و رگرسیون",
        ],
        "deadline": "به‌زودی اعلام می‌شود",
        "contact": "sportmed@tums.ac.ir",
        "poster": "",
        "open": False,
    },
    {
        "id": "writing-1405",
        "title": "کارگاه نگارش مقاله انگلیسی",
        "subtitle": "مرکز تحقیقات پزشکی ورزشی",
        "level": "از ساختار مقاله تا پاسخ به داوران",
        "description": "ویژه دانشجویان علوم پزشکی",
        "topics": [
            "ساختار IMRaD و نگارش بخش‌های اصلی",
            "انتخاب مجله مناسب و جلوگیری از پلاگیاریسم",
            "مکاتبه با ادیتور و پاسخ به داوران",
        ],
        "deadline": "به‌زودی اعلام می‌شود",
        "contact": "sportmed@tums.ac.ir",
        "poster": "",
        "open": False,
    },
]

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ─── دیتابیس ─────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                workshop_id TEXT NOT NULL,
                full_name   TEXT NOT NULL,
                student_id  TEXT NOT NULL,
                mobile      TEXT NOT NULL,
                email       TEXT NOT NULL,
                degree      TEXT NOT NULL,
                major       TEXT NOT NULL DEFAULT '',
                term        TEXT NOT NULL DEFAULT '',
                interest    TEXT NOT NULL,
                cv_file     TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL,
                UNIQUE (student_id, workshop_id)
            )
        """)
        # مهاجرت دیتابیس‌های قدیمی (اگر ستون نبود اضافه می‌شود)
        for col in ("term", "cv_file", "major"):
            try:
                conn.execute(f"ALTER TABLE registrations ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # ستون از قبل هست


# ─── اعتبارسنجی ──────────────────────────────────────────────────
def validate(data):
    errors = {}
    if not (data.get("full_name") or "").strip() or len(data["full_name"].strip()) < 3:
        errors["full_name"] = "نام و نام خانوادگی را کامل وارد کنید."
    sid = (data.get("student_id") or "").strip()
    if not re.fullmatch(r"\d{6,14}", sid):
        errors["student_id"] = "شماره دانشجویی باید فقط شامل ۶ تا ۱۴ رقم باشد."
    mob = (data.get("mobile") or "").strip()
    mob = re.sub(r"[^\d]", "", mob.replace("+98", "0")
                 .translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")))
    if mob.startswith("98"):
        mob = "0" + mob[2:]
    if not re.fullmatch(r"09\d{9}", mob):
        errors["mobile"] = "شماره موبایل باید به شکل ۰۹xxxxxxxxx وارد شود."
    email = (data.get("email") or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors["email"] = "ایمیل معتبر وارد کنید."
    if data.get("degree") not in DEGREES:
        errors["degree"] = "مقطع تحصیلی را انتخاب کنید."
    if not (data.get("major") or "").strip():
        errors["major"] = "رشته تحصیلی را وارد کنید."
    if data.get("term") not in TERMS:
        errors["term"] = "ترم تحصیلی را انتخاب کنید."
    if not (data.get("interest") or "").strip():
        errors["interest"] = "حوزه علاقه‌مندی را وارد کنید."
    return errors, mob, email


def save_cv(cv_file, workshop_id, student_id):
    """فایل رزومه را در پوشه‌ی uploads ذخیره می‌کند و نامش را برمی‌گرداند."""
    if cv_file is None or not cv_file.filename:
        return ""
    ext = cv_file.filename.rsplit(".", 1)[-1].lower() if "." in cv_file.filename else ""
    if ext not in ALLOWED_CV_EXT:
        raise ValueError("قالب فایل مجاز نیست (PDF، Word، تصویر یا ZIP).")
    content = cv_file.read()
    if len(content) > MAX_CV_SIZE:
        raise ValueError("حجم فایل رزومه باید حداکثر ۵ مگابایت باشد.")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    fname = f"cv-{workshop_id}-{student_id}-{int(datetime.now().timestamp())}.{ext}"
    with open(os.path.join(UPLOAD_FOLDER, fname), "wb") as f:
        f.write(content)
    return fname


# ─── صفحات عمومی ─────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", workshops=WORKSHOPS, degrees=DEGREES)


@app.route("/workshop/<workshop_id>")
def workshop_page(workshop_id):
    w = next((w for w in WORKSHOPS if w["id"] == workshop_id), None)
    if not w:
        return redirect(url_for("index"))
    return render_template("workshop.html", w=w, degrees=DEGREES, terms=TERMS)


@app.route("/api/register", methods=["POST"])
def register():
    # فرم به‌صورت multipart ارسال می‌شود (به‌خاطر فایل رزومه)
    data = {k: (request.form.get(k) or "") for k, _ in FIELDS}
    data["workshop_id"] = request.form.get("workshop_id") or ""
    cv = request.files.get("cv")

    workshop = next((w for w in WORKSHOPS if w["id"] == data["workshop_id"]), None)
    if not workshop:
        return jsonify(ok=False, errors={"general": "کارگاه انتخابی معتبر نیست."}), 400
    if not workshop["open"]:
        return jsonify(ok=False, errors={"general": "ثبت‌نام این کارگاه هنوز فعال نشده است."}), 400

    errors, mobile, email = validate(data)
    if errors:
        return jsonify(ok=False, errors=errors), 400

    try:
        cv_name = save_cv(cv, workshop["id"], data["student_id"].strip())
    except ValueError as e:
        return jsonify(ok=False, errors={"cv": str(e)}), 400

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO registrations (workshop_id, full_name, student_id, mobile, email, degree, major, term, interest, cv_file, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (workshop["id"], data["full_name"].strip(), data["student_id"].strip(),
                 mobile, email, data["degree"], data["major"].strip(), data["term"],
                 data["interest"].strip(), cv_name, datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
    except sqlite3.IntegrityError:
        # اگر فایل ذخیره شده ولی ثبت تکراری بود، فایل اضافی را حذف کن
        if cv_name:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, cv_name))
            except OSError:
                pass
        return jsonify(ok=False, errors={"general": "شما قبلاً با این شماره دانشجویی در این کارگاه ثبت‌نام کرده‌اید."}), 409

    return jsonify(ok=True, message=f"ثبت‌نام شما در «{workshop['title']}» با موفقیت انجام شد. ✓")


# ─── پنل مدیریت ──────────────────────────────────────────────────
def is_admin():
    return session.get("admin") is True


@app.route("/admin", methods=["GET"])
def admin():
    if not is_admin():
        return render_template("admin.html", logged_in=False)
    return render_template("admin.html", logged_in=True,
                           workshops=WORKSHOPS, degrees=DEGREES)


@app.route("/admin/login", methods=["POST"])
def admin_login():
    if request.form.get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        return redirect(url_for("admin"))
    flash("رمز عبور اشتباه است.")
    return render_template("admin.html", logged_in=False)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


@app.route("/api/admin/stats")
def admin_stats():
    if not is_admin():
        return jsonify(ok=False), 403
    with get_db() as conn:
        rows = conn.execute(
            "SELECT workshop_id, COUNT(*) AS n FROM registrations GROUP BY workshop_id"
        ).fetchall()
    counts = {r["workshop_id"]: r["n"] for r in rows}
    return jsonify(ok=True, stats={w["id"]: counts.get(w["id"], 0) for w in WORKSHOPS})


@app.route("/api/admin/registrations/<workshop_id>")
def admin_registrations(workshop_id):
    if not is_admin():
        return jsonify(ok=False), 403
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM registrations WHERE workshop_id = ? ORDER BY id",
            (workshop_id,),
        ).fetchall()
    return jsonify(ok=True, rows=[dict(r) for r in rows])


@app.route("/admin/cv/<path:filename>")
def admin_cv(filename):
    """دانلود فایل رزومه — فقط برای مدیر."""
    if not is_admin():
        return redirect(url_for("admin"))
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


# ─── خروجی اکسل ──────────────────────────────────────────────────
def sheet_for(ws, title, rows):
    """یک شیت اکسل راست‌به‌چپ با سربرگ طلایی می‌سازد."""
    ws.sheet_view.rightToLeft = True
    ws.title = title[:31]
    headers = ["ردیف"] + [f[1] for f in FIELDS] + ["کارگاه", "تاریخ ثبت‌نام"]
    ws.append(headers)

    head_fill = PatternFill("solid", fgColor="F2B705")
    head_font = Font(bold=True, size=12)
    center = Alignment(horizontal="center", vertical="center")
    thin = Border(*[Side(style="thin")] * 4)
    for c, _ in enumerate(headers, 1):
        cell = ws.cell(row=1, column=c)
        cell.fill, cell.font, cell.alignment, cell.border = head_fill, head_font, center, thin

    for i, r in enumerate(rows, 1):
        ws.append([i] + [r.get(k, "") for k, _ in FIELDS] + [r.get("workshop_title", ""), r["created_at"]])

    for c in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(c)].width = 18
    ws.freeze_panes = "A2"


def build_workbook(workshop_id=None):
    wb = Workbook()
    targets = [w for w in WORKSHOPS if workshop_id in (None, w["id"])]
    first = True
    with get_db() as conn:
        for w in targets:
            rows = [dict(r) for r in conn.execute(
                "SELECT * FROM registrations WHERE workshop_id = ? ORDER BY id", (w["id"],))]
            for r in rows:
                r["workshop_title"] = w["title"]
            ws = wb.active if first else wb.create_sheet()
            first = False
            sheet_for(ws, w["title"], rows)
    return wb


@app.route("/admin/export/<workshop_id>")
def export_one(workshop_id):
    if not is_admin():
        return redirect(url_for("admin"))
    wb = build_workbook(workshop_id)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = f"registrations-{workshop_id}.xlsx"
    return send_file(buf, as_attachment=True, download_name=fname,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/admin/export/all")
def export_all():
    if not is_admin():
        return redirect(url_for("admin"))
    wb = build_workbook(None)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="registrations-all.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


init_db()

if __name__ == "__main__":
    print("=" * 60)
    print("  سامانه ثبت‌نام کارگاه‌ها راه‌اندازی شد")
    print("  لندینگ پیج:      http://127.0.0.1:5000")
    print("  پنل مدیریت:      http://127.0.0.1:5000/admin")
    print("=" * 60)
    app.run(debug=True, port=5000)
