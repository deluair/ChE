import pandas as pd

class CSVDataReader:
    """Reads historical process data from a CSV file and provides an interface to query it."""
    def __init__(self, file_path):
        """
        Args:
            file_path (str): The path to the CSV file containing the historical data.
        """
        try:
            self.data = pd.read_csv(file_path, index_col='timestamp', parse_dates=True)
            print(f"Successfully loaded data from {file_path}")
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
            self.data = pd.DataFrame()

    def get_data_at_timestamp(self, timestamp):
        """
        Retrieves the process data for a specific timestamp.

        Args:
            timestamp (pd.Timestamp or str): The timestamp for which to retrieve data.

        Returns:
            pd.Series: A series containing the data for the requested timestamp, or None if not found.
        """
        try:
            # Use asof to find the nearest data point before or at the given timestamp
            return self.data.asof(timestamp)
        except KeyError:
            return None

# Example Usage:
if __name__ == '__main__':
    # Path to the generated data file
    data_path = '../../data/historical_process_data.csv'

    # Create a data reader instance
    reader = CSVDataReader(file_path=data_path)

    if not reader.data.empty:
        # Define a timestamp to query
        query_time = pd.Timestamp('2022-05-15 10:00:00')

        # Get the data
        process_data = reader.get_data_at_timestamp(query_time)

        if process_data is not None:
            print(f"\nData at {query_time}:")
            print(process_data)
        else:
            print(f"No data found at or before {query_time}")
