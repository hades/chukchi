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

DATABASE = 'postgresql:///chukchi'
DATABASE_ENGINE_CONFIG = {}
DEBUG = False
FROM_EMAIL = 'no-reply@chukchi.hades.name'
SECRET_KEY = 'N\xc6\x95&\xb2$\xdaeY\xea\xce\xa2\xba(\xbf\x94"\xb8\x0b\xb9\xfa\xcf\xf8\xbe\x17\xdfMO\xe6W\x93\x8f/\xdc\xc8\x14\xc8\xe53E'
SITE_URL = "http://127.0.0.1:5000"
UPDATE_DELAY = {'minutes': 30}

# vi: sw=4:ts=4:et
