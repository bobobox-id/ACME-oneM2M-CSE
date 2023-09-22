from typing import Callable, cast, List, Optional, Sequence

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo import errors as MongoErrors
from threading import Lock

from ..etc.DateUtils import utcTime, fromDuration
from ..etc.Types import ResourceTypes, JSON, Operation
from ..etc import DateUtils, Utils
from ..etc.ResponseStatusCodes import ResponseStatusCode, NOT_FOUND, INTERNAL_SERVER_ERROR, CONFLICT
from ..services.Configuration import Configuration
from ..services import CSE
from ..resources.Resource import Resource
from ..resources import Factory
from ..resources.ACTR import ACTR
from ..services.Logging import Logging as L

class MongoBinding():
    __COL_RESOURCES = "resources"
    __COL_IDENTIFIERS = "identifiers"
    __COL_CHILDREN = "children"
    __COL_SRN = "srn"
    __COL_SUBSCRIPTIONS = "subscriptions"
    __COL_BATCHNOTIF = "batch_notifications"
    __COL_ACTIONS = "actions"
    __COL_REQUESTS = "requests"
    __COL_STATISTICS = "statistics"
    def __init__(self) -> None:
        L.isInfo and L.log("Initialize mongodb binding and create connection!")
        
        # Create collection names as list
        self._l_col = [self.__COL_RESOURCES, self.__COL_IDENTIFIERS, self.__COL_CHILDREN, self.__COL_SRN, self.__COL_SUBSCRIPTIONS, 
                    self.__COL_BATCHNOTIF, self.__COL_ACTIONS, self.__COL_REQUESTS]

        # Initiate connection to mongodb server
        # TODO: Add parameter to mongo host, port, DB name and auth and get it from configuration file
        # TODO: Connection pool; Actually it's already enabled on default
        # TODO: Check connection if successfully connected
        self._client = MongoClient("mongodb://username:password@127.0.0.1/acme-cse?authMechanism=PLAIN", 27017)
        self._db = self._client["acme-cse"]
        # TODO: Add transaction if possible when querying (with)
        # TODO: Print error log when CRUD
        # TODO: Get config from configfile 
        
        # Add locking to each collection access. Lock object are different for each collection
        self.lockResources				= Lock()
        self.lockIdentifiers			= Lock()
        self.lockChildResources			= Lock()
        self.lockSrn	        		= Lock()
        self.lockSubscriptions			= Lock()
        self.lockBatchNotifications		= Lock()
        self.lockStatistics 			= Lock()
        self.lockActions 				= Lock()
        self.lockRequests 				= Lock()

        
        self.maxRequests = Configuration.get('cse.operation.requests.size')
        
        self._setupDatabase()
        
        
    def closeDB(self) -> None:
        L.log("Close MongoDB connection")
        self._client.close()
        
        
    def purgeDB(self) -> None:
        L.isInfo and L.log('Purging DBs')
        for col in self._l_col:
            self._db.drop_collection(col)
        self._setupDatabase()
    
    
    def backupDB(self, dir: str) -> bool:
        # NOTE: Bypass this
        return True
        
    
        
    # def _check_connection(self) -> bool:
    #     try:
    #         # The ping command is cheap and does not require auth.
    #         self._client.admin.command('ping')
    #         return True
    #     except ConnectionFailure:
    #         L.logErr("Server not available")
    #         return False
        
    #
    #   Resources
    #
    
    def insertResource(self, resource: Resource, ri: str) -> None:
        """ Insert resource

        Args:
            resource (Resource): Data of the resource
        """
        with self.lockResources:
            self._insertOne(self.__COL_RESOURCES, resource.dict)
        
        
    def upsertResource(self, resource: Resource, ri: str) -> None:
        """ Update resource if exist and insert if not exist

        Args:
            ri (str): Resource ri to update if exist
            resource (Resource): Data of the resource
        """
        with self.lockResources:
            self._updateOne(self.__COL_RESOURCES, {'ri': ri}, resource.dict, True)
        
        
    def updateResource(self, resource: Resource, ri: str) -> Resource:
        """ Update resource from a document
        By first removing field that have None value from the dictionary

        Args:
            ri (str): resource id of a document
            resource (Resource): new data of a resource

        Returns:
            Resource: updated resource
        """
        with self.lockResources:
            # remove nullified fields from db and resource
            for k in list(resource.dict):
                if resource.dict[k] is None:	# only remove the real None attributes, not those with 0
                    del resource.dict[k]
            self._updateOne(self.__COL_RESOURCES, {'ri': ri}, resource.dict, False)
            return resource


    def deleteResource(self, resource: Resource) -> None:
        """ Delete resource

        Args:
            resource (Resource): Target resource to delete
        """
        with self.lockResources:
            self._deleteOne(self.__COL_RESOURCES, {'ri': resource.ri})
    

    def searchResources(self, ri:Optional[str] = None, 
							  csi:Optional[str] = None, 
							  srn:Optional[str] = None, 
							  pi:Optional[str] = None, 
							  ty:Optional[int] = None, 
							  aei:Optional[str] = None) -> list[dict]:
        """ Search resource from hosting cse by using attribute as filter

        Args:
            ri (Optional[str], optional): ri of resource. Defaults to None.
            csi (Optional[str], optional): csi of CSE resource. Defaults to None.
            srn (Optional[str], optional): srn of resource. Defaults to None.
            pi (Optional[str], optional): pi of multiple resource. Defaults to None.
            ty (Optional[int], optional): ty of multiple resource. Defaults to None.
            aei (Optional[str], optional): aei of AE resource. Defaults to None.

        Returns:
            list[dict]: List of resource data
        """
        if not srn:
            with self.lockResources:
                if ri:
                    # Limit resource to 1 because every resource should have unique ri
                    return self._find(self.__COL_RESOURCES, {'ri': ri}, 1)
                elif csi:
                    # Limit resource to 1 because every CSE should have unique csi
                    return self._find(self.__COL_RESOURCES, {'csi': csi}, 1)
                elif aei:
                    # Limit resource to 1 because every AE should have unique aei
                    return self._find(self.__COL_RESOURCES, {'aei': aei}, 1)
                elif pi:
                    # Format query, by adding ty field if exist
                    query = {'pi': pi}
                    if ty:
                        query['ty'] = ty
                        
                    # Can have multiple value, so set limit to default
                    return self._find(self.__COL_RESOURCES, query)
                elif ty:
                    # Can have multiple value, so set limit to default
                    return self._find(self.__COL_RESOURCES, {'ty': ty})
            
        else:
            # for SRN find the ri first from identifiers collection and then find resource using ri
            # TODO: Consider to find directly to resources collection
            with self.lockIdentifiers:
                identifiers = self._find(self.__COL_IDENTIFIERS, {'srn': srn}, 1)
            if len(identifiers) != 1:
                return []

            with self.lockResources:
                return self._find(self.__COL_RESOURCES, {'ri': identifiers[0]['ri']}, 1)
        

    def discoverResourcesByFilter(self, func:Callable[[JSON], bool]) -> list[dict]:
        return []
    
    
    def retrieveLatestOldestResource(self, oldest: bool, ty: int, pi: Optional[str]) -> Optional[dict]:
        """ Retrieve latest or oldest resource

		Args:
			oldest (bool): True if want to find oldest, False otherwise
			ty (int): Resource type to retrieve
			pi (Optional[str]): Find specific resource that has pi as parents

		Returns:
			Optional[Resource]: Resource data in dict object or None
		"""
        with self.lockResources:
            col = self._db[self.__COL_RESOURCES]
            filter = {'ty': ty}
            if pi:
                filter['pi'] = pi
            
            result: dict = None
            if oldest:
                result = col.find(filter).sort('_id', ASCENDING).limit(1)
            else:
                result = col.find(filter).sort('_id', DESCENDING).limit(1)

            return result
    
    
    def retrieveResourcesByContain(self, field: str, contain: str) -> list[dict]:
        """ Retrieve resources by checking value exist in array field

		Args:
			field (str): Target field to find
			contain (str): Value to find in an array

		Returns:
			list[Resource]: List of found resource in dict object
		"""
        with self.lockResources:
            filter = {field: contain}
            return self._find(self.__COL_RESOURCES, filter)


    def hasResource(self, ri:Optional[str] = None, 
                            csi:Optional[str] = None, 
                            srn:Optional[str] = None,
                            ty:Optional[int] = None) -> bool:
        """ Check if resource is exist by using attribute as filter

        Args:
            ri (Optional[str], optional): ri of the resource. Defaults to None.
            csi (Optional[str], optional): csi of the CSE resource. Defaults to None.
            srn (Optional[str], optional): srn of the resource. Defaults to None.
            ty (Optional[int], optional): ty to check if exist in hosting cse. Defaults to None.

        Returns:
            bool: True if resource is exist and vice versa
        """
        if not srn:
            with self.lockResources:
                if ri:
                    # Limit document count result to 1 because only ri is unique
                    return bool( self._countDocuments(self.__COL_RESOURCES, {'ri': ri}, 1) )
                elif csi :
                    # Limit document count result to 1 because only csi is unique
                    return bool( self._countDocuments(self.__COL_RESOURCES, {'csi': csi}, 1) )
                elif ty is not None:	# ty is an int
                    # Limit is provided because hasResource only expect if resource with ty is exist
                    return bool( self._countDocuments(self.__COL_RESOURCES, {'ty': ty}, 1) )
        else:
            # TODO: Consider directly count srn from resources collection
            # for SRN find the ri first from identifiers collection and then find resource using ri
            with self.lockIdentifiers:
                identifiers = self._find(self.__COL_IDENTIFIERS, {'srn': srn}, 1)
            if len(identifiers) != 1:
                return False

            with self.lockResources:
                return bool( self._countDocuments(self.__COL_RESOURCES, {'ri': identifiers[0]['ri']}, 1) )


    def countResources(self) -> int:
        """ Count how many resources in hosting CSE

        Returns:
            int: Total resources exist
        """
        with self.lockResources:
            return self._countDocuments(self.__COL_RESOURCES, {})


    def searchByFragment(self, dct: dict) -> list[dict]:
        """ Search and return all resources that match the given dictionary/document

        Args:
            dct (dict): Fragments filter

        Returns:
            list[dict]: list of found documents
        """
        with self.lockResources:
            return self._find(self.__COL_RESOURCES, dct)
    
    
    #
	#	Identifiers, Structured RI, Child Resources
	#
 
    def insertIdentifier(self, resource: Resource, ri: str, srn: str) -> None:
        """ Insert resource identifier to identifier and srn collection

        Args:
            resource (Resource): Data of the resource to insert
            ri (str): ri of the resource
            srn (str): srn of the resource
        """
        # Upsert identifier first
        data = \
        {	
            'ri' : ri, 
            'rn' : resource.rn, 
            'srn' : srn,
            'ty' : resource.ty 
        }
        with self.lockIdentifiers:
            self._updateOne(self.__COL_IDENTIFIERS, {'ri': ri}, data, True)

        # Then upsert structuredIds
        data2 = \
        {
            'srn': srn,
            'ri' : ri 
        }
        with self.lockSrn:
            self._updateOne(self.__COL_SRN, {'srn': resource.getSrn()}, data2, True)
    
    
    def deleteIdentifier(self, resource: Resource) -> None:
        """ Delete identifier from identifier and srn collection

        Args:
            resource (Resource): Data of the resource to delete
        """
        with self.lockIdentifiers:
            self._deleteOne(self.__COL_IDENTIFIERS, {'ri': resource.ri})
        with self.lockSrn:
            self._deleteOne(self.__COL_SRN, {'srn': resource.getSrn()})
    
    
    def searchIdentifiers(self, ri: Optional[str] = None, 
                           srn: Optional[str] = None) -> list[dict]:
        """ Search for an resource ID OR for a structured name in the identifiers DB.

			Either *ri* or *srn* shall be given. If both are given then *srn*
			is taken.

        Args:
            ri (Optional[str], optional): ri to search for. Defaults to None.
            srn (Optional[str], optional): srn to search for. Defaults to None.

        Returns:
            list[dict]: A list of found identifier documents (see `insert_identifier`), or an empty list if not found.
        """
        with self.lockSrn:
            if srn:
                if ( _r := self._find(self.__COL_SRN, {'srn': srn}, 1) ):
                    ri = _r['ri'] if _r else None
                else:
                    return []
        
        with self.lockIdentifiers:
            if ri:
                return self._find(self.__COL_IDENTIFIERS, {'ri': ri}, 1)

        return []
    
    
    def addChildResource(self, resource: Resource, ri: str) -> None:
        """ Save resource with list of child resource it has
        
            Also it will add the resource ri to it's parent resource child list

        Args:
            resource (Resource): Data of resource to add
            ri (str): ri of the resource
        """
        # First add a new document to children collection
        with self.lockChildResources:
            children = \
            {
                'ri': ri,
                'ch': []
            }
            # TODO: Add check if insert success before continue
            self._insertOne(self.__COL_CHILDREN, children)
            
            # Then add just inserted resource to parents document (ch field)
            if resource.pi: # ATN: CSE has no parent
                tmp = self._find(self.__COL_CHILDREN, {'ri': resource.pi}, 1) # Find parent document
                if len(tmp) == 0:
                    return
                _r = tmp[0]
                _ch:list = _r['ch']
                if ri not in _ch:
                    _ch.append( [ri, resource.ty] )
                    _r['ch'] = _ch
                    self._updateOne(self.__COL_CHILDREN, {'ri': resource.pi}, _r)


    def removeChildResource(self, resource: Resource) -> None:
        """ Remove resource with child list
        
            Also it will remove the resource from it's parent child list

        Args:
            resource (Resource): Target resource to remove
        """
        with self.lockChildResources:
            # First remove resource from children collection
            # TODO: Add check if delete success before continue
            self._deleteOne(self.__COL_CHILDREN, {'ri': resource.ri})

            # Then remove resource data from parent ch field
            tmp = self._find(self.__COL_CHILDREN, {'ri': resource.pi}, 1)
            if len(tmp) == 0:
                return
            _r = tmp[0]
            _t = [resource.ri, resource.ty]
            _ch:list = _r['ch']
            if _t in _ch:
                _ch.remove(_t)
                _r['ch'] = _ch
                # L.isDebug and L.logDebug(f'remove_child_resource _r:{_r}')
                self._updateOne(self.__COL_CHILDREN, {'ri': resource.pi}, _r)	


    def searchChildResourcesByParentRI(self, pi: str, ty:Optional[int] = None) -> Optional[list[str]]:
        """ Retrieve child resource of a resource

        Args:
            pi (str): Target parent to get it's child
            ty (Optional[int], optional): More filter to retrieve specific ty. Defaults to None.

        Returns:
            Optional[list[str]]: List of resource childs
        """
        with self.lockChildResources:
            tmp = self._find(self.__COL_CHILDREN, {'ri': pi}, 1)
            if len(tmp) > 0:
                _r = tmp[0]
                if ty is None:	# optimization: only check ty once for None
                    return [ c[0] for c in _r['ch'] ]
                return [ c[0] for c in _r['ch'] if ty == c[1] ]	# c is a tuple (ri, ty)
            return []
 
    
    #
	#	Subscriptions
	#
 
    def searchSubscriptions(self, ri: Optional[str] = None, 
								  pi: Optional[str] = None) -> Optional[list[dict]]:
        with self.lockSubscriptions:
            if ri:
                return self._find(self.__COL_SUBSCRIPTIONS, {'ri': ri}, 1)
            if pi:
                return self._find(self.__COL_SUBSCRIPTIONS, {'pi': pi})

        return None
        

    def upsertSubscription(self, subscription: Resource) -> bool:
        data = \
        {
            'ri'  	: subscription.ri, 
            'pi'  	: subscription.pi,
            'nct' 	: subscription.nct,
            'net' 	: subscription['enc/net'],	# TODO perhaps store enc as a whole?
            'atr' 	: subscription['enc/atr'],
            'chty'	: subscription['enc/chty'],
            'exc' 	: subscription.exc,
            'ln'  	: subscription.ln,
            'nus' 	: subscription.nu,
            'bn'  	: subscription.bn,
            'cr'  	: subscription.cr,
            'org'	: subscription.getOriginator(),
            'ma' 	: fromDuration(subscription.ma) if subscription.ma else None, # EXPERIMENTAL ma = maxAge
            'nse' 	: subscription.nse
        }
        with self.lockSubscriptions:
            return self._updateOne(self.__COL_SUBSCRIPTIONS, {'ri': data['ri']}, data, True)


    def removeSubscription(self, subscription: Resource) -> bool:
        with self.lockSubscriptions:
            return self._deleteOne(self.__COL_SUBSCRIPTIONS, {'ri': subscription.ri})
    
    
    #
	#	BatchNotifications
	#
    
    def addBatchNotification(self, ri: str, nu: str, notificationRequest: JSON) -> bool:
        data = \
        {	
            'ri' 		: ri,
            'nu' 		: nu,
            'tstamp'	: utcTime(),
            'request'	: notificationRequest
        }
        with self.lockBatchNotifications:
            return self._insertOne(self.__COL_BATCHNOTIF, data)


    def countBatchNotifications(self, ri: str, nu: str) -> int:
        with self.lockBatchNotifications:
            return self._countDocuments(self.__COL_BATCHNOTIF, {'ri': ri, 'nu': nu})


    def getBatchNotifications(self, ri: str, nu: str) -> list[dict]:
        with self.lockBatchNotifications:
            return self._find(self.__COL_BATCHNOTIF, {'ri': ri, 'nu': nu})


    def removeBatchNotifications(self, ri: str, nu: str) -> bool:
        with self.lockBatchNotifications:
            return self._deleteOne(self.__COL_BATCHNOTIF, {'ri': ri, 'nu': nu})


    #
	#	Statistics
	#

    def searchStatistics(self) -> JSON:
        with self.lockStatistics:
            if len(stats := self._find(self.__COL_STATISTICS)) > 0:
                return stats[0]
        return None


    def upsertStatistics(self, statisticsData: JSON) -> bool:
        with self.lockStatistics:
            if len(stats := self._find(self.__COL_STATISTICS)) > 0:
                return self._updateOne(self.__COL_STATISTICS, {'_id': stats[0]['_id']}, statisticsData)
            else:
                return self._insertOne(self.__COL_STATISTICS, statisticsData)


    def purgeStatistics(self) -> None:
        """	Purge the statistics DB.
        """
        # Truncate: just drop target collection and re-create the collection
        with self.lockStatistics:
            self._db.drop_collection(self.__COL_STATISTICS)
        self._setupDatabase()


    #
	#	Actions
	#
 
    def searchActionReprs(self) -> list[dict]:
        with self.lockActions:
            actions = self._find(self.__COL_ACTIONS)
            return actions if len(actions) > 0 else None


    def getAction(self, ri: str) -> Optional[dict]:
        with self.lockActions:
            actions = self._find(self.__COL_ACTIONS, {'ri': ri}, 1)
            return actions[0] if len(actions) > 0 else None
    

    def searchActionsDeprsForSubject(self, ri: str) -> Sequence[JSON]:
        with self.lockActions:
            return self._find(self.__COL_ACTIONS, {'subject': ri})
    

    # TODO add only?
    def upsertActionRepr(self, action:ACTR, periodTS:float, count:int) -> bool:
        data = \
        {	
            'ri':		action.ri,
            'subject':	action.sri if action.sri else action.pi,
            'dep':		action.dep,
            'apy':		action.apy,
            'evm':		action.evm,
            'evc':		action.evc,	
            'ecp':		action.ecp,
            'periodTS': periodTS,
            'count':	count,
        }
        with self.lockActions:
            return self._updateOne(self.__COL_ACTIONS, {'ri': action.ri}, data, True)


    def updateActionRepr(self, actionRepr: JSON) -> bool:
        with self.lockActions:
            return self._updateOne(self.__COL_ACTIONS, {'ri': actionRepr['ri']}, actionRepr)
    

    def removeActionRepr(self, ri: str) -> bool:
        with self.lockActions:
            return self._deleteOne(self.__COL_ACTIONS, {'ri': ri})
    
    
    #
	#	Requests
	#

    def insertRequest(self, op: Operation, 
                            ri: str, 
                            srn: str, 
                            originator: str, 
                            outgoing: bool, 
                            ot: str,
                            request: JSON, 
                            response: JSON) -> bool:
        """	Add a request to the *requests* database.
    
        Args:
            op: Operation.
            ri: Resource ID of a request's target resource.
            srn: Structured resource ID of a request's target resource.
            originator: Request originator.
            outgoing: If true, then this is a request sent by the CSE.
            ot: Request creation timestamp.
            request: The request to store.
            response: The response to store.
        
        Return:
            Boolean value to indicate success or failure.
        """
        with self.lockRequests:
            try:
                # First check whether we reached the max number of allowed requests.
                # If yes, then remove the oldest.
                if ( self._countDocuments(self.__COL_REQUESTS, {}) > self.maxRequests ):
                    col = self._db[self.__COL_REQUESTS]
                    oldDoc = col.find({}).sort('_id').limit(1)
                    if not ( self._deleteOne(self.__COL_REQUESTS, {'_id': oldDoc['_id']}) ):
                        return False
                
                # Adding a request    
                ts = utcTime()
                #op = request.get('op') if 'op' in request else Operation.NA
                rsc = response['rsc'] if 'rsc' in response else ResponseStatusCode.UNKNOWN
                # The following removes all None values from the request and response, and the requests structure
                _doc = \
                {
                    'ri': ri,
                    'srn': srn,
                    'ts': ts,
                    'org': originator,
                    'op': op,
                    'rsc': rsc,
                    'out': outgoing,
                    'ot': ot,
                    'req': { k: v for k, v in request.items() if v is not None }, 
                    'rsp': { k: v for k, v in response.items() if v is not None }
                }
                toInsert = {k: v for k, v in _doc.items() if v is not None}
                
                return self._insertOne(self.__COL_REQUESTS, toInsert)
            except Exception as e:
                L.logErr(f'Exception inserting request/response for ri: {ri}', exc = e)
                return False
    
    
    def getRequests(self, ri:Optional[str] = None) -> list[dict]:
        """	Get requests for a resource ID, or all requests.
        
            Args:
                ri: The target resource's resource ID. If *None* or empty, then all requests are returned
            
            Return:
                List of *dict*. May be empty.
        """
        with self.lockRequests:
            if not ri:
                return self._find(self.__COL_REQUESTS)
            return self._find(self.__COL_REQUESTS, {'ri': ri})
  
    
    def deleteRequests(self, ri:Optional[str] = None) -> None:
        """	Remnove all stord requests from the database.

            Args:
                ri: Optional resouce ID. Only requests for this resource ID will be deleted.
        """
        setupDatabase = False
        with self.lockRequest:
            if ri:
                self._deleteOne(self.__COL_REQUESTS, {'ri': ri})
            else:
                # Truncate: just drop target collection and re-create the collection
                self._db.drop_collection(self.__COL_REQUESTS)
                setupDatabase = True

        if setupDatabase:
            self._setupDatabase()
    
    
    #
    #   Internal functions
    #
        
    def _setupDatabase(self):
        """ Setup mongo database by create acme-cse collection if not exist and add unique index of respective collection
        """
        # TODO: Set csi, aei to unique on resource collection
        L.isInfo and L.log("Setup acme-cse mongodb database")
        l_existing_collection = self._db.list_collection_names()
        all_exist = True
        
        # loop through acme-cse collection
        for col in self._l_col:
            # check if each acme-cse collection not exist then add unique index
            if col not in l_existing_collection:
                all_exist = False
                if col == self.__COL_SRN:
                    tmp = self._db[self.__COL_SRN]
                    tmp.create_index("srn", unique = True)
                elif col == self.__COL_REQUESTS:
                    tmp = self._db[self.__COL_REQUESTS]
                    tmp.create_index("ts", unique = True)
                elif (col == self.__COL_BATCHNOTIF) or (col == self.__COL_STATISTICS):
                    # TODO: Set ri and nu as index but not unique for batchNotif. Maybe??
                    continue # Statistics and Batch notifications collection don't need index
                else:
                    tmp = self._db[col]
                    tmp.create_index("ri", unique = True)

        if not all_exist:
            L.isInfo and L.log("One or more collections not exist and just created")
        
    def _insertOne(self, collection: str, data: dict) -> bool:
        """ Insert resource to a collection

        Args:
            collection (str): Target collection to where it will inserted
            data (dict): data to insert (document)

        Returns:
            bool: Success insert or not
        """
        try:
            col = self._db[collection]
            result = col.insert_one(data)
            L.isDebug and L.log(f'Success insert data: {result.inserted_id}')
            return True
        except MongoErrors.DuplicateKeyError as e:
            L.logErr("Failed insert data")
        except Exception:
            L.logErr(f'_insertOne failed: {str(e)}')
            L.logErr(f'data: {data}')
        return False
    
            
    def _updateOne(self, collection: str, query: dict, data: dict, upsert: bool = False) -> bool:
        """ Update document from collection; It actually replace the whole document

        Args:
            collection (str): Target collection to update the document
            query (dict): Target filter to update/upsert a document
            data (dict): data to update (changed attribute and not)
            upsert (bool, optional): Set to true if want to insert if query/filter is not found. Defaults to False.

        Returns:
            bool: Success update or upsert
        """
        # TODO: Add exception
        # TODO: Consider using update_one. But how to know the only specific field to update?
        try:
            col = self._db[collection]
            result = col.replace_one(query, data, upsert=upsert)
            return (result.modified_count == 1) or result.upserted_id
        except Exception as e:
            L.logErr(f'_updateOne failed: {str(e)}')
            L.logErr(f'query: {query}')
            L.logErr(f'data: {data}')
        return False
    
    
    def _deleteOne(self, collection: str, query: dict) -> bool:
        """ Delete a document from collection

        Args:
            collection (str): Target collection to find the document
            query (dict): Target filter to delete a document

        Returns:
            bool: success or not deleting document; False might be because document is not found
        """
        # TODO: Add exception
        try:
            col = self._db[collection]
            result = col.delete_one(query)
            return (result.deleted_count == 1)
        except Exception as e:
            L.logErr(f'_deleteOne failed: {str(e)}')
            L.logErr(f'query: {query}')
        return False
    
    
    def _find(self, collection: str, query: dict = None, limit: int = 0) -> list[dict]:
        """ Find document on a collection

        Args:
            collection (str): Target collection to find
            query (dict): Filter of the search
            limit (int, optional): Limit of how many documents as a result. Defaults to 0 will make it unlimited

        Returns:
            list[dict]: List of documents found
        """
        # TODO: Add exception
        try:
            print(f"Mongo._find: {query}")
            print()
            col = self._db[collection]
            result = col.find(filter = query, limit = limit)
            return [x for x in result]
        except Exception as e:
            L.logErr(f'_find failed: {str(e)}')
            L.logErr(f'query: {query}')
        return []

    
    def _countDocuments(self, collection: str, query: dict, limit: int = 0) -> int:
        """ Count how many document/s found on a collection

        Args:
            collection (str): Target collection to search
            query (dict): Filter of the search
            limit (int, optional): Limit of how many document to search for. Don't set limit don't want to limit count. Defaults to 0.

        Returns:
            int: Total documents found
        """
        # TODO: Add exception
        try:
            col = self._db[collection]
            result = None
            if limit > 0:
                result = col.count_documents(filter = query, limit = limit)
            else:
                result = col.count_documents(filter = query)
            return result
        except Exception as e:
            L.logErr(f'_countDocuments failed: {str(e)}')
            L.logErr(f'query: {query}')
        return 0
            

if __name__ == "__main__":
    mongo = MongoBinding()
    print("done")
    mongo.stop_connection()
