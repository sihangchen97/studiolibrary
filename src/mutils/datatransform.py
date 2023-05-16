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
from collections import OrderedDict
import logging

import mutils
from mutils.cmds import listOperator

try:
    import maya.cmds
except Exception:
    import traceback
    traceback.print_exc()


logger = logging.getLogger(__name__)


def saveDataTransform(path, csvPath='', metadata=None):
    """
    Convenience function for saving a selection set to the given disc location.
    
    :type path: str
    :type objects: list[str]
    :type metadata: dict or None
    :type args: list
    :type kwargs: dict
    :rtype: SelectionSet 
    """
    dataTransform = DataTransform()

    if metadata:
        dataTransform.updateMetadata(metadata)
    if csvPath:
        dataTransform.setDataTransformByCsv(csvPath)

    dataTransform.save(path)

    return dataTransform


class DataTransform(mutils.TransferObject):

    @classmethod
    def fromPath(cls, path):
        """
        Return a new transfer instance for the given path.

        :type path: str
        :rtype: TransferObject
        """
        t = cls()
        t.setPath(path)
        t.read(path+'/DataTransform.json')
        t.setDataTransformByCsv(path + '/datatransform.csv')
        return t

    def __init__(self):
        super(DataTransform, self).__init__()
        self._datatransform = {}

    def save(self, path):
        super(DataTransform, self).save(path + '/datatransform.json')
        with open(path + "/datatransform.csv", "w") as f:
            names = self.dataNames()
            for name in names:
                f.write(name+","+",".join([str(v) for v in self.dataTransformConfig(name)]) + '\n')
    
    def dataNames(self):
        return self.datatransform().keys()
    
    def dataTransformConfig(self, dataName):
        try:
            return self.datatransform()[dataName]
        except:
            return []

    def datatransform(self):
        return self._datatransform
    
    def setDataTransformByCsv(self, csvPath=''):
        self._datatransform = self.readCsv(csvPath, columnMajor=False, type=['float','str'])
    
    def method(self):
        return self.metadata().get("method", "")

    def doDataTransform(self, inCurveValueMap):

        def getCurveValueInMap(curveValueMap, curveName):
            return curveValueMap[curveName]  if curveName in curveValueMap.keys() else 0.0

        outCurveValueMap = OrderedDict()
        for name in self.dataNames():
            configs = self.dataTransformConfig(name)
            value = 0.0
            for i in range(len(configs)//2):
                if configs[i*2]=='' or configs[i*2+1]=='':
                    break
                try:
                    v = getCurveValueInMap(inCurveValueMap, configs[i*2])
                    w = float(configs[i*2+1])
                except:
                    print("Found Invalid Config! Data Name: " + name + "\nIndex: " + str(i*2+1))
                    continue
                if self.method()=='max':
                    value = max(value, v*w)
                elif self.method()=='sum':
                    value = value + v*w
            outCurveValueMap[name] = value
        
        return outCurveValueMap
    
    def doDataTransformList(self, inCurveValueListMap):

        def getCurveValueListInMap(curveValueListMap, curveName):
            for k in curveValueListMap.keys():
                if k.lower()==curveName.lower():
                    return curveValueListMap[k]
            return []

        outCurveValueListMap = OrderedDict()
        for name in self.dataNames():
            configs = self.dataTransformConfig(name)
            valueList = []
            for i in range(len(configs)//2):
                if configs[i*2]=='' or configs[i*2+1]=='':
                    break
                try:
                    vList = getCurveValueListInMap(inCurveValueListMap, configs[i*2])
                    w = float(configs[i*2+1])
                except:
                    print("Found Invalid Config! Data Name: " + name + "\nIndex: " + str(i*2+1))
                    continue
                if self.method()=='max':
                    valueList = listOperator(valueList, listOperator(vList, w, 'multiplyFloat'), 'max')
                elif self.method()=='sum':
                    valueList = listOperator(valueList, listOperator(vList, w, 'multiplyFloat'), 'add')
            outCurveValueListMap[name] = valueList
        
        return outCurveValueListMap
