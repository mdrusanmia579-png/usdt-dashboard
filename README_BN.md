
# USDT Dashboard Starter (বাংলা)

এটি একটি **শিক্ষামূলক ডেমো**: রেজিস্ট্রেশন, লগইন, জমার অনুরোধ, উত্তোলনের অনুরোধ, অ্যাডমিন approval এবং ledger হিসাব আছে। এটি blockchain-এ USDT গ্রহণ/পাঠায় না, স্বয়ংক্রিয় মুনাফা দেয় না, এবং কোনো আয়ের নিশ্চয়তা দেয় না।

## ১) কী লাগবে
- Python 3.11 বা নতুন
- কমান্ড লাইন/টার্মিনাল
- পরীক্ষার জন্য নিজের কম্পিউটার

## ২) চালু করুন
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```
`.env.example` কপি করে `.env` বানান। `SECRET_KEY` এবং `ADMIN_PASSWORD`-এ শক্তিশালী, আলাদা মান দিন। তারপর:
```bash
python app.py
```
ব্রাউজারে `http://127.0.0.1:5000` খুলুন। সাধারণ ইউজার হিসেবে Register করুন। অ্যাডমিন হিসেবে লগইন করতে `.env`-এর `ADMIN_USERNAME` এবং `ADMIN_PASSWORD` ব্যবহার করুন।

## ৩) পরীক্ষা
1. সাধারণ ইউজার অ্যাকাউন্ট খুলুন।
2. Deposit request-এ পরিমাণ ও একটি পরীক্ষামূলক TxID দিন।
3. অ্যাডমিন লগইন করে `/admin` খুলুন।
4. বাস্তব লেনদেন নয়—শুধু ডেমো পরীক্ষা করার জন্য অনুরোধ approve/reject করুন।
5. Withdrawal request-ও কেবল ledger-এ নথিভুক্ত হয়; কোনো coin পাঠানো হয় না।

## ৪) বাস্তব ব্যবহারের আগে জরুরি কাজ
এই starter-কে সরাসরি public internet-এ deploy করবেন না। Production-এর আগে অন্তত:
- CSRF protection, rate limiting, email/2FA, secure cookie, HTTPS এবং security headers যোগ করুন।
- Withdrawal-এর জন্য database transaction ও atomic fund reservation/locking, দৈনিক সীমা এবং audit log যোগ করুন।
- deposit approval হাতে না করে blockchain provider-এর নির্ভরযোগ্য confirmation, সঠিক network/token contract, confirmations, replay protection ও reconciliation যাচাই করুন।
- ব্যক্তিগত wallet seed/private key কখনো এই ওয়েব অ্যাপে রাখবেন না। নিরাপদ custody/payment provider ব্যবহার করুন।
- বাস্তব deposit/withdrawal চালুর আগে আপনার দেশের আইন, AML/KYC, কর ও সেবা-প্রদানকারীর শর্ত সম্পর্কে যোগ্য পেশাদারের পরামর্শ নিন।
- লাভ/ROI দেখাবেন শুধু সত্যিকারের, যাচাইযোগ্য আয়ের উৎস থাকলে; জমা টাকার ওপর নিশ্চিত দৈনিক মুনাফার দাবি করবেন না।

## গুরুত্বপূর্ণ সীমাবদ্ধতা
এটি production-ready financial service নয়। Withdrawal pending থাকাকালে একই ব্যালেন্স একাধিকবার request করার race condition পুরোপুরি প্রতিরোধ করে না। বাস্তব অর্থ চালুর আগে এই অংশটি transaction-safe করে পুনর্লিখতে হবে।



## Render-এ হোস্টিং (পরীক্ষার জন্য)
- GitHub-এ প্রজেক্ট ফাইলগুলো আপলোড করুন (ZIP ফাইল নয়, ZIP extract করে ভেতরের ফাইল ও `templates` ফোল্ডারসহ)।
- Render Dashboard → New → Web Service → GitHub repository নির্বাচন করুন।
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Environment Variables-এ `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DATABASE_URL` দিন।
- `DATABASE_URL`-এ Render PostgreSQL-এর Internal Database URL ব্যবহার করুন, SQLite নয়। `ADMIN_PASSWORD`-এ দীর্ঘ, অনন্য পাসওয়ার্ড দিন।

Render-এর Free Web Service ১৫ মিনিট নিষ্ক্রিয় থাকলে sleep করে এবং local SQLite data হারাতে পারে। সত্যিকারের ২৪/৭ ও স্থায়ী ডেটার জন্য paid always-on web service এবং স্থায়ী/managed database প্রয়োজন। এই ডেমোকে বাস্তব টাকা পরিচালনার জন্য সরাসরি ব্যবহার করবেন না।
