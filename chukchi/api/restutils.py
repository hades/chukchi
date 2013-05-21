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

from flask import json, jsonify, request, Response
from werkzeug.exceptions import default_exceptions, HTTPException

class JsonResponse(Response):
    def __init__(self, response=None, *args, **kwargs):
        if isinstance(response, dict):
            response = json.dumps(response,
                                  indent=None if request.is_xhr else 2)
        super(JsonResponse, self).__init__(response, *args, **kwargs)
        self.mimetype = 'application/json'

    @classmethod
    def force_type(cls, rv, *args, **kwargs):
        if isinstance(rv, dict):
            return JsonResponse(rv)
        return super(JsonResponse, cls).force_type(rv, *args, **kwargs)

def setup_json_handlers(app):
    def make_json_error(ex):
        code = ex.code if isinstance(ex, HTTPException) else 500
        response = jsonify(message=str(ex), error=code)
        response.status_code = code
        return response

    for code in default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = make_json_error

    return app

def setup_rest_app(app):
    setup_json_handlers(app)
    app.response_class = JsonResponse
