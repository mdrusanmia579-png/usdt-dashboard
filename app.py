import os
from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-this")
database_url = os.getenv("DATABASE_URL", "sqlite:///usdt_demo.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

class Ledger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    kind = db.Column(db.String(20), nullable=False)  # deposit, withdrawal
    amount = db.Column(db.Numeric(18, 6), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    reference = db.Column(db.String(150), default="", nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        user = db.session.get(User, session["user_id"])
        if not user or not user.is_admin:
            flash("এই পৃষ্ঠাটি শুধু অ্যাডমিনের জন্য।")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapper

def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

def balance_for(user_id):
    rows = Ledger.query.filter_by(user_id=user_id, status="approved").all()
    total = Decimal("0")
    for row in rows:
        total += row.amount if row.kind == "deposit" else -row.amount
    return total

@app.route("/")
def home():
    return redirect(url_for("dashboard") if current_user() else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(username) > 40 or len(password) < 12:
            flash("ইউজারনেম ৩–৪০ অক্ষর এবং পাসওয়ার্ড অন্তত ১২ অক্ষরের হতে হবে।")
        elif User.query.filter_by(username=username).first():
            flash("এই ইউজারনেমটি আগে থেকেই আছে।")
        else:
            user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("অ্যাকাউন্ট তৈরি হয়েছে। এটি এখন ডেমো লেজার; বাস্তব USDT জমা হয়নি।")
            return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("লগইন তথ্য সঠিক নয়।")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    rows = Ledger.query.filter_by(user_id=user.id).order_by(Ledger.created_at.desc()).all()
    return render_template("dashboard.html", user=user, balance=balance_for(user.id), rows=rows)

@app.route("/request-deposit", methods=["POST"])
def request_deposit():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    try:
        amount = Decimal(request.form.get("amount", "0"))
    except InvalidOperation:
        amount = Decimal("0")
    reference = request.form.get("reference", "").strip()[:150]
    if amount <= 0 or amount > Decimal("1000000"):
        flash("সঠিক পরিমাণ দিন।")
    elif not reference:
        flash("লেনদেনের TxID/রেফারেন্স দিন। যাচাই না হওয়া পর্যন্ত ব্যালেন্স বাড়বে না।")
    else:
        db.session.add(Ledger(user_id=user.id, kind="deposit", amount=amount,
                              status="pending", reference=reference))
        db.session.commit()
        flash("জমার অনুরোধ জমা হয়েছে। অন-চেইন যাচাইয়ের পর অ্যাডমিন অনুমোদন করবেন।")
    return redirect(url_for("dashboard"))

@app.route("/request-withdrawal", methods=["POST"])
def request_withdrawal():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    try:
        amount = Decimal(request.form.get("amount", "0"))
    except InvalidOperation:
        amount = Decimal("0")
    address = request.form.get("address", "").strip()[:150]
    if amount <= 0 or amount > balance_for(user.id):
        flash("পরিমাণ সঠিক নয় অথবা অনুমোদিত ব্যালেন্স যথেষ্ট নয়।")
    elif not address:
        flash("আপনার গ্রহণকারী wallet address দিন।")
    else:
        # Pending withdrawal does not deduct funds yet; production must reserve funds
        # atomically to prevent multiple pending withdrawals spending the same balance.
        db.session.add(Ledger(user_id=user.id, kind="withdrawal", amount=amount,
                              status="pending", reference="Wallet: " + address))
        db.session.commit()
        flash("উত্তোলনের অনুরোধ জমা হয়েছে; এটি এখনো পাঠানো হয়নি।")
    return redirect(url_for("dashboard"))

@app.route("/admin")
@admin_required
def admin():
    rows = Ledger.query.filter_by(status="pending").order_by(Ledger.created_at.asc()).all()
    return render_template("admin.html", rows=rows)

@app.route("/admin/decision/<int:row_id>", methods=["POST"])
@admin_required
def admin_decision(row_id):
    row = db.session.get(Ledger, row_id)
    decision = request.form.get("decision")
    if not row or row.status != "pending" or decision not in ("approve", "reject"):
        flash("অনুরোধটি আর pending নেই বা অবৈধ।")
        return redirect(url_for("admin"))
    if decision == "approve":
        if row.kind == "withdrawal":
            # Re-check balance. For production, reserve funds at request time and use DB transactions.
            if row.amount > balance_for(row.user_id):
                row.status = "rejected"
                db.session.commit()
                flash("ব্যালেন্স যথেষ্ট নয়; উত্তোলন প্রত্যাখ্যান করা হয়েছে।")
                return redirect(url_for("admin"))
        row.status = "approved"
    else:
        row.status = "rejected"
    db.session.commit()
    flash("স্ট্যাটাস আপডেট হয়েছে। মনে রাখুন: withdrawal অনুমোদন এখানে টাকা পাঠায় না।")
    return redirect(url_for("admin"))

def bootstrap_admin():
    with app.app_context():
        db.create_all()
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "")
        if password and not User.query.filter_by(username=username).first():
            db.session.add(User(username=username, password_hash=generate_password_hash(password), is_admin=True))
            db.session.commit()
        elif not password:
            print("ADMIN_PASSWORD not set: admin account was NOT created.")

# Initialize schema for both local runs and production WSGI servers (e.g. Gunicorn).
bootstrap_admin()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
