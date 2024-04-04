from flask_restful import Resource, Api
from app import app


api = Api(app)


class Section(Resource):
    def get(self):
        return {"hello": "world"}


api.add_resource(Section, "/api/section")
