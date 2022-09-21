"""User views tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase
# from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app
from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test
app.config['WTF_CSRF_ENABLED'] = False

class UserViewsTestCase(TestCase):
    """Test user model"""

    def setUp(self):
        """Create test client, add sample data."""

        # does this work the same as .query.delete()?
        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        self.u1 = User.signup(
            email="u1email@u1.com",
            username="u1username",
            password="u1password",
            image_url=None
        )
        self.u1.id = 111

        self.u2 = User.signup(
            email="u2email@u2.com",
            username="u2username",
            password="u2password",
            image_url=None
        )
        self.u2.id = 222

        db.session.add_all([self.u1, self.u2])
        db.session.commit()


    def tearDown(self):
        """rollback setUp data"""

        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_model(self):
        """Tests setup User models"""

        self.assertEqual(self.u1.username, "u1username")
        self.assertEqual(self.u1.email, "u1email@u1.com")
        self.assertEqual(self.u1.image_url, "/static/images/default-pic.png")

        self.assertEqual(self.u2.username, "u2username")
        self.assertEqual(self.u2.email, "u2email@u2.com")
        self.assertEqual(self.u2.image_url, "/static/images/default-pic.png")

        self.assertTrue(self.u1.authenticate(self.u1.username, "u1password"))
        self.assertTrue(self.u2.authenticate(self.u2.username, "u2password"))

    def test_signup_page(self):
        """Test GET/POST requests for signup page."""

        with self.client as client:
            response = client.get('/signup')

            self.assertEqual(response.status_code, 200)
            self.assertIn("Join Warbler today.", response.get_data(as_text=True))

            # follow_redirects=True, otherwise status code will be 302. Should be 200.
            response = client.post('/signup', data = {
                'username':'test',
                'email':'test@email.com',
                'password':'hashed_pwd',
                'image_url':'None'
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 200)

    def test_login_get(self):
        """Test GET request for login route"""

        with self.client as client:
            response = client.get('/login')

            self.assertEqual(response.status_code, 200)
            self.assertIn("Welcome back.", response.get_data(as_text=True))    

    def test_users_page(self):
        """Test all users display page."""

        with self.client as client:
            response = client.get('/users')

            self.assertEqual(response.status_code, 200)
            self.assertIn(f'@{self.u1.username}', response.get_data(as_text=True))  
            self.assertIn(f'@{self.u2.username}', response.get_data(as_text=True))  

    def test_user_detail_page(self):
        """Test individual user detail page."""

        with self.client as client:
            response = client.get(f'/users/{self.u2.id}')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.u2.id, 222)  
            self.assertIn(f'@{self.u2.username}', response.get_data(as_text=True))  
            self.assertIn('Messages', response.get_data(as_text=True))  
            self.assertIn('Followers', response.get_data(as_text=True))  
            self.assertIn('Following', response.get_data(as_text=True))  
            self.assertIn('Likes', response.get_data(as_text=True)) 

    def test_see_following(self):
        """Tests a user following another user"""

        one_follows_two = Follows(
            user_being_followed_id=self.u2.id, 
            user_following_id=self.u1.id
        )
        db.session.add(one_follows_two)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1.id

            response = client.get(f'/users/{self.u1.id}/following', follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('@u2username', response.get_data(as_text=True))

    def test_see_followers(self):
        """Tests a user being followed by another user."""

        one_follows_two = Follows(
            user_being_followed_id=self.u2.id, 
            user_following_id=self.u1.id
        )
        db.session.add(one_follows_two)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.u2.id

            response = client.get(f'/users/{self.u2.id}/followers', follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('@u1username', response.get_data(as_text=True))

    def test_follower_logged_out(self):
        """Can a user go to a followers page while logged out?"""

        with self.client as client:

            response = client.get('/users/301/followers', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('What\'s Happening?', response.get_data(as_text=True))

    def test_following_logged_out(self):
        """Can a user go to a following page while logged out?"""

        with self.client as client:

            response = client.get('/users/301/following', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('What\'s Happening?', response.get_data(as_text=True))