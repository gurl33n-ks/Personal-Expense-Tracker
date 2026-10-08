from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import calendar
import sqlite3

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

# ----------------------------------------
# APPLICATION CONFIGURATION
# ----------------------------------------

app = Flask(__name__)
app.secret_key = "local-demo-only-change-this-before-deployment"

DATABASE = Path(__file__).with_name("smartspend.db")

CATEGORIES = (
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Other"
)

DEFAULT_BUDGET_PAISE = 2000000  # ₹20,000


# ----------------------------------------
# DATABASE CONNECTION
# ----------------------------------------

def db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount_paise INTEGER NOT NULL
                    CHECK(amount_paise > 0),
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                monthly_budget_paise INTEGER NOT NULL
                    CHECK(monthly_budget_paise > 0)
            )
        """)

        connection.execute(
            """
            INSERT OR IGNORE INTO settings
            (id, monthly_budget_paise)
            VALUES (1, ?)
            """,
            (DEFAULT_BUDGET_PAISE,)
        )


# ----------------------------------------
# AMOUNT VALIDATION
# ----------------------------------------

def money_to_paise(value):
    try:
        amount = Decimal(str(value)).quantize(
            Decimal("0.01")
        )
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid amount.")

    if (
        not amount.is_finite()
        or amount <= 0
        or amount > 10000000
    ):
        raise ValueError(
            "Amount must be greater than ₹0 "
            "and at most ₹1,00,00,000."
        )

    return int(amount * 100)


def valid_date(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise ValueError("Choose a valid date.")


# ----------------------------------------
# UNUSUAL SPENDING DETECTION
# ----------------------------------------

def spending_alerts(expenses):

    history = {}
    flagged = set()

    sorted_expenses = sorted(
        expenses,
        key=lambda e: (
            e["expense_date"],
            e["id"]
        )
    )

    for item in sorted_expenses:

        category = item["category"]
        previous = history.get(category, [])

        if len(previous) >= 3:

            average = sum(previous) / len(previous)

            if item["amount_paise"] > 2 * average:
                flagged.add(item["id"])

        history.setdefault(
            category, []
        ).append(item["amount_paise"])

    return flagged


# ----------------------------------------
# SPENDING FORECAST
# ----------------------------------------

def calculate_forecast(
    total_paise,
    budget_paise,
    today
):
    """
    Predict month-end spending based on
    average daily spending so far.
    """

    days_in_month = calendar.monthrange(
        today.year,
        today.month
    )[1]

    days_elapsed = today.day

    daily_average_paise = (
        total_paise / days_elapsed
    )

    forecast_paise = round(
        daily_average_paise * days_in_month
    )

    forecast_difference_paise = abs(
        budget_paise - forecast_paise
    )

    if total_paise == 0:
        forecast_status = "no_data"

    elif forecast_paise > budget_paise:
        forecast_status = "over_budget"

    else:
        forecast_status = "within_budget"

    return {
        "forecast_paise": forecast_paise,
        "forecast_difference_paise":
            forecast_difference_paise,
        "forecast_status": forecast_status,
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month
    }


# ----------------------------------------
# HOME DASHBOARD
# ----------------------------------------

@app.route("/")
def index():

    with db() as connection:

        expenses = connection.execute(
            """
            SELECT * FROM expenses
            ORDER BY expense_date DESC, id DESC
            """
        ).fetchall()

        budget_paise = connection.execute(
            """
            SELECT monthly_budget_paise
            FROM settings
            WHERE id = 1
            """
        ).fetchone()[0]

    today = date.today()

    current_month = today.strftime("%Y-%m")

    this_month = [
        expense
        for expense in expenses
        if expense["expense_date"][:7] == current_month
    ]

    total_paise = sum(
        expense["amount_paise"]
        for expense in this_month
    )

    # Budget health score
    score = max(
        0,
        round(
            100 * (1 - total_paise / budget_paise)
        )
    )

    # Spending by category
    category_totals = {}

    for item in this_month:

        category = item["category"]

        category_totals[category] = (
            category_totals.get(category, 0)
            + item["amount_paise"]
        )

    sorted_categories = sorted(
        category_totals.items(),
        key=lambda item: -item[1]
    )

    # Unusual spending alerts
    flagged = spending_alerts(expenses)

    # NEW: Spending forecast
    forecast = calculate_forecast(
        total_paise,
        budget_paise,
        today
    )

    return render_template(
        "index.html",
        expenses=expenses,
        flagged=flagged,
        total_paise=total_paise,
        budget_paise=budget_paise,
        score=score,
        category_totals=sorted_categories,
        categories=CATEGORIES,
        today=today.isoformat(),
        month=today.strftime("%B %Y"),
        **forecast
    )


# ----------------------------------------
# ADD EXPENSE
# ----------------------------------------

@app.post("/add")
def add_expense():

    try:
        title = request.form.get(
            "title", ""
        ).strip()

        if not title or len(title) > 80:
            raise ValueError(
                "Description must be between "
                "1 and 80 characters."
            )

        amount_paise = money_to_paise(
            request.form.get("amount", "")
        )

        category = request.form.get(
            "category", ""
        )

        if category not in CATEGORIES:
            raise ValueError(
                "Choose a valid category."
            )

        expense_date = valid_date(
            request.form.get("expense_date")
        )

        with db() as connection:

            connection.execute(
                """
                INSERT INTO expenses
                (
                    title,
                    amount_paise,
                    category,
                    expense_date
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    title,
                    amount_paise,
                    category,
                    expense_date
                )
            )

        flash(
            "Expense added successfully.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("index"))


# ----------------------------------------
# DELETE EXPENSE
# ----------------------------------------

@app.post("/delete/<int:expense_id>")
def delete_expense(expense_id):

    with db() as connection:

        connection.execute(
            """
            DELETE FROM expenses
            WHERE id = ?
            """,
            (expense_id,)
        )

    flash("Expense deleted.", "success")

    return redirect(url_for("index"))


# ----------------------------------------
# EDIT EXPENSE
# ----------------------------------------

@app.post("/edit/<int:expense_id>")
def edit_expense(expense_id):

    try:

        title = request.form.get(
            "title", ""
        ).strip()

        if not title or len(title) > 80:
            raise ValueError(
                "Description must be between "
                "1 and 80 characters."
            )

        amount_paise = money_to_paise(
            request.form.get("amount", "")
        )

        category = request.form.get(
            "category", ""
        )

        if category not in CATEGORIES:
            raise ValueError(
                "Choose a valid category."
            )

        expense_date = valid_date(
            request.form.get("expense_date")
        )

        with db() as connection:

            connection.execute(
                """
                UPDATE expenses
                SET title = ?,
                    amount_paise = ?,
                    category = ?,
                    expense_date = ?
                WHERE id = ?
                """,
                (
                    title,
                    amount_paise,
                    category,
                    expense_date,
                    expense_id
                )
            )

        flash("Expense updated.", "success")

    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("index"))


# ----------------------------------------
# UPDATE MONTHLY BUDGET
# ----------------------------------------

@app.post("/budget")
def update_budget():

    try:

        budget_paise = money_to_paise(
            request.form.get("budget", "")
        )

        with db() as connection:

            connection.execute(
                """
                UPDATE settings
                SET monthly_budget_paise = ?
                WHERE id = 1
                """,
                (budget_paise,)
            )

        flash(
            "Monthly budget updated.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("index"))


# ----------------------------------------
# CURRENCY FORMATTING
# ----------------------------------------

@app.template_filter("rupees")
def rupees(paise):

    return f"₹{paise / 100:,.2f}"


# ----------------------------------------
# START APPLICATION
# ----------------------------------------

init_db()

if __name__ == "__main__":
    app.run(debug=True)