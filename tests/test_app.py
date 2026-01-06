"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Check that expected activities exist
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Basketball Team" in activities


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Soccer Club" in data["message"]

    def test_signup_activity_not_found(self):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_student(self):
        """Test signup fails when student is already registered"""
        # First signup should succeed
        client.post(
            "/activities/Drama%20Club/signup?email=duplicate@mergington.edu"
        )
        
        # Second signup with same email should fail
        response = client.post(
            "/activities/Drama%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"

    def test_signup_multiple_students_same_activity(self):
        """Test multiple students can signup for the same activity"""
        email1 = "student1@test.edu"
        email2 = "student2@test.edu"
        
        response1 = client.post(
            "/activities/Art%20Club/signup?email=" + email1
        )
        response2 = client.post(
            "/activities/Art%20Club/signup?email=" + email2
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_signup_student_multiple_activities(self):
        """Test a student can signup for multiple activities"""
        email = "versatile@test.edu"
        
        response1 = client.post(
            "/activities/Debate%20Team/signup?email=" + email
        )
        response2 = client.post(
            "/activities/Math%20Club/signup?email=" + email
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        # First signup
        email = "toremove@mergington.edu"
        client.post(
            "/activities/Programming%20Class/signup?email=" + email
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=" + email
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_activity_not_found(self):
        """Test unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/Fake%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_student_not_registered(self):
        """Test unregister fails when student is not registered"""
        response = client.delete(
            "/activities/Basketball%20Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"

    def test_unregister_removes_from_participants(self):
        """Test that unregister actually removes participant from activity"""
        email = "tocheck@mergington.edu"
        
        # Signup
        client.post("/activities/Gym%20Class/signup?email=" + email)
        
        # Get activities and verify participant is there
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Gym Class"]["participants"]
        
        # Unregister
        client.delete("/activities/Gym%20Class/unregister?email=" + email)
        
        # Get activities again and verify participant is removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Gym Class"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivityDetails:
    """Tests for activity details structure"""

    def test_activity_has_required_fields(self):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activity_participants_are_strings(self):
        """Test that participant list contains valid email strings"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_data in activities.values():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant
