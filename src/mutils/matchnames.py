# Copyright 2020 by Kurt Rathjen. All Rights Reserved.
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

import logging

import mutils

__all__ = [
    "matchNames",
    "groupObjects",
]


logger = logging.getLogger(__name__)


def rotateSequence(seq, current):
    """
    :type seq:
    :type current:
    :rtype:
    """
    n = len(seq)
    for i in range(n):
        yield seq[(i + current) % n]


def groupObjects(objects):
    """
    :type objects:
    :rtype:
    """
    results = {}
    for name in objects:
        node = mutils.Node(name)
        results.setdefault(node.namespace(), [])
        results[node.namespace()].append(name)
    return results


def indexObjects(objects):
    """
    :type objects: list[str]
    :rtype: dict
    """
    result = {}
    if objects:
        for name in objects:
            node = mutils.Node(name)
            result.setdefault(node.shortname(), [])
            result[node.shortname()].append(node)
    return result


def matchInIndex(node, index):
    """
    :type node: mutils.Node
    :type index: dict[list[mutils.Node]]
    :rtype: Node
    """
    result = None
    if node.shortname() in index:
        nodes = index[node.shortname()]
        if nodes:
            for n in nodes:
                if node.name().endswith(n.name()) or n.name().endswith(node.name()):
                    result = n
                    break
        if result is not None:
            index[node.shortname()].remove(result)

    return result


def matchNames(srcObjects, dstObjects=None, dstNamespaces=None, search=None, replace=None):
    """
    :type srcObjects: list[str]
    :type dstObjects: list[str]
    :type dstNamespaces: list[str]
    :rtype: list[(mutils.Node, mutils.Node)]
    """
    results = []
    if dstObjects is None:
        dstObjects = []

    srcGroup = groupObjects(srcObjects)
    srcNamespaces = srcGroup.keys()

    if not dstObjects and not dstNamespaces:  # and not selection:
        dstNamespaces = srcNamespaces

    if not dstNamespaces and dstObjects:
        dstGroup = groupObjects(dstObjects)
        dstNamespaces = dstGroup.keys()

    dstIndex = indexObjects(dstObjects)
    # DESTINATION NAMESPACES NOT IN SOURCE OBJECTS
    dstNamespaces2 = list(set(dstNamespaces) - set(srcNamespaces))

    # DESTINATION NAMESPACES IN SOURCE OBJECTS
    dstNamespaces1 = list(set(dstNamespaces) - set(dstNamespaces2))

    # CACHE DESTINATION OBJECTS WITH NAMESPACES IN SOURCE OBJECTS
    usedNamespaces = []
    notUsedNamespaces = []

    # FIRST LOOP THROUGH ALL DESTINATION NAMESPACES IN SOURCE OBJECTS
    for srcNamespace in srcNamespaces:
        if srcNamespace in dstNamespaces1:
            usedNamespaces.append(srcNamespace)
            for name in srcGroup[srcNamespace]:

                srcNode = mutils.Node(name)

                if search is not None and replace is not None:
                    # Using the mirror table which supports * style replacing
                    name = mutils.MirrorTable.replace(name, search, replace)

                dstNode = mutils.Node(name)

                if dstObjects:
                    dstNode = matchInIndex(dstNode, dstIndex)
                if dstNode:
                    results.append((srcNode, dstNode))
                    yield (srcNode, dstNode)
                else:
                    logger.debug("Cannot find matching destination object for %s" % srcNode.name())
        else:
            notUsedNamespaces.append(srcNamespace)

    # SECOND LOOP THROUGH ALL OTHER DESTINATION NAMESPACES
    srcNamespaces = notUsedNamespaces
    srcNamespaces.extend(usedNamespaces)
    _index = 0
    for dstNamespace in dstNamespaces2:
        match = False
        i = _index
        for srcNamespace in rotateSequence(srcNamespaces, _index):
            if match:
                _index = i
                break
            i += 1
            for name in srcGroup[srcNamespace]:
                srcNode = mutils.Node(name)
                dstNode = mutils.Node(name)
                dstNode.setNamespace(dstNamespace)

                if dstObjects:
                    dstNode = matchInIndex(dstNode, dstIndex)
                elif dstNamespaces:
                    pass

                if dstNode:
                    match = True
                    results.append((srcNode, dstNode))
                    yield (srcNode, dstNode)
                else:
                    logger.debug("Cannot find matching destination object for %s" % srcNode.name())

    if logger.parent.level == logging.DEBUG or logger.level == logging.DEBUG:
        for dstNodes in dstIndex.values():
            for dstNode in dstNodes:
                logger.debug("Cannot find matching source object for %s" % dstNode.name())


def matchCurveNames(srcCurveNames, dstObjects=None, dstNamespaces=None, exactMatch=True, fuzzyMatch=False):
    """
    :type srcCurveNames: list[str]
    :type dstObjects: list[str]
    :type dstNamespaces: list[str]
    :rtype: list[(mutils.Node, mutils.Node)]
    """
    results = []
    if dstObjects is None:
        dstObjects = []

    if not dstObjects and not dstNamespaces:
        dstNamespaces = []

    if not dstNamespaces and dstObjects:
        dstGroup = groupObjects(dstObjects)
        dstNamespaces = dstGroup.keys()

    def formatNodeAttr(name):
        s = name.split('.', 1)
        return s[0], s[1] if len(s)==2 else s[0]

    for dstObject in dstObjects:
        dstNode = mutils.Node(dstObject)
        dstAttrs = mutils.listAttr(dstObject, k=True)

        dstNodeName = dstNode.basename()

        for dstAttr in dstAttrs:
            dstAttrName = dstAttr.attr()

            matchCurve = ""
            matchType = 0 # 0 not found; 1 fuzzy match; 2 exact match

            for srcCurveName in srcCurveNames:
                srcNodeName, srcAttrName = formatNodeAttr(srcCurveName)

                dstNodeName = dstNodeName.lower()
                dstAttrName = dstAttrName.lower()
                srcNodeName = srcNodeName.lower()
                srcAttrName = srcAttrName.lower()

                v = 0
                v += 8 if srcNodeName==dstNodeName else 0
                v += 4 if srcAttrName==dstAttrName else 0
                v += 2 if dstNodeName.find(srcNodeName)!=-1 and dstAttrName.find(srcAttrName)!=-1 else 0
                
                if v>matchType:
                    matchType = v
                    matchCurve = srcCurveName
               
            if matchType>0:
                results.append((matchCurve, dstAttr))
        
    return results
