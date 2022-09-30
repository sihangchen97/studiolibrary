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
from mutils.namemapping import NameMapping

try:
    import mutils
except ImportError as error:
    print(error)

from studiolibrarymaya import baseitem


def save(path, *args, **kwargs):
    """Convenience function for saving a NameMappingItem."""
    NameMappingItem(path).safeSave(*args, **kwargs)


def load(path, *args, **kwargs):
    """Convenience function for loading a NameMappingItem."""
    NameMappingItem(path).load(*args, **kwargs)


class NameMappingItem(baseitem.BaseItem):

    NAME = "Name Mapping"
    EXTENSION = ".namemapping"
    ICON_PATH = os.path.join(os.path.dirname(__file__), "icons", "selectionSet.png")
    TRANSFER_CLASS = mutils.SelectionSet
    TRANSFER_BASENAME = "namemapping.json"

    def saveSchema(self):
        schema = super(NameMappingItem, self).saveSchema()[:-1]
        mappingText = ""
        for k, v in NameMapping.fromPath(self.path()).mapping().items():
            mappingText += "\""+k+"\": \""+v+"\",\n"
        mappingText = mappingText[:-2]
        schema.append({
                "name": "mapping",
                "type": "text",
                "layout": "vertical",
                "default": mappingText
            }
        )
        return schema
    
    def loadSchema(self):
        schema = super(NameMappingItem, self).loadSchema()[:-3]
        schema.append(
            {
                "name": "mappingGroup",
                "title": "Mapping",
                "type": "group",
                "order": 10,
            },
        )
        for i, (k, v) in enumerate(NameMapping.fromPath(self.path()).mapping().items()):
            schema.append({"name": str(i),"value": k+' -> '+v})
        return schema
    
    def saveValidator(self, **kwargs):
        fields = super(NameMappingItem, self).saveValidator(**kwargs)[:-1]
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
        super(NameMappingItem, self).save(**kwargs)

        # Save the name mapping to the given path
        mutils.saveNameMapping(
            self.path(),
            mapping=json.loads('{'+kwargs.get('mapping')+'}', object_pairs_hook=OrderedDict),
            metadata={"description": kwargs.get("comment", "")}
        )

    def safeSave(self, *args, **kwargs):
        return super(NameMappingItem, self).safeSave(*args, objects = [], **kwargs)