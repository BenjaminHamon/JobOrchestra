__copyright__ = None
__version__ = None
__date__ = None


try:
	import bhamon_orchestra_master.__metadata__

	__copyright__ = bhamon_orchestra_master.__metadata__.__copyright__
	__version__ = bhamon_orchestra_master.__metadata__.__version__
	__date__ = bhamon_orchestra_master.__metadata__.__date__

except ImportError:
	pass
