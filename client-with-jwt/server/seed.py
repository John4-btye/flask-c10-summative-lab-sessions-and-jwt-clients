from config import create_app
from models import db, User, JournalEntry


app = create_app()


with app.app_context():
    print("Seeding database...")

    # Clear existing data
    JournalEntry.query.delete()
    User.query.delete()
    db.session.commit()

    # Create users
    user1 = User(username="alice")
    user1.password_hash = "password"

    user2 = User(username="bob")
    user2.password_hash = "password"

    db.session.add_all([user1, user2])
    db.session.commit()

    # Create journal entries
    entries = [
        JournalEntry(title="Alice Entry 1", content="Hello world", user_id=user1.id),
        JournalEntry(title="Alice Entry 2", content="Another note", user_id=user1.id),
        JournalEntry(title="Bob Entry 1", content="Bob's thoughts", user_id=user2.id),
    ]

    db.session.add_all(entries)
    db.session.commit()

    print("Seeding complete!")