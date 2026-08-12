"""
Integration tests for the Mergington High School Activities API.
Tests cover happy paths and error cases for activity viewing and signup/removal operations.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities with correct structure"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have multiple activities
        assert len(data) > 0
        
        # Each activity should have required fields
        for activity_name, activity_details in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_includes_sample_activities(self, client):
        """Test that GET /activities includes expected sample activities"""
        response = client.get("/activities")
        data = response.json()
        
        # Check for some known activities
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_participants_have_emails(self, client):
        """Test that participants in activities are email strings"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            for participant in activity_details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email format check


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "alice@mergington.edu"
        
        # Verify email is not in activity initially (or is, but we'll check after signup)
        response_before = client.get("/activities")
        chess_participants_before = response_before.json()["Chess Club"]["participants"]
        
        # Signup
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Verify participant was added
        response_after = client.get("/activities")
        chess_participants_after = response_after.json()["Chess Club"]["participants"]
        
        assert len(chess_participants_after) == len(chess_participants_before) + 1
        assert email in chess_participants_after
    
    def test_signup_duplicate_fails(self, client):
        """Test that signup fails when student is already registered"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup fails when activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signup_missing_email_fails(self, client):
        """Test that signup fails when email parameter is missing"""
        response = client.post("/activities/Chess Club/signup")
        
        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == 422
    
    def test_signup_multiple_different_activities(self, client):
        """Test that a student can signup for multiple different activities"""
        email = "bob@mergington.edu"
        
        # Signup for two different activities
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both signups were successful
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestRemoveFromActivity:
    """Tests for POST /activities/{activity_name}/remove endpoint"""
    
    def test_remove_participant_success(self, client):
        """Test successful removal of a participant from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(f"/activities/Chess Club/remove?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_remove_actually_removes_participant(self, client):
        """Test that remove actually removes the participant from the activity"""
        email = "michael@mergington.edu"
        
        # Verify email is in activity before removal
        response_before = client.get("/activities")
        assert email in response_before.json()["Chess Club"]["participants"]
        
        # Remove
        client.post(f"/activities/Chess Club/remove?email={email}")
        
        # Verify participant was removed
        response_after = client.get("/activities")
        assert email not in response_after.json()["Chess Club"]["participants"]
    
    def test_remove_nonexistent_activity_fails(self, client):
        """Test that remove fails when activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/remove?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_remove_email_not_in_activity_fails(self, client):
        """Test that remove fails when email is not a participant"""
        email = "notparticipant@mergington.edu"
        
        response = client.post(f"/activities/Chess Club/remove?email={email}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_remove_missing_email_fails(self, client):
        """Test that remove fails when email parameter is missing"""
        response = client.post("/activities/Chess Club/remove")
        
        assert response.status_code == 422
    
    def test_remove_then_signup_again_succeeds(self, client):
        """Test that a participant can be removed and then re-signup"""
        email = "testuser@mergington.edu"
        
        # Signup
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Remove
        response2 = client.post(f"/activities/Chess Club/remove?email={email}")
        assert response2.status_code == 200
        
        # Signup again - should succeed since they were removed
        response3 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response3.status_code == 200
        
        # Verify they're back in the activity
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
