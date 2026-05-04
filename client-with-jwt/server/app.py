from flask import request
from flask_restful import Api, Resource
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from config import create_app
from models import db, User, JournalEntry

app = create_app()
api = Api(app)


# -----------------------
# AUTH ROUTES
# -----------------------

class Signup(Resource):
    def post(self):
        data = request.get_json() or {}

        username = data.get("username")
        password = data.get("password")
        password_confirmation = data.get("password_confirmation")

        if not username or not password:
            return {"error": "Username and password required"}, 400

        if password != password_confirmation:
            return {"error": "Passwords do not match"}, 400

        if User.query.filter_by(username=username).first():
            return {"error": "Username already exists"}, 400

        user = User(username=username)
        user.password_hash = password

        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=user.id)

        return {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username
            }
        }, 201


class Login(Resource):
    def post(self):
        data = request.get_json() or {}

        if not data.get("username") or not data.get("password"):
            return {"error": "Username and password required"}, 400

        user = User.query.filter_by(username=data.get("username")).first()

        if user and user.authenticate(data.get("password")):
            token = create_access_token(identity=user.id)

            return {
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username
                }
            }, 200

        return {"error": "Invalid credentials"}, 401


class Me(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)

        if not user:
            return {"error": "User not found"}, 404

        return {
            "id": user.id,
            "username": user.username
        }, 200


# -----------------------
# RESOURCE ROUTES
# -----------------------

class JournalEntries(Resource):

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 5))

        pagination = JournalEntry.query\
            .filter_by(user_id=user_id)\
            .order_by(JournalEntry.id.desc())\
            .paginate(page=page, per_page=per_page)

        return {
            "entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "content": e.content,
                    "created_at": e.created_at.isoformat()
                } for e in pagination.items
            ],
            "total": pagination.total,
            "pages": pagination.pages
        }, 200

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        if not data.get("title") or not data.get("content"):
            return {"error": "Title and content required"}, 400

        entry = JournalEntry(
            title=data["title"],
            content=data["content"],
            user_id=user_id
        )

        db.session.add(entry)
        db.session.commit()

        return {"message": "Created"}, 201


class JournalEntryByID(Resource):

    @jwt_required()
    def patch(self, id):
        user_id = get_jwt_identity()
        entry = db.session.get(JournalEntry, id)

        if not entry:
            return {"error": "Not found"}, 404

        if entry.user_id != user_id:
            return {"error": "Unauthorized"}, 403

        data = request.get_json() or {}

        entry.title = data.get("title", entry.title)
        entry.content = data.get("content", entry.content)

        db.session.commit()

        return {"message": "Updated"}, 200

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        entry = db.session.get(JournalEntry, id)

        if not entry:
            return {"error": "Not found"}, 404

        if entry.user_id != user_id:
            return {"error": "Unauthorized"}, 403

        db.session.delete(entry)
        db.session.commit()

        return {"message": "Deleted"}, 200


# -----------------------
# ROUTES
# -----------------------

api.add_resource(Signup, "/signup")
api.add_resource(Login, "/login")
api.add_resource(Me, "/me")
api.add_resource(JournalEntries, "/entries")
api.add_resource(JournalEntryByID, "/entries/<int:id>")


if __name__ == "__main__":
    app.run(port=5555, debug=True)