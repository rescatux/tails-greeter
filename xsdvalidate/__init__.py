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

__version__ = '0.5'

# Quick Access imports
from xsdvalidate.xsd import Validator

"""
Validate complex data structures with an xsd definition.

Based on xsd and xml validation, this is an attempt to provide those functions
without either xml or the hidous errors given out by modules like XPath.

The idea behind the error reporting is that the errors can reflect the structure
of the original structure replacing each variable with an error code and message.

Synopse:

from xsdvalidate import Validator

val = Validator( definition )
err = val.validate( data )

print err or "All is well!"

Definitions:

A definition is a hash containing information like an xml node containing children.

An example definition for registering a user on a website:

definition = {
    'root' : [
      { 'name' : 'input', 'type' : 'newuser' },
      { 'name' : 'foo',   'type' : 'string'  },
    ],

    'simpleTypes' : {
      'confirm'  : { 'base' : 'id',   'match'     : '/input/password' },
      'rname'    : { 'base' : 'name', 'minLength' : 1 },
      'password' : { 'base' : 'id',   'minLength' : 6 },
    },

    'complexTypes' : {
      'newuser' : [
        { 'name : 'username',     'type' : 'token'                                   },
        { 'name : 'password',     'type' : 'password'                                },
        { 'name : 'confirm',      'type' : 'confirm'                                 },
        { 'name : 'firstName',    'type' : 'rname'                                   },
        { 'name : 'familyName',   'type' : 'name',  'minOccurs' : 0                  },
        { 'name : 'nickName',     'type' : 'name',  'minOccurs' : 0                  },
        { 'name : 'emailAddress', 'type' : 'email', 'minOccurs' : 1, 'maxOccurs' : 3 },
    [
      { 'name' : 'aim',    'type' : 'index'  },
      { 'name' : 'msn',    'type' : 'email'  },
      { 'name' : 'jabber', 'type' : 'email'  },
      { 'name' : 'irc',    'type' : 'string' },
    ]
      ],
    },
}


Data:

And this is an example of the data that would validate against it:

data = {
    'input' : {
      'username'     : 'abcdef',
      'password'     : '1234567',
      'confirm'      : '1234567',
      'firstName'    : 'test',
      'familyName'   : 'user',
      'nickName'     : 'foobar',
      'emailAddress' : [ 'foo@bar.com', 'some@other.or', 'great@nice.con' ],
      'msn'          : 'foo@msn.com',
    },
    'foo' : 'extra content',
}


We are asking for a username, a password typed twice, some real names, a nick name,
between 1 and 3 email addresses and at least one instant message account, foo is an
extra string of information to show that the level is arbitary. bellow the definition
and all options are explained.

Errors and Results:

The first result you get is a structure the second is a boolean, the boolean explains the total stuctures pass or fail status.

The structure that is returned is almost a mirror structure of the input:

errors = {
    'input' : {
       'username'     : 0,
       'password'     : 0,
       'confirm'      : 0,
       'firstName'    : 0,
       'familyName'   : 0,
       'nickName'     : 0,
       'emailAddress' : 0,
    }
},


DETAILED DEFINITION:

Definition Root:

  root         - The very first level of all structures, it should contain the first
                 level complex type (see below). The data by default is a hash since
                 all xml have at least one level of xml tags names.

  import       - A list of file names, local to perl that should be loaded to include
                 further and shared simple and complex types. Supported formats are
                 "perl code", xml and yml.

  simpleTypes  - A hash reference containing each simple definition which tests a
                 scalar type (see below for format of each definition)
                

  complexTypes - A hash reference containing each complex definition which tests a
                 structure (see below for definition).


Simple Types:

  A simple type is a definition which will validate data directly, it will never validate
  arrays, hashes or any future wacky structural types. In perl parlance it will only validate
  SCALAR types. These options should match the w3c simple types definition:

  base           - The name of another simple type to first test the value against.
  fixed          - The value should match this exactly.
  pattern        - Should be a regular expresion reference which matchs the value i.e qr/\w/
  minLength      - The minimum length of a string value.
  maxLength      - The maximum length of a string value.
  match          - An XPath link to another data node it should match.
  notMatch       - An XPath link to another data node it should NOT match.
  enumeration    - An array reference of possible values of which value should be one.
  custom         - Should contain a CODE reference which will be called upon to validate the value.
  minInclusive   - The minimum value of a number value inclusive, i.e greater than or eq to (>=).
  maxInclusive   - The maximum value of a number value inclusive, i.e less than of eq to (<=).
  minExclusive   - The minimum value of a number value exlusive, i.e more than (>).
  maxExclusive   - The maximum value of a number value exlusive, i.e less than (<).
  fractionDigits - The maximum number of digits on a fractional number.

Complex Types:

  A complex type is a definition which will validate a hash reference, the very first structure,
  'root' is a complex definition and follows the same syntax as all complex types. each complex
  type is a list of data which should all occur in the hash, when a list entry is a hash it
  equates to one named entry in the hash data and has the following options:

  name      - Required name of the entry in the hash data.
  minOccurs - The minimum number of the named that this data should have in it.
  maxOccurs - The maximum number of the named that this data should have in it.
  type      - The type definition which validates the contents of the data.

  Where the list entry is an array, it will toggle the combine mode and allow further list entries
  With in it this allows for parts of the sturcture to be optional only if different parts of the
  stucture exist.

Inbuilt Types:

  By default these types are available to all definitions as base types.

    string           - /^.*$/
    integer          - /^[\-]{0,1}\d+$/
    index            - /^\d+$/
    double           - /^[0-9\-\.]*$/
    token            - /^\w+$/
    boolean          - /^1|0|true|false$/
    email            - /^.+@.+\..+$/
    date             - /^\d\d\d\d-\d\d-\d\d$/ + datetime
    'time'           - /^\d\d:\d\d$/ + datetime
    datetime         - /^(\d\d\d\d-\d\d-\d\d)?[T ]?(\d\d:\d\d)?$/ + valid_date method
    percentage       - minInclusive == 0 + maxInclusive == 100 + double

"""
