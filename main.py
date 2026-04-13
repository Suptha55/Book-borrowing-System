from processor import LibraryProcessor
import pandas as pd
import sys


def main():
    # Load data
    books = pd.read_csv("books.csv")
    borrow = pd.read_csv("borrow_records.csv")

    processor = LibraryProcessor(books, borrow)

    processor.validate_records()
    processor.calculate_fines()

    fine_report, summary = processor.generate_reports()

    # Save outputs
    fine_report.to_csv("fine_report.csv", index=False)
    summary.to_csv("book_usage_summary.csv", index=False)

    print("Reports generated successfully!")

    # FINE NOTIFICATIONS
    if "--notify" in sys.argv:
        from notifier import send_fine_notices
        send_fine_notices(fine_report)

    # Dashboard
    if "--dashboard" in sys.argv:
        from dashboard import run_dashboard
        run_dashboard(fine_report, summary, books)


if __name__ == "__main__":
    main()
