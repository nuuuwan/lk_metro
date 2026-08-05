import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, ClassVar, TypeVar


DataType = TypeVar("DataType", bound="AbstractData")


class AbstractData:
	DATA_FILE: ClassVar[str]

	@classmethod
	def read_all(cls: type[DataType]) -> list[DataType]:
		data_path = Path(__file__).resolve().parents[2] / "data" / cls.DATA_FILE

		with data_path.open(encoding="utf-8") as file:
			records = json.load(file)

		if not isinstance(records, list):
			raise ValueError(f"Expected a JSON list in {data_path}")

		instances = []
		for index, record in enumerate(records):
			if not isinstance(record, dict):
				raise ValueError(
					f"Expected an object at index {index} in {data_path}"
				)
			instances.append(cls(**record))

		return instances

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)
