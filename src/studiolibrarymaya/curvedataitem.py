# Copyright 2022 by Sihang Chen. All Rights Reserved.
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
import os
from mutils.curvedata import CurveData
from mutils.datatransform import DataTransform
from mutils.matchnames import matchCurveNames
from mutils.namemapping import NameMapping

try:
    import mutils
except ImportError as error:
    print(error)

from studiolibrarymaya import baseitem


def save(path, *args, **kwargs):
    """Convenience function for saving a CurveDataItem."""
    CurveDataItem(path).safeSave(*args, **kwargs)


def load(path, *args, **kwargs):
    """Convenience function for loading a CurveDataItem."""
    CurveDataItem(path).load(*args, **kwargs)


class CurveDataItem(baseitem.BaseItem):

    NAME = "Curve Data"
    EXTENSION = ".curvedata"
    ICON_PATH = os.path.join(os.path.dirname(__file__), "icons", "selectionSet.png")
    TRANSFER_CLASS = mutils.CurveData

    def saveSchema(self):
        schema = [
            {
                "name": "folder",
                "type": "path",
                "layout": "vertical",
                "visible": False,
            },
            {
                "name": "name",
                "type": "string",
                "layout": "vertical"
            },
            {
                "name": "dataSource",
                "type": "enum",
                "layout": "vertical",
                "default": "csv",
                "items": ["csv", "maya"],
                "persistent": True
            },
            {
                "name": "csvPath",
                "type": "string",
                "layout": "vertical",
                "actions": [
                    {
                        "name": "Select .csv File",
                        "callback": mutils.getSingleCsvFile
                    },
                ]
            },
            {
                "name": "curveFilter",
                "type": "enum",
                "layout": "vertical",
                "default": "none",
                "items": ["none", "arkit"],
                "persistent": True
            },
            {
                "name": "comment",
                "type": "text",
                "layout": "vertical"
            },
        ]
        return schema
    
    def loadSchema(self):
        schema = super(CurveDataItem, self).loadSchema()[:-3]
        curveData = self.transferObject()
        schema += [
            {
                "name": "curveDataGroup",
                "title": "Curve Data",
                "type": "group",
                "order": 10,
            },
            {
                "name": "names", 
                "value": ", ".join(curveData.curveNames())
            },
            {
                "name": "count", 
                "value": len(curveData.curveNames())
            },
            {
                "name": "duration", 
                "value": curveData.totalFrame()
            },
        ]

        dataTransformItems = self.library().findItems([{'filters': [('name', 'contains', '.datatransform'),]}])
        dataTransformItemNames = ['none'] + [item.name()[:-14] for item in dataTransformItems]
        nameMappingItems = self.library().findItems([{'filters': [('name', 'contains', '.namemapping'),]}])
        nameMappingItemNames = ['none'] + [item.name()[:-12] for item in nameMappingItems]
        schema += [
            {
                "name": "applyConfigsGroup",
                "title": "Apply Configs",
                "type": "group",
                "order": 20,
            },
            {
                "name": "dataTransform1",
                "type": "enum",
                "default": "none",
                "items": dataTransformItemNames,
                "persistent": True,
            },
            {
                "name": "dataTransform2",
                "type": "enum",
                "default": "none",
                "items": dataTransformItemNames,
                "persistent": True,
            },
            {
                "name": "nameMapping",
                "type": "enum",
                "default": "none",
                "items": nameMappingItemNames,
                "persistent": True,
            },
        ]

        schema += [
            {
                "name": "optionsGroup",
                "title": "Options",
                "type": "group",
                "order": 2,
            },
            {
                "name": "connect",
                "type": "bool",
                "inline": True,
                "default": False,
                "persistent": True,
                "label": {"name": ""}
            },
            {
                "name": "currentTime",
                "type": "bool",
                "inline": True,
                "default": True,
                "persistent": True,
                "label": {"name": ""}
            },
            {
                "name": "option",
                "type": "enum",
                "default": "replace all",
                "items": ["replace", "replace all", "insert", "merge"],
                "persistent": True,
            },
        ]
        return schema
    
    def saveValidator(self, **kwargs):
        fields = super(CurveDataItem, self).saveValidator(**kwargs)[:-1]
        return fields
        if kwargs.get("name"):
            name = kwargs.get("name")
            if not name.endswith(self.EXTENSION):
                name += self.EXTENSION
            if self.name()!=name and self.library().findItems([{'filters': [('name', 'is', name),]}]) != []:
                fields.append({
                    "name": "name",
                    "error": "Name has been used.",
                })

        if not kwargs.get('mapping'):
            fields.append({
                "name": "mapping",
                "error": "No mapping specified.",
            })
        else:
            try:
                json.loads('{'+kwargs.get('mapping')+'}')
            except:
                fields.append({
                    "name": "mapping",
                    "error": "Mapping not valid.",
                })
        return fields

    def load(self, **kwargs):

        anim = mutils.CurveData.fromPath(self.path())

        dataTransform1 = self.library().findItems([{'filters': [('name', 'is', kwargs.get("dataTransform1","") + '.datatransform'),]}])
        dataTransform2 = self.library().findItems([{'filters': [('name', 'is', kwargs.get("dataTransform2","") + '.datatransform'),]}])
        nameMapping = self.library().findItems([{'filters': [('name', 'is', kwargs.get("nameMapping","") + '.namemapping'),]}])

        anim.load(
            objects=kwargs.get("objects"),
            namespaces=kwargs.get("namespaces"),
            attrs=kwargs.get("attrs"),
            startFrame=kwargs.get("startFrame"),
            sourceTime=kwargs.get("sourceTime"),
            option=kwargs.get("option"),
            connect=kwargs.get("connect"),
            mirrorTable=kwargs.get("mirrorTable"),
            currentTime=kwargs.get("currentTime"),
            dataTransforms=[dataTransform1, dataTransform2],
            nameMapping=nameMapping
        )
        pass
    
    def save(self, objects, **kwargs):
        """
        Save all the given object data to the item path on disc.

        :type objects: list[str]
        :type kwargs: dict
        """
        super(CurveDataItem, self).save(**kwargs)

        # Save the name mapping to the given path
        mutils.saveCurveData(
            self.path(),
            csvPath=kwargs.get('csvPath'),
            metadata={"description": kwargs.get("comment", "")}
        )

    def safeSave(self, *args, **kwargs):
        return super(CurveDataItem, self).safeSave(*args, objects = [], **kwargs)