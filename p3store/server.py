import falcon
import json


class RedirectResource:
    def on_get(self, req, resp):
        """Redirect / to /quote"""
        resp.status = falcon.HTTP_302
        resp.location = '/v1/:/obj/myserver.tld'


class ObjectResource:
    def on_get(self, req, resp, object_):
        """Handles GET requests"""
        resp.body = json.dumps({
            'object': {
                'name': object_,
                'properties': ['a', 'b', 'c'],
            },
        })


class ObjectPropertyResource:
    def on_put(self, req, resp, object_, property):
        """Handles GET requests"""
        resp.body = json.dumps({
            'object': {
                'name': object_,
                'properties': ['a', 'b', 'c'],
            },
        })


api = falcon.API()
api.add_route('/', RedirectResource())
# v1 API
# : for default namespace
#
# #api.add_route('/v1/./grp/???', QuoteResource())  # get misc group info?
# #api.add_route('/v1/./usr/???', QuoteResource())  # get misc group info?
# GET for general info, POST for create (requires larger JS as input)
api.add_route('/v1/:/obj/{object_}', ObjectResource())
# GET for get, POST/PUT for create/replace
api.add_route('/v1/:/obj/{object_}/{property}', ObjectPropertyResource())

application = api
