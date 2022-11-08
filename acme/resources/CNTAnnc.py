#
#	CNTAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CNT : Announceable variant
#

from typing import Optional
from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.AnnouncedResource import AnnouncedResource


class CNTAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR, 
								   ResourceTypes.ACTRAnnc,
								   ResourceTypes.CNT, 
								   ResourceTypes.CNTAnnc, 
								   ResourceTypes.CIN, 
								   ResourceTypes.CINAnnc, 
								   ResourceTypes.FCNT, 
								   ResourceTypes.FCNTAnnc, 
								   ResourceTypes.SUB, 
								   ResourceTypes.TS, 
								   ResourceTypes.TSAnnc ]

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
		'loc': None,
		'lnk': None,

		# Resource attributes
		'mni': None,
		'mbs': None,
		'mia': None,
		'li': None,
		'or': None,
		'disr': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.CNTAnnc, dct, pi = pi, create = create)

