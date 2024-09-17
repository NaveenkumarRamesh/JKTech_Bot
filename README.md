
# Book Review API**

This is a FastAPI-based application for managing books and reviews, with LLM integration for generating summaries and recommendations.

## Prerequisites

- Python 3.10+
- PostgreSQL database
- Docker (for containerized deployment)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/NaveenkumarRamesh/JKTech_Bot.git
cd JKTech_Bot
```

### 2. Install Dependencies

First, ensure you have a virtual environment set up to isolate your project dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Next, install the necessary Python libraries:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

You'll need to create a `.env` file to configure your environment variables (e.g., database URL, API keys). Here's an example of what your `.env` file should look like:

```
DATABASE_URL=postgresql://user:password@localhost/db_name
LLM_API_KEY=your_llm_api_key
```

### 4. Set Up the PostgreSQL Database

Make sure PostgreSQL is running. You can install it using the following command (for Ubuntu):

```bash
sudo apt-get install postgresql postgresql-contrib
```

Then create a database and a user:

```bash
sudo -u postgres psql
CREATE DATABASE book_review_db;
CREATE USER book_review_user WITH PASSWORD 'password';
ALTER ROLE book_review_user SET client_encoding TO 'utf8';
ALTER ROLE book_review_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE book_review_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE book_review_db TO book_review_user;
```

### 5. Apply Database Migrations

You can use Alembic or SQLAlchemy to handle database migrations. If using Alembic, run the following commands:

```bash
alembic upgrade head
```

### 6. Start the Application

Run the FastAPI application by executing the following command:

```bash
uvicorn app_start:app --reload
```

This will start the application, and you can access it at [http://127.0.0.1:8000](http://127.0.0.1:8000).

### 7. Running with Docker (Optional)

If you prefer to use Docker for containerized deployment, you can follow these steps:

1. Build the Docker image:

```bash
docker build -t book_review_api .
```

2. Run the Docker container:

```bash
docker run -d --name book_review_api -p 8000:8000 book_review_api
```

This will run the API inside a Docker container, and you can still access it at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

### Files
- `Dockerfile`: Contains the Docker instructions to set up and run the container.
- `app_start.py`: Entry point for starting the FastAPI app.

---
