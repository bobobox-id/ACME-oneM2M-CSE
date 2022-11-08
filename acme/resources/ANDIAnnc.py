#
#	ANDIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ANDI : Announceable variant
#

from __future__ import annotations

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.MgmtObjAnnc import *

# TODO resourceMappingRules, announceSyncType, owner

class ANDIAnnc(MgmtObjAnnc):

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes for announced resources
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'lbl': None,
		'acpi':None,
		'daci': None,
		'ast': None,
		'lnk': None,

		# MgmtObj attributes
		'mgd': None,
		'obis': None,
		'obps': None,
		'dc': None,
		'mgs': None,
		'cmlk': None,

		# Resource attributes
		'dvd': None,
		'dvt': None,
		'awi': None,
		'sli': None,
		'sld': None,
		'ss': None,
		'lnh': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.ANDI, create = create)

