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
from mutils import datatransform
from mutils.datatransform import DataTransform

try:
    import mutils
except ImportError as error:
    print(error)

from studiolibrarymaya import baseitem


def save(path, *args, **kwargs):
    """Convenience function for saving a DataTransformItem."""
    DataTransformItem(path).safeSave(*args, **kwargs)


def load(path, *args, **kwargs):
    """Convenience function for loading a DataTransformItem."""
    DataTransformItem(path).load(*args, **kwargs)


class DataTransformItem(baseitem.BaseItem):

    NAME = "Data Transform"
    EXTENSION = ".datatransform"
    ICON_PATH = os.path.join(os.path.dirname(__file__), "icons", "selectionSet.png")
    TRANSFER_CLASS = mutils.DataTransform

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
                "name": "method",
                "type": "enum",
                "layout": "vertical",
                "default": "sum",
                "items": ["sum", "max"],
                "persistent": True
            },
            {
                "name": "dataFilter",
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
        schema = super(DataTransformItem, self).loadSchema()[:-3]
        dataTransform = self.transferObject()
        schema += [
            {
                "name": "dataTransformGroup",
                "title": "Curve Data",
                "type": "group",
                "order": 10,
            },
            {
                "name": "names", 
                "value": ", ".join(dataTransform.dataNames())
            },
            {
                "name": "count", 
                "value": len(dataTransform.dataNames())
            },
            {
                "name": "method", 
                "value": dataTransform.method()
            },
        ]
        return schema
    
    def saveValidator(self, **kwargs):
        fields = super(DataTransformItem, self).saveValidator(**kwargs)[:-1]
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

    def loadFromCurrentValues(self):
        pass

    def load(self, **kwargs):
        pass
    
    def save(self, objects, **kwargs):
        """
        Save all the given object data to the item path on disc.

        :type objects: list[str]
        :type kwargs: dict
        """
        super(DataTransformItem, self).save(**kwargs)

        # Save the name mapping to the given path
        mutils.saveDataTransform(
            self.path(),
            csvPath=kwargs.get('csvPath'),
            metadata={"description": kwargs.get("comment", ""),
                      "method": kwargs.get("method", "")}
        )

    def safeSave(self, *args, **kwargs):
        return super(DataTransformItem, self).safeSave(*args, objects = [], **kwargs)