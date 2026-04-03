# 25Carat CRM

Premium mobile-friendly CRM for jewelry sales, built with Django.

## Quick start

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Run migrations and start the server:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

3. Open `http://127.0.0.1:8000/` and log in with:

   - Email: `admin@25carat.com`
   - Password: `25Carat@123`

## Features

- Secure login / logout / password change
- Customer quick add + advanced fields
- Purchase history and follow-up management
- Dashboard with totals, pending reminders, and top customers
- Search + filters for fast results
- Mobile-first dark gold theme
