import pandas as pd
import sys

class TurbostatProcessor():
    """
    A class used to process turbostat data files and generate a CSV result with power consumption statistics.

    Attributes
    ----------
    path_turbostat : str
        The path to the input turbostat CSV file.
    path_result : str
        The path where the resulting CSV file will be saved.
    block : int
        The block size for calculating metrics like average and variance.
    df : pandas.DataFrame
        DataFrame used to store the parsed turbostat data.
    df_metrics : pandas.DataFrame
        DataFrame used to store the calculated metrics such as average and variance of power consumption.
    
    Methods
    -------
    __init__(path_turbostat, path_result, block)
        Initializes a new TurbostatProcessor object with input file paths and block size.
    load_data()
        Loads the turbostat CSV data into a pandas DataFrame.
    calculate_metrics()
        Calculates average and variance of power consumption (PkgWatt) per block.
    save_results()
        Saves the calculated metrics to a CSV result file.
    """
    
    def __init__(self, path_turbostat: str, path_result: str, block: int):
        """
        Initializes the TurbostatProcessor object with input file paths and block size.

        Parameters
        ----------
        path_turbostat : str
            The path to the input turbostat CSV file.
        path_result : str
            The path where the resulting CSV file will be saved.
        block : int
            The block size for calculating metrics like average and variance.
        """
        
        self.path_turbostat = path_turbostat
        self.path_result = path_result
        self.block = block
        self.df = pd.DataFrame()
        self.df_metrics = pd.DataFrame()

    def load_data(self) -> None:
        """
        This method reads the input turbostat CSV file and stores it into the instance's DataFrame.
        
        Parameters
        ----------
        None
        """

        self.df = pd.read_csv(self.path_turbostat, sep='\s+')

    def calculate_metrics(self) -> None:
        """
        This method groups the data into blocks and computes:
        - Timestamp: The first timestamp in each block.
        - PkgWattAvg: The average power consumption (PkgWatt) in each block.
        - PkgWattVar: The variance of power consumption (PkgWatt) in each block.
        - Samples: The number of rows per block (defined by the block size).

        Parameters
        ----------
        None
        """

        self.df_metrics['Timestamp'] = self.df['Time_Of_Day_Seconds'].groupby(self.df.index // self.block).first()
        self.df_metrics['PkgWattAvg'] = self.df['PkgWatt'].groupby(self.df.index // self.block).mean()
        self.df_metrics['PkgWattVar'] = self.df['PkgWatt'].groupby(self.df.index // self.block).var()
        self.df_metrics['Samples'] = self.block

    def save_results(self) -> None:
        """
        This method writes the calculated metrics to the output CSV file.

        Parameters
        ----------
        None
        """

        self.df_metrics.to_csv(self.path_result, index=False)


def main():
    """
    Main function to execute the TurbostatProcessor.

    This function expects three command-line arguments:
    - path_turbostat: Path to the turbostat input CSV file.
    - path_result: Path to save the resulting output CSV file.
    - block: The number of rows per block to group the data for statistics calculation.
    """

    path_turbostat = sys.argv[1]
    path_result = sys.argv[2]
    block = int(sys.argv[3])

    ts = TurbostatProcessor(path_turbostat, path_result, block)
    ts.load_data()
    ts.calculate_metrics()
    ts.save_results()


if __name__ == "__main__":
    main()