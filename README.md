# SmartSpend

An educational personal expense tracker built with Flask, SQLite, HTML, and CSS. Supports add/edit/delete, monthly summaries, custom budgets, and rule-based unusual-spending alerts.

## Run

1. Open this folder in VS Code.
2. Create a virtual environment: `python -m venv .venv` (Windows: `py -m venv .venv`).
3. Activate it: Windows PowerShell `.venv\Scripts\Activate.ps1`; macOS/Linux `source .venv/bin/activate`.
4. Install dependencies: `python -m pip install -r requirements.txt`.
5. Run: `python app.py`.
6. Open http://127.0.0.1:5000.

## Test the smart alert
Add **four Food expenses in date order**, for example ₹200, ₹250, ₹300 and ₹1,500. The last one will be flagged because it is over twice the mean of the first three. The budget health score uses the current month's spending only.

## Notes
This is a local educational prototype, not a production banking application. It does not use authentication, CSRF protection, or production deployment configuration. Never enter sensitive real banking data.
