from datetime import date

import pytest
import app as expense_app

from ml_model import predict_category


# Create a separate temporary database for each test.
# Your real expenses will not be affected.

@pytest.fixture
def client(tmp_path, monkeypatch):

    test_database = tmp_path / "test_expenses.db"

    monkeypatch.setattr(
        expense_app,
        "DATABASE",
        test_database
    )

    expense_app.app.config["TESTING"] = True

    expense_app.init_db()

    with expense_app.app.test_client() as client:
        yield client


def add_sample_expense(client, amount="250"):

    return client.post("/add", data={
        "title": "Lunch",
        "amount": amount,
        "category": "Food",
        "expense_date": date.today().isoformat()
    })


# TEST 1: Homepage loads successfully

def test_homepage(client):

    response = client.get("/")

    assert response.status_code == 200

    assert b"Spending overview" in response.data


# TEST 2: Add expense

def test_add_expense(client):

    response = add_sample_expense(client)

    assert response.status_code == 302

    with expense_app.db() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM expenses"
        ).fetchone()[0]

    assert count == 1


# TEST 3: Reject invalid amount

def test_invalid_expense(client):

    add_sample_expense(client, amount="-500")

    with expense_app.db() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM expenses"
        ).fetchone()[0]

    assert count == 0


# TEST 4: Update expense

def test_edit_expense(client):

    add_sample_expense(client)

    response = client.post("/edit/1", data={
        "title": "Updated Lunch",
        "amount": "500",
        "category": "Food",
        "expense_date": date.today().isoformat()
    })

    assert response.status_code == 302

    with expense_app.db() as connection:
        expense = connection.execute(
            "SELECT * FROM expenses WHERE id = 1"
        ).fetchone()

    assert expense["amount_paise"] == 50000
    assert expense["title"] == "Updated Lunch"


# TEST 5: Delete expense

def test_delete_expense(client):

    add_sample_expense(client)

    response = client.post("/delete/1")

    assert response.status_code == 302

    with expense_app.db() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM expenses"
        ).fetchone()[0]

    assert count == 0


# TEST 6: Spending forecast

def test_spending_forecast():

    result = expense_app.calculate_forecast(
        total_paise=225000,
        budget_paise=2000000,
        today=date(2026, 10, 8)
    )

    assert result["forecast_paise"] == 871875

    assert result["forecast_status"] == "within_budget"


# TEST 7: Anomaly detection

def test_anomaly_detection():

    amounts = [20000, 25000, 30000, 150000]

    expenses = [
        {
            "id": index + 1,
            "category": "Food",
            "amount_paise": amount,
            "expense_date": "2026-10-08"
        }
        for index, amount in enumerate(amounts)
    ]

    flagged = expense_app.spending_alerts(expenses)

    assert 4 in flagged

    assert 1 not in flagged


# TEST 8: ML prediction returns a valid category

def test_ml_prediction():

    result = predict_category(
        "uber ride to college"
    )

    assert result["category"] in (
        "Food",
        "Transport",
        "Shopping",
        "Bills",
        "Entertainment",
        "Health",
        "Other"
    )

    assert 0 <= result["confidence"] <= 1


# TEST 9: ML endpoint responds to a description

def test_ml_endpoint(client):

    response = client.post(
        "/predict-category",
        json={
            "description": "movie tickets"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "category" in data
    assert "confidence" in data


# TEST 10: Invalid ML input is rejected

def test_invalid_ml_input(client):

    response = client.post(
        "/predict-category",
        json={
            "description": ""
        }
    )

    assert response.status_code == 400