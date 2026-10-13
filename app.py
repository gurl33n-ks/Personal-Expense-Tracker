import pandas as pd 
import plotly.express as px
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import calendar
import sqlite3
from ml_model import predict_category

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    jsonify
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

# ---------------------------------------
    # INTERACTIVE SPENDING ANALYTICS
    # ---------------------------------------

    chart_expenses = [
        {
            "category": item["category"],
            "amount": item["amount_paise"] / 100,
            "date": item["expense_date"]
        }
        for item in expenses
    ]

    category_chart = None
    monthly_chart = None

    if chart_expenses:
        df = pd.DataFrame(chart_expenses)

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        df = df.dropna(subset=["date"])

        # Category-wise spending
        category_data = (
            df.groupby("category", as_index=False)["amount"]
            .sum()
        )

        fig_category = px.pie(
            category_data,
            names="category",
            values="amount",
            hole=0.58,
            title="Spending by Category",
            color_discrete_sequence=[
                "#73617D",
                "#BBA7C6",
                "#D9C5D3",
                "#E8DCCF",
                "#A8B9AD",
                "#D8A8A8"
            ]
        )

        fig_category.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Arial",
                color="#302D32"
            ),
            margin=dict(l=20, r=20, t=60, b=20),
            height=350
        )

        category_chart = fig_category.to_json()

        # Monthly spending trend
        df["month"] = (
            df["date"].dt.to_period("M").astype(str)
        )

        monthly_data = (
            df.groupby("month", as_index=False)["amount"]
            .sum()
            .sort_values("month")
        )
        monthly_data["month"] = pd.to_datetime(
            monthly_data["month"],
            format="%Y-%m"
        ).dt.strftime("%b %Y")

        fig_monthly = px.bar(
            monthly_data,
            x="month",
            y="amount",
            title="Monthly Spending Trend",
            labels={
                "month": "Month",
                "amount": "Spending (₹)"
            },
            color_discrete_sequence=["#73617D"]
        )

        fig_monthly.update_traces(
            width=0.45,
            marker_line_width=0,
            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Spending: ₹%{y:,.2f}"
                "<extra></extra>"
            )
        )

        fig_monthly.update_xaxes(
            type="category",
            tickangle=0,
            showgrid=False
        )

        fig_monthly.update_yaxes(
            tickprefix="₹",
            tickformat=",.0f",
            gridcolor="#EAE5E1",
            zeroline=False
        )

        fig_monthly.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Arial",
                color="#302D32"
            ),
            margin=dict(
                l=55,
                r=20,
                t=60,
                b=50
            ),
            height=350,
            bargap=0.55,
            showlegend=False
        )

        monthly_chart = fig_monthly.to_json()

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
        **forecast,
        category_chart=category_chart,
        monthly_chart=monthly_chart
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

# ----------------------------------------
# ML EXPENSE CATEGORY PREDICTION
# ----------------------------------------

@app.post("/predict-category")
def predict_expense_category():

    data = request.get_json(silent=True) or {}

    description = data.get("description", "")

    if not isinstance(description, str):
        return jsonify({
            "error": "Invalid description."
        }), 400

    if len(description) > 80:
        return jsonify({
            "error": "Description is too long."
        }), 400

    try:
        result = predict_category(description)

        return jsonify(result)

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400
        
init_db()

if __name__ == "__main__":
    app.run(debug=True)