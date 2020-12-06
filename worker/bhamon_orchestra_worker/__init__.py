__product__ = None
__copyright__ = None
__version__ = None
__date__ = None


try:
	import bhamon_orchestra_worker.__metadata__

	__product__ = bhamon_orchestra_worker.__metadata__.__product__
	__copyright__ = bhamon_orchestra_worker.__metadata__.__copyright__
	__version__ = bhamon_orchestra_worker.__metadata__.__version__
	__date__ = bhamon_orchestra_worker.__metadata__.__date__

except ImportError:
	pass
