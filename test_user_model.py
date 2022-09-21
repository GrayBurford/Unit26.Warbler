"""User model tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_user_model.py

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

class UserModelTestCase(TestCase):
    """Test user model"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        # u1 = User(
        #     email="u1@u1.com",
        #     username="u1",
        #     password="u1pw",
        #     image_url = "www.u1.com",
        #     header_image_url="www.u1header.com",
        #     bio="u1bio",
        #     location="u1location"
        # )

        # u2 = User(
        #     email="u2@u2.com",
        #     username="u2",
        #     password="u2pw",
        #     image_url = "www.u2.com",
        #     header_image_url="www.u2header.com",
        #     bio="u2bio",
        #     location="u2location"
        # )

        # db.session.add_all([u1, u2])
        # db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """rollback setUp data"""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url = "www.google.com",
            header_image_url="www.reddit.com",
            bio="I am a test bio",
            location="Testing location"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.following), 0)
        self.assertEqual(len(u.likes), 0)

        user_id = User.query.filter_by(username="testuser").one()
        self.assertEqual(u.id, user_id.id)
        self.assertEqual(u.email, "test@test.com")
        self.assertEqual(u.username, "testuser")
        self.assertEqual(u.password, "HASHED_PASSWORD")
        self.assertEqual(u.image_url, "www.google.com")
        self.assertEqual(u.header_image_url, "www.reddit.com")
        self.assertEqual(u.bio, "I am a test bio")
        self.assertEqual(u.location, "Testing location")

    def test_repr_function(self):
        """Test representation of User model with repr"""

        user = User(
            email="abc@123.com",
            username="testuser",
            password="HASH"
        )

        db.session.add(user)
        db.session.commit()

        self.assertEqual(repr(user), f"<User #{user.id}: testuser, abc@123.com>")

    def test_is_following_function(self):
        """Tests is_following function when user1 follows user2"""

        u1 = User(
            email="u1@u1.com",
            username="u1",
            password="u1pw",
            image_url = "www.u1.com",
            header_image_url="www.u1header.com",
            bio="u1bio",
            location="u1location"
        )

        u2 = User(
            email="u2@u2.com",
            username="u2",
            password="u2pw",
            image_url = "www.u2.com",
            header_image_url="www.u2header.com",
            bio="u2bio",
            location="u2location"
        )

        db.session.add_all([u1,u2])
        db.session.commit()

        self.assertEqual(len(u2.followers), 0)
        self.assertFalse(u1.is_following(u2))

        follow_test = Follows(user_being_followed_id=u2.id, user_following_id=u1.id)
        db.session.add(follow_test)
        db.session.commit()

        self.assertEqual(len(u2.followers), 1)
        self.assertTrue(u1.is_following(u2))


    def test_is_followed_by_function(self):
        """Tests is_followed_by function when user1 follows user2"""

        u1 = User(
            email="u1@u1.com",
            username="u1",
            password="u1pw",
            image_url = "www.u1.com",
            header_image_url="www.u1header.com",
            bio="u1bio",
            location="u1location"
        )

        u2 = User(
            email="u2@u2.com",
            username="u2",
            password="u2pw",
            image_url = "www.u2.com",
            header_image_url="www.u2header.com",
            bio="u2bio",
            location="u2location"
        )

        db.session.add_all([u1,u2])
        db.session.commit()

        self.assertEqual(len(u2.followers), 0)
        self.assertFalse(u2.is_followed_by(u1))

        follow_test = Follows(user_being_followed_id=u2.id, user_following_id=u1.id)
        db.session.add(follow_test)
        db.session.commit()

        self.assertEqual(len(u2.followers), 1)
        self.assertTrue(u2.is_followed_by(u1))

    def test_user_signup(self):
        """Test User model signup function"""

        test_user = User.signup('testusername', 'test@gmail.com', 'testpass', 'http://www.test.com')
        db.session.add(test_user)
        db.session.commit()

        user = User.query.get(test_user.id)

        self.assertEqual(user.username, 'testusername')
        self.assertEqual(user.email, 'test@gmail.com')
        # Bcrypt strings should start with $2b$
        self.assertIn('$2b$', user.password)

    def test_invalid_username_signup(self):
        user = User.signup(None, 'test@gmail.com', 'testpass', None)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        user = User.signup("testusername", None, "testpass", None)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testusername", "test@gmail.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testusername", "test@gmail.com", None, None)

    def test_user_authenticate(self):
        """Test User model authenticate function"""

        user = User.signup(
            email="abc@123.com",
            username="testusername",
            password="testingpassword",
            image_url="http://www.google.com"
        )
        db.session.add(user)
        db.session.commit()

        test = User.authenticate("testusername", "testingpassword")
        self.assertIsNotNone(test)

        wrong_pass = User.authenticate(user.username, "wrongpassword")
        self.assertFalse(wrong_pass)

        wrong_username = User.authenticate("wrongusername", user.password)
        self.assertFalse(wrong_username)