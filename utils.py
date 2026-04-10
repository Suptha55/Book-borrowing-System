import pandas as pd


def load_data(books_path, borrow_path):
    books = pd.read_csv(books_path)
    borrow = pd.read_csv(borrow_path)
    return books, borrow


def save_reports(fine_report, summary):
    fine_report.to_csv("fine_report.csv", index=False)
    summary.to_csv("book_usage_summary.csv", index=False)