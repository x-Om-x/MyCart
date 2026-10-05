# MyCart

MyCart is a Django-based shopping project with a storefront, cart flow, checkout process, order tracking, product search, contact form, and PDF invoice generation.

## Features

- Product listing and category-based browsing
- Search by product name, description, or category
- Product detail page
- Cart operations in the browser with local storage
- Checkout form and order creation
- Order tracking by order ID and email
- PDF invoice generation for each order
- Contact form for customer inquiries

## Tech Stack

- Python
- Django
- Pillow for uploaded product images
- SQLite locally and PostgreSQL on Render
- Bootstrap for frontend styling
- ReportLab for PDF generation
- WhiteNoise for production static files

## Project Structure

```text
mc/
├── shop/
│   ├── migrations/
│   ├── templates/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
├── mc/
│   ├── settings.py
│   ├── urls.py
│   └── templates/
├── manage.py
├── requirements.txt
├── render.yaml
├── .gitignore
├── README.md
└── media/ (local uploads; ignored by Git)
```

## Requirements

- Python 3.10 or newer
- Dependencies listed in `requirements.txt`

## Setup

1. Clone the repository.
2. Create and activate a virtual environment:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set the required Django environment variables. Use a newly generated secret key, and keep it out of source control:

```bash
# PowerShell
$env:DJANGO_SECRET_KEY = "paste-a-newly-generated-secret-key-here"
$env:DJANGO_DEBUG = "true"

# macOS/Linux
export DJANGO_SECRET_KEY="paste-a-newly-generated-secret-key-here"
export DJANGO_DEBUG="true"
```

Generate a key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

For deployment, set `DJANGO_DEBUG=false` and set `DJANGO_ALLOWED_HOSTS` to a comma-separated list of the site's hostnames. The allowed-hosts default is only for local development.

5. Apply database migrations:

```bash
python manage.py migrate
```

6. Create a superuser if needed:

```bash
python manage.py createsuperuser
```

7. Run the development server:

```bash
python manage.py runserver
```

Then open:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/shop/

## Common Commands

```bash
python manage.py check
python manage.py test
python manage.py makemigrations
python manage.py migrate
```

## Render Demo Deployment

The repository includes a Render Blueprint in `render.yaml`. To create a demo deployment:

1. Push the repository to GitHub.
2. In Render, create a new Blueprint and connect `x-Om-x/MyCart`.
3. Review the web service and PostgreSQL database, then apply the Blueprint.

The Blueprint generates `DJANGO_SECRET_KEY`, configures PostgreSQL, runs migrations and collects static files during build, and starts the app with Gunicorn. Render sets the public hostname automatically.

This is for demonstration and testing only. Render's free web service can spin down when idle, and its free PostgreSQL database expires after 30 days. The app's uploaded product images are stored on the web service's temporary filesystem and can be lost on restart or redeploy. Do not use this configuration for real orders or important data. For production, use a persistent paid database and external persistent media storage, and confirm backups and retention.

## Notes

- Media uploads are stored under the `media/` directory.
- The project uses SQLite locally; Render uses PostgreSQL through `DATABASE_URL`.
- Local database files, uploads, virtual environments, and secrets are excluded via `.gitignore`.
