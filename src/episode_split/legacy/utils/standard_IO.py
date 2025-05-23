import json
import pandas as pd


def read_json_file(file_path):
    """
    Reads a JSON file and returns its content as a Python data structure.

    Parameters:
    - file_path (str): Path to the JSON file.

    Returns:
    - dict: Content of the JSON file.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' contains invalid JSON.")
        return None


def read_csv_file(file_path):
    """
    Reads a CSV file and returns its content as a Python data structure.

    Parameters:
    - file_path (str): Path to the CSV file.

    Returns:
    - dict: Content of the CSV file.
    """
    try:
        data = pd.read_csv(file_path)
        return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
