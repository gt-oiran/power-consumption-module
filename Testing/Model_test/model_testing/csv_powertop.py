import os
import csv
import pandas as pd
from datetime import datetime
import re
import sys
import numpy as np

class PowertopProcessor:
    """
    This class handles the analysis of PowerTOP log files, calculating moving averages of power consumption
    and saving the processed results in a CSV file.

    Attributes
    ----------
    col : int
        The index of the column in the CSV files containing the power data description.
    desc : str
        The substring used to identify the process in the logs.
    file_name : str
        The identifier for PowerTOP log files.
    path : str
        The directory path where the PowerTOP log files are located.
    results : str
        The base name used to save the generated result files.
    files : list
        A list of filenames in the specified directory containing the PowerTOP log files.
    df : pandas.DataFrame
        A DataFrame used to store the data extracted from the log files.
    df_metrics : pandas.DataFrame
        A DataFrame used to store the moving average of power consumption.
    window_size : int
        The number of items in the moving window to perform the operation.

    Methods
    -------
    __init__(path: str, results: str, window_size: int)
        Initializes a new PowertopProcessor object with the directory path, result base name, and window size.
    load_data() -> None
        Loads the PowerTOP log data and stores it in the instance's DataFrame.
    set_ts(ts: int) -> None
        Adds a new timestamp to the DataFrame as a new row.
    set_pw(ts: int, pid: str, pw: float) -> None
        Updates the DataFrame with power consumption values for a specific timestamp and process ID.
    conv_w(string: str) -> float
        Converts a power consumption string (in various units) to a value in watts.
    sum_col(df: pandas.DataFrame) -> list
        Sums the values of each row in the DataFrame (excluding the timestamp column).
    window() -> None
        Calculates the moving average of power consumption.
    save_results() -> None
        Saves the calculated metrics to a CSV file.
    process_files() -> None
        Processes the PowerTOP log files in the specified directory, extracting relevant data.
    """

    def __init__(self, path: str, results: str, window_size: int):
        """
        Initializes the PowertopProcessor object with the directory path, result base name, and window size.

        Parameters
        ----------
        path : str
            The directory path where the PowerTOP log files are located.
        results : str
            The base name used to save the generated result files.
        window_size : int
            The window size for calculating moving averages.
        """

        self._col = 6
        self._desc = '//gnb -c'
        self._file_name = 'powertop'
        self._path = path
        self._results = results
        self._files = os.listdir(self._path)
        self._df = pd.DataFrame(columns=['Timestamp'])
        self._df_metrics = pd.DataFrame()
        self._window_size = window_size

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, value: int):
        self._col = value

    @property
    def desc(self):
        return self._desc

    @desc.setter
    def desc(self, value: str):
        self._desc = value

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, value: str):
        self._file_name = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value: str):
        self._path = value

    @property
    def results(self):
        return self._results

    @results.setter
    def results(self, value: str):
        self._results = value

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, value: list):
        self._files = value

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, value: pd.DataFrame):
        self._df = value

    @property
    def df_metrics(self):
        return self._df_metrics

    @df_metrics.setter
    def df_metrics(self, value: pd.DataFrame):
        self._df_metrics = value

    @property
    def window_size(self):
        return self._window_size

    @window_size.setter
    def window_size(self, value: int):
        self._window_size = value

    def load_data(self) -> None:
        """
        This method reads the PowerTOP CSV files, processes each log file, and stores the extracted data
        in the instance's DataFrame.
        """

        for file in self.files:
            if self.file_name in file:
                ts = int(datetime.strptime(file, 'powertop-%Y%m%d-%H%M%S.csv').timestamp())
                self.set_ts(ts)

                with open(os.path.join(self.path, file), 'r') as file:
                    file_n = csv.reader(file, delimiter=';')
                    for row in file_n:
                        if len(row) > self.col and self.desc in row[self.col]:
                            pid = re.search(r'\[(.*?)\]', row[self.col]).group(1)
                            pw = self.conv_w(row[7])
                            self.set_pw(ts, pid, pw)

    def set_ts(self, ts: int) -> None:
        """
        This method adds a new row to the DataFrame where the first column is the timestamp.

        Parameters
        ----------
        ts : int
            The timestamp value to be added as a new row in the DataFrame.
        """

        new_row = [ts] + [np.nan] * (self.df.shape[1] - 1)
        self.df.loc[len(self.df)] = new_row

    def set_pw(self, ts: int, pid: str = None, pw: float = None) -> None:
        """
        Updates the DataFrame with power consumption values for a specific timestamp and process ID.

        Parameters
        ----------
        ts : int
            The timestamp corresponding to the row to be updated.
        pid : str, optional
            The process ID associated with the power consumption value (default is None).
        pw : float, optional
            The power consumption value in watts (default is None).
        """

        self.df.loc[self.df['Timestamp'] == ts, pid] = pw

    def conv_w(self, string: str) -> float:
        """
        This method converts power consumption values from units like mW and μW to watts.

        Parameters
        ----------
        string : str
            The power consumption string, which may be in different units (e.g., "mW", "μW").

        Returns
        -------
        float
            The power consumption value converted to watts.
        """

        num = float(string.split()[0])
        if 'mW' in string:
            num *= 0.001
        elif '\u03BCW' in string or 'uW' in string:
            num *= 0.000001
        return num

    def sum_col(self, df: pd.DataFrame) -> list:
        """
        This method sums all the values of each row in the DataFrame (excluding the timestamp column).

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame containing the power consumption data.

        Returns
        -------
        list
            A list containing the sum of each row in the DataFrame.
        """

        return df.sum(axis=1).tolist()

    def window(self) -> None:
        """
        This method calculates the moving average of power consumption.
        """

        self.df_metrics['Timestamp'] = self.df['Timestamp']
        self.df_metrics['ProcWatt'] = self.df['ProcWatt'].rolling(window=self.window_size).mean()

    def save_results(self) -> None:
        """
        This method saves two CSV files:
        1. The metrics file, which contains power consumption statistics (mean, variance, and sample count).
        2. The full data file, which contains the original and processed data with timestamps and power consumption values.
        """

        self.df_metrics.to_csv(self.results + '.csv', index=False)
        self.df.to_csv(self.results + '-full.csv', index=False)

    def process_files(self) -> None:
        """
        This method extracts timestamps, PIDs, and power consumption information from the PowerTOP logs,
        updates the DataFrame with these values, calculates the power consumption metrics, and saves the results.
        """

        self.load_data()
        self.df = self.df.sort_values(by='Timestamp')
        self.df.replace(np.nan, 0, inplace=True)
        self.df['ProcWatt'] = self.sum_col(self.df.iloc[:, 1:])
        self.window()
        self.save_results()

def main():
    """
    This function parses the command-line arguments for the path to the PowerTOP log files, the base name for saving the results,
    and the window size for aggregating the metrics. It then processes the files using the PowertopProcessor class.
    """
    
    path = sys.argv[1]
    results = sys.argv[2]
    window_size = int(sys.argv[3])

    pt = PowertopProcessor(path, results, window_size)
    pt.process_files()

if __name__ == "__main__":
    main()
