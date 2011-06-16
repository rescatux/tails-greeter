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
"""Structural Errors which track err throughout a complex structure."""

class ElementErrors(dict):
    """Keep track of errors as they're added, true if errors."""
    def __init__(self, mode='AND'):
        self._in_error = 0
        self._added = 0
        self._mode = mode

    def __setitem__(self, key, value):
        if super(ElementErrors, self).has_key(key):
            self.remove_error(self[key])
        super(ElementErrors, self).__setitem__(key, value)
        self.add_error(value)

    def __repr__(self):
        return "Err:%s" % super(ElementErrors, self).__repr__()

    def pop(self, key):
        self.remove_error(super(ElementErrors, self).pop(key))

    def update(self, iterable):
        # Adding a batch of errors is counted as one.
        #for key in iterable.keys():
        #    self._data[key] = iterable[key]
        super(ElementErrors, self).update(iterable)
        self.add_error(iterable)

    def add_error(self, error):
        if error:
            self._in_error += 1
        self._added += 1

    def remove_error(self, error):
        if error:
            self._in_error -= 1
        self._added -= 1

    def __nonzero__(self):
        #print "In ERROR: %s %i:%i" % (str(self._data), self._in_error, self._added)
        if self._mode == 'OR' and self._added > 0:
            return self._in_error >= self._added
        else: # AND
            return self._in_error != 0

    def __eq__(self, errors):
        if not isinstance(errors, dict):
            raise ValueError("Can't compare error dictionary with %s" % type(errors))
        for (key, value) in super(ElementErrors, self).iteritems():
            if not errors.has_key(key) or errors[key] != value:
                return False
        return True

    def __ne__(self, opt):
        return not self.__eq__(opt)


class ValidateError(object):
    """Control the validation errrors and how they're displayed"""
    def __init__(self, code, msg, desc=None):
        self._code = code
        self._msg  = msg
        self._desc = desc

    def __repr__(self):
        return "#%s" % self._msg

    def __int__(self):
        return self._code

    def __str__(self):
        result = [ self._msg ]
        if self._desc:
            result.append( self._desc )
        return ' '.join(result)

    def __unicode__(self):
        return unicode(str(elf._msg))

    def __nonzero__(self):
        return self._code > 0

    def __eq__(self, opt):
        if isinstance(opt, ValidateError):
            opt = opt._code
        return self._code == opt

    def __ne__(self, opt):
        return not self.__eq__(opt)



# Error codes
NOERROR             = ValidateError(0x00, 'OK')
INVALID_TYPE        = ValidateError(0x01, 'Invalid Node Type')
INVALID_PATTERN     = ValidateError(0x02, 'Invalid Pattern', 'Regex Pattern failed')
INVALID_MINLENGTH   = ValidateError(0x03, 'Invalid MinLength', 'Not enough nodes present')
INVALID_MAXLENGTH   = ValidateError(0x04, 'Invalid MaxLength', 'Too many nodes present')
INVALID_MATCH       = ValidateError(0x05, 'Invalid Match', 'Node to Node match failed')
INVALID_VALUE       = ValidateError(0x06, 'Invalid Value', 'Fixed string did not match')
INVALID_NODE        = ValidateError(0x07, 'Invalid Node', 'Required data does not exist for this node')
INVALID_ENUMERATION = ValidateError(0x08, 'Invalid Enum', 'Data not equal to any values supplied')
INVALID_MIN_RANGE   = ValidateError(0x09, 'Invalid Number', 'Less than allowable range')
INVALID_MAX_RANGE   = ValidateError(0x0A, 'Invalid Number', 'Greater than allowable range')
INVALID_NUMBER      = ValidateError(0x0B, 'Invalid Number', 'Data is not a real number')
INVALID_COMPLEX     = ValidateError(0x0C, 'Invalid Complex Type', 'Failed to validate Complex Type')
INVALID_EXIST       = ValidateError(0x0D, 'Invalid Exists', 'Data didn\'t exist, and should.')
INVALID_MIN_OCCURS  = ValidateError(0x0E, 'Invalid Occurs', 'Minium number of occurances not met')
INVALID_MAX_OCCURS  = ValidateError(0x0F, 'Invalid Occurs', 'Maxium number of occurances exceeded')
INVALID_CUSTOM      = ValidateError(0x10, 'Invalid Custom Filter', 'Method returned false')
CRITICAL            = ValidateError(0x11, 'Critical Problem')

