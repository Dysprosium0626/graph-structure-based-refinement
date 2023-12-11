import json
import os


def dictionary_to_json(dictionary: dict, file_path: str):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(file_path, 'w') as fp:
        json.dump(dictionary, fp)


if __name__ == "__main__":

    dictionary_to_json({"a": 1}, "./1.json")
