import unittest
import pandas as pd
from processor import LibraryProcessor


class TestLibraryProcessor(unittest.TestCase):

    def setUp(self):
        self.books = pd.DataFrame({
            "book_id": [1, 2]
        })

    def test_invalid_book_rejected(self):
        borrow = pd.DataFrame({
            "book_id": [1, 999],  # invalid
            "borrow_date": ["01-01-2024", "01-01-2024"],
            "return_date": ["02-01-2024", "02-01-2024"]
        })

        p = LibraryProcessor(self.books, borrow)
        p.validate_records()

        self.assertEqual(len(p.borrow), 1)

    def test_invalid_date_ignored(self):
        borrow = pd.DataFrame({
            "book_id": [1],
            "borrow_date": ["bad-date"],
            "return_date": ["02-01-2024"]
        })

        p = LibraryProcessor(self.books, borrow)
        p.validate_records()

        self.assertEqual(len(p.borrow), 0)

    def test_no_fine_within_due_date(self):
        borrow = pd.DataFrame({
            "book_id": [1],
            "borrow_date": ["01-01-2024"],
            "return_date": ["05-01-2024"]  # 4 days
        })

        p = LibraryProcessor(self.books, borrow)
        p.validate_records()
        p.calculate_fines()

        self.assertEqual(p.borrow.iloc[0]["fine"], 0)
        self.assertFalse(p.borrow.iloc[0]["late_return"])

    def test_fine_calculation(self):
        borrow = pd.DataFrame({
            "book_id": [1],
            "borrow_date": ["01-01-2024"],
            "return_date": ["10-01-2024"]  # 9 days → 4 extra
        })

        p = LibraryProcessor(self.books, borrow)
        p.validate_records()
        p.calculate_fines()

        self.assertEqual(p.borrow.iloc[0]["fine"], 80)

    def test_late_return_flag(self):
        borrow = pd.DataFrame({
            "book_id": [1],
            "borrow_date": ["01-01-2024"],
            "return_date": ["10-01-2024"]
        })

        p = LibraryProcessor(self.books, borrow)
        p.validate_records()
        p.calculate_fines()

        self.assertTrue(p.borrow.iloc[0]["late_return"])


if __name__ == "__main__":
    unittest.main()
