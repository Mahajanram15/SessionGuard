"""
Test Suite for LearnSphere E-Learning Domain APIs.

Validates:
1. Each e-learning endpoint returns expected HTTP status codes and response schemas.
2. Identical requests produce deterministic responses.
3. Filtering by category and difficulty works as expected.
4. Pagination functions correctly and validates limits (422 Unprocessable Entity).
5. Unknown course IDs return 404 Not Found.
6. Search queries match titles, descriptions, categories, and instructors.
7. Simulated enrollment confirms registration without financial transaction or PII persistence.
8. No mutations occur to session cache, database, or research datasets.
9. Existing telemetry, health, model status, and mock product endpoints continue to function.
"""

import os
import unittest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.session_service import session_service
from backend.app.schemas.elearning_domain import MOCK_COURSES


class TestElearningDomainApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Save snapshot of cache to ensure complete isolation
        cls.cache_path = session_service._get_cache_path()
        if os.path.exists(cls.cache_path):
            with open(cls.cache_path, "r", encoding="utf-8") as f:
                cls._cache_backup = f.read()
        else:
            cls._cache_backup = None
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        if cls._cache_backup is not None:
            with open(cls.cache_path, "w", encoding="utf-8") as f:
                f.write(cls._cache_backup)
        session_service._load_cache()

    def setUp(self):
        self.created_sessions = []

    def tearDown(self):
        for s_id in self.created_sessions:
            if s_id in session_service._sessions:
                del session_service._sessions[s_id]
            if s_id in session_service._events_count:
                del session_service._events_count[s_id]
            if s_id in session_service._events_by_session:
                del session_service._events_by_session[s_id]
            if s_id in session_service._api_requests:
                del session_service._api_requests[s_id]
            if s_id in session_service._api_requests_count:
                del session_service._api_requests_count[s_id]

    # --------------------------------------------------------------------------
    # 1. Course Catalog & Listing
    # --------------------------------------------------------------------------
    def test_courses_list_structure_and_success(self):
        """Verify GET /api/courses returns paginated course list with expected schema."""
        res = self.client.get("/api/courses")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("courses", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("page_size", data)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["total"], len(MOCK_COURSES))
        self.assertGreaterEqual(len(data["courses"]), 1)

        first = data["courses"][0]
        self.assertIn("id", first)
        self.assertIn("title", first)
        self.assertIn("category", first)
        self.assertIn("difficulty", first)
        self.assertIn("duration_hours", first)
        self.assertIn("instructor", first)
        self.assertIn("rating", first)
        self.assertIn("price", first)
        self.assertIn("is_free", first)
        self.assertIn("lesson_count", first)

    def test_courses_category_filtering(self):
        """Verify GET /api/courses?category=Cybersecurity filters courses by category."""
        res = self.client.get("/api/courses?category=Cybersecurity")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["category"], "Cybersecurity")
        self.assertGreater(data["total"], 0)
        for course in data["courses"]:
            self.assertEqual(course["category"].lower(), "cybersecurity")

    def test_courses_difficulty_filtering(self):
        """Verify GET /api/courses?difficulty=Advanced filters courses by difficulty level."""
        res = self.client.get("/api/courses?difficulty=Advanced")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["difficulty"], "Advanced")
        self.assertGreater(data["total"], 0)
        for course in data["courses"]:
            self.assertEqual(course["difficulty"].lower(), "advanced")

    def test_courses_combined_filtering(self):
        """Verify GET /api/courses?category=Cybersecurity&difficulty=Beginner matches expected items."""
        res = self.client.get("/api/courses?category=Cybersecurity&difficulty=Beginner")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["category"], "Cybersecurity")
        self.assertEqual(data["difficulty"], "Beginner")
        for course in data["courses"]:
            self.assertEqual(course["category"].lower(), "cybersecurity")
            self.assertEqual(course["difficulty"].lower(), "beginner")

    def test_courses_pagination(self):
        """Verify pagination slicing with page and page_size."""
        res = self.client.get("/api/courses?page=1&page_size=2")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 2)
        self.assertEqual(len(data["courses"]), 2)

        res2 = self.client.get("/api/courses?page=2&page_size=2")
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["page"], 2)
        # Ensure page 2 courses are distinct from page 1
        ids_page1 = {c["id"] for c in data["courses"]}
        ids_page2 = {c["id"] for c in data2["courses"]}
        self.assertEqual(len(ids_page1.intersection(ids_page2)), 0)

    def test_courses_invalid_pagination_returns_422(self):
        """Verify invalid pagination values return HTTP 422."""
        res_zero = self.client.get("/api/courses?page=0")
        self.assertEqual(res_zero.status_code, 422)

        res_oversize = self.client.get("/api/courses?page_size=100")
        self.assertEqual(res_oversize.status_code, 422)

    # --------------------------------------------------------------------------
    # 2. Course Details & Curriculum
    # --------------------------------------------------------------------------
    def test_course_details_success(self):
        """Verify GET /api/courses/details?id=course_cs101 returns full details and lessons."""
        res = self.client.get("/api/courses/details?id=course_cs101")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], "course_cs101")
        self.assertIn("learning_objectives", data)
        self.assertIn("prerequisites", data)
        self.assertIn("lessons", data)
        self.assertIsInstance(data["lessons"], list)
        self.assertGreaterEqual(len(data["lessons"]), 1)

        first_lesson = data["lessons"][0]
        self.assertIn("id", first_lesson)
        self.assertIn("title", first_lesson)
        self.assertIn("duration_minutes", first_lesson)
        self.assertIn("order", first_lesson)
        self.assertIn("video_url", first_lesson)

        # Check quiz structure if present
        if first_lesson.get("quiz"):
            first_q = first_lesson["quiz"][0]
            self.assertIn("id", first_q)
            self.assertIn("question", first_q)
            self.assertIn("options", first_q)
            self.assertIn("correct_option_id", first_q)
            self.assertIn("explanation", first_q)

    def test_course_details_unknown_id_returns_404(self):
        """Verify GET /api/courses/details with invalid ID returns HTTP 404."""
        res = self.client.get("/api/courses/details?id=non_existent_course_999")
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertIn("detail", data)
        self.assertIn("not found", data["detail"].lower())

    def test_course_details_missing_id_returns_422(self):
        """Verify GET /api/courses/details without required id returns HTTP 422."""
        res = self.client.get("/api/courses/details")
        self.assertEqual(res.status_code, 422)

    # --------------------------------------------------------------------------
    # 3. Course Search
    # --------------------------------------------------------------------------
    def test_course_search_by_title(self):
        """Verify GET /api/courses/search?q=machine matches ML course."""
        res = self.client.get("/api/courses/search?q=machine&limit=5")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["query"], "machine")
        self.assertIn("results", data)
        self.assertIn("total_results", data)
        self.assertIn("limit", data)
        self.assertGreaterEqual(data["total_results"], 1)
        found_titles = [c["title"].lower() for c in data["results"]]
        self.assertTrue(any("machine" in t for t in found_titles))

    def test_course_search_by_instructor(self):
        """Verify GET /api/courses/search?q=Brody matches instructor name."""
        res = self.client.get("/api/courses/search?q=Brody")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total_results"], 1)
        self.assertTrue(any("brody" in c["instructor"].lower() for c in data["results"]))

    def test_course_search_variations(self):
        """Verify course search handles punctuation, casing, spacing, and compact variations."""
        variations = [
            "Full-Stack",
            "full stack",
            "FULL STACK",
            "fullstack",
            "stack",
            "  full stack  ",
        ]
        for q in variations:
            res = self.client.get(f"/api/courses/search?q={q}")
            self.assertEqual(res.status_code, 200, f"Search failed for variation: '{q}'")
            data = res.json()
            self.assertGreaterEqual(data["total_results"], 1, f"Expected at least 1 match for '{q}'")
            matched_ids = [c["id"] for c in data["results"]]
            self.assertIn("course_web102", matched_ids, f"Expected 'course_web102' for query '{q}'")

    def test_course_search_partial_tokens(self):
        """Verify relevant partial searches such as 'web' and 'react' match relevant courses."""
        for q in ["web", "react"]:
            res = self.client.get(f"/api/courses/search?q={q}")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertGreaterEqual(data["total_results"], 1)
            matched_ids = [c["id"] for c in data["results"]]
            self.assertIn("course_web102", matched_ids)

    def test_course_search_empty_query_restores_catalog(self):
        """Verify empty query or whitespace trims and restores full course catalog."""
        # Empty query string
        res_empty = self.client.get("/api/courses/search?q=")
        self.assertEqual(res_empty.status_code, 200)
        data_empty = res_empty.json()
        self.assertEqual(data_empty["total_results"], len(MOCK_COURSES))
        self.assertEqual(len(data_empty["results"]), min(10, len(MOCK_COURSES)))

        # Whitespace query string
        res_spaces = self.client.get("/api/courses/search?q=%20%20%20")
        self.assertEqual(res_spaces.status_code, 200)
        data_spaces = res_spaces.json()
        self.assertEqual(data_spaces["total_results"], len(MOCK_COURSES))

        # Query parameter omitted entirely
        res_omitted = self.client.get("/api/courses/search")
        self.assertEqual(res_omitted.status_code, 200)
        data_omitted = res_omitted.json()
        self.assertEqual(data_omitted["total_results"], len(MOCK_COURSES))

    def test_course_search_no_matching_results(self):
        """Verify search with no matching results returns 0 items."""
        res = self.client.get("/api/courses/search?q=quantum_teleportation_nonexistent")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_results"], 0)
        self.assertEqual(len(data["results"]), 0)

    # --------------------------------------------------------------------------
    # 4. Simulated Course Enrollment
    # --------------------------------------------------------------------------
    def test_course_enrollment_free_plan(self):
        """Verify POST /api/courses/enroll with free plan returns simulated confirmation."""
        payload = {
            "course_id": "course_cs101",
            "plan_type": "free",
            "learner_name": "Test Student"
        }
        res = self.client.post("/api/courses/enroll", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "ENROLLED")
        self.assertEqual(data["course_id"], "course_cs101")
        self.assertEqual(data["plan_type"], "free")
        self.assertTrue(data["is_demo"])
        self.assertIn("enrollment_id", data)
        self.assertIn("enrolled_at", data)
        self.assertIn("message", data)

    def test_course_enrollment_pro_plan(self):
        """Verify POST /api/courses/enroll with pro_certificate plan succeeds without payment."""
        payload = {
            "course_id": "course_sec301",
            "plan_type": "pro_certificate",
            "learner_name": "Pro Candidate"
        }
        res = self.client.post("/api/courses/enroll", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "ENROLLED")
        self.assertEqual(data["plan_type"], "pro_certificate")
        self.assertTrue(data["is_demo"])

    def test_course_enrollment_unknown_course_returns_404(self):
        """Verify enrollment for non-existent course returns HTTP 404."""
        payload = {
            "course_id": "course_unknown_fake",
            "plan_type": "free"
        }
        res = self.client.post("/api/courses/enroll", json=payload)
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertIn("not found", data["detail"].lower())

    def test_course_enrollment_invalid_plan_returns_422(self):
        """Verify enrollment with unauthorized plan_type returns HTTP 422."""
        payload = {
            "course_id": "course_cs101",
            "plan_type": "lifetime_vip_access"
        }
        res = self.client.post("/api/courses/enroll", json=payload)
        self.assertEqual(res.status_code, 422)
        data = res.json()
        self.assertIn("invalid plan_type", data["detail"].lower())

    # --------------------------------------------------------------------------
    # 5. Determinism of Identical Requests
    # --------------------------------------------------------------------------
    def test_identical_requests_return_deterministic_results(self):
        """Verify identical requests return deterministic identical payloads."""
        r1 = self.client.get("/api/courses?category=Machine%20Learning&page=1&page_size=2")
        r2 = self.client.get("/api/courses?category=Machine%20Learning&page=1&page_size=2")
        self.assertEqual(r1.json(), r2.json())

        d1 = self.client.get("/api/courses/details?id=course_sec301")
        d2 = self.client.get("/api/courses/details?id=course_sec301")
        self.assertEqual(d1.json(), d2.json())

        s1 = self.client.get("/api/courses/search?q=systems&limit=2")
        s2 = self.client.get("/api/courses/search?q=systems&limit=2")
        self.assertEqual(s1.json(), s2.json())

    # --------------------------------------------------------------------------
    # 6. Absence of State Mutations & Isolation
    # --------------------------------------------------------------------------
    def test_courses_api_does_not_mutate_session_cache(self):
        """Verify calling e-learning endpoints does not alter active session count or cache."""
        initial_sessions = dict(session_service._sessions)
        initial_events_count = dict(session_service._events_count)

        self.client.get("/api/courses")
        self.client.get("/api/courses/details?id=course_cs101")
        self.client.get("/api/courses/search?q=web")
        self.client.post("/api/courses/enroll", json={"course_id": "course_web102", "plan_type": "free"})

        self.assertEqual(dict(session_service._sessions), initial_sessions)
        self.assertEqual(dict(session_service._events_count), initial_events_count)

    # --------------------------------------------------------------------------
    # 7. Non-Regression: Existing Telemetry & Mock Domain Still Function
    # --------------------------------------------------------------------------
    def test_existing_endpoints_continue_functioning(self):
        """Verify existing /health, /api/products, and /api/model/status are unaffected."""
        # 1. Health check
        res_h = self.client.get("/health")
        self.assertEqual(res_h.status_code, 200)
        self.assertEqual(res_h.json()["status"], "healthy")

        # 2. Model status
        res_m = self.client.get("/api/model/status")
        self.assertEqual(res_m.status_code, 200)
        self.assertEqual(res_m.json()["status"], "available")

        # 3. Existing e-commerce mock domain
        res_p = self.client.get("/api/products")
        self.assertEqual(res_p.status_code, 200)
        self.assertIn("products", res_p.json())

        # 4. Existing session lifecycle endpoint
        res_s = self.client.post(
            "/api/session/start",
            json={
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TestBrowser/1.0",
                "client_timestamp": 1700000000000,
                "collection_mode": "HUMAN"
            }
        )
        self.assertEqual(res_s.status_code, 201)
        sess_id = res_s.json()["session_id"]
        self.created_sessions.append(sess_id)
