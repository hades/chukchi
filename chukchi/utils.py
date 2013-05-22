# This file is part of Chukchi, the free web-based RSS aggregator
#
#   Copyright (C) 2013 Edward Toroshchin <chukchi-project@hades.name>
#
# Chukchi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Chukchi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# Please see the file COPYING in the root directory of this project.
# If you are unable to locate this file, see <http://www.gnu.org/licenses/>.

from datetime import datetime
from json import JSONEncoder
from pytz import UTC
from time import strftime, struct_time

def now():
    return datetime.utcnow().replace(tzinfo=UTC)

def make_datetime(time):
    if time is None:
        return None
    if isinstance(time, datetime):
        return time
    return datetime(*time[:6]).replace(tzinfo=UTC)

class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, struct_time):
            return strftime("%a, %d %b %Y %H:%M:%S +0000", o)
        return super(CustomJSONEncoder, self).default(o)

def json_dumps(o, *args, **kwargs):
    return CustomJSONEncoder(*args, **kwargs).encode(o)

# vi: sw=4:ts=4:et
