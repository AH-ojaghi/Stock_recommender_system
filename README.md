
## 📈 Stock Recommender System:

This repository contains a complete MLOps pipeline for a stock recommendation system based on a **Learning-to-Rank (LtR)** model. The system predicts the 7-day return potential of stocks, ranks them, and serves the top recommendations via a daily scheduled scoring job exposed through a **FastAPI** web service.

### ⚙️ System Architecture

The system follows a Scheduled Inference pattern:

1.  **Data Source:** Fetches the latest daily engineered features.
2.  **Scoring Engine (`scoring_engine.py`):** Loads the pre-trained `CatBoostRanker` (`.cbm`) and the `StandardScaler` (`.pkl`). It preprocesses the new data, scales it, runs inference, and ranks the results.
3.  **Database (SQLAlchemy/SQLite):** Stores the ranked daily recommendations.
4.  **API (`main.py`):** A FastAPI server exposes the latest ranked recommendations.
5.  **Scheduler:** A background thread manages the daily execution of the Scoring Engine.

### 💡 API Endpoint

Retrieve the latest stock recommendations:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/recommendations/latest` | Returns the latest $\text{TOPK}$ recommendations sorted by rank. |

### 🛑 Production Disclaimer

The included scheduler (`threading.Thread` in `main.py`) is for local demonstration. For production deployment, use dedicated MLOps tools for scheduling and execution (e.g., **Celery**, **Apache Airflow**, or a **Kubernetes CronJob**).
