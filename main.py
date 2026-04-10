from processor import LibraryProcessor
import pandas as pd


def main():
    books = pd.read_csv("books.csv")
    borrow = pd.read_csv("borrow_records.csv")

    processor = LibraryProcessor(books, borrow)

    processor.validate_records()
    processor.calculate_fines()

    fine_report, summary = processor.generate_reports()

    fine_report.to_csv("fine_report.csv", index=False)
    summary.to_csv("book_usage_summary.csv", index=False)

    print("Reports generated successfully!")


if __name__ == "__main__":
    main()