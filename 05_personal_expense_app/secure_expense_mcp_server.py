
import sqlite3
import json
from datetime import date
from pathlib import Path
from fastmcp import FastMCP
from starlette.types import ASGIApp, Scope, Receive, Send
import os
from dotenv import load_dotenv
import uvicorn
import hmac

# How to create API KEY?
# py -c "import secrets; print(secrets.token_urlsafe(48))"
# Add the generated API KEY inside .env as shown below
# MCP_API_KEY=XNFHU0oST2j1YVaUqdozxnNWORBdXiUWw06jW4k4zp5yHifiWLdnL2MS0_iSTylR


load_dotenv()

API_KEY = os.environ.get("MCP_API_KEY")
EXPECTED_AUTH = b"Bearer " + API_KEY.encode("utf-8")

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


# -----------------------------------
# 3. MCP TOOL: Add Expense
# -----------------------------------

@mcp.tool()
def add_expense(
    amount: float,
    category: str,
    description: str,
    expense_date: str = ""
) -> str:
    """
    Add a new expense to the database.

    Args:
        amount: Expense amount.
        category: Expense category.
        description: Description of expense.
        expense_date: Date in YYYY-MM-DD format.
    """

    if amount <= 0:
        return "Error: Amount must be greater than zero."

    category = category.strip().title()

    if category not in CATEGORIES:
        return f"Invalid category. Choose from: {CATEGORIES}"

    if not expense_date:
        expense_date = date.today().isoformat()

    try:
        date.fromisoformat(expense_date)
    except ValueError:
        return "Invalid date. Use YYYY-MM-DD."

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO expenses
            (amount, category, description, expense_date)
            VALUES (?, ?, ?, ?)
        """, (amount, category, description, expense_date))

        expense_id = cursor.lastrowid

    return f"Expense added successfully. ID: {expense_id}"


# -----------------------------------
# 4. MCP TOOL: Search Expenses
# -----------------------------------

@mcp.tool()
def search_expenses(
    category: str = "",
    start_date: str = "",
    end_date: str = ""
) -> str:
    """
    Search expenses by category and date range.
    All filters are optional.
    """

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category.strip().title())

    if start_date:
        try:
            date.fromisoformat(start_date)
        except ValueError:
            return "Invalid start date. Use YYYY-MM-DD."

        query += " AND expense_date >= ?"
        params.append(start_date)

    if end_date:
        try:
            date.fromisoformat(end_date)
        except ValueError:
            return "Invalid end date. Use YYYY-MM-DD."

        query += " AND expense_date <= ?"
        params.append(end_date)

    if start_date and end_date and start_date > end_date:
        return "Start date must not be after end date."

    query += " ORDER BY expense_date DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return json.dumps(
        [dict(row) for row in rows],
        indent=2
    )


# -----------------------------------
# 5. MCP TOOL: Monthly Summary
# -----------------------------------

@mcp.tool()
def get_monthly_summary(month: str) -> str:
    """
    Calculate monthly expense summary.

    Args:
        month: Month in YYYY-MM format.
    """

    try:
        parsed_month = date.fromisoformat(month + "-01")
    except ValueError:
        return "Invalid month. Use YYYY-MM."

    with get_connection() as conn:

        total = conn.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE strftime('%Y-%m', expense_date) = ?
        """, (month,)).fetchone()[0]

        category_data = conn.execute("""
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE strftime('%Y-%m', expense_date) = ?
            GROUP BY category
            ORDER BY total DESC
        """, (month,)).fetchall()

    result = {
        "month": month,
        "total_expense": total or 0,
        "category_breakdown": [
            dict(row) for row in category_data
        ]
    }

    return json.dumps(result, indent=2)


# -----------------------------------
# 6. MCP RESOURCE: All Expenses
# -----------------------------------

@mcp.resource("expenses://all")
def get_all_expenses() -> str:
    """
    Read all expense records.
    """

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM expenses
            ORDER BY expense_date DESC
            LIMIT 1000
        """).fetchall()

    return json.dumps(
        [dict(row) for row in rows],
        indent=2
    )


# -----------------------------------
# 7. MCP RESOURCE: Categories
# -----------------------------------

@mcp.resource("expenses://categories")
def get_categories() -> str:
    """
    Return all supported expense categories.
    """

    return json.dumps(CATEGORIES, indent=2)


# -----------------------------------
# 8. MCP RESOURCE: Expense By ID
# -----------------------------------

@mcp.resource("expenses://{expense_id}")
def get_expense_by_id(expense_id: int) -> str:
    """
    Retrieve one expense using its ID.
    """

    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM expenses
            WHERE id = ?
        """, (expense_id,)).fetchone()

    if row is None:
        return "Expense not found."

    return json.dumps(dict(row), indent=2)


# -----------------------------------
# 9. MCP PROMPT: Analyze Expenses
# -----------------------------------

@mcp.prompt()
def analyze_expenses(month: str) -> str:
    """
    Generate instructions for analyzing expenses.
    """

    return f"""
    You are a personal finance assistant.

    Analyze the user's expenses for {month}.

    Please:
    1. Calculate total expenses.
    2. Identify the highest spending category.
    3. Identify unusual spending patterns.
    4. Suggest practical ways to save money.
    5. Provide a concise financial summary.

    Use the expense data provided through
    the available MCP resources or tools.

    Never invent missing financial information.
    """


# -----------------------------------
# 10. MCP PROMPT: Monthly Report
# -----------------------------------

@mcp.prompt()
def generate_monthly_report(month: str) -> str:
    """
    Generate instructions for a monthly report.
    """

    return f"""
    Generate a professional monthly expense report
    for {month}.

    Include:

    1. Executive summary
    2. Total monthly expenditure
    3. Category-wise breakdown
    4. Highest spending category
    5. Spending observations
    6. Recommendations

    Use only the actual expense data.
    Format the response using Markdown tables.
    """





# --------------------------------------------------
# Authentication Middleware
# --------------------------------------------------

class APIKeyMiddleware:

    def __init__(
        self,
        app: ASGIApp,
        expected_auth: bytes,
    ):
        self.app = app
        self.expected_auth = expected_auth

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ):

        # Pass non-HTTP ASGI events through.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Require exactly one Authorization header.
        auth_headers = [
            value
            for name, value in scope.get("headers", [])
            if name.lower() == b"authorization"
        ]

        authenticated = (
            len(auth_headers) == 1
            and hmac.compare_digest(
                auth_headers[0],
                self.expected_auth,
            )
        )

        if not authenticated:

            body = json.dumps({
                "error": "unauthorized",
                "message": "Valid API key required",
            }).encode("utf-8")

            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"cache-control", b"no-store"),
                    (b"www-authenticate", b'Bearer realm="mcp"'),
                ],
            })

            await send({
                "type": "http.response.body",
                "body": body,
            })

            return

        # Authentication succeeded.
        await self.app(scope, receive, send)


# --------------------------------------------------
# ASGI Application
# --------------------------------------------------

#mcp_http_app = mcp.streamable_http_app()
mcp_http_app = mcp.http_app()

app = APIKeyMiddleware(
    app=mcp_http_app,
    expected_auth=EXPECTED_AUTH,
)


# -----------------------------------
# 11. Run MCP Server
# -----------------------------------

if __name__ == "__main__":
    #mcp.run(transport="http", port=8000)
    uvicorn.run(
        app,
        port=8000
    )
