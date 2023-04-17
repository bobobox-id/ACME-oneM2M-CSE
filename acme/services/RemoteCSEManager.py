#
#	RemoteCSEManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles the registration to remote CSEs as well as the management
#	of remotly registered CSEs in this CSE. It also handles the forwarding of
#	transit requests to remote CSEs.
#

"""	This module implements remote CSR registration service and helper functions. """

from __future__ import annotations
from typing import List, Tuple, Dict, cast, Optional, Any

from ..etc.Types import CSEStatus, ResourceTypes, Result, CSEType, ResponseStatusCode, JSON
from ..etc.ResponseStatusCodes import exceptionFromRSC, ResponseException, NOT_FOUND, BAD_REQUEST, INTERNAL_SERVER_ERROR
from ..etc.Utils import pureResource, csiFromRelativeAbsoluteUnstructured
from ..etc.Constants import Constants
from ..helpers.TextTools import findXPath, setXPath
from ..resources.CSR import CSR
from ..resources.CSEBase import CSEBase, getCSE
from ..resources.Resource import Resource
from ..resources.Factory import resourceFromDict
from ..services.Configuration import Configuration
from ..services import CSE
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..services.Logging import Logging as L


class RemoteCSEManager(object):
	"""	This class defines functionalities to handle remote CSE/CSR registrations.

		Attributes:
			connectionMonitor: A `BackgroundWorker` that periodically checks the registrations.
			ownCSRonRegistrarCSE: The CSR resource on the registrar CSE, or None if not registered.
			registrarCSE: The registrar's CSEBase resource, or None if not registered.
			descendantCSR: A dictionary of descendant CSEs mappings: csi -> (CSR, registeredATcsi)
			registrarAddress: Configuration setting. The physical URL to the registrar CSE.
			registrarRoot: Configuration setting. The optional root path for the `registrarAddress` for the URL to the registrar CSE.
			registrarCSI: Configuration setting. The registrar CSE's CSE-ID.
			registrarCseRN: Configuration setting. The registrar CSE's resource name.
			checkInterval: Configuration setting. The interval in seconds to check for connectivity.
			registrarSerialization: Configuration setting. The request serialization to use when communicating with the registrar CSE.
			checkLiveliness: Configuration setting. Whether to check remote CSE's connectivity.
			excludeCSRAttributes: Configuration setting. Optional list of attributes to exclide from the CSR, eg. when not supported by a remote CSE.
			enableRemoteCSE: Configuration setting. Enable or disable remote registrations.
			registrarCSEURL: The URL to the point-of-access of the registrar CSE. This is a real URL.
			registrarCSEURI: The registrar CSE's CSE-ID and resource name.
			csrOnRegistrarURI: The SP-relative ID of the CSR resource on the registrar CSE.
	"""

	__slots__ = (
		'ownCSRonRegistrarCSE',
		'registrarCSE',
		'connectionMonitor',
		'descendantCSR',

		'registrarAddress',
		'registrarRoot',
		'checkInterval',
		'registrarSerialization',
		'checkLiveliness',
		'registrarCSI',
		'registrarCseRN',
		'excludeCSRAttributes',
		'enableRemoteCSE',
		'registrarCSEURL',
		'registrarCSEURI',
		'csrOnRegistrarURI',

		'_eventRegisteredToRegistrarCSE',
		'_eventDeregisteredFromRegistrarCSE',
	)


	def __init__(self) -> None:
		"""	Class constructor.
		
		"""

		# Some manager attributes
		self.ownCSRonRegistrarCSE:Resource					= None 	# The own CSR at the registrar if there is one
		self.registrarCSE:Resource							= None 	# The registrar CSE if there is one 
		self.connectionMonitor:BackgroundWorker				= None	# BackgroundWorker
		self.descendantCSR:Dict[str, Tuple[Resource, str]]	= {}	# dict of descendantCSR's - "csi : (CSR, registeredATcsi)". CSR is None for CSEs further down 

		# Get the configuration settings
		self._assignConfig()

		#	The following lines register event handlers for registration and de-registration events.
		#	The following events are registered when registerueng and de-registerung from the registrar CSE
		CSE.event.addHandler(CSE.event.registeredToRegistrarCSE, self.handleRegistrarRegistration)				# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRegistrarCSE, self.handleRegistrarDeregistration)		# type: ignore

		#	The following events are usually thrown by the Registration Manager.
		CSE.event.addHandler(CSE.event.registreeCSEHasRegistered, self.handleRegistreeCSERegistration)			# type: ignore
		CSE.event.addHandler(CSE.event.registreeCSEHasDeregistered, self.handleRegistreeCSEDeregistration)		# type: ignore
		CSE.event.addHandler(CSE.event.registreeCSEUpdate, self.handleRegistreeCSEUpdate)							# type: ignore

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)		# type: ignore

		# Add a handler when the CSE is started
		CSE.event.addHandler(CSE.event.cseStartup, self.start)	# type: ignore
		L.isInfo and L.log('RemoteCSEManager initialized')

		# Optimize event handling
		self._eventRegisteredToRegistrarCSE = CSE.event.registeredToRegistrarCSE			# type: ignore [attr-defined]
		self._eventDeregisteredFromRegistrarCSE = CSE.event.deregisteredFromRegistrarCSE	# type: ignore [attr-defined]



	def shutdown(self) -> bool:
		"""	Shutdown the RemoteCSEManager.
		
			Return:
				Always return True.
		"""
		self.stop()
		L.isInfo and L.log('RemoteCSEManager shut down')
		return True


	def restart(self) -> None:
		"""	Restart the remote service monitor.
		"""
		if self.connectionMonitor:
			self.connectionMonitor.workNow()
		L.isDebug and L.logDebug('RemoteManager restarted')


	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		self.registrarAddress		= Configuration.get('cse.registrar.address')
		self.registrarRoot 			= Configuration.get('cse.registrar.root')
		self.checkInterval			= Configuration.get('cse.registrar.checkInterval')
		self.registrarSerialization	= Configuration.get('cse.registrar.serialization')
		self.checkLiveliness		= Configuration.get('cse.registration.checkLiveliness')
		self.registrarCSI			= Configuration.get('cse.registrar.csi')
		self.registrarCseRN			= Configuration.get('cse.registrar.rn')
		self.excludeCSRAttributes	= Configuration.get('cse.registrar.excludeCSRAttributes')
		self.enableRemoteCSE		= Configuration.get('cse.enableRemoteCSE')

		# Set other manager attributes
		self.registrarCSEURL		= f'{self.registrarAddress}{self.registrarRoot}/{self.registrarCSI}/{self.registrarCseRN}'
		self.registrarCSEURI		= f'{self.registrarCSI}/{self.registrarCseRN}'
		self.csrOnRegistrarURI		= f'{self.registrarCSI}{CSE.cseCsi}'


	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'cse.registrar.address', 
						'cse.registrar.root',
						'cse.registrar.checkInterval',
						'cse.registrar.serialization',
						'cse.registration.checkLiveliness',
						'cse.registrar.csi',
						'cse.registrar.rn',
						'cse.registrar.excludeCSRAttributes',
						'cse.enableRemoteCSE' ]:
			return

		# assign new values
		self._assignConfig()


	#########################################################################
	#
	#	Connection Monitor
	#

	def start(self, name:str) -> None:
		"""	Start the remote monitor as a background worker. 
		"""
		if not self.enableRemoteCSE:
			return
		
		L.isDebug and L.logDebug('Rebuild internal descendants list')
		self.descendantCSR.clear()
		for eachCsr in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.CSR):
			if (csi := eachCsr.csi) != self.registrarCSI:			# Skipping the own registrar csr
				L.isDebug and L.logDebug(f'Addind remote CSE: {csi}')
				self.descendantCSR[csi] = (eachCsr, CSE.cseCsi)		# Add the direct child CSR
				
				# Add the descendant CSE's
				if eachCsr.dcse:
					for eachDcse in eachCsr.dcse:
						L.isDebug and L.logDebug(f'Adding descendant CSE: {csi} -> {eachDcse}')
						self.descendantCSR[eachDcse] = (None, csi)

		L.isInfo and L.log('Starting remote CSE connection monitor')
		self.connectionMonitor = BackgroundWorkerPool.newWorker(self.checkInterval, self.connectionMonitorWorker, 'csrMonitor').start()


	def stop(self) -> None:
		"""	Stop the connection monitor. Also delete the CSR resources on both sides, if possible.
		"""
		if not self.enableRemoteCSE:
			return
		L.isInfo and L.log('Stopping remote CSE connection monitor')

		# Stop the worker
		if self.connectionMonitor:
			self.connectionMonitor.stop()
			self.connectionMonitor = None

		# Remove <csr> resources
		if CSE.cseType in [ CSEType.ASN, CSEType.MN ]:
			try:
				self._deleteOwnCSRonRegistrarCSE()	# delete remote CSR. Ignore result
			except:
				pass
			L.isInfo and L.log(f'De-registered from registrar CSE: {self.registrarCSI}')
		if len(resources := self._retrieveLocalCSRResources(includeRegistrarCSR = True)):	# retrieve local CSR of the registrar
			L.isDebug and L.logDebug('Deleting local registrar CSR ')
			self._deleteRegistreeCSR(resources[0])		# delete local CSR of the registrar
	

	def connectionMonitorWorker(self) -> bool:
		"""	The background worker that checks periodically whether the connection to the registrar and
			registree CSEs is still valid.

			Return:
				Always *True* to keep the worker running.
		"""
		if CSE.cseStatus != CSEStatus.RUNNING:
			return True

		try:

			# Check the current state of the connection to the registrar CSE
			if CSE.cseType in [ CSEType.ASN, CSEType.MN ]:

				# when checkLiveliness == False then only check when there is no connection to registrar CSEs
				if not self.checkLiveliness:
					if len(self._retrieveLocalCSRResources(includeRegistrarCSR = True)) == 1:
						return True
					# fallthrough
			
				# Check the connection to the registrar CSE and establish one if necessary
				self._checkConnectionToRegistrarCSE()

			# Check the liveliness of registree CSR connections
			# Only when we validate the registrations
			if CSE.cseType in [ CSEType.MN, CSEType.IN ]:
				if self.checkLiveliness:	
					self._checkRegistreeLiveliness()

		except Exception as e:
			L.logErr(f'Exception during connection monitor run: {e}', exc = e)
			return True

		return True


	#########################################################################
	#
	#	Event Handlers
	#

	def handleRegistrarRegistration(self, name:str,  
										   registrarCSE:Resource, 
										   ownRegistrarCSR:Resource) -> None:
		""" Event handler for adding a registrar CSE/CSR CSI to the list of registered csi.

			Args:
				name:Event name.
			 	registrarCSE: The CSR that just registered (the CSR from the registrar CSE).
				ownRegistrarCSR: The own CSR on the the registrar CSE
		"""
		self.registrarCSE = registrarCSE
		self.ownCSRonRegistrarCSE = ownRegistrarCSR


	def handleRegistrarDeregistration(self, name:str, registrarCSE:Optional[Resource] = None) -> None:
		"""	Event handler for removing the registrar CSE/CSR CSI from the list of registered csi.

			Args:
				name:Event name.
				registrarCSE: The registrar CSE that is de-registered.
		"""
		self.registrarCSE = None
		self.ownCSRonRegistrarCSE = None


	def handleRegistreeCSERegistration(self, name:str, registreeCSR:Resource) -> None:
		"""	Event handler for adding a registree's CSE's <CSR> to the list of registered descendant CSE. 

			Args:
				name:Event name.
				registreeCSR: The CSR that just registered.
		"""
		if not (registreeCSRcsi := registreeCSR.csi):	# Not a CSR?
			return
		if registreeCSRcsi in self.descendantCSR:	# already registered
			return

		# don't register registrar CSE here
		if (registrarCSE := self.registrarCSE) and (registrarCSEcsi := registrarCSE.csi) and registrarCSEcsi == registreeCSRcsi:
			return

		# Add to the descendant CSE : (remoteCSR, this CSE's csi )
		self.descendantCSR[registreeCSRcsi] = (registreeCSR, CSE.cseCsi)

		# Update the own dcse list with the dcse's from the remoteCSR
		if registreeCSR.dcse:	
			L.isDebug and L.logDebug(f'Adding registree CSEs descendants: {registreeCSR.dcse}')

			for eachDcse in registreeCSR.dcse:
				if eachDcse in self.descendantCSR:	# don't overwrite existing ones
					continue
				self.descendantCSR[eachDcse] = (None, registreeCSRcsi)	# add the remoteCSRcsr to self's dcse list

		L.isDebug and L.logDebug(f'Registree CSE registered {registreeCSRcsi}')
		
		# Update the registrar CSE with the new values
		if CSE.cseType in [ CSEType.ASN, CSEType.MN ]:
			self._updateCSRonRegistrarCSE()
		
		# Send another event when the own CSE has fully registered
		CSE.event.registeredToRemoteCSE(registreeCSR)	# type: ignore


	def handleRegistreeCSEDeregistration(self, name:str, registreeCSR:Resource ) -> None:
		"""	Event handler for removals of registree's CSE/CSR CSI from the list of registered descendant CSE. 

			Args:
				name:Event name.
				registreeCSR: the CSR that just de-registered.
		"""
		L.isDebug and L.logDebug(f'Handling de-registration of registree CSE: {registreeCSR.csi}')

		# Remove the deregistering CSE from the descendant list
		if (registreeCSRcsi := registreeCSR.csi) and registreeCSRcsi in self.descendantCSR:
			del self.descendantCSR[registreeCSRcsi]
			
		# Also remove all descendants that are refer to that remote CSE
		for eachDescendantCsi in list(self.descendantCSR):	# List might change in the loop
			dcse = self.descendantCSR[eachDescendantCsi]	# returns tuple (CSR, csi)
			if dcse[1] == registreeCSRcsi:	# registered to deregistering remote CSE?
				del self.descendantCSR[eachDescendantCsi]
		
		if CSE.cseType in [ CSEType.ASN, CSEType.MN ] and registreeCSR.csi != self.registrarCSI:	# No need to update the own CSR on the registrar when deregistering anyway
			self._updateCSRonRegistrarCSE()


	def handleRegistreeCSEUpdate(self, name:str, registreeCSR:Resource, updateDict:JSON) -> None:
		"""	Event handler for an updates of a registree CSE.

			Args:
				name:Event name.
				registreeCSR: The updated registree CSE.
				updateDict: The resource dictionary with the updated attributes.
		"""
		L.isDebug and L.logDebug(f'Handle registree CSE update: {registreeCSR}\nupdate: {updateDict}')

		# handle update of dcse in remoteCSR
		registreeCsi = registreeCSR.csi

		L.isDebug and L.logDebug(f'Update of descendantCSRs: {self.descendantCSR}')
		# remove all descendant tuples that are from this CSR
		for eachDcse in list(self.descendantCSR.keys()):	# !!! make a copy of the keys bc the list changes in this loop
			if eachDcse in self.descendantCSR:	# Entry could have been deleted, so we need to check
				(_, registeredAtCsi) = self.descendantCSR[eachDcse]
				if registeredAtCsi == registreeCsi :	# remove all descedants EXCEPT the ones hosted on THIS CSE
					L.isDebug and L.logDebug(f'Removing from internal dcse list: {eachDcse}')
					if eachDcse in self.descendantCSR:
						del self.descendantCSR[eachDcse]

		# add new/updated values from remoteCSR
		if dcse := findXPath(updateDict, 'm2m:csr/dcse'):
			for eachDcse in dcse:
				if eachDcse in self.descendantCSR:	# don't overwrite existing ones. Can this actually happen?
					continue
				self.descendantCSR[eachDcse] = (None, registreeCsi)	# don't have the CSR for further descendants available

		if CSE.cseType in [ CSEType.ASN, CSEType.MN ]:	# update own registrar CSR
			self._updateCSRonRegistrarCSE()


	#########################################################################
	#
	#	Connection Checkers
	#

	def _checkConnectionToRegistrarCSE(self) -> None:
		"""	Check the connection for this CSE to the registrar CSE.
		"""
		L.isDebug and L.logDebug('Checking connection to Registrar CSE')
		# first check whether there is already a local CSR
		if len(_csrs := self._retrieveLocalCSRResources(includeRegistrarCSR = True)):
			registrarCSR = _csrs[0] # hopefully, there is only one registrar CSR

			# retrieve own CSR from the registrar CSE
			try:
				csr = self._retrieveCSRfromRegistrarCSE()
				L.isDebug and L.logDebug('CSR found on registrar CSE')
				self.ownCSRonRegistrarCSE = csr

				# own CSR is still on the registrar CSE, so check for changes in remote CSE
				try:
					self.registrarCSE = self._retrieveRegistrarCSE() # retrieve the remote CSE
					if self.registrarCSE.isModifiedAfter(registrarCSR):	# remote CSE modified
						# Update the local registrar <CSR> resource
						L.isDebug and L.logDebug(f'Updating local registrar CSR resource: {registrarCSR.rn}')
						self._copyCSE2CSR(registrarCSR, self.registrarCSE)
						registrarCSR.dbUpdate()		# update in DB only
						L.isDebug and L.logDebug('Local CSR updated')
				except ResponseException as e:
					self.registrarCSE = None	# Always assign, if there is an error "resource" is None
					
				# Check whether the own CSE has been changed. If yes, then update it on the registrar CSE
				localCSE = getCSE()
				if localCSE.isModifiedAfter(self.ownCSRonRegistrarCSE):	# local CSE modified
					self._updateCSRonRegistrarCSE(localCSE)
					L.isDebug and L.logDebug('Remote CSR updated')

			# No CSR on registrar CSE found, try to register
			except:
				L.isDebug and L.logDebug('CSR not found on registrar CSE')
				# Potential disconnect
				self._deleteRegistreeCSR(registrarCSR)	# ignore result
				self.registrarCSE = None				# Indicate that we are not registered to the registrar CSE anymore
				try:
					csr = self._createCSRonRegistrarCSE()
					self.ownCSRonRegistrarCSE = csr
					try:
						self.registrarCSE = self._retrieveRegistrarCSE()	# We are registered to the registrar CSE again
						self._createLocalCSR(self.registrarCSE)		# ignore result
						L.isInfo and L.log(f'registered to registrar CSE: {self.registrarCSI}')
						self._eventRegisteredToRegistrarCSE(self.registrarCSE, self.ownCSRonRegistrarCSE)
					except:
						pass
				except:
					L.isInfo and L.log('Disconnected from registrar CSE')
					self._eventDeregisteredFromRegistrarCSE(self.ownCSRonRegistrarCSE)
					self.registrarCSE = None
		
		else:
			# No local CSR, so try to delete an optional remote one and re-create everything. 
			rsc = ResponseStatusCode.UNKNOWN
			try:
				self._deleteOwnCSRonRegistrarCSE()
				rsc = ResponseStatusCode.DELETED
			except ResponseException as e:
				rsc = e.rsc
			if rsc in [ ResponseStatusCode.DELETED, ResponseStatusCode.NOT_FOUND ]:	# delete potential remote CSR
				try:
					# Should be None after an exception of the following calls
					self.ownCSRonRegistrarCSE = self._createCSRonRegistrarCSE()
					self.registrarCSE = self._retrieveRegistrarCSE()	# retrieve remote CSE
					self._createLocalCSR(self.registrarCSE) 	# create local CSR including ACPs to local CSR and local CSE. Ignore result
					L.isInfo and L.log(f'Registered to registrar CSE: {self.registrarCSI}')
					self._eventRegisteredToRegistrarCSE(self.registrarCSE, self.ownCSRonRegistrarCSE)
				except:
					self.ownCSRonRegistrarCSE = None	
					self.registrarCSE = None

						

	def _checkRegistreeLiveliness(self) -> None:
		"""	Check the liveliness of all registree CSE's that are connected to this CSE.
			This is done by trying to retrieve the own remote <CSR> from the remote CSE.
			If it cannot be retrieved then the related local CSR is removed.
		"""
		for eachCsr in self._retrieveLocalCSRResources(withRegistreeCSR = True):
			L.isDebug and L.logDebug(f'Checking connection to registree CSE: {eachCsr.csi}')
			if (to := self.getRemoteCSEBaseAddress(eachCsr.csi)) is None:
				self._deleteRegistreeCSR(eachCsr)
				continue
			if CSE.request.sendRetrieveRequest(to, originator = CSE.cseCsi).rsc != ResponseStatusCode.OK:
				L.isWarn and L.logWarn(f'Registree CSE unreachable. Removing CSR: {eachCsr.rn if eachCsr else ""}')
				self._deleteRegistreeCSR(eachCsr)


	#
	#	Local CSR
	#

	def _retrieveLocalCSRResources(self, includeRegistrarCSR:Optional[bool] = False, 
										 withRegistreeCSR:Optional[bool] = False) -> List[Resource]:
		"""	Retrieve the local <CSR> resources.
		
			Args:
				includeRegistrarCSR: If *True* then include the CSR to the registrar CSE in the result.
				withRegistreeCSR: if *True* then include the CSR(s) to the registree CSE(s) in the result.

			Return:
				A list of found CSR resources.
		"""
		registreeCsrList = []
		for eachCSR in CSE.dispatcher.directChildResources(pi = CSE.cseRi, ty = ResourceTypes.CSR):
			if eachCSR.csi == self.registrarCSI:		# type: ignore[name-defined]
				if includeRegistrarCSR: 	
					registreeCsrList.append(eachCSR)
			else:
				if withRegistreeCSR: 	
					registreeCsrList.append(eachCSR)
		return registreeCsrList


	def _createLocalCSR(self, remoteCSE: Resource) -> Resource:
		L.isDebug and L.logDebug(f'Creating local CSR for CSE: {remoteCSE.ri}')

		# copy local CSE attributes into a new CSR
		localCSE = getCSE()
		csrResource = CSR(pi = localCSE.ri, rn = remoteCSE.csi[1:])	# remoteCSE.csi as name!
		self._copyCSE2CSR(csrResource, remoteCSE)
		csrResource['ri'] = remoteCSE.csi[1:] 						# set the ri to the remote CSE's ri

		# add local CSR and ACP's
		try:
			CSE.dispatcher.createLocalResource(csrResource, localCSE)
			CSE.registration.handleCSRRegistration(csrResource, remoteCSE.csi)
		except ResponseException as e:
			raise BAD_REQUEST(f'cannot register CSR: {e.dbg}')

		return csrResource.dbUpdate()


	def _deleteRegistreeCSR(self, registreeCSR:Resource) -> None:
		"""	Delete a local registree <CSR> resource. Unregister it first.

			Args:
				registreeCSR: The <CSR> resource to de-register and delete.
		"""
		L.isDebug and L.logDebug(f'Deleting registree CSR: {registreeCSR.ri}')

		# De-register the registree CSR first
		if not CSE.registration.handleRegistreeCSRDeRegistration(registreeCSR):
			raise BAD_REQUEST('cannot de-register registree CSR')

		# Delete local CSR
		CSE.dispatcher.deleteLocalResource(registreeCSR)


	#
	#	Remote Registrar CSR request methods
	#

	def _retrieveCSRfromRegistrarCSE(self) -> Resource:
		"""	Retrieve the own <CSR> resource from the registrar CSE.
		
			Return:
				Resource object
		"""
		L.isDebug and L.logDebug(f'Retrieving own CSR from registrar CSE: {self.registrarCSI}')
		res = CSE.request.sendRetrieveRequest(self.csrOnRegistrarURI, CSE.cseCsi, ct = self.registrarSerialization)	# own CSE.csi is the originator
		if not res.rsc == ResponseStatusCode.OK:
			_exc = exceptionFromRSC(res.rsc)
			if _exc:
				raise _exc(dbg = L.logDebug(f'cannot retrieve CSR from registrar CSE: {int(res.rsc)} dbg: {res.dbg}')) # type:ignore[call-arg]
			raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')
		# <CSR> found, return it in the result
		return resourceFromDict(cast(JSON, res.data), pi='')


	def _createCSRonRegistrarCSE(self) -> Resource:
		L.isDebug and L.logDebug(f'creating CSR at registrar CSE: {self.registrarCSI} uri: {self.registrarCSEURI}')	
		
		# get local CSEBase and copy relevant attributes
		localCSE = getCSE()
		csrResource = CSR(rn = localCSE.ri) # ri as name!
		self._copyCSE2CSR(csrResource, localCSE)
		for _ in ['ty','ri', 'ct', 'lt']: csrResource.delAttribute(_, setNone = False)	# remove a couple of attributes

		# Create the <csr> on the registrar CSE
		res = CSE.request.sendCreateRequest(self.registrarCSEURL, 				 # We may not have the resource yet, so we need to use the configured URL
											CSE.cseCsi, 						 # own CSE.csi is the originator
											ty = ResourceTypes.CSR, 
											content = csrResource.asDict(), 
											ct = self.registrarSerialization)
		if res.rsc not in [ ResponseStatusCode.CREATED, ResponseStatusCode.OK, ResponseStatusCode.CONFLICT ]:
			_exc = exceptionFromRSC(res.rsc)
			if _exc:
				raise _exc(dbg = L.logDebug(f'error creating CSR on registrar CSE: {int(res.rsc)} dbg: {res.dbg}')) # type:ignore[call-arg]
			raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')
		
		# If the resource already exists then perhaps it is a leftover from a previous session. It should have been deleted,
		# but who knows? Just re-use that one for now.
		if res.rsc == ResponseStatusCode.CONFLICT:
			L.isWarn and L.logWarn(f'error creating CSR on registrar CSE: {int(res.rsc)} dbg: {res.dbg}')
		else:
			L.isDebug and L.logDebug(f'created CSR on registrar CSE: {self.registrarCSI}')
		return resourceFromDict(cast(JSON, res.data), pi = '')


	def _updateCSRonRegistrarCSE(self, hostingCSE:Optional[Resource] = None) -> Resource:
		"""	Update the own <CSR> resource on the registrar CSE.

			Args:
				hostingCSE: Optional CSE resource to use for the update. If None, the hosting <CSEBase> resource will be used.

			Return:
				Resource
		"""
		L.isDebug and L.logDebug(f'updating own <CSR> on registrarCSE: {self.registrarCSI} URI: {self.csrOnRegistrarURI}')
		if not hostingCSE:
			hostingCSE = getCSE()
		
		# create a new CSR resource and fill it with the current attributes
		csr = CSR()
		self._copyCSE2CSR(csr, hostingCSE, isUpdate = True)
		del csr['acpi']			# remove ACPI (don't provide ACPI in updates!)
		
		res = CSE.request.sendUpdateRequest(self.csrOnRegistrarURI, 
											CSE.cseCsi, 
											content = csr.asDict(), 
											ct = self.registrarSerialization) 	# own CSE.csi is the originator
		if res.rsc not in [ ResponseStatusCode.UPDATED, ResponseStatusCode.OK ]:
			if res.rsc != ResponseStatusCode.CONFLICT:
				L.isDebug and L.logDebug(f'error updating registrar CSR on CSE: {int(res.rsc)}')
			_exc = exceptionFromRSC(res.rsc)
			if _exc:
				raise _exc(dbg = L.logDebug(f'cannot update remote CSR: {int(res.rsc)} dbg: {res.dbg}')) # type:ignore[call-arg]
			raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')

		L.isDebug and L.logDebug(f'registrar CSR updated on CSE: {self.registrarCSI}')
		return resourceFromDict(cast(JSON, res.data), pi = '')


	def _deleteOwnCSRonRegistrarCSE(self) -> None:
		"""	Delete the own <CSR> resource from the registrar CSE.
		"""
		L.isDebug and L.logDebug(f'Deleting own CSR on registrar CSE: {self.registrarCSI} URI: {self.csrOnRegistrarURI}')
		res = CSE.request.sendDeleteRequest(self.csrOnRegistrarURI, 
											CSE.cseCsi, 
											ct = self.registrarSerialization)	# own CSE.csi is the originator
		if res.rsc not in [ ResponseStatusCode.DELETED, ResponseStatusCode.OK ]:
			_exc = exceptionFromRSC(res.rsc)
			if _exc:
				raise _exc(dbg = L.logDebug(f'cannot delete remote CSR: {int(res.rsc)} dbg: {res.dbg}')) # type:ignore[call-arg]
			raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')
		L.isDebug and L.logDebug(f'Registrar CSR deleted: {self.registrarCSI}')


	#
	#	Remote Registrar CSE
	#

	def _retrieveRegistrarCSE(self) -> Resource:
		"""	Retrieve the remote registrar CSE.

			The actual request uses a direct URL as a fallback because the RETRIEVE request happens when the 
			actual registration may not yet have happened, and the registrars <CSR> resource with the actual
			POA is not available at that time.

			Return:
				The registrar's <CSE> resource.
		"""
		L.isDebug and L.logDebug(f'Retrieving registrar CSE from: {self.registrarCSI}')	
		
		# The following request uses a direct URL as a fallback because this method is called when the actual registration
		# may not yet happened.
		res = CSE.request.sendRetrieveRequest(self.registrarCSEURI if self.registrarCSE else self.registrarCSEURL, 
											  CSE.cseCsi, 
											  ct = self.registrarSerialization)	# own CSE.csi is the originator

		if (registrarCSI := findXPath(cast(JSON, res.data), 'm2m:cb/csi')) == None:
			raise BAD_REQUEST(L.logErr('csi not found in remote CSE resource', showStackTrace = False))
		
		# Correcting the registrar CSI
		if not registrarCSI.startswith('/'):
			L.isWarn and L.logWarn('Remote CSE.csi doesn\'t start with /. Correcting.')	# TODO Decide whether correcting this is actually correct. Also in validator.validateCSICB()
			setXPath(cast(JSON, res.data), 'm2m:cb/csi', f'/{registrarCSI}')


		return CSEBase(cast(JSON, res.data)) # Don't use the Factory here (less checks)


	def getAllLocalCSRs(self) -> List[Resource]:
		"""	Return all local <CSR> resources. This includes the <CSR> of the registrar CSE.
			This function builds the list from a temporary internal list, but not from the database.

			Return:
				List of <CSR> resources.
		"""
		csrList = [ csr for (csr, _) in self.descendantCSR.values() if csr ]
		csrList.append(self.ownCSRonRegistrarCSE)
		return csrList


	#########################################################################


	def retrieveRemoteResource(self, id:str, originator:Optional[str] = None) -> Resource:
		"""	Retrieve a remote resource from one of the interconnected CSEs.

			Args:
				id: The resource ID. It must be at least in SP-relative format.
				originator: Optional request originator. If *None* is given then the CSE's CSE-ID is used.
			
			Return:
				Result object with the status and, if successful, the resource object in the *resource* attribute.
		"""

		# We cannot regularly retrieve a remote resource if we are not fully registered (yet).
		resourceList = self._retrieveLocalCSRResources(includeRegistrarCSR = True, withRegistreeCSR = True)
		L.inspect(id)

		_id = f'{id}/'
		for eachCsr in resourceList:
			if _id.startswith(eachCsr.csi):
				break	# found a matching CSR
		else: # Not found, so not registered
			raise NOT_FOUND(L.logDebug(f'Not registered to remote CSE to retrieve: {id}'))
			
		# Assign fallback originator
		if not originator:
			originator = CSE.cseCsi
		
		# Retrieve the remote resource via its SP-relative ID
		L.isDebug and L.logDebug(f'Retrieve remote resource id: {id}')
		res = CSE.request.sendRetrieveRequest(id, originator)
		
		# assign the remote ID to the resource's dictionary
		_, tpe, _ = pureResource(cast(JSON, res.data))
		setXPath(cast(JSON, res.data), f'{tpe}/{Constants.attrRemoteID}', id)

		# Instantiate
		return resourceFromDict(cast(JSON, res.data))


	def getCSRFromPath(self, id:str) -> Optional[Tuple[Resource, List[str]]]:
		"""	Try to get a CSR even from a longer path (only the first 2 path elements are relevant). 

			If no direct CSR could be found then that CSR is returned where the addressed csi is a descendant.

			Args:
				id: CSE-ID to search for

			Return:
				A tuple (csr resource, list of path elements), or (None, None) in case of an error).
		"""

		# L.logWarn(f'getCSRFromPath id: {id} ')
		def getCSRWithDescendant(csi:str) -> Resource:
			"""	Get the <CSR> which descendant is a <CSE> with the *csi*.
			
				Args:
					csi: CSE ID for the CSE to look for.
				
				Return:
					The <CSR> resource that has the looked-for CSE as a descendant.
			"""
			# L.logWarn(self.descendantCSR)
			t = self.descendantCSR.get(csi)
			
			if t and t[0]:
				return t[0]		# already a CSR resource
			if t and t[1]:
				return getCSRWithDescendant(t[1]) # indirect, need further step
			return None

		if not id:
			return None, None
		csi, ids = csiFromRelativeAbsoluteUnstructured(id)

		# Search for a <CSR> that either has the csi attribute set, or that has the looked-for
		# registree CSE as a descendant CSE.

		try:
			registreeCSR = CSE.dispatcher.retrieveLocalResource(ri = csi)
		except ResponseException as e:
			registreeCSR = getCSRWithDescendant(f'/{csi}')
		# L.logWarn(csr)
		return registreeCSR, ids


	def getRemoteCSEBaseAddress(self, csi:str) -> Optional[str]:
		# TODO doc
		if csi == CSE.cseCsi:
			return f'{CSE.cseCsi}/{CSE.cseRi}'
		if (csr := CSE.remote.getCSRFromPath(csi))[0] is None:
			return None
		return csr[0].cb


	#########################################################################


	def _copyCSE2CSR(self, target:Resource, source:Resource, isUpdate:Optional[bool] = False) -> None:
		"""	Copy the relevant attributes from a <CSEBase> to a <CSR> resource.
		
			Args:
				target: The target <CSEBase> resource.
				source: The source <CSR> resource.
				isUpdate: Indicator that the copy operation is for an UPDATE request.
		"""

		if 'csb' in source and 'csb' not in self.excludeCSRAttributes:
			target['csb'] = self.registrarCSEURL
		
		# copy certain attributes
		for attr in [ 'csi', 'cst', 'csz', 'lbl', 'nl', 'poa', 'rr', 'srv', 'st' ]:
			if attr in source and attr not in self.excludeCSRAttributes:
				target[attr] = source[attr]

		if 'cb' not in self.excludeCSRAttributes:
			target['cb'] = f'{source.csi}/{source.rn}'
		if 'dcse' not in self.excludeCSRAttributes:
			target['dcse'] = list(self.descendantCSR.keys())		# Always do this bc it might be different, even empty for an update
		
		# Always remove some attributes
		for attr in [ 'acpi' ]:
			if attr in target:
				target.delAttribute(attr, setNone = False)
		
		# Remove attributes in updates
		if isUpdate:
			# rm some attributes
			for attr in [ 'ri', 'rn', 'ct', 'lt', 'ty', 'cst', 'cb', 'csi']:
				if attr in target:
					target.delAttribute(attr, setNone = False)

