"""Message model tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_message_model.py

import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app
from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user = User.signup("testusername", "abc@123.com", "testingpassword", None)
        user.id = 99
        db.session.add(user)
        db.session.commit()

        self.assertIsNotNone(user)

    def tearDown(self):
        """Rollback changes to database"""

        res = super().tearDown()
        db.session.rollback()
        return res

    def test_create_user(self):
        """Testing user creation"""

        u1 = User.query.get(99)
        self.assertIsNotNone(u1)
        self.assertEqual(u1.username, "testusername")

    def test_message_model(self):
        """Test message model"""

        msg = Message(text="Warble Warble", user_id=99)
        db.session.add(msg)
        db.session.commit()

        u1 = User.query.get(99)

        self.assertEqual(len(u1.messages), 1)
        db.session.delete(msg)
        db.session.commit()
        self.assertEqual(len(u1.messages), 0)
