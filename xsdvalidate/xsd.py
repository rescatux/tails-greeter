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
"""XSD based data validation, see xsdvalidate documentation"""

import re
import os

from datetime import datetime, time, date
from xsdvalidate.parse import ParseXML
from xsdvalidate.errors import *


def test_datetime(data, stype=None):
    """Test to make sure it's a valid datetime"""
    try:
        if '-' in data and ':' in data:
            datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
        elif '-' in data:
            datetime.strptime(data, "%Y-%m-%d")
        elif ':' in data:
            datetime.strptime(data, "%H:%M:%S")
        else:
            return ValidateError(0x10, 'Invalid Date', 'Wasnt a known date format')
    except:
        return ValidateError(0x10, 'Invalid Date', 'Wasnt a valid date')
    return NOERROR


BASE_CLASSES = {
  'complexTypes': {},
  'simpleTypes': {
   'string'    : { 'pattern' : '.*' },
   'integer'   : { 'pattern' : '[\-]{0,1}\d+' },
   'index'     : { 'pattern' : '\d+' },
   'double'    : { 'pattern' : '[0-9\-\.]*' },
   'token'     : { 'base'    : 'string', 'pattern' : '\w+' },
   'boolean'   : { 'pattern' : '1|0|true|false' },
   'email'     : { 'pattern' : '.+@.+\..+' },
   'date'      : { 'pattern' : '\d\d\d\d-\d\d-\d\d', 'base' : 'datetime' },
   'time'      : { 'pattern' : '\d\d:\d\d:\d\d',     'base' : 'datetime' },
   'datetime'  : { 'pattern' : '(\d\d\d\d-\d\d-\d\d)?[T ]?(\d\d:\d\d:\d\d)?', 'custom' : test_datetime },
   'percentage': { 'base'    : 'double', 'minInclusive' : 0, 'maxInclusive' : 100 },
   }
}


class Validator(object):
    """Validation object"""
    def __init__(self, definition, debug=False):
        self._strict = False
        self._definition = None
        self._debug = debug
        if isinstance(definition, str):
            definition = self._load_file( definition, True )
        self.setDefinition( definition )

    def validate(self, data):
        """
        Validate a set of data against this validator.
        Returns an errors structure or 0 if there were no errors.
        """
        if isinstance(data, str):
            data = self._load_file( data )
        d = self._definition
        # Save the root data for this validation so it can be
        # used for xpath queries later on in the validation.
        self.current_root_data = data

        if d.has_key('root'):
            if data:
                return self._validate_elements( d['root'], data )
            else:
                raise Exception("VAL Error: No data provided")
        else:
            raise Exception("VAL Error: No root document definition")

    def setStrict(self, value=False):
        """Should missing data be considered an error."""
        self._strict = value

    def setDefinition(self, definition):
        """Set the validators definition, will load it (used internally too)"""
        self._definition = self._load_definition( definition )

    def getErrorString(self, err):
        """Return a human readable string for each error code."""
        if err > 0 and err <= len(ERRORS):
            return ERRORS[err]
        return 'Invalid error code'

    def _load_definition(self, definition):
        """Internal method for loading a definition into the validator."""
        # Make sure we have base classes in our definition.
        self._update_types(definition, BASE_CLASSES)

        # Now add any includes (external imports)
        for filename in definition.get('include', []):
            include = None
            if type(filename) in (str, unicode):
                include = self._load_definition_from_file( filename )
            elif type(filename) == dict:
                include = filename
            if include:
                self._update_types(definition, include)
            else:
                raise Exception("Can't load include: %s" % str(filename))
        return definition

    def _update_types(self, definition, source):
        """Update both simple and compelx types."""
        self._update_type(definition, source, 'simpleTypes')
        self._update_type(definition, source, 'complexTypes')

    def _update_type(self, definition, source, ltype):
        """This merges the types together to get a master symbol table."""
        definition[ltype] = definition.get(ltype, {})
        definition[ltype].update(source.get(ltype, {}))

    def _load_definition_from_file(self, filename):
        """Internal method for loading a definition from a file"""
        return self._load_definition( self._load_file( filename ) )

    def _validate_elements(self, definition, data, mode='AND'):
        """Internal method for validating a list of elements"""
        errors = ElementErrors(mode)

        # This should be AND or OR and controls the logic flow of the data varify
        if mode not in ('AND', 'OR'):
            raise Exception("Invalid mode '%s', should be AND or OR." % mode)

        if not isinstance(definition, list):
            raise Exception("Definition is not in the correct format: expected list (got %s)." % type(definition))

        for element in definition:
            # Element data check
            if isinstance(element, dict):
                name = element.get('name', None)
                # Skip element if it's not defined
                if not name:
                    continue
                errors[name] = self._validate_element( element, data.get(name, None), name )
            elif isinstance(element, list):
                subr = {}
                new_mode = mode == 'OR' and 'AND' or 'OR'
                errors.update(self._validate_elements( element, data, new_mode ))
            else:
                logging.warn("This is a complex type, but isn't element.")
        return errors


    def _validate_element(self, definition, data, name):
        """Internal method for validating a single element"""
        results = []
        proped  = False

        if data != None and not isinstance(data, list):
            proped = True
            data   = [ data ]

        minOccurs = int(definition.get('minOccurs', 1))
        maxOccurs = definition.get('maxOccurs', 1)
        dataType  = definition.get('type',      'string')
        fixed     = definition.get('fixed',     None)
        default   = definition.get('default',   None)

        # minOccurs checking
        if minOccurs >= 1:
            if data != None:
                if minOccurs > len(data):
                    return INVALID_MIN_OCCURS
            else:
                return INVALID_EXIST
        elif data == None:
            # No data and it wasn't required
            return NOERROR

        # maxOccurs Checking
        if maxOccurs != 'unbounded':
            if int(maxOccurs) < len(data):
                return INVALID_MAX_OCCURS

        for element in data:
            # Fixed checking
            if fixed != None:
                if not isinstance(element, basestring) or element != fixed:
                    results.push(INVALID_VALUE)
                    continue
            # Default checking
            if default != None and element == None:
                element = default

            opts = {}
            for option in ('minLength', 'maxLength'):
                opts[option] = definition.get(option, None)

            # Element type checking
            result = self._validate_type( dataType, element, **opts )
            if result:
                results.append(result)

        if len(results) > 0:
            return proped and results[0] or results
        return NOERROR


    def _validate_type(self, typeName, data, **opts):
        """Internal method for validating a single data type"""
        definition = self._definition
        stt = definition['simpleTypes'].get(typeName, None)
        ctt = definition['complexTypes'].get(typeName, None)

        if stt:
            simpleType = stt.copy()
            simpleType.update(opts)
            base    = simpleType.get('base',    None)
            pattern = simpleType.get('pattern', None)
            custom  = simpleType.get('custom',  None)

            # Base type check
            if base:
                err = self._validate_type( base, data )
                if err:
                    return err

            # Pattern type check, assumes edge detection
            if pattern:
                if not re.match("^%s$" % pattern, data):
                    return INVALID_PATTERN

            # Custom method check
            if custom:
                failure = custom(data, simpleType)
                if failure:
                    return failure

            # Maximum Length check
            maxLength = simpleType.get('maxLength', None)
            if maxLength != None and len(data) > int(maxLength):
                return INVALID_MAXLENGTH

            # Minimum Length check
            minLength = simpleType.get('minLength', None)
            if minLength != None and len(data) < int(minLength):
                return INVALID_MINLENGTH

            # Match another node
            match = simpleType.get('match', None)
            nMatch = simpleType.get('notMatch', None)
            if match != None and self._find_value( match, data ) != data:
                return INVALID_MATCH
            if nMatch != None and self._find_value( nMatch, data ) == data:
                return INVALID_MATCH

            # Check Enumeration
            enum = simpleType.get('enumeration', None)
            if enum:
                if not isinstance(enum, list):
                    raise Exception("Validator Error: Enumberation not a list")
                if not data in enum:
                    return INVALID_ENUMERATION

            # This over-writes the data, so be careful
            try:
                data = long(data)
            except:
                pass

            for testName in ('minInclusive', 'maxInclusive', 'minExclusive',
                         'maxExclusive', 'fractionDigits'):
                operator = simpleType.get(testName, None)
                if operator != None:
                    if not isinstance(data, long):
                        return INVALID_NUMBER
                    if testName == 'minInclusive' and data < operator:
                        return INVALID_MIN_RANGE
                    if testName == 'maxInclusive' and data > operator:
                        return INVALID_MAX_RANGE
                    if testName == 'minExclusive' and data <= operator:
                        return INVALID_MIN_RANGE
                    if testName == 'maxExclusive' and data >= operator:
                        return INVALID_MAX_RANGE
                    # This is a bit of a hack, but I don't care so much.
                    if testName == 'fractionDigits' and '.' in str(data):
                        if len(str(data).split('.')[1]) > operator:
                            return INVALID_FRACTION

        elif ctt:
            if isinstance(data, dict):
                return self._validate_elements( ctt, data )
            else:
                return INVALID_COMPLEX
        else:
            logging.error("Validator Error: Can not find type definition '%s'" % typeName)
            return CRITICAL  
        return NOERROR


    def _find_value(self, path, data):
        """Internal method for finding a value match (basic xpath)"""
        # Remove root path, and stop localisation
        data  = path[0] == '/' and self.current_root_data or data
        paths = path.split('/')

        for segment in paths:
            if isinstance(data, dict):
                try:
                    data = data[segment]
                except:
                    logging.warn("Validator Error: Can't find nodes for '%s'" % path)
            else:
                logging.warn("Validator Error: Can't find nodes for '%s'" % path)
        return data



    def _load_file(self, filename, definition=None):
        """
        Internal method for loading a file, must be valid perl syntax.
        Yep that's right, be bloody careful when loading from files.
        """
        if not os.path.exists(filename):
            raise Exception("file doesn't exist: %s" % filename)
        fh = open( filename, 'r' )
        content = fh.read()
        fh.close()
  
        if content[0] == '<':
            # XML File, parse and load
            parser = ParseXML( filename )
            if definition and 'XMLSchema' in content:
                data = parser.definition
            else:
                data = parser.data
        else:
            # Try and execure the code like python
            data = eval('{ '+content+' }')
        return data

