# Personal Expense Tracker

A full-stack web application built with Python, Flask, and SQLite to help users manage expenses, track monthly budgets, detect unusual spending patterns, and forecast future expenditure.

The application combines expense management with rule-based financial insights through a clean, responsive interface.

## Features

### 1. Expense Management
- Add, view, edit, and delete expenses.
- Categorize transactions by spending type.
- Store transaction records in a SQLite database.
- Maintain transaction history across browser refreshes.

### 2. Spending Anomaly Detection
- Detect unusually high transactions based on historical spending.
- Compare each expense with earlier transactions in the same category.
- Flag expenses exceeding twice the average of at least three earlier category transactions.
- Display warnings beside unusual transactions.

### 3. Month-End Spending Forecast
- Calculate average daily spending.
- Estimate total expenditure by the end of the current month.
- Compare predicted spending against the monthly budget.
- Display alerts when projected expenses exceed the budget.

### 4. Budget Management
- Set and update monthly spending budgets.
- Monitor monthly expenditure.
- Calculate a budget health score from 0 to 100.
- View category-wise spending summaries.

### 5. User Interface
- Responsive dashboard built using HTML and CSS.
- Editorial-inspired design with neutral colors and subtle lavender accents.
- Interactive forms for expense management.
- Clear financial summaries and spending alerts.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python |
| Web Framework | Flask |
| Database | SQLite |
| Frontend | HTML, CSS |
| Template Engine | Jinja2 |
| Version Control | Git, GitHub |

## Project Structure

```text
Personal-Expense-Tracker/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   └── index.html
│
└── static/
    └── style.css
```

The SQLite database is created locally when the application runs.

## How It Works

### Expense Management

Users can create, update, and delete expense records.

Flask handles incoming requests, performs input validation, and executes SQL queries to manage transactions in the SQLite database.

### Anomaly Detection

The application uses a rule-based detection algorithm.

For each transaction:

1. Retrieve earlier expenses from the same category.
2. Calculate their average amount when at least three earlier transactions exist.
3. Compare the new transaction against that average.
4. Flag the transaction when its amount exceeds twice the historical average.

Example:

Previous food expenses:
- Breakfast: Rs. 200
- Lunch: Rs. 250
- Snacks: Rs. 300

Average spending = Rs. 250

A new food expense of Rs. 1,500 exceeds twice the average and is flagged as unusual.

### Spending Forecast

The application estimates month-end expenditure using average daily spending.

Formula:

```text
Average Daily Spending =
Total Monthly Expenses / Days Elapsed

Projected Month-End Spending =
Average Daily Spending × Days in Month
```

Example:

```text
Monthly spending so far: Rs. 2,250
Days elapsed: 8
Days in month: 31

Average daily spending = Rs. 281.25

Projected spending = Rs. 8,718.75
```

If projected spending exceeds the monthly budget, the application displays a warning.

This is a simple statistical projection, not a machine learning model.

### Budget Health Score

The application calculates a score based on the proportion of the monthly budget remaining.

```text
Budget Health Score =
max(0, round(100 × (1 - Monthly Spending / Monthly Budget)))
```

A higher score indicates more of the monthly budget remains.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/gurl33n-ks/Personal-Expense-Tracker.git
```

### 2. Navigate to the Project Folder

```bash
cd Personal-Expense-Tracker
```

### 3. Create a Virtual Environment

```bash
python3 -m venv .venv
```

### 4. Activate the Virtual Environment

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 5. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 6. Run the Application

```bash
python app.py
```

### 7. Open the Application

Visit:

http://127.0.0.1:5000/

## Screenshots

### Dashboard

Screenshot coming soon.

### Spending Forecast

Screenshot coming soon.

### Anomaly Detection

Screenshot coming soon.

## Technical Concepts Demonstrated

- Full-stack web application development
- REST-style request handling with Flask
- SQLite database integration
- CRUD operations
- SQL queries and data persistence
- Input validation and error handling
- Rule-based anomaly detection
- Financial forecasting calculations
- Responsive web interface development
- Git version control

## Limitations

- The application is currently designed for local use.
- It does not connect to real banking systems.
- The anomaly detection algorithm uses predefined rules rather than machine learning.
- Spending forecasts assume the current average daily spending rate continues throughout the month.
- User authentication and multi-user account management are not implemented.

## Future Improvements

- User authentication
- Interactive spending charts
- CSV transaction export
- Category-specific spending limits
- Historical spending comparisons

## Author

Gurleen Kaur Sawhney

GitHub: https://github.com/gurl33n-ks

---

This project was developed for educational and portfolio purposes. It does not provide financial advice.