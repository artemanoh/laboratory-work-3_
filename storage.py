import json
from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):
    @abstractmethod
    def read(self): ...

    @abstractmethod
    def write(self, data): ...


class JsonStorage(Storage):
    def __init__(self, input_file, output_file):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)

    def read(self):
        try:
            with self.input_file.open(encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(f"Помилка формату JSON: {error}") from error
        if not isinstance(data, dict):
            raise ValueError("Очікується JSON-об'єкт")
        return data

    def write(self, data):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with self.output_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)