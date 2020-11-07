import logging


def configure_logging_handlers() -> None:
	for handler in logging.root.handlers:
		default_formatter = handler.formatter
		raw_formatter = logging.Formatter("{message}", style = "{")
		handler.formatter = DispatchingFormatter(default_formatter, raw_formatter)


class DispatchingFormatter: # pylint: disable = too-few-public-methods

	def __init__(self, default_formatter: logging.Formatter, raw_formatter: logging.Formatter) -> None:
		self.default_formatter = default_formatter
		self.raw_formatter = raw_formatter

	def format(self, record: logging.LogRecord) -> str:
		formatter = self.default_formatter
		if record.name == "raw":
			formatter = self.raw_formatter
		return formatter.format(record)
