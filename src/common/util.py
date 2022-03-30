import json
from typing import Dict, List

from prefect import task


@task
def serialize_to_json(obj):
    """Calls the json.dumps function and returns it's value

    Args:
        obj (_type_): _description_

    Returns:
        _type_: _description_
    """
    return json.dumps(obj)


@task
def extract_value(dictionary: Dict, key: str) -> str:
    """Extracts a value for a given key, from a dictionary

    Args:
        dictionary (Dict): _description_
        key (str): _description_

    Returns:
        str: _description_
    """
    return dictionary.get(key)


@task
def extract_value_from_list(l: List[Dict], key: str):
    """_summary_

    Args:
        l (List[Dict]): _description_
        key (str): _description_

    Returns:
        List: _description_
    """
    return [element.get(key) for element in l]


@task
def flatten_dict_list(list_of_dicts: List[Dict]) -> Dict:
    """Flattens list of dicts into one dict.

    :param list_of_dicts:

    Returns
    -------
    :return: A result Dict
    :rtype: dict
    """
    flattened_dict = dict()

    for d in list_of_dicts:
        flattened_dict = {**flattened_dict, **d}

    return flattened_dict


@task
def nested_dict_to_records(nested_dict: Dict[str, Dict]) -> List[Dict]:
    """
    Processes a dictionary of dictionaries into a flat list of records

    :param nested_dict:

    Returns
    -------
    :return: List[Dict]

    """
    return [{**value, "CustomerID": key} for key, value in nested_dict.items()]


def split_list_into_chunks(l: List, chunk_size: int) -> List[List]:
    """
    Split list into list of lists with length chunk_size

    Parameters
    ----------
    :param l:  Input list
    :param chunk_size: Chunk length

    Returns
    -------
    :return: List[List]: List of lists
    """
    for i in range(0, len(l), chunk_size):
        yield l[i : i + chunk_size]
