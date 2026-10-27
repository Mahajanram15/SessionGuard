import re
from typing import Optional, Any, Dict, List
from fastapi import APIRouter, Request, status, HTTPException, Depends, Query

from backend.app.core.database import get_db
from backend.app.schemas.session import (
    SessionStartRequest,
    SessionStartResponse,
    SessionEndRequest,
    SessionEndResponse,
)
from backend.app.schemas.behavior import (
    BehaviorBatchRequest,
    BehaviorBatchResponse,
)
from backend.app.schemas.api_log import (
    ApiRequestCreate,
    ApiRequestResponse,
)
from backend.app.schemas.risk import (
    RiskResponse,
    ExplanationResponse,
)
from backend.app.schemas.dashboard import (
    DashboardStatsResponse,
)
from backend.app.schemas.mock_domain import (
    MOCK_PRODUCTS,
    ProductItem,
    ProductListResponse,
    ProductDetailResponse,
    SearchResponse,
    SearchFilterResponse,
    CatalogResponse,
    CartItemRequest,
    CartItemResponse,
    CheckoutVerifyRequest,
    CheckoutVerifyResponse,
)
from backend.app.schemas.elearning_domain import (
    MOCK_COURSES,
    CourseItem,
    CourseDetailResponse,
    CourseListResponse,
    CourseSearchResponse,
    EnrollmentRequest,
    EnrollmentResponse,
)
from backend.app.services.session_service import session_service
from backend.app.services.risk_service import risk_service

router = APIRouter(prefix="/api", tags=["Behavioral Integrity API"])

# ------------------------------------------------------------------------------
# 1. Session Lifecycle Endpoints
# ------------------------------------------------------------------------------
@router.post("/session/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    req: SessionStartRequest,
    request: Request,
    db: Optional[Any] = Depends(get_db)
):
    """
    Initializes a new tracking session and returns a bound session ID and telemetry configuration.
    Accepts collection metadata (collection_mode, task_id, label) for research dataset collection.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    return await session_service.create_session(req, client_ip, db=db)

@router.post("/session/end", response_model=SessionEndResponse, status_code=status.HTTP_200_OK)
async def end_session(
    req: SessionEndRequest,
    db: Optional[Any] = Depends(get_db)
):
    """
    Terminates an active session, computes summary statistics, triggers feature extraction, and finalizes scoring.
    """
    return await session_service.end_session(
        session_id=req.session_id,
        end_reason=req.end_reason or "USER_EXIT",
        collection_mode=req.collection_mode,
        automation_condition=req.automation_condition,
        participant_id=req.participant_id,
        task_id=req.task_id,
        label=req.label,
        db=db
    )

# ------------------------------------------------------------------------------
# 2. Telemetry Ingestion Endpoints
# ------------------------------------------------------------------------------
@router.post("/behavior/events", response_model=BehaviorBatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_behavior_events(
    req: BehaviorBatchRequest,
    db: Optional[Any] = Depends(get_db)
):
    """
    Ingests batched client behavioral dynamics (mouse, keystroke timing metadata, scrolling).
    PRIVACY COMPLIANCE: Zero raw keystroke characters or input values accepted.
    """
    from ml.data.privacy_validator import PrivacyViolationError
    try:
        return await session_service.record_events(req, db=db)
    except PrivacyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/api-requests", response_model=ApiRequestResponse, status_code=status.HTTP_201_CREATED)
async def log_api_request(
    req: ApiRequestCreate,
    db: Optional[Any] = Depends(get_db)
):
    """
    Ingests backend API access log to enable cross-layer behavioral correlation.
    Validates bound session, enforces privacy parameters, and tracks per-session sequence numbers.
    """
    return await session_service.record_api_request(req, db=db)

# ------------------------------------------------------------------------------
# 3. Risk & Explainability Endpoints
# ------------------------------------------------------------------------------
@router.get("/risk/{session_id}", response_model=RiskResponse, status_code=status.HTTP_200_OK)
async def get_session_risk(session_id: str):
    """
    Retrieves the multi-signal behavioral risk score breakdown and policy decision for a session.
    """
    return await risk_service.get_risk_score(session_id)

@router.get("/explanation/{session_id}", response_model=ExplanationResponse, status_code=status.HTTP_200_OK)
async def get_session_explanation(session_id: str):
    """
    Retrieves SHAP feature contributions and triggered security rules explaining the risk score.
    """
    return await risk_service.get_explanation(session_id)

@router.get("/model/status", status_code=status.HTTP_200_OK)
async def get_model_status():
    """
    Returns the operational status, active model, version, and integrity digest.
    """
    from backend.app.services.ml_inference_service import ml_inference_service
    return ml_inference_service.get_status()

from pydantic import BaseModel, Field

class ModelSelectPayload(BaseModel):
    model: str = Field(default="experiment_a", description="Model identifier ('experiment_a' or 'experiment_b')")

@router.post("/model/select", status_code=status.HTTP_200_OK)
async def select_model(payload: ModelSelectPayload):
    """
    Reversibly selects the active ML model ('experiment_a' or 'experiment_b').
    Strictly defaults to 'experiment_a' when the payload is absent, invalid, or unset.
    """
    from backend.app.services.ml_inference_service import ml_inference_service
    active = ml_inference_service.set_active_model(payload.model)
    return {
        "status": "success",
        "active_model": active,
        "model_status": ml_inference_service.get_status(),
    }

# ------------------------------------------------------------------------------
# 4. Security Dashboard Endpoints
# ------------------------------------------------------------------------------
@router.get("/dashboard/stats", response_model=DashboardStatsResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_stats():
    """
    Returns aggregated fleet statistics, risk distribution, and flagged sessions for the analyst UI.
    """
    return await risk_service.get_dashboard_stats()

# ------------------------------------------------------------------------------
# 5. Research Dataset Collection Endpoints
# ------------------------------------------------------------------------------
@router.get("/dataset/summary", status_code=status.HTTP_200_OK)
async def get_dataset_summary():
    """
    Returns summary statistics on collected sessions (human vs automated counts, task distribution).
    """
    return session_service.get_dataset_summary()

@router.post("/dataset/export", status_code=status.HTTP_200_OK)
async def export_dataset(
    target_partition: Optional[str] = Query(None, description="Target partition: 'phase2_development' or 'phase1'")
):
    """
    Triggers export of recorded sessions.
    When target_partition is 'phase2_development', exports strictly to ml/data/phase2_development/.
    Defaults to Phase 1 path ('ml/data') for backward compatibility.
    """
    if target_partition == "phase2_development":
        return session_service.export_phase2_development_dataset()
    return session_service.export_dataset()

@router.post("/dataset/export/phase2", status_code=status.HTTP_200_OK)
async def export_phase2_dataset():
    """
    Dedicated endpoint: triggers export of Phase 2 development sessions exclusively into ml/data/phase2_development/.
    """
    return session_service.export_phase2_development_dataset()

# ------------------------------------------------------------------------------
# 6. Mock Application Domain Endpoints (Controlled Research Experiments)
# NOTE: These are lightweight, deterministic demonstration endpoints for
# Experiment B (TASK_01, TASK_02, TASK_03). They simulate application HTTP traffic
# without persisting data or modifying research datasets.
# ------------------------------------------------------------------------------

@router.get("/products", response_model=ProductListResponse, status_code=status.HTTP_200_OK)
async def list_products(
    category: Optional[str] = Query(None, description="Optional category filter (e.g. 'laptops')"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page")
):
    """
    Returns a deterministic paginated list of mock products.
    Optionally accepts category and page query parameters.
    """
    items = list(MOCK_PRODUCTS.values())
    if category:
        cat_lower = category.strip().lower()
        items = [p for p in items if p["category"].lower() == cat_lower]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]

    return ProductListResponse(
        products=[ProductItem(**p) for p in paginated_items],
        total=total,
        page=page,
        page_size=page_size,
        category=category
    )

@router.get("/products/details", response_model=ProductDetailResponse, status_code=status.HTTP_200_OK)
async def get_product_details(
    id: str = Query(..., min_length=1, max_length=64, description="Unique product ID")
):
    """
    Returns mock product details for a validated product ID.
    Returns 404 if the product is not found.
    """
    prod = MOCK_PRODUCTS.get(id)
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{id}' not found"
        )
    return ProductDetailResponse(**prod)

@router.get("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_products(
    q: str = Query(..., min_length=1, max_length=128, description="Search query string"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return")
):
    """
    Returns deterministic mock search results for query parameter 'q'.
    """
    q_lower = q.strip().lower()
    matches = [
        p for p in MOCK_PRODUCTS.values()
        if q_lower in p["name"].lower()
        or q_lower in p["category"].lower()
        or q_lower in p["description"].lower()
    ]
    sliced = matches[:limit]
    return SearchResponse(
        query=q,
        results=[ProductItem(**p) for p in sliced],
        total_results=len(matches),
        limit=limit
    )

@router.get("/search/filter", response_model=SearchFilterResponse, status_code=status.HTTP_200_OK)
async def filter_search_products(
    filter: str = Query(..., min_length=1, max_length=64, description="Filter category or keyword"),
    sort: str = Query("relevance", description="Sort order: relevance, price_asc, price_desc, rating, name_asc")
):
    """
    Accepts validated filter and sort parameters and returns deterministic results.
    """
    allowed_sorts = {"relevance", "price_asc", "price_desc", "rating", "name_asc"}
    sort_clean = sort.strip().lower()
    if sort_clean not in allowed_sorts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid sort parameter '{sort}'. Allowed options: {sorted(list(allowed_sorts))}"
        )

    f_lower = filter.strip().lower()
    matches = [
        p for p in MOCK_PRODUCTS.values()
        if f_lower in p["category"].lower()
        or f_lower in p["name"].lower()
        or f_lower in p["description"].lower()
    ]

    # Deterministic sorting
    if sort_clean == "price_asc":
        matches = sorted(matches, key=lambda x: x["price"])
    elif sort_clean == "price_desc":
        matches = sorted(matches, key=lambda x: x["price"], reverse=True)
    elif sort_clean == "rating":
        matches = sorted(matches, key=lambda x: x["rating"], reverse=True)
    elif sort_clean == "name_asc":
        matches = sorted(matches, key=lambda x: x["name"])
    # "relevance" preserves canonical catalog ordering

    return SearchFilterResponse(
        filter=filter,
        sort=sort_clean,
        results=[ProductItem(**p) for p in matches],
        total_results=len(matches)
    )

@router.get("/catalog", response_model=CatalogResponse, status_code=status.HTTP_200_OK)
async def get_catalog(
    category: Optional[str] = Query(None, description="Optional category focus")
):
    """
    Returns a fixed catalog overview with available categories and featured products.
    """
    categories = sorted(list({p["category"] for p in MOCK_PRODUCTS.values()}))
    items = list(MOCK_PRODUCTS.values())
    if category:
        cat_lower = category.strip().lower()
        items = [p for p in items if p["category"].lower() == cat_lower]

    featured = items[:4]
    return CatalogResponse(
        category=category,
        categories=categories,
        featured_products=[ProductItem(**p) for p in featured],
        total_catalog_items=len(MOCK_PRODUCTS)
    )

@router.post("/cart/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_cart_item(req: CartItemRequest):
    """
    Accepts validated JSON payload (item_id, positive quantity) and returns a mock success response.
    Does not mutate persistent database state.
    """
    if req.item_id not in MOCK_PRODUCTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{req.item_id}' not found in catalog"
        )
    return CartItemResponse(
        status="ADDED",
        item_id=req.item_id,
        quantity=req.quantity,
        message=f"Added {req.quantity} of '{MOCK_PRODUCTS[req.item_id]['name']}' to mock cart"
    )

@router.post("/checkout/verify", response_model=CheckoutVerifyResponse, status_code=status.HTTP_200_OK)
async def verify_checkout(req: CheckoutVerifyRequest):
    """
    Accepts validated JSON payload (shipping_method, currency) and returns mock verification response.
    """
    allowed_methods = {"standard", "express", "overnight", "pickup"}
    method_clean = req.shipping_method.strip().lower()
    if method_clean not in allowed_methods:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid shipping_method '{req.shipping_method}'. Allowed: {sorted(list(allowed_methods))}"
        )

    allowed_currencies = {"USD", "EUR", "GBP", "CAD", "JPY"}
    curr_clean = req.currency.strip().upper()
    if curr_clean not in allowed_currencies:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid currency code '{req.currency}'. Supported demo currencies: {sorted(list(allowed_currencies))}"
        )

    return CheckoutVerifyResponse(
        status="VERIFIED",
        shipping_method=method_clean,
        currency=curr_clean,
        is_valid=True,
        message="Mock checkout parameters verified for research demonstration"
    )

# ------------------------------------------------------------------------------
# 7. LearnSphere E-Learning Domain Endpoints (Controlled Research Experiments)
# NOTE: These are lightweight, deterministic demonstration endpoints for
# the LearnSphere e-learning platform. They simulate course catalog, lesson
# navigation, and mock enrollment without persisting PII, charging money, or
# modifying research datasets.
# ------------------------------------------------------------------------------

@router.get("/courses", response_model=CourseListResponse, status_code=status.HTTP_200_OK)
async def list_courses(
    category: Optional[str] = Query(None, description="Optional category filter (e.g. 'Cybersecurity')"),
    difficulty: Optional[str] = Query(None, description="Optional difficulty filter (e.g. 'Beginner', 'Intermediate', 'Advanced')"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page")
):
    """
    Returns a deterministic paginated list of mock courses for LearnSphere.
    Supports optional category and difficulty filtering.
    """
    items = list(MOCK_COURSES.values())
    if category:
        cat_lower = category.strip().lower()
        items = [c for c in items if c["category"].lower() == cat_lower]

    if difficulty:
        diff_lower = difficulty.strip().lower()
        items = [c for c in items if c["difficulty"].lower() == diff_lower]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]

    return CourseListResponse(
        courses=[CourseItem(**c) for c in paginated_items],
        total=total,
        page=page,
        page_size=page_size,
        category=category,
        difficulty=difficulty,
    )

@router.get("/courses/details", response_model=CourseDetailResponse, status_code=status.HTTP_200_OK)
async def get_course_details(
    id: str = Query(..., min_length=1, max_length=64, description="Unique course identifier")
):
    """
    Returns full details, curriculum lessons, and quiz definitions for a validated course ID.
    Returns 404 if the course ID is not found.
    """
    course = MOCK_COURSES.get(id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{id}' not found"
        )
    return CourseDetailResponse(**course)

def _normalize_search_text(text: str) -> str:
    """Replaces common punctuation with spaces and folds case."""
    return re.sub(r'[\-_/.,:;()\[\]{}!?"\']', ' ', text.lower())

def _compact_search_text(text: str) -> str:
    """Removes all non-alphanumeric characters and folds case."""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def _course_matches_query(query: str, course: Dict[str, Any]) -> bool:
    q_trimmed = query.strip()
    if not q_trimmed:
        return True

    fields = [
        str(course.get("title", "")),
        str(course.get("category", "")),
        str(course.get("instructor", "")),
        str(course.get("description", "")),
    ]

    # 1. Direct case-insensitive substring match
    q_lower = q_trimmed.lower()
    for field in fields:
        if q_lower in field.lower():
            return True

    # 2. Normalized punctuation match (e.g. 'full stack' matching 'Full-Stack')
    q_norm = _normalize_search_text(q_trimmed)
    q_tokens = [tok for tok in q_norm.split() if tok]
    combined_norm = " ".join(_normalize_search_text(f) for f in fields)
    if q_tokens and all(tok in combined_norm for tok in q_tokens):
        return True

    # 3. Compact alphanumeric match (e.g. 'fullstack' matching 'Full-Stack')
    q_compact = _compact_search_text(q_trimmed)
    if len(q_compact) >= 2:
        for field in fields:
            if q_compact in _compact_search_text(field):
                return True

    return False

@router.get("/courses/search", response_model=CourseSearchResponse, status_code=status.HTTP_200_OK)
async def search_courses(
    q: str = Query(default="", max_length=128, description="Course search query string"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return")
):
    """
    Returns deterministic course search results matching title, category, instructor, or description.
    Supports case-insensitivity, punctuation normalization, partial tokens, and compact matching.
    An empty query restores the full course catalog.
    """
    q_trimmed = q.strip()
    if not q_trimmed:
        items = list(MOCK_COURSES.values())[:limit]
        return CourseSearchResponse(
            query=q,
            results=[CourseItem(**c) for c in items],
            total_results=len(MOCK_COURSES),
            limit=limit
        )

    matches = [c for c in MOCK_COURSES.values() if _course_matches_query(q_trimmed, c)]
    sliced = matches[:limit]
    return CourseSearchResponse(
        query=q,
        results=[CourseItem(**c) for c in sliced],
        total_results=len(matches),
        limit=limit
    )

@router.post("/courses/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_course(req: EnrollmentRequest):
    """
    Simulates student course enrollment for research demonstrations.
    Validates course existence and enrollment plan without charging money or persisting PII.
    """
    course = MOCK_COURSES.get(req.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{req.course_id}' not found in course catalog"
        )

    allowed_plans = {"free", "pro_certificate"}
    plan_clean = req.plan_type.strip().lower()
    if plan_clean not in allowed_plans:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid plan_type '{req.plan_type}'. Allowed options: {sorted(list(allowed_plans))}"
        )

    import uuid
    from datetime import datetime
    demo_enrollment_id = f"enr_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()

    return EnrollmentResponse(
        status="ENROLLED",
        enrollment_id=demo_enrollment_id,
        course_id=req.course_id,
        course_title=course["title"],
        plan_type=plan_clean,
        is_demo=True,
        enrolled_at=now,
        message=f"Simulated enrollment confirmed for '{course['title']}'. No financial transaction processed or stored."
    )


