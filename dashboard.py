from flask import Flask, jsonify, request, render_template
import pandas as pd

app = Flask(__name__)

_fine_report = None
_summary = None
_books = None


def run_dashboard(fine_report: pd.DataFrame, summary: pd.DataFrame, books: pd.DataFrame, host="127.0.0.1", port=5000):
    global _fine_report, _summary, _books

    _fine_report = fine_report.copy()
    _summary = summary.copy()
    _books = books.copy()

    # Normalize column names
    _fine_report.columns = _fine_report.columns.str.strip().str.lower()
    _summary.columns = _summary.columns.str.strip().str.lower()
    _books.columns = _books.columns.str.strip().str.lower()

    # Format dates for JSON
    for col in ["borrow_date", "return_date"]:
        if col in _fine_report.columns:
            _fine_report[col] = pd.to_datetime(_fine_report[col]).dt.strftime("%Y-%m-%d")

    print(f"\nDashboard running at http://{host}:{port}")
    print("Press Ctrl+C to stop.\n")

    app.run(host=host, port=port, debug=False)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/records")
def get_records():
    df = _fine_report.copy()

    # 🔍 Search
    q = request.args.get("q", "").strip().lower()
    if q:
        df = df[
            df["record_id"].str.lower().str.contains(q, na=False)
            | df["user_id"].str.lower().str.contains(q, na=False)
            | df["book_id"].str.lower().str.contains(q, na=False)
        ]

    # Status filter
    status = request.args.get("status", "all")
    if status == "late":
        df = df[df["late_return"] == True]
    elif status == "ontime":
        df = df[df["late_return"] == False]

    # Sorting
    sort = request.args.get("sort", "user_id")
    if sort == "fine":
        df = df.sort_values("fine", ascending=False)
    elif sort == "days":
        df["_days"] = (
            pd.to_datetime(df["return_date"]) - pd.to_datetime(df["borrow_date"])
        ).dt.days
        df = df.sort_values("_days", ascending=False)
        df = df.drop(columns=["_days"])
    else:
        df = df.sort_values("user_id")

    # Stats
    total = len(df)
    late_count = int(df["late_return"].sum())
    total_fine = int(df["fine"].sum())

    # Pagination
    page = int(request.args.get("page", 0))
    page_size = int(request.args.get("page_size", 100))  # increased

    if page < 0:
        page = 0

    start = page * page_size
    end = start + page_size

    df_page = df.iloc[start:end]

    # Response
    records = []
    for _, row in df_page.iterrows():
        borrow_dt = pd.to_datetime(row["borrow_date"])
        return_dt = pd.to_datetime(row["return_date"])
        days = (return_dt - borrow_dt).days

        records.append({
            "record_id": row["record_id"],
            "user_id": row["user_id"],
            "book_id": row["book_id"],
            "borrow_date": str(row["borrow_date"]),
            "return_date": str(row["return_date"]),
            "days": int(days),
            "fine": int(row["fine"]),
            "late_return": bool(row["late_return"]),
        })

    return jsonify({
        "records": records,
        "total": total,
        "late_count": late_count,
        "ontime_count": total - late_count,
        "total_fine": total_fine,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    })


@app.route("/api/summary")
def get_summary():
    df = _summary.copy()

    if "book_name" in _books.columns:
        df = df.merge(_books[["book_id", "book_name"]], on="book_id", how="left")

    records = []
    for _, row in df.iterrows():
        records.append({
            "book_id": row["book_id"],
            "book_name": row.get("book_name", ""),
            "total_borrows": int(row["total_borrows"]),
            "total_fine": int(row["total_fine"]),
        })

    return jsonify({"summary": records})


@app.route("/api/member/<user_id>")
def get_member(user_id):
    df = _fine_report[_fine_report["user_id"].str.upper() == user_id.upper()].copy()

    records = []
    for _, row in df.iterrows():
        borrow_dt = pd.to_datetime(row["borrow_date"])
        return_dt = pd.to_datetime(row["return_date"])
        days = (return_dt - borrow_dt).days

        records.append({
            "record_id": row["record_id"],
            "book_id": row["book_id"],
            "borrow_date": str(row["borrow_date"]),
            "return_date": str(row["return_date"]),
            "days": int(days),
            "fine": int(row["fine"]),
            "late_return": bool(row["late_return"]),
        })

    total_fine = int(df["fine"].sum())
    late_count = int(df["late_return"].sum())

    return jsonify({
        "user_id": user_id.upper(),
        "records": records,
        "total_borrows": len(records),
        "late_count": late_count,
        "total_fine": total_fine,
    })
