//
//  shortnames.js
//
//  (c) 2020 by Andreas Kraft
//  License: BSD 3-Clause License. See the LICENSE file for further details.
//
//  Mapping between oneM2M short and long names
//

// There are basically 4 types of attributes:
// - common & universal : same as oneM2M
// - custom : from flexContainer and mgmtObj specializations
// - all others


const shortNames = {
  "aa"    : { "ln" : "announcedAttribute", "type" : "common" },
  "acn"   : { "ln" : "action", "type": "" },
  "act"   : { "ln" : "activate", "type": "" },
  "acts"  : { "ln" : "activeStatus", "type": "" },
  "acpi"  : { "ln" : "accessControlPolicyIDs", "type": "common" },
  "acn"   : { "ln" : "action", "type": "" },
  "aei"   : { "ln" : "AE-ID", "type": "" },
  "altie" : { "ln" : "altitude", "type": "custom" },
  "ant"   : { "ln" : "areaNwkType", "type": "custom" },
  "ape"   : { "ln" : "activityPatternElements", "type": "" },
  "api"   : { "ln" : "App-ID", "type": "" },
  "apn"   : { "ln" : "AppName", "type": "" },
  "at"    : { "ln" : "announcedTo", "type" : "common" },
  "att"   : { "ln" : "attached", "type": "custom" },
  "awi"   : { "ln" : "areaNwkId", "type": "custom" },
  "batTd" : { "ln" : "batteryThreshold", "type": "custom" },
  "btl"   : { "ln" : "batteryLevel", "type": "custom" },
  "bts"   : { "ln" : "batteryStatus", "type": "custom" },
  "can"   : { "ln" : "capabilityName", "type": "custom" },
  "capay" : { "ln" : "capacity", "type": "custom" },
  "cb"    : { "ln" : "CSEBase", "type": "" },
  "charg" : { "ln" : "charging", "type": "custom" },
  "cas"   : { "ln" : "capabilityActionStatus", "type": "custom" },
  "cbs"   : { "ln" : "currentByteSize", "type": "" },
  "cCTEs" : { "ln" : "currentCycleTransmissionErrors", "type": "custom" },
  "celID" : { "ln" : "cellID", "type": "custom" },
  "cnd"   : { "ln" : "containerDefinition", "type": "" },
  "cnf"   : { "ln" : "contentInfo", "type": "custom" },
  "cni"   : { "ln" : "currentNrOfInstances", "type": "" },
  "cnm"   : { "ln" : "currentNrOfMembers", "type": "" },
  "cnty"  : { "ln" : "country", "type": "custom" },
  "coFVe" : { "ln" : "commFreqValue", "type": "custom" },
  "con"   : { "ln" : "content", "type": "" },
  "cr"    : { "ln" : "creator", "type": "common" },
  "cs"    : { "ln" : "contentSize", "type": "" },
  "csi"   : { "ln" : "CSE-ID", "type": "" },
  "cst"   : { "ln" : "cseType", "type": "" },
  "csy"   : { "ln" : "consistencyStrategy", "type": "" },
  "csz"   : { "ln" : "contentSerialization", "type": "" },
  "ct"    : { "ln" : "creationTime", "type": "universal" },
  "ctm"    : { "ln" : "currentTime", "type": "" },
  "cuCBn" : { "ln" : "currentCycleBeginn", "type": "custom" },
  "cuCVe" : { "ln" : "currentCycleVolume", "type": "custom" },
  "cus"   : { "ln" : "currentState", "type": "custom" },
  "daci"  : { "ln" : "dynamicAuthorizationConsultationIDs", "type": "common" },
  "daATe" : { "ln" : "dailyActivityTime", "type": "custom" },
  "dc"    : { "ln" : "description", "type": "" },
  "dcrp"  : { "ln" : "descriptorRepresentation", "type": "" },
  "dea"   : { "ln" : "deactivate", "type": "" },
  "defVe" : { "ln" : "defaultValue", "type": "custom" },
  "dgt"   : { "ln" : "dataGenerationTime", "type": "" },
  "dis"   : { "ln" : "disable", "type": "" },
  "discg" : { "ln" : "discharging", "type": "custom" },
  "disr"  : { "ln" : "disableRetrieval", "type": "" },
  "dlb"   : { "ln" : "deviceLabel", "type": "custom" },
  "dNOCs" : { "ln" : "dailyNumberOfConnections", "type": "custom" },
  "dcse"  : { "ln" : "descendantCSEs", "type": "" },
  "dsp"   : { "ln" : "descriptor", "type": "" },
  "dty"   : { "ln" : "deviceType", "type": "custom" },
  "dvd"   : { "ln" : "devId", "type": "custom" },
  "dvi"   : { "ln" : "deviceInfo", "type": "" },
  "dvnm"  : { "ln" : "deviceName", "type": "custom" },
  "dvt"   : { "ln" : "devType", "type": "custom" },
  "egid"  : { "ln" : "externalGroupID", "type": "" },
  "eleEy" : { "ln" : "electricEnergy", "type": "custom" },
  "ena"   : { "ln" : "enable", "type": "" },
  "enc"   : { "ln" : "eventNotificationCriteria", "type": "" },
  "esi"   : { "ln" : "e2eSecInfo", "type": "common" },
  "et"    : { "ln" : "expirationTime", "type": "common" },
  "far"   : { "ln" : "factoryReset", "type": "" },
  "fwn"   : { "ln" : "firmwareName", "type": "custom" },
  "fwv"   : { "ln" : "fwVersion", "type": "custom" },
  "gn"    : { "ln" : "groupName", "type": "" },
  "hael"  : { "ln" : "hostedAELinks", "type": "" },
  "hash"  : { "ln" : "hash", "type": "custom" },
  "hcl"   : { "ln" : "hostedCSELink", "type": "" },
  "heaAy" : { "ln" : "headingAccuracy", "type": "custom" },
  "headg" : { "ln" : "heading", "type": "custom" },
  "horAy" : { "ln" : "horizontalAccuracy", "type": "custom" },
  "hsl"   : { "ln" : "hostedServiceLink", "type": "" },
  "hwv"   : { "ln" : "hwVersion", "type": "custom" },
  "in"    : { "ln" : "install",  "type": "" },
  "ins"   : { "ln" : "installStatus", "type": "" },
  "latie" : { "ln" : "latitude", "type": "custom" },
  "lbl"   : { "ln" : "labels", "type": "common" },
  "ldv"   : { "ln" : "listOfDevices", "type": "custom" },
  "lga"   : { "ln" : "logStart", "type": "custom" },
  "lgd"   : { "ln" : "logData", "type": "custom" },
  "lgo"   : { "ln" : "logStop", "type": "custom" },
  "lgst"  : { "ln" : "logStatus", "type": "custom" },
  "lgt"   : { "ln" : "logTypeId", "type": "custom" },
  "li"    : { "ln" : "locationID", "type": "" },
  "lnh"   : { "ln" : "listOfNeighbors", "type": "custom" },
  "lnk"   : { "ln" : "link", "type": "custom" },
  "loc"   : { "ln" : "location", "type": "custom" },
  "logNe" : { "ln" : "loginName", "type": "custom" },
  "latie" : { "ln" : "latitude", "type": "custom" },
  "longe" : { "ln" : "longitude", "type": "custom" },
  "lt"    : { "ln" : "lastModifiedTime", "type": "universal" },
  "lvl"   : { "ln" : "level", "type": "custom" },
  "macp"  : { "ln" : "membersAccessControlPolicyIDs", "type": "" },
  "man"   : { "ln" : "manufacturer", "type": "custom" },
  "matel" : { "ln" : "material", "type": "custom" },
  "maxLh" : { "ln" : "maxLength", "type": "custom" },
  "mbs"   : { "ln" : "maxByteSize", "type": "" },
  "mcfc"  : { "ln" : "myCertFileContent", "type": "custom" },
  "mcff"  : { "ln" : "myCertFileFormat", "type": "custom" },
  "mdc"   : { "ln" : "missingDataCurrentNr", "type": "" },
  "mdd"   : { "ln" : "missingDataDetect", "type": "" },
  "mdn"   : { "ln" : "missingDataMaxNr", "type": "" },
  "mdt"   : { "ln" : "missingDataDetectTimer", "type": "" },
  "mei"   : { "ln" : "M2M-Ext-ID", "type": "" },
  "mesEg" : { "ln" : "messageEncoding", "type": "custom" },
  "mfd"   : { "ln" : "manufacturingDate", "type": "custom" },
  "mfdl"  : { "ln" : "manufacturerDetailsLink", "type": "custom" },
  "mgca"  : { "ln" : "mgmtClientAddress", "type": "" },
  "mgd"   : { "ln" : "mgmtDefinition", "type": "" },
  "mi"    : { "ln" : "metaInformation", "type" : "" },
  "miCLy" : { "ln" : "minimumCommunicationLatency", "type": "custom" },
  "mid"   : { "ln" : "memberIDs", "type": "" },
  "minLh" : { "ln" : "minLength", "type": "custom" },
  "mma"   : { "ln" : "memAvailable", "type": "custom" },
  "mmt"   : { "ln" : "memTotal", "type": "custom" },
  "mni"   : { "ln" : "maxNrOfInstances", "type": "" },
  "mnm"   : { "ln" : "maxNrOfMembers", "type": "" },
  "mod"   : { "ln" : "model", "type": "custom" },
  "mt"    : { "ln" : "memberType", "type": "" },
  "mtv"   : { "ln" : "memberTypeValidated", "type": "" },
  "nar"   : { "ln" : "notifyAggregation", "type": "" },
  "nct"   : { "ln" : "notificationContentType", "type": "" },
  "ni"    : { "ln" : "nodeID", "type": "" },
  "nid"   : { "ln" : "networkID", "type": "" },
  "nl"    : { "ln" : "nodeLink", "type": "" },
  "nu"    : { "ln" : "notificationURI",  "type": "" },
  "objet" : { "ln" : "object", "type": "custom" },
  "objTe" : { "ln" : "objectType", "type": "custom" },
  "op"    : { "ln" : "operation", "type" : "" },
  "or"    : { "ln" : "ontologyRef", "type" : "" },
  "osv"   : { "ln" : "osVersion", "type": "custom" },
  "pci"   : { "ln" : "pci", "type": "custom" },
  "pei"   : { "ln" : "periodicInterval", "type": "" },
  "peid"   : { "ln" : "periodicIntervalDelta", "type": "" },
  "pi"    : { "ln" : "parentID", "type": "universal" },
  "poa"   : { "ln" : "pointOfAccess", "type": "" },
  "ptl"   : { "ln" : "protocol", "type": "custom" },
  "purl"  : { "ln" : "presentationURL", "type": "custom" },
  "pushd" : { "ln" : "pushed", "type": "custom" },
  "pv"    : { "ln" : "privileges", "type": "" },
  "pvs"   : { "ln" : "selfPrivileges", "type": "" },
  "pwd"   : { "ln" : "password", "type": "custom" },
  "rbo"   : { "ln" : "reboot", "type": "" },
  "regs"  : { "ln" : "registrationStatus", "type": "" },
  "ri"    : { "ln" : "resourceID", "type": "universal" },
  "rid"   : { "ln" : "requestID", "type" : "" },
  "rms"   : { "ln" : "roamingStatus", "type": "" },
  "rn"    : { "ln" : "resourceName", "type": "universal" },
  "rr"    : { "ln" : "requestReachability", "type": "" },
  "rs"    : { "ln" : "requestStatus", "type" : "" },
  "rsrp"  : { "ln" : "rsrp", "type": "custom" },
  "rsrq"  : { "ln" : "rsrq", "type": "custom" },
  "rssi"  : { "ln" : "rssi", "type": "custom" },
  "scp"   : { "ln" : "sessionCapabilities", "type": "" },
  "siECL" : { "ln" : "signalECL", "type": "custom" },
  "sinr"  : { "ln" : "sinr", "type": "custom" },
  "size"  : { "ln" : "size", "type": "custom" },
  "sld"   : { "ln" : "sleepDuration", "type": "custom" },
  "sli"   : { "ln" : "sleepInterval", "type": "custom" },
  "smod"  : { "ln" : "subModel", "type": "custom" },
  "snr"   : { "ln" : "sequenceNr", "type" : "" },
  "spty"  : { "ln" : "specializationType", "type": "" },
  "spur"  : { "ln" : "supportURL", "type": "custom" },
  "srt"   : { "ln" : "supportedResourceType", "type": "" },
  "srv"   : { "ln" : "supportedReleaseVersions", "type": "" },
  "ssi"   : { "ln" : "semanticSupportIndicator", "type": "" },
  "st"    : { "ln" : "stateTag", "type": "common" },
  "suids" : { "ln" : "SUIDs", "type": "custom" },
  "suMVs" : { "ln" : "supportedMessageValues", "type": "custom" },
  "sus"   : { "ln" : "status", "type": "" },
  "swn"   : { "ln" : "softwareName", "type": "" },
  "swr"   : { "ln" : "software", "type": "" },
  "svd"   : { "ln" : "semanticValidated", "type": "" },
  "swv"   : { "ln" : "swVersion", "type": "custom" },
  "syst"  : { "ln" : "systemTime", "type": "custom" },
  "tarAe" : { "ln" : "targetAltitude", "type": "custom" },
  "tarLe" : { "ln" : "targetLatitude", "type": "custom" },
  "tarL0" : { "ln" : "targetLongitude", "type": "custom" },
  "texMe" : { "ln" : "textMessage", "type": "custom" },
  "tg"    : { "ln" : "target", "type" : "" },
  "tk"    : { "ln" : "token", "type": "custom" },
  "tri"   : { "ln" : "trigger-Recipient-ID", "type": "" },
  "tren"  : { "ln" : "triggerEnable", "type": "" },
  "trn"   : { "ln" : "triggerReferenceNumber", "type": "" },
  "trps"  : { "ln" : "trackRegistrationPoints", "type": "" },
  "ty"    : { "ln" : "resourceType", "type": "universal" },
  "ud"    : { "ln" : "update", "type": "custom" },
  "uds"   : { "ln" : "updateStatus", "type": "custom" },
  "un"    : { "ln" : "uninstall", "type": "" },
  "url"   : { "ln" : "URL", "type": "custom" },
  "verAy" : { "ln" : "verticalAccuracy", "type": "custom" },
  "vlde"  : { "ln" : "validationEnable", "type": "" },
  "volte" : { "ln" : "voltage", "type": "custom" },
  "vr"    : { "ln" : "version", "type": "custom" },


  // proprietary custom attributes
  "crRes" : { "ln" : "createdResources", "type": "custom" },
  "cseSU" : { "ln" : "cseStartUpTime", "type": "custom" },
  "cseUT" : { "ln" : "cseUptime", "type": "custom" },
  "ctRes" : { "ln" : "resourceCount", "type": "custom" },
  "htCre" : { "ln" : "httpCreates", "type": "custom" },
  "htDel" : { "ln" : "httpDeletes", "type": "custom" },
  "htRet" : { "ln" : "httpRetrieves", "type": "custom" },
  "htUpd" : { "ln" : "httpUpdates", "type": "custom" },
  "lgErr" : { "ln" : "logErrors", "type": "custom" },
  "lgWrn" : { "ln" : "logWarnings", "type": "custom" },
  "rmRes" : { "ln" : "deletedResources", "type": "custom" },
  "upRes" : { "ln" : "updatedResources", "type": "custom" }
}


function shortToLongname(sn) {
  if (printLongNames && sn in shortNames) {
    return shortNames[sn].ln
  }
  return sn
}

function attributeRole(sn) {
    if (sn in shortNames) {
    return shortNames[sn].type
  }
  return "custom"
}