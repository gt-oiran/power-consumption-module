import pandas as pd
import sys

class TurbostatProcessor:
    """
    A class used to process turbostat data files and generate a CSV result with power consumption statistics.

    Attributes
    ----------
    path_turbostat : str
        The path to the input turbostat CSV file.
    path_result : str
        The path where the resulting CSV file will be saved.
    window_size : int
        The rolling window size for averaging power consumption.
    df : pandas.DataFrame
        DataFrame used to store the parsed turbostat data.
    df_metrics : pandas.DataFrame
        DataFrame used to store the calculated average of power consumption metrics.
    
    Methods
    -------
    __init__(path_turbostat, path_result, window_size)
        Initializes a new TurbostatProcessor object with input file paths and rolling window size.
    load_data()
        Loads the turbostat CSV data into the `df` DataFrame.
    window()
        Calculates the rolling average of power consumption (PkgWatt) using the specified window size.
    save_results()
        Saves the calculated power consumption metrics to a CSV result file.
    process_files()
        Orchestrates the entire processing pipeline: loading data, calculating metrics, and saving results.
    """
    
    def __init__(self, path_turbostat: str, path_result: str, window_size: int):
        """
        Initializes the TurbostatProcessor object with input file paths and window size.

        Parameters
        ----------
        path_turbostat : str
            The path to the input turbostat CSV file.
        path_result : str
            The path where the resulting CSV file will be saved.
        window_size : int
            The rolling window size for calculating the power consumption average.
        """
        
        self._path_turbostat = path_turbostat
        self._path_result = path_result
        self._window_size = window_size
        self._df = pd.DataFrame()
        self._df_metrics = pd.DataFrame()

    @property
    def path_turbostat(self) -> str:
        return self._path_turbostat
    
    @path_turbostat.setter
    def path_turbostat(self, path: str) -> None:
        self._path_turbostat = path

    @property
    def path_result(self) -> str:
        return self._path_result
    
    @path_result.setter
    def path_result(self, path: str) -> None:
        self._path_result = path

    @property
    def window_size(self) -> int:
        return self._window_size
    
    @window_size.setter
    def window_size(self, size: int) -> None:
        self._window_size = size

    @property
    def df(self) -> pd.DataFrame:
        return self._df
    
    @df.setter
    def df(self, data: pd.DataFrame) -> None:
        self._df = data

    @property
    def df_metrics(self) -> pd.DataFrame:
        return self._df_metrics
    
    @df_metrics.setter
    def df_metrics(self, metrics: pd.DataFrame) -> None:
        self._df_metrics = metrics

    def load_data(self) -> None:
        """
        Loads the turbostat CSV data into the `df` DataFrame.

        This method reads the input turbostat CSV file, parses it, and stores the data into the `df` attribute.
        The file is expected to be in CSV format with whitespace-separated values.

        Notes
        -----
        - The file should contain columns such as 'Time_Of_Day_Seconds' and 'PkgWatt'.
        """
        
        self.df = pd.read_csv(self._path_turbostat, sep='\s+')

    def window(self) -> None:
        """
        Calculates the rolling average of power consumption (PkgWatt) using the specified window size.

        The method uses the `window_size` attribute to apply a rolling mean to the 'PkgWatt' column 
        of the `df` DataFrame and stores the results in the `df_metrics` DataFrame.

        Parameters
        ----------
        None
        
        Returns
        -------
        None
        
        Notes
        -----
        - The method assumes that the 'PkgWatt' column exists in the `df` DataFrame.
        - The rolling mean is computed on the 'PkgWatt' column and assigned to `df_metrics['PkgWatt']`.
        """
        
        self.df_metrics['Timestamp'] = self.df['Time_Of_Day_Seconds']
        self.df_metrics['PkgWatt'] = self.df['PkgWatt'].rolling(window=self._window_size).mean()

    def save_results(self) -> None:
        """
        Saves the calculated power consumption metrics to the result CSV file.

        This method writes the `df_metrics` DataFrame, which contains the power consumption averages,
        to the file specified in `path_result`.
        
        Notes
        -----
        - The results are saved as a CSV file without the index.
        """
        
        self.df_metrics.to_csv(self._path_result, index=False)

    def process_files(self) -> None:
        """
        Orchestrates the entire processing pipeline: loading data, calculating power consumption metrics,
        and saving the results to the output file.

        This method sequentially calls `load_data()`, `window()`, and `save_results()` to process the 
        turbostat data and produce the final output.
        """
        
        self.load_data()
        self.window()
        self.save_results()


def main():
    """
    Main function to execute the TurbostatProcessor.

    This function expects three command-line arguments:
    - path_turbostat: Path to the turbostat input CSV file.
    - path_result: Path to save the resulting output CSV file.
    - window_size: The rolling window size for calculating power consumption averages.
    """
    
    path_turbostat = sys.argv[1]
    path_result = sys.argv[2]
    window_size = int(sys.argv[3])

    ts = TurbostatProcessor(path_turbostat, path_result, window_size)
    ts.process_files()


if __name__ == "__main__":
    main()
