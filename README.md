# Jai shree Fashion CRM

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

   - Email: `admin@jaishreefashion.com`
   - Password: `JaiShreeFashion@123`

## Render Deploy

This repo includes a `render.yaml` blueprint for Render.

1. Create a new Blueprint in Render from this repository.
2. Let Render create the PostgreSQL database and inject `DATABASE_URL`.
3. Deploy the service once so `python manage.py migrate --noinput` runs before the app starts.
4. Use the service URL `https://jaishreefashioncrm.onrender.com/`.

## Features

- Secure login / logout / password change
- Customer quick add + advanced fields
- Purchase history and follow-up management
- Dashboard with totals, pending reminders, and top customers
- Search + filters for fast results
- Mobile-first dark gold theme
