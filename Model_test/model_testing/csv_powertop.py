import os
import csv
import pandas as pd
from datetime import datetime
import re
import sys
import numpy as np

class PowertopProcessor:
    """
    This class handles parsing PowerTOP log files, extracting relevant data, calculating power consumption metrics
    (such as average and variance), and saving the processed results into a CSV file.

    Attributes
    ----------
    col : int
        The index of the column in the CSV files that contains the description of power data.
    desc : str
        The identifier substring used to filter rows for relevant data.
    file_name : str
        The identifier for PowerTOP log files.
    path : str
        The directory path where the PowerTOP log files are located.
    results : str
        The base name used for saving the generated result files.
    files : list
        A list of filenames in the specified directory containing PowerTOP log files.
    df : pandas.DataFrame
        DataFrame used to store the parsed data with a 'Timestamp' column.
    block : int
        The block size for calculating metrics like average and variance.
    df_metrics : pandas.DataFrame
        DataFrame used to store the calculated metrics (average and variance of power consumption).

    Methods
    -------
    __init__(path: str, results: str, block: int)
        Initializes a new PowertopProcessor object with directory path, results base name, and block size.
    load_data() -> None
        Loads the PowerTOP log data into a pandas DataFrame.
    set_ts(ts: int) -> None
        Adds a new timestamp to the DataFrame as a new row.
    set_pw(ts: int, pid: str, pw: float) -> None
        Updates the DataFrame with power consumption values for a specific timestamp and process ID.
    conv_w(string: str) -> float
        Converts a power consumption string (in different units) to a value in watts.
    sum_col(df: pandas.DataFrame) -> list
        Sums the values in each row of the DataFrame (excluding the timestamp column).
    calculate_metrics() -> None
        Calculates power consumption statistics (average and variance) for each block.
    save_results() -> None
        Saves the calculated metrics to a CSV file.
    process_files() -> None
        Processes the PowerTOP log files in the specified directory, extracting relevant data.
    """

    def __init__(self, path: str, results: str, block: int):
        """
        Initializes the CSV_PT object with directory path, results base name, and block size.

        Parameters
        ----------
        path : str
            The directory path where the PowerTOP log files are located.
        results : str
            The base name used for saving the generated result files.
        block : int
            The block size for calculating metrics like average and variance.
        """

        self.col = 6
        self.desc = 'gnb'
        self.file_name = 'powertop'
        self.path = path
        self.results = results
        self.files = os.listdir(self.path)
        self.df = pd.DataFrame(columns=['Timestamp'])
        self.df_metrics = pd.DataFrame()
        self.block = block

    def load_data(self) -> None:
        """
        This method reads the input PowerTOP CSV files, processes each log file, and stores the extracted
        information into the instance's DataFrame.

        Parameters
        ----------
        None
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
        This method appends a new row to the DataFrame where the first column is the timestamp.

        Parameters
        ----------
        ts : int
            The timestamp value to add as a new row in the DataFrame.
        """

        new_row = [ts] + [np.nan] * (self.df.shape[1] - 1)
        self.df.loc[len(self.df)] = new_row

    def set_pw(self, ts: int, pid: str = None, pw: float = None) -> None:
        """
        Updates the DataFrame with power consumption values for a specific timestamp and process ID.

        This method updates the corresponding cell in the DataFrame with the provided power consumption value.

        Parameters
        ----------
        ts : int
            The timestamp corresponding to the row to update.
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
            Power consumption string, which can be in different units (e.g., "mW", "μW").

        Returns
        -------
        float
            The converted power consumption value in watts.
        """

        num = float(string.split()[0])
        if 'mW' in string:
            num *= 0.001
        elif '\u03BCW' in string:
            num *= 0.000001
        return num

    def sum_col(self, df: pd.DataFrame) -> list:
        """
        This method sums all columns in each row of the DataFrame (excluding the timestamp column).

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing the power consumption data.

        Returns
        -------
        list
            A list containing the sum of each row in the DataFrame.
        """

        return df.sum(axis=1).tolist()

    def calculate_metrics(self) -> None:
        """
        Calculates power consumption statistics (average and variance) for each block.

        This method groups the data into blocks and computes:
        - Timestamp: The first timestamp in each block.
        - ProcWattAvg: The average power consumption (ProcWatt) in each block.
        - ProcWattVar: The variance of power consumption (ProcWatt) in each block.
        - Samples: The number of rows per block (defined by the block size).

        Parameters
        ----------
        None
        """

        self.df_metrics['Timestamp'] = self.df['Timestamp'].groupby(self.df.index // self.block).first()
        self.df_metrics['ProcWattAvg'] = self.df['ProcWatt'].groupby(self.df.index // self.block).mean()
        self.df_metrics['ProcWattVar'] = self.df['ProcWatt'].groupby(self.df.index // self.block).var()
        self.df_metrics['Samples'] = self.block

    def save_results(self) -> None:
        """
        This method saves two CSV files:
        1. The metrics file, which contains power consumption statistics (average, variance, and sample count).
        2. The full data file, which contains the original and processed data with timestamps and power consumption values.

        Parameters
        ----------
        None
        """
        
        self.df_metrics.to_csv(self.results + '.csv', index=False)
        self.df.to_csv(self.results + '-full.csv', index=False)

    def process_files(self) -> None:
        """
        This method extracts timestamps, PIDs, and power consumption information from the PowerTOP logs,
        updates the DataFrame with these values, calculates power consumption metrics, and saves the results.

        Parameters
        ----------
        None
        """

        self.load_data()
        self.df = self.df.sort_values(by='Timestamp')
        self.df.replace(np.nan, 0, inplace=True)
        self.df['ProcWatt'] = self.sum_col(self.df.iloc[:, 1:])
        self.calculate_metrics()
        self.save_results()

def main():
    """
    This function parses command-line arguments for the path to PowerTOP log files, the base name for saving results,
    and the block size for metrics aggregation. It then processes the files using the PowertopProcessor class.

    Parameters
    ----------
    None
    """

    path = sys.argv[1]
    results = sys.argv[2]
    block = int(sys.argv[3])

    pt = PowertopProcessor(path, results, block)

    pt.process_files()

if __name__ == "__main__":
    main()
