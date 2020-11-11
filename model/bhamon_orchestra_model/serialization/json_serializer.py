import json
import os
from typing import Any, Optional

from bhamon_orchestra_model.serialization.serializer import Serializer


class JsonSerializer(Serializer):


	def __init__(self, indent = None) -> None:
		self.indent = indent


	def get_content_type(self) -> str:
		return "application/json"


	def get_file_extension(self) -> str:
		return ".json"


	def serialize_to_file(self, path: str, value: Optional[Any]) -> None:
		with open(path + ".tmp", mode = "w", encoding = "utf-8") as data_file:
			json.dump(value, data_file, indent = self.indent)
		os.replace(path + ".tmp", path)


	def deserialize_from_file(self, path: str) -> Optional[Any]:
		with open(path, mode = "r", encoding = "utf-8") as data_file:
			return json.load(data_file)


	def serialize_to_string(self, value: Optional[Any]) -> str:
		return json.dumps(value, indent = self.indent)


	def deserialize_from_string(self, serialized_value: str) -> Optional[Any]:
		return json.loads(serialized_value)
