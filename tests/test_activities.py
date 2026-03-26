"""Test suite for FastAPI activities management endpoints.

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the API endpoint
- Assert: Verify the response and state changes
"""

from fastapi.testclient import TestClient
import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client: TestClient) -> None:
        """Arrange: No setup needed.
        
        Act: Make GET request to /activities.
        
        Assert: Verify response contains all 9 activities with correct structure.
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        
    def test_get_activities_returns_complete_activity_data(self, client: TestClient) -> None:
        """Arrange: No setup needed.
        
        Act: Make GET request to /activities.
        
        Assert: Verify each activity has required fields.
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
        
    def test_get_activities_returns_participant_list(self, client: TestClient) -> None:
        """Arrange: No setup needed.
        
        Act: Make GET request to /activities.
        
        Assert: Verify participant lists match initial state.
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_successful(self, client: TestClient) -> None:
        """Arrange: Student not yet signed up.
        
        Act: POST signup request with new email.
        
        Assert: Verify student added to participants list with success message.
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify student was added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants
        
    def test_signup_duplicate_student_returns_error(self, client: TestClient) -> None:
        """Arrange: Student already signed up for activity.
        
        Act: POST signup request with existing participant email.
        
        Assert: Verify 400 error and participant list unchanged.
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already enrolled
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
        
    def test_signup_nonexistent_activity_returns_error(self, client: TestClient) -> None:
        """Arrange: Activity does not exist.
        
        Act: POST signup request for non-existent activity.
        
        Assert: Verify 404 error.
        """
        # Arrange
        activity_name = "Non-existent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_signup_multiple_students_independent(self, client: TestClient) -> None:
        """Arrange: Multiple different students signing up.
        
        Act: POST signup for different students sequentially.
        
        Assert: Verify all students added successfully and independently.
        """
        # Arrange
        activity_name = "Programming Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act & Assert - signup each student
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
            assert response.status_code == 200
            
        # Verify all students added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        for email in emails:
            assert email in participants
            
    def test_signup_preserves_existing_participants(self, client: TestClient) -> None:
        """Arrange: Activity has existing participants.
        
        Act: POST signup request for new student.
        
        Assert: Verify new student added and existing participants preserved.
        """
        # Arrange
        activity_name = "Tennis Club"
        original_count = len(client.get("/activities").json()[activity_name]["participants"])
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": new_email})
        
        # Assert
        assert response.status_code == 200
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        assert len(participants) == original_count + 1
        assert "maya@mergington.edu" in participants  # Original participant
        assert new_email in participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_student_successful(self, client: TestClient) -> None:
        """Arrange: Student is signed up for activity.
        
        Act: DELETE unregister request for enrolled student.
        
        Assert: Verify student removed from participants list with success message.
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        
        # Verify student was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email not in participants
        
    def test_unregister_non_enrolled_student_returns_error(self, client: TestClient) -> None:
        """Arrange: Student not enrolled in activity.
        
        Act: DELETE unregister request for non-enrolled student.
        
        Assert: Verify 400 error and participants list unchanged.
        """
        # Arrange
        activity_name = "Chess Club"
        email = "nonenrolled@mergington.edu"
        original_participants = client.get("/activities").json()[activity_name]["participants"].copy()
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
        
        # Verify participants unchanged
        activities_response = client.get("/activities")
        current_participants = activities_response.json()[activity_name]["participants"]
        assert current_participants == original_participants
        
    def test_unregister_from_nonexistent_activity_returns_error(self, client: TestClient) -> None:
        """Arrange: Activity does not exist.
        
        Act: DELETE unregister request for non-existent activity.
        
        Assert: Verify 404 error.
        """
        # Arrange
        activity_name = "Non-existent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_unregister_multiple_students_independent(self, client: TestClient) -> None:
        """Arrange: Activity has multiple participants.
        
        Act: DELETE unregister for each participant sequentially.
        
        Assert: Verify each student removed successfully.
        """
        # Arrange
        activity_name = "Art Studio"
        emails_to_remove = ["isabella@mergington.edu", "lucas@mergington.edu"]
        
        # Act & Assert - unregister each student
        for email in emails_to_remove:
            response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
            assert response.status_code == 200
            
        # Verify all students removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert len(participants) == 0
        for email in emails_to_remove:
            assert email not in participants
            
    def test_unregister_preserves_other_participants(self, client: TestClient) -> None:
        """Arrange: Activity has multiple participants.
        
        Act: DELETE unregister request for one participant.
        
        Assert: Verify removed student gone but other participants preserved.
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister", params={"email": email_to_remove})
        
        # Assert
        assert response.status_code == 200
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        assert email_to_remove not in participants
        assert email_to_keep in participants


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_endpoint_redirects_to_static(self, client: TestClient) -> None:
        """Arrange: No setup needed.
        
        Act: Make GET request to root endpoint.
        
        Assert: Verify redirect response to /static/index.html.
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestEdgeCases:
    """Tests for edge cases and data integrity."""

    def test_signup_with_special_characters_in_activity_name(self, client: TestClient) -> None:
        """Arrange: Activity name with special characters.
        
        Act: POST signup request with special character activity name.
        
        Assert: Verify 404 error (activity doesn't exist) or proper handling.
        """
        # Arrange
        activity_name = "Chess Club@Special"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 404
        
    def test_signup_unregister_signup_cycle(self, client: TestClient) -> None:
        """Arrange: Student signs up and unregisters from activity.
        
        Act: Signup, then unregister, then signup again.
        
        Assert: Verify all operations succeed and final state is signed up.
        """
        # Arrange
        activity_name = "Programming Class"
        email = "cycle@mergington.edu"
        
        # Act - Sign up
        response1 = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        assert response1.status_code == 200
        
        # Act - Unregister
        response2 = client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
        assert response2.status_code == 200
        
        # Act - Sign up again
        response3 = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        assert response3.status_code == 200
        
        # Assert - Verify final state
        activities_data = client.get("/activities").json()
        participants = activities_data[activity_name]["participants"]
        assert email in participants
        
    def test_case_sensitive_activity_names(self, client: TestClient) -> None:
        """Arrange: Test case sensitivity of activity names.
        
        Act: Create requests with different case variations.
        
        Assert: Verify only exact case match works.
        """
        # Arrange
        email = "student@mergington.edu"
        
        # Act & Assert - lowercase variation
        response_lower = client.post("/activities/chess club/signup", params={"email": email})
        assert response_lower.status_code == 404
        
        # Act & Assert - uppercase variation
        response_upper = client.post("/activities/CHESS CLUB/signup", params={"email": email})
        assert response_upper.status_code == 404
        
        # Act & Assert - correct case
        response_correct = client.post("/activities/Chess Club/signup", params={"email": email})
        assert response_correct.status_code == 200
        
    def test_participant_count_accuracy(self, client: TestClient) -> None:
        """Arrange: Track participant counts across operations.
        
        Act: Perform multiple signup/unregister operations.
        
        Assert: Verify participant count remains accurate.
        """
        # Arrange
        activity_name = "Science Club"
        initial_count = len(client.get("/activities").json()[activity_name]["participants"])
        
        # Act - Add 3 new students
        new_students = ["s1@m.edu", "s2@m.edu", "s3@m.edu"]
        for student in new_students:
            client.post(f"/activities/{activity_name}/signup", params={"email": student})
            
        # Assert - Count increased by 3
        current_data = client.get("/activities").json()
        assert len(current_data[activity_name]["participants"]) == initial_count + 3
        
        # Act - Remove 2 students
        client.delete(f"/activities/{activity_name}/unregister", params={"email": new_students[0]})
        client.delete(f"/activities/{activity_name}/unregister", params={"email": new_students[1]})
        
        # Assert - Count increased by 1
        current_data = client.get("/activities").json()
        assert len(current_data[activity_name]["participants"]) == initial_count + 1
