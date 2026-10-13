# Personal Expense Tracker

A full-stack financial analytics application developed using Python, Flask, SQLite, and Machine Learning to help users manage expenses, identify unusual transactions, predict monthly expenditure, and understand spending patterns.

The application combines persistent transaction management, NLP-based expense categorization, statistical forecasting, and interactive data visualizations in a responsive financial dashboard.

## Key Features

### 1. Expense Management
- Add, view, edit, and delete expenses.
- Categorize transactions by spending type.
- Store and retrieve transactions using SQLite.
- Maintain expense history across browser refreshes.
- Validate transaction inputs.

### 2. Machine Learning-Based Expense Categorization
- Automatically suggest expense categories from transaction descriptions.
- Use TF-IDF vectorization for text feature extraction.
- Apply a Multinomial Naive Bayes classifier for category prediction.
- Train and evaluate the model using a labeled financial transaction dataset.
- Allow users to manually change suggested categories.

### 3. Spending Anomaly Detection
- Identify unusually large transactions based on historical spending.
- Compare new expenses with earlier transactions in the same category.
- Flag transactions exceeding twice the average of at least three previous category expenses.
- Display unusual spending alerts.

Anomaly detection uses explainable statistical rules rather than an ML-based fraud detection model.

### 4. Month-End Spending Forecast
- Calculate average daily expenditure.
- Estimate spending through the end of the current month.
- Compare predicted expenses against the monthly budget.
- Display warnings when projected spending exceeds the available budget.

### 5. Interactive Financial Analytics
- Visualize category-wise spending through interactive Plotly donut charts.
- Analyze historical monthly expenditure with bar charts.
- Generate financial summaries using Pandas.
- Display category spending breakdowns and budget utilization.

### 6. Budget Management
- Set and update monthly budgets.
- Monitor current monthly expenditure.
- Calculate a budget health score.
- Display budget-related insights and warnings.

### 7. Automated Testing
- Implemented 10 automated tests using Pytest.
- Verified expense creation, editing, and deletion.
- Tested input validation and financial calculations.
- Tested anomaly detection and forecasting logic.
- Validated ML predictions and the categorization endpoint.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Template Engine | Jinja2 |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| NLP | TF-IDF |
| Classification Algorithm | Multinomial Naive Bayes |
| Data Visualization | Plotly |
| Dataset Processing | PyArrow |
| Model Serialization | Joblib |
| Automated Testing | Pytest |
| Version Control | Git, GitHub |

## Machine Learning Implementation

### Dataset

The classification model was trained using the Transaction Categorization dataset published on Hugging Face.

Dataset:
https://huggingface.co/datasets/mitulshah/transaction-categorization

The dataset contains approximately 4.5 million labeled transaction records with transaction descriptions, categories, countries, and currencies.

A filtered and sampled subset was used for training and evaluation.

The dataset is not included in this repository.

### Data Preprocessing

The ML training pipeline:

1. Reads transaction data from Parquet format.
2. Filters records using compatible expense categories.
3. Cleans and normalizes transaction descriptions.
4. Samples category-specific records.
5. Removes duplicate and ambiguously labeled descriptions.
6. Splits the processed data into training and test sets.

### Model Architecture

The classification pipeline uses:

- TF-IDF vectorization with character n-grams.
- Multinomial Naive Bayes for expense category classification.
- Scikit-learn Pipeline for preprocessing and prediction.

The application supports the following expense categories:

- Food
- Transport
- Shopping
- Bills
- Entertainment
- Health
- Other (manual category)

### Model Evaluation

The trained classifier produced the following results on a held-out subset of the transaction dataset.

| Metric | Result |
|---|---:|
| Processed records | 8,555 |
| Training records | 6,844 |
| Testing records | 1,711 |
| Test accuracy | 97.66% |
| Weighted F1-score | 0.976 |

These metrics describe performance on the sampled dataset, not verified performance on real-world banking transactions.

Because the dataset contains generated or curated transaction descriptions, predictions may be less accurate on unfamiliar merchants, inconsistent descriptions, or real banking data.

The ML model provides category suggestions that users can manually correct.

## Spending Anomaly Detection

The application uses rule-based anomaly detection.

For a new transaction:

1. Retrieve earlier expenses belonging to the same category.
2. Calculate the historical average when at least three earlier transactions exist.
3. Compare the transaction amount with the historical average.
4. Flag the expense if it exceeds twice that average.

Example:

| Transaction | Amount |
|---|---:|
| Breakfast | ₹200 |
| Lunch | ₹250 |
| Snacks | ₹300 |
| New restaurant expense | ₹1,500 |

Historical average = ₹250

Anomaly threshold = ₹500

The ₹1,500 transaction is flagged as unusual.

This is a spending alert, not a determination that a transaction is fraudulent.

## Spending Forecasting

The application estimates month-end expenditure using average daily spending.

Average Daily Spending:

    Total Spending This Month / Days Elapsed

Projected Month-End Spending:

    Average Daily Spending × Total Days in Month

Example:

    Monthly spending so far: ₹2,250
    Days elapsed: 8
    Days in month: 31

    Average daily spending: ₹281.25
    Projected month-end spending: ₹8,718.75

The projected expenditure is compared with the user's monthly budget to identify potential overspending.

This is a statistical projection rather than a machine learning forecasting model.

## Budget Health Score

The budget health score is calculated using the proportion of the monthly budget remaining.

    Score = max(
        0,
        round(100 × (1 - Monthly Spending / Monthly Budget))
    )

A higher score indicates a greater proportion of the monthly budget remains.

## Project Structure

    Personal-Expense-Tracker/
    |
    |-- app.py
    |-- ml_model.py
    |-- train_model.py
    |-- requirements.txt
    |-- README.md
    |-- .gitignore
    |
    |-- templates/
    |   |-- index.html
    |
    |-- static/
    |   |-- style.css
    |
    |-- tests/
    |   |-- test_app.py
    |
    |-- data/                     (not included)
    |   |-- transactions.parquet
    |
    |-- models/                   (generated locally)
        |-- expense_classifier.joblib
        |-- evaluation.json

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/gurl33n-ks/Personal-Expense-Tracker.git
```

### 2. Open the Project Directory

```bash
cd Personal-Expense-Tracker
```

### 3. Create a Virtual Environment

```bash
python3 -m venv .venv
```

### 4. Activate the Environment

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 6. Run the Application

```bash
python app.py
```

### 7. Open the Dashboard

Visit:

http://127.0.0.1:5000/

The application creates and uses a local SQLite database.

The application can run without the dataset-trained model by using its built-in demonstration classifier.

## Training the Dataset-Based ML Model

To reproduce the enhanced machine learning model:

1. Visit the dataset page:

   https://huggingface.co/datasets/mitulshah/transaction-categorization

2. Download the Parquet training file.

3. Create a folder named `data` in the project directory.

4. Rename the downloaded file to `transactions.parquet`.

5. Place the file inside the `data` folder.

6. Run:

```bash
python train_model.py
```

The script trains the classification model and generates:

    models/expense_classifier.joblib
    models/evaluation.json

Restart the Flask application to load the trained model.

The model file is intended to be generated locally from the downloaded dataset.

## Automated Testing

Run the test suite using:

```bash
python -m pytest tests/ -v
```

Latest local test result:

    10 passed

The tests validate core functionality and API behavior. They do not independently establish the ML model's real-world accuracy.

## Screenshots

### Financial Dashboard

Screenshot to be added.

### Spending Analytics

Screenshot to be added.

### ML Category Prediction

Screenshot to be added.

## Technical Concepts Demonstrated

- Full-stack web application development
- Python and Flask backend programming
- Relational database integration
- SQL and CRUD operations
- Input validation
- NLP-based text classification
- TF-IDF feature extraction
- Machine learning model training
- Train-test evaluation
- Accuracy and F1-score measurement
- Data preprocessing with Pandas and NumPy
- Interactive Plotly visualizations
- Financial anomaly detection
- Statistical expenditure forecasting
- Automated testing with Pytest
- Git and GitHub version control

## Limitations

- The application is primarily designed for local use.
- The application does not connect to real banking systems.
- The ML model is trained using a curated transaction dataset.
- High held-out test accuracy does not guarantee equivalent performance on real financial transactions.
- Spending anomaly detection relies on historical comparison rules.
- Month-end forecasting assumes the current average daily spending rate continues throughout the month.
- User authentication and multi-user account management are not implemented.
- The application is an educational portfolio project, not a production banking system.

## Future Improvements

- Secure user authentication and authorization
- Transaction search and advanced filters
- CSV transaction export
- Category-specific budget management
- More representative ML training data
- Additional model evaluation and error analysis
- Automated deployment and CI/CD

## Author

**Gurleen Kaur Sawhney**

GitHub: https://github.com/gurl33n-ks



