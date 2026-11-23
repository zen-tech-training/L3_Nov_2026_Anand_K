
import sqlite3
import json
from datetime import date
from pathlib import Path
from fastmcp import FastMCP

# -----------------------------------
# 1. Initialize MCP Server
# -----------------------------------

mcp = FastMCP("Expense Management Server")

DB_PATH = Path(__file__).parent / "expenses.db"

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Entertainment",
    "Bills",
    "Healthcare",
    "Other"
]


# -----------------------------------
# 2. Database Connection
# -----------------------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                expense_date TEXT NOT NULL
            )
        """)


initialize_database()

@mcp.tool
def add_expense(amount: float, category: str, description: str, expense_date: str):
    """
    Adds a new expense to the database.
    Args:
        amount: Expense amount.
        category: Expense category.
        description: Description of the expense.
        expense_date: Expense Date is in YYYY-MM-DD format.
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO expenses
            (amount, category, description, expense_date)
            VALUES(?, ?, ?, ?)
        """,
        (amount, category, description, expense_date))
        expense_id = cursor.lastrowid
    return f"Expense is added successfully.. ID: {expense_id}"

@mcp.tool
def search_expense(category: str="", start_date: str="", end_date: str="") -> str:
    """
    Searches expenses by category and date range.
    """
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category.strip().title())
    if start_date:
        query += " AND expense_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND expense_date <= ?"
        params.append(end_date)
    if start_date and end_date and start_date > end_date:
        return "Invalid date range"

    query += " ORDER BY expense_date DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return json.dumps([dict(row) for row in rows], indent=2)

@mcp.tool
def get_monthly_summary(month: str) -> str:
    """
    Calculate monthly expense summary.
    Args:
        month: Month in YYYY-MM format
    """
    with get_connection() as conn:
        total = conn.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE strftime('%Y-%m', expense_date) = ?""", (month,)).fetchone()[0]
        category_data = conn.execute("""SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE strftime('%Y-%m', expense_date) = ?
            GROUP BY category
            ORDER BY total DESC
        """,
        (month,)).fetchall()
    result = {
        "month": month,
        "total_expense": total or 0,
        "category_breakdown": [
            dict(row) for row in category_data
        ]
    }
    return json.dumps(result, indent=2)

@mcp.resource("expenses://all")
def get_all_expenses():
    """Read all expense records"""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM expenses ORDER BY expense_date DESC
        """).fetchall()
    return json.dumps([dict(row) for row in rows], indent=2)

@mcp.resource("expenses://categories")
def get_categories():
    """"
    Return all supported expense categories.
    """
    return json.dumps(CATEGORIES, indent=2)


@mcp.resource("expenses://{expense_id}")
def get_expense_by_id(expense_id):
    """
    Retrieves one expense by expense id
    """
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM expenses WHERE id = ?
        """,
        (expense_id,)).fetchone()

    return json.dumps(dict(row), indent=2)

@mcp.prompt()
def analyze_expenses(month) -> str:
    """
    Generate instructions for analyzing expenses.
    """
    return f"""
        You are an expert personal finance assistant.

        Analyze the user's expenses for {month}

        Please:
        1) Calculate total expenses.
        2) Identify the spending category.
        3) Identify unusual spending categories.
        4) Suggest practical ways to save money
    """

@mcp.prompt()
def generate_monthly_expense(month) -> str:
    """
    Generate instructtions for month expense report.
    """

    return f""""
        Generate professional monthly expense report for {month}
        Please include:
        1) Executive summary
        2) Total montly expensdituere
        3) Highest sprnding category
        4) Recommendations
    """

# -----------------------------------
# 11. Run MCP Server
# -----------------------------------

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
