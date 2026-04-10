import pandas as pd
from datetime import datetime

FINE_PER_DAY = 20
ALLOWED_DAYS = 5


class LibraryProcessor:
    def __init__(self, books_df, borrow_df):
        self.books = books_df.copy()
        self.borrow = borrow_df.copy()

        # Normalize column names
        self.books.columns = self.books.columns.str.strip().str.lower()
        self.borrow.columns = self.borrow.columns.str.strip().str.lower()

        # Ensure book_id exists
        if "book_id" not in self.books.columns:
            raise ValueError("books.csv must contain 'book_id'")

    def validate_records(self):
        # Check valid book_ids
        valid_book_ids = set(self.books["book_id"])

        self.borrow = self.borrow[self.borrow["book_id"].isin(valid_book_ids)]

        # Convert dates
        self.borrow["borrow_date"] = pd.to_datetime(
            self.borrow["borrow_date"], errors="coerce"
        )
        self.borrow["return_date"] = pd.to_datetime(
            self.borrow["return_date"], errors="coerce"
        )

        # Drop invalid dates
        self.borrow = self.borrow.dropna(subset=["borrow_date", "return_date"])

    def calculate_fines(self):
        def compute(row):
            duration = (row["return_date"] - row["borrow_date"]).days

            if duration <= ALLOWED_DAYS:
                return pd.Series([0, False])

            extra_days = duration - ALLOWED_DAYS
            fine = extra_days * FINE_PER_DAY
            return pd.Series([fine, True])

        self.borrow[["fine", "late_return"]] = self.borrow.apply(compute, axis=1)

    def generate_reports(self):
        # Fine report
        fine_report = self.borrow.copy()

        # Book usage summary
        summary = (
            self.borrow.groupby("book_id")
            .agg(
                total_borrows=("book_id", "count"),
                total_fine=("fine", "sum"),
            )
            .reset_index()
        )

        return fine_report, summary