# Employee API (Flask)



This project is a simple **Employee Management REST API** built with **Flask** and **Flask‑SQLAlchemy**, featuring:

- **User registration and login** with hashed passwords (`bcrypt`)
- **JWT-based authentication** (`PyJWT`)
- CRUD endpoints for managing employees, stored in a local **SQLite** database


## Requirements

- Python 3.10+ (recommended)
- `pip` (Python package manager)


## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Shivani-Chauhan-Dev/employee_api_task.git
   cd employee_api_task
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux / macOS
   ```

3. **Install dependencies** from `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

## Running the App

From the project root (where `main.py` is located), run:

```bash
python main.py
```

The server will start in **debug mode** on port **5000**:

- Base URL: `http://127.0.0.1:5000`

On first run, the app will create `employees.db` in the `instance` folder (if it doesn't already exist) and set up the required tables.


## Testing

The project includes a comprehensive test suite using **pytest**. To run the tests:

```bash
pytest
```

For more verbose output:

```bash
pytest -vv
```

The test suite covers:
- User registration and login endpoints
- Edge cases (duplicate emails, invalid credentials, etc.)
- All CRUD operations for employees
- Authentication requirements
- Error handling (404s, 400s, 401s)

## Main Endpoints (Summary)

- **Auth**
  - `POST /api/register` – Register a new user (email, password)
  - `POST /api/login` – Login and receive a JWT token

- **Employees** (all require `Authorization: Bearer <JWT>`)
  - `POST /api/employees` – Create an employee
  - `GET /api/employees/` – List employees (with optional filtering & pagination)
  - `GET /api/employees/<emp_id>/` – Get a single employee
  - `PUT /api/employees/<emp_id>/` – Update an employee
  - `DELETE /api/employees/<emp_id>/` – Delete an employee




