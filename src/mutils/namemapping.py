# Copyright 2020 by Sihang Chen. All Rights Reserved.
#
# This library is free software: you can redistribute it and/or modify it 
# under the terms of the GNU Lesser General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. This library is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <http://www.gnu.org/licenses/>.

import json
import logging

import mutils

try:
    import maya.cmds
except Exception:
    import traceback
    traceback.print_exc()


logger = logging.getLogger(__name__)


def saveNameMapping(path, mapping={}, metadata=None):
    """
    Convenience function for saving a selection set to the given disc location.
    
    :type path: str
    :type objects: list[str]
    :type metadata: dict or None
    :type args: list
    :type kwargs: dict
    :rtype: SelectionSet 
    """
    nameMapping = NameMapping()

    if metadata:
        nameMapping.updateMetadata(metadata)
    if mapping:
        nameMapping.updateMapping(mapping)

    nameMapping.save(path)

    return nameMapping


class NameMapping(mutils.TransferObject):

    @classmethod
    def fromPath(cls, path):
        """
        Return a new transfer instance for the given path.

        :type path: str
        :rtype: TransferObject
        """
        t = cls()
        t.setPath(path)
        t.read(path+'/namemapping.json')
        t.setMappingByPath(path+'/mapping.json')
        return t

    def __init__(self):
        super(NameMapping, self).__init__()
        self._mapping = {}

    def save(self, path):
        super(NameMapping, self).save(path + '/namemapping.json')
        with open(path + "/mapping.json", "w") as f:
            json.dump(self.mapping(), f)
    
    def mapping(self):
        return self._mapping
    
    def setMappingByPath(self, path=''):
        self._mapping = self.readJson(path, keepOrder=True)

    def updateMapping(self, mapping):
        self.mapping().update(mapping)
    
    def doNameMapping(self, name):
        return self.mapping()[name] if name in self.mapping().keys() else name
    
    def doNameMappingList(self, nameList):
        return [self.doNameMapping(name) for name in nameList]
