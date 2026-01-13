import csv
from datetime import datetime, timedelta
from pathlib import Path


class DailyCSVLogger:
    def __init__(self, log_dir: str = "logs", retention_days: int = 7):
        """
        Daily CSV logger with automatic deletion of old files.

        Args:
            log_dir: Directory to store CSV logs
            retention_days: Number of days to keep old logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.retention_days = retention_days
        self.headers = [
            "Timestamp",
            "Battery Voltage",
            "Battery Current",
            "PV Voltage",
            "PV Current",
            "PV PI Temperature"
            ]

        self.current_file = self._get_today_file()

        # Cleanup old logs at startup
        self.cleanup_old_logs()

    def _get_today_file(self) -> Path:
        """Return the Path object for today's CSV file."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{today_str}.csv"

    def cleanup_old_logs(self):
        """Delete CSV files older than retention_days."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        for file in self.log_dir.glob("*.csv"):
            try:
                file_date = datetime.strptime(file.stem, "%Y-%m-%d")
                if file_date < cutoff:
                    file.unlink()
            except ValueError:
                # Skip files that don't match the date pattern
                continue

    def log_row(self, row: list):
        """Append a row to today's CSV file, creating headers if needed."""

        self.cleanup_old_logs()

        self.current_file = self._get_today_file()  # update file if day changed
        write_header = not self.current_file.exists() and bool(self.headers)

        with self.current_file.open("a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(self.headers)
            writer.writerow(row)

    def log_stats(self, bat_v, bat_c, pv_v, pv_c, temp):
        now = datetime.now()
        datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

        row = [
            datetime_str, 
            bat_v, bat_c, 
            pv_v, pv_c,
            temp]

        self.log_row(row)
        



