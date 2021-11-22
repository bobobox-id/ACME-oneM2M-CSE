#
#	CSEBaseAnnc.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CNT : Announceable variant
#


from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.AnnouncedResource import AnnouncedResource


class CSEBaseAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.ACP, T.ACPAnnc, T.AE, T.AEAnnc, T.CNT, T.CNTAnnc, T.FCNT, T.FCNTAnnc, T.GRP, T.GRPAnnc, T.NOD
	, T.NODAnnc, T.SUB, T.TS, T.TSAnnc ]


	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'lbl': None,
		'loc': None,	
		'hld': None,
		'acpi': None,
		'daci': None,
		'lnk': None,

		# Resource attributes
		'esi': None,
		'srv': None,
		# TODO no CSI?
	}


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.CSEBaseAnnc, dct, pi=pi, create=create)
