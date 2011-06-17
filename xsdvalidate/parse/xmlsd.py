#
# Copyright 2010 Martin Owens
#
# This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>
#
"""
Parse an XML file into a data structure for validation

  Used internally to load xml files for both xsd definitions
  and xml data. For the xml data we use a simple conversion metric which treats each
  tag level as an hash reference and multiple tags witht he same name as an array reference.

  For the xsd defininitions we use the same method as the data to aquire the data but then
  It's converted into a simpler format and any features which arn't available will produce
  warnings.
"""

import xml.sax
from xml.sax.handler import ContentHandler
import logging

class ParseXML(object):
    """Create a new xml parser"""
    def __init__(self, xml):
        self._data = None
        self._xml = xml

    @property
    def data(self):
        """Return the parsed data structure."""
        if not self._data:
            parser = CustomParser()
            xml.sax.parse( self._xml, parser )
            self._data = parser._root
        return self._data

    @property
    def definition(self):
        """Convert the data into a definition, assume it's in xsd format."""
        data   = self.data.get('schema', None)
        result = {}
        if data:
            cdata = data.get('complexType', None)
            sdata = data.get('simpleType', None)
            result['complexTypes'] = self._decode_complexes( cdata )
            result['simpleTypes'] = self._decode_simples( sdata )
            result['root'] = self._decode_elements(data['element'])
        return result

    def _decode_complexes(self, data):
        if not data:
            return {}
        if not isinstance( data, list ):
            data = [ data ]
        complexes = {}
        for item in data:
            if item.has_key('_name'):
                complexes[item['_name']] = self._decode_complex( item )
            else:
                logging.warn("Complex type without a name!")
        return complexes

    def _decode_complex(self, data, extend=False):
        elements = []
        if data.has_key('element'):
            elements = self._decode_elements( data['element'] )
        # Logical And/Or have to be added as arrays of complexes
        for item in list(data.get('or', [])):
            result = self._decode_complex( item, extend=True )
            if extend:
                elements.extend( result )
            else:
                elements.append( result )
        # Elements can be extended or appended depending on their logic.
        for item in list(data.get('and', [])):
            result = self._decode_complex( item, extend=False )
            if extend:
                elements.extend( result )
            else:
                elements.append( result )
        # Politly return the elements configuration.
        return elements

    def _decode_elements(self, data):
        if not isinstance(data, list):
            data = [ data ]
        els = []
        for element in data:
            els.append(self._decode_element( element ))
        return els

    def _decode_simples(self, data):
        if not data:
            return {}
        simples = {}
        for item in data:
            name = data.pop('_name')
            simples[name] = self._decode_simple( name, item )
        return simples

    def _decode_simple(self, name, data):
        result = {}
        for key in data.keys():
            if key[1] == '_':
                result[key[1:]] = data[key]
        return result

    def _decode_element(self, data):
        element = {}
        if data.has_key('complexType'):
            element['complexType'] = self._decode_complex( data.pop('complexType') )
        elif data.has_key('_type'):
            # Get rid of the namespace, we don't need it.
            if ':' in data['_type']:
                element['type'] = data.pop('_type').split(':')[-1]
            else:
                element['type'] = data.pop('_type')
        # Translate the rest of the element's attributes
        for key in data.keys():
            if key[0] == '_':
                element[key[1:]] = data[key]
        return element



class CustomParser(ContentHandler):
    """Parsing the xml via SAX."""
    def __init__(self):
        """Create a new parser object."""
        self._root    = {}
        self._current = self._root
        self._parents = [ self._root ]
        self._count   = 0
        super(type(self), self).__init__()

    def skippedEntity(self, name):
        """Any elements that are skipped"""
        logging.warn("Skipping element %s" % name)

    def startElement(self, name, atrs):
        """Start a new xml element"""
        name = name.split(':')[-1]
        c    = self._current
        new  = {}

        if not c.has_key(name) or not c[name]:
            c[name] = new
        else:
            if not isinstance(c[name], list):
                c[name] = [ c[name] ]
            c[name].append( new )

        self._parents.append(c)
        self._count += 1
        self._name = name
        self._current = new

        for key in atrs.keys():
            value = atrs[key]
            key = key.split(':')
            if key[0] != 'xmlns':
                self._current['_' + key[-1]] = value

    def endElement(self, name):
        """Ends an xml element"""
        name = name.split(':')[-1]
        self._count += 1
        self._current = self._parents.pop()

    def characters(self, text):
        """Handle part of a cdata by concatination"""
        t = text
        # There must be a better way to test char exists.
        if t.strip():
            p = self._parents[-1]
            c = p.get(self._name, '')
            if isinstance(c, dict):
                if c:
                    if c.has_key('+data'):
                        c['+data'] += t
                    else:
                        c['+data'] = t

                else:
                    p[self._name] = t

            elif isinstance(c, list):
                # Remove an empty end item
                if isinstance(c[-1], dict) and not c[-1]:
                    c.pop()
                c.append(t)
            elif p.has_key(self._name):
                p[self._name] += t
            else:
                p[self._name] = t

