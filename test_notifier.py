import os
import unittest
import pandas as pd
from unittest.mock import patch
import tempfile

from notifier import (
    send_fine_notices,
    LOG_FILE,
)

SEND_PATH = "notifier._send_email"


def _make_record(record_id, user_id, book_id, borrow_date, return_date,
                 fine, late_return, email="user@example.com"):
    return {
        "record_id": record_id,
        "user_id": user_id,
        "book_id": book_id,
        "borrow_date": pd.Timestamp(borrow_date),
        "return_date": pd.Timestamp(return_date),
        "fine": fine,
        "late_return": late_return,
        "email": email,
    }


class TestFineNotices(unittest.TestCase):

    def test_only_sends_to_late_records(self):
        df = pd.DataFrame([
            _make_record("R1", "U1", "B1", "2024-01-01", "2024-01-05", 0, False),
            _make_record("R2", "U2", "B2", "2024-01-01", "2024-01-10", 100, True),
        ])

        with patch(SEND_PATH, return_value=True) as mock_send:
            send_fine_notices(df)
            self.assertEqual(mock_send.call_count, 1)

    def test_skips_no_email(self):
        df = pd.DataFrame([
            _make_record("R2", "U2", "B2", "2024-01-01", "2024-01-10", 100, True, email="")
        ])

        with patch(SEND_PATH, return_value=True) as mock_send:
            send_fine_notices(df)
            mock_send.assert_not_called()

    def test_fine_in_subject(self):
        df = pd.DataFrame([
            _make_record("R2", "U2", "B2", "2024-01-01", "2024-01-10", 100, True)
        ])

        with patch(SEND_PATH, return_value=True) as mock_send:
            send_fine_notices(df)
            subject = mock_send.call_args[0][1]
            self.assertIn("100", subject)


class TestNotificationLog(unittest.TestCase):

    def test_log_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "notification_log.csv")

            import notifier
            notifier.LOG_FILE = log_path

            df = pd.DataFrame([
                _make_record("R2", "U2", "B2", "2024-01-01", "2024-01-10", 100, True)
            ])

            with patch(SEND_PATH, return_value=True):
                send_fine_notices(df)

            self.assertTrue(os.path.isfile(log_path))

            log_df = pd.read_csv(log_path)
            self.assertEqual(len(log_df), 1)
            self.assertEqual(log_df.iloc[0]["Type"], "fine")
            self.assertEqual(log_df.iloc[0]["Status"], "Sent")



    def test_log_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "notification_log.csv")

            import notifier
            notifier.LOG_FILE = log_path

            df = pd.DataFrame([
                _make_record("R2", "U2", "B2", "2024-01-01", "2024-01-10", 100, True)
            ])

            with patch(SEND_PATH, return_value=False):
                send_fine_notices(df)

            log_df = pd.read_csv(log_path)
            self.assertEqual(log_df.iloc[0]["Status"], "Failed")


if __name__ == "__main__":
    unittest.main()
