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
from mutils import matchCurveNames, initFloat
from mutils.datatransform import DataTransform
from mutils.animation import PasteOption, findFirstLastKeyframes, insertKeyframe, insertStaticKeyframe, moveTime
from mutils.namemapping import NameMapping

try:
    import maya.cmds
except Exception:
    import traceback
    traceback.print_exc()


logger = logging.getLogger(__name__)


def saveCurveData(path, csvPath="", metadata=None):
    """
    Convenience function for saving a selection set to the given disc location.
    
    :type path: str
    :type objects: list[str]
    :type metadata: dict or None
    :type args: list
    :type kwargs: dict
    :rtype: SelectionSet 
    """
    curveData = CurveData()

    if metadata:
        curveData.updateMetadata(metadata)
    if csvPath:
        curveData.setCurveDataByCsv(csvPath)

    curveData.save(path)

    return curveData


class CurveData(mutils.TransferObject):

    IMPORT_NAMESPACE = "REMOVE_IMPORT"

    @classmethod
    def fromPath(cls, path):
        """
        Return a new transfer instance for the given path.

        :type path: str
        :rtype: TransferObject
        """
        t = cls()
        t.setPath(path)
        t.read(path+'/CurveData.json')
        t.setCurveDataByCsv(path + '/curvedata.csv')
        return t

    def __init__(self):
        super(CurveData, self).__init__()
        self._curvedata = {}

    def save(self, path):
        super(CurveData, self).save(path + '/curvedata.json')
        with open(path + "/curvedata.csv", "w") as f:
            names = self.curveNames()
            f.write(",".join(names) + '\n')
            for i in range(self.totalFrame()):
                f.write(",".join([str(self.curveValue(name, i)) for name in names]) + '\n')

    def totalFrame(self):
        try:
            return len(self.curvedata()[self.curveNames()[0]])
        except:
            return 0
    
    def curveNames(self):
        return self.curvedata().keys()
    
    def curveValue(self, curveName, frame, default=0.0):
        try:
            return self.curvedata()[curveName][frame]
        except:
            return default
    
    def curveValueMapAtFrame(self, frame):
        data = OrderedDict()
        for name in self.curveNames():
            data[name] = self.curveValue(name, frame)
        return data

    def curvedata(self):
        return self._curvedata
    
    def setCurveDataByCsv(self, csvPath=''):
        self._curvedata = self.readCsv(csvPath, columnMajor=True, type=['int','float','str'])


    def open(self, inCurveData):
        """
        The reason we use importing and not referencing is because we
        need to modify the imported animation curves and modifying
        referenced animation curves is only supported in Maya 2014+
        """
        self.close()  # Make sure everything is cleaned before importing
        
        curveMap = {}
        for name in inCurveData.keys():
            data = inCurveData[name]
            curve = maya.cmds.createNode("animCurveTL", n=CurveData.IMPORT_NAMESPACE + ":CURVE")
            curveMap[name] = curve
            for i,v in enumerate(data):
                maya.cmds.setKeyframe(curve, t=i, v=initFloat(v))
        return curveMap

    def close(self):
        """
        Clean up all imported nodes, as well as the namespace.
        Should be called in a finally block.
        """
        nodes = maya.cmds.ls(CurveData.IMPORT_NAMESPACE + ":*", r=True) or []
        if nodes:
            maya.cmds.delete(nodes)

        # It is important that we remove the imported namespace,
        # otherwise another namespace will be created on next
        # animation open.
        namespaces = maya.cmds.namespaceInfo(ls=True) or []

        if CurveData.IMPORT_NAMESPACE in namespaces:
            maya.cmds.namespace(set=':')
            maya.cmds.namespace(rm=CurveData.IMPORT_NAMESPACE)

    
    @mutils.timing
    @mutils.showWaitCursor
    def load(
            self,
            objects=None,
            namespaces=None,
            attrs=None,
            startFrame=None,
            sourceTime=None,
            option=None,
            connect=False,
            mirrorTable=None,
            currentTime=None,
            dataTransforms=None,
            nameMapping=None
    ):
        """
        Load the animation data to the given objects or namespaces.

        :type objects: list[str]
        :type namespaces: list[str]
        :type startFrame: int
        :type sourceTime: (int, int) or None
        :type attrs: list[str]
        :type option: PasteOption or None
        :type connect: bool
        :type mirrorTable: mutils.MirrorTable
        :type currentTime: bool or None
        """
        logger.info(u'Loading: {0}'.format(self.path()))


        trgCurveData = self.curvedata()

        for dataTransform in dataTransforms:
            if dataTransform:
                dataTransform = DataTransform.fromPath(dataTransform[0].path())
                trgCurveData = dataTransform.doDataTransformList(trgCurveData)
            print(trgCurveData)        

        if nameMapping:
            nameMapping = NameMapping.fromPath(nameMapping[0].path())
            srcNames = trgCurveData.keys()
            trgNames = nameMapping.doNameMappingList(srcNames)
            srcCurveData = trgCurveData
            trgCurveData = OrderedDict()
            for i in range(len(srcNames)):
                trgCurveData[trgNames[i]] = srcCurveData[srcNames[i]]

        print(trgCurveData)

        matches = matchCurveNames(trgCurveData.keys(), objects, namespaces, exactMatch=True, fuzzyMatch=False)

        for src,dst in matches:
            print(src)
            print(dst.name()+"."+dst.attr())
        


        connect = bool(connect)  # Make false if connect is None

        if not sourceTime:
            sourceTime = (0, self.totalFrame()-1)

        if option and option.lower() == "replace all":
            option = "replaceCompletely"

        if option is None or option == PasteOption.ReplaceAll:
            option = PasteOption.ReplaceCompletely

        self.validate(namespaces=namespaces)

        objects = objects or []

        logger.debug("CurveData.load(objects=%s, option=%s, namespaces=%s, srcTime=%s, currentTime=%s)" %
                     (len(objects), str(option), str(namespaces), str(sourceTime), str(currentTime)))

        # if mirrorTable:
        #     self.setMirrorTable(mirrorTable)

        valid = False
        # matches = list(mutils.matchNames(srcObjects=srcObjects, dstObjects=objects, dstNamespaces=namespaces))

        for curveName, dstAttr in matches:
            if dstAttr.exists():
                valid = True
                break

        if not matches or not valid:

            text = "No objects match when loading data. " \
                   "Turn on debug mode to see more details."

            raise mutils.NoMatchFoundError(text)

        # Load the animation data.
        srcCurveMap = self.open(trgCurveData)
        srcCurves = srcCurveMap.values()
        print(srcCurveMap)

        try:
            maya.cmds.flushUndo()
            maya.cmds.undoInfo(openChunk=True)

            if currentTime and startFrame is None:
                startFrame = int(maya.cmds.currentTime(query=True))

            srcTime = findFirstLastKeyframes(srcCurves, sourceTime)
            dstTime = moveTime(srcTime, startFrame)

            if option != PasteOption.ReplaceCompletely:
                insertKeyframe(srcCurves, srcTime)

            for curveName, dstAttr in matches:

                # Remove the first pipe in-case the object has a parent
                # dstNode.stripFirstPipe()

                srcCurve = srcCurveMap[curveName]

                # Skip if the destination attribute does not exists.
                if not dstAttr.exists():
                    logger.debug('Skipping attribute: The destination attribute "%s.%s" does not exist!' %
                                    (dstAttr.name(), dstAttr.attr()))
                    continue

                if srcCurve:
                    dstAttr.setAnimCurve(
                        srcCurve,
                        time=dstTime,
                        option=option,
                        source=srcTime,
                        connect=connect
                    )

        finally:
            self.close()
            maya.cmds.undoInfo(closeChunk=True)

            # Return the focus to the Maya window
            maya.cmds.setFocus("MayaWindow")

        logger.info(u'Loaded: {0}'.format(self.path()))