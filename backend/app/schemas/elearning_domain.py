"""
Pydantic Schemas and Deterministic Mock Data for LearnSphere E-Learning Domain.

Provides realistic, deterministic mock course catalog, lessons, quizzes, and simulated
enrollments to support behavioral integrity verification on an educational web application.

PRIVACY & SAFETY CONSTRAINTS:
- Fictional demonstration content only; no external network or payment dependencies.
- No user personal identifiable information (PII) or quiz response text stored or tracked.
- Telemetry isolation: Course content and quiz structures remain strictly separated from
  behavioral interaction biometrics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# 1. Lesson & Quiz Schemas
# ------------------------------------------------------------------------------

class QuizOption(BaseModel):
    id: str = Field(..., description="Option identifier (e.g. 'opt_a')")
    text: str = Field(..., description="Option display text")


class QuizQuestion(BaseModel):
    id: str = Field(..., description="Question identifier (e.g. 'q_01')")
    question: str = Field(..., description="Quiz question prompt")
    options: List[QuizOption] = Field(..., description="Selectable answer options")
    correct_option_id: str = Field(..., description="Correct option identifier for client self-test")
    explanation: str = Field(..., description="Educational explanation for the correct answer")


class LessonItem(BaseModel):
    id: str = Field(..., description="Unique lesson identifier")
    title: str = Field(..., description="Lesson title")
    duration_minutes: int = Field(..., ge=1, description="Estimated duration in minutes")
    order: int = Field(..., ge=1, description="Lesson sequence order within the course")
    video_url: str = Field(default="/demo/videos/placeholder.mp4", description="Safe mock video URL")
    description: str = Field(..., description="Summary of lesson learning outcomes")
    quiz: Optional[List[QuizQuestion]] = Field(default=None, description="Optional end-of-lesson knowledge check")


# ------------------------------------------------------------------------------
# 2. Course Schemas
# ------------------------------------------------------------------------------

class CourseItem(BaseModel):
    id: str = Field(..., description="Unique course identifier")
    title: str = Field(..., description="Course display title")
    category: str = Field(..., description="Discipline category")
    difficulty: str = Field(..., description="Level: Beginner, Intermediate, or Advanced")
    duration_hours: float = Field(..., ge=0.5, description="Total course duration in hours")
    instructor: str = Field(..., description="Instructor name and credentials")
    rating: float = Field(default=5.0, ge=0.0, le=5.0, description="Average learner review score")
    review_count: int = Field(default=0, ge=0, description="Total learner reviews")
    price: float = Field(default=0.0, ge=0.0, description="Course price in USD (0.0 for free)")
    is_free: bool = Field(default=True, description="Whether the course is free to audit")
    description: str = Field(..., description="High-level course overview")
    thumbnail_url: str = Field(default="/demo/thumbnails/placeholder.jpg", description="Course banner image")
    lesson_count: int = Field(default=0, ge=0, description="Number of lessons in the curriculum")


class CourseDetailResponse(CourseItem):
    learning_objectives: List[str] = Field(default_factory=list, description="Target competencies and takeaways")
    prerequisites: List[str] = Field(default_factory=list, description="Recommended background preparation")
    lessons: List[LessonItem] = Field(default_factory=list, description="Detailed curriculum lesson breakdown")
    enrollment_count: int = Field(default=0, ge=0, description="Simulated enrolled student count")


class CourseListResponse(BaseModel):
    courses: List[CourseItem] = Field(default_factory=list, description="Paginated courses list")
    total: int = Field(..., ge=0, description="Total matching courses count")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, description="Items per page")
    category: Optional[str] = Field(default=None, description="Applied category filter")
    difficulty: Optional[str] = Field(default=None, description="Applied difficulty filter")


class CourseSearchResponse(BaseModel):
    query: str = Field(..., description="Search query string executed")
    results: List[CourseItem] = Field(default_factory=list, description="Matching courses")
    total_results: int = Field(..., ge=0, description="Total number of matching courses")
    limit: int = Field(..., ge=1, description="Maximum returned results limit")


# ------------------------------------------------------------------------------
# 3. Simulated Enrollment Schemas
# ------------------------------------------------------------------------------

class EnrollmentRequest(BaseModel):
    course_id: str = Field(..., min_length=1, max_length=64, description="Course identifier to enroll in")
    plan_type: str = Field(default="free", description="Enrollment plan: 'free' or 'pro_certificate'")
    learner_name: Optional[str] = Field(default="Demo Learner", max_length=64, description="Simulated student name")


class EnrollmentResponse(BaseModel):
    status: str = Field(default="ENROLLED", description="Enrollment status")
    enrollment_id: str = Field(..., description="Generated demo enrollment reference ID")
    course_id: str = Field(..., description="Enrolled course identifier")
    course_title: str = Field(..., description="Enrolled course title")
    plan_type: str = Field(..., description="Validated enrollment plan")
    is_demo: bool = Field(default=True, description="Flags that this is a simulated research enrollment")
    enrolled_at: datetime = Field(..., description="Timestamp of simulated enrollment")
    message: str = Field(default="Demonstration enrollment successful. No financial transaction or persistent PII recorded.")


# ------------------------------------------------------------------------------
# 4. Deterministic Mock E-Learning Dataset (7 Realistic Courses)
# ------------------------------------------------------------------------------

MOCK_COURSES: Dict[str, Dict[str, Any]] = {
    "course_cs101": {
        "id": "course_cs101",
        "title": "Foundations of Computer Systems & Architecture",
        "category": "Computer Science",
        "difficulty": "Beginner",
        "duration_hours": 12.5,
        "instructor": "Dr. Aris Vance, Senior Lecturer in Systems",
        "rating": 4.9,
        "review_count": 340,
        "price": 0.0,
        "is_free": True,
        "description": "Explore the structural hierarchy of modern computing: CPU datapath execution, memory hierarchies, virtual addressing, and operating system primitives.",
        "thumbnail_url": "/demo/thumbnails/cs101.jpg",
        "lesson_count": 4,
        "enrollment_count": 1820,
        "learning_objectives": [
            "Understand binary arithmetic, logic gates, and instruction cycle timing",
            "Trace memory access across L1/L2 caches and virtual memory paging",
            "Analyze system call interfaces between user space and kernel boundaries"
        ],
        "prerequisites": [
            "Basic familiarity with high-level programming concepts",
            "Elementary high-school algebra"
        ],
        "lessons": [
            {
                "id": "les_cs101_01",
                "title": "Von Neumann Architecture & The Datapath",
                "duration_minutes": 35,
                "order": 1,
                "video_url": "/demo/videos/cs101_01.mp4",
                "description": "Instruction fetch, decode, and execute cycles in modern RISC and CISC processors.",
                "quiz": [
                    {
                        "id": "q_cs101_01",
                        "question": "Which component in the CPU holds the memory address of the next instruction to execute?",
                        "options": [
                            {"id": "opt_a", "text": "Program Counter (PC)"},
                            {"id": "opt_b", "text": "Accumulator Register"},
                            {"id": "opt_c", "text": "Instruction Register (IR)"},
                            {"id": "opt_d", "text": "Memory Buffer Register (MBR)"}
                        ],
                        "correct_option_id": "opt_a",
                        "explanation": "The Program Counter (PC) stores the address of the next machine instruction in sequence."
                    }
                ]
            },
            {
                "id": "les_cs101_02",
                "title": "Memory Hierarchy: Caches, RAM, and Locality",
                "duration_minutes": 40,
                "order": 2,
                "video_url": "/demo/videos/cs101_02.mp4",
                "description": "Temporal and spatial locality, cache line invalidation, and hit latency.",
                "quiz": [
                    {
                        "id": "q_cs101_02",
                        "question": "Spatial locality in program execution primarily benefits from which hardware mechanism?",
                        "options": [
                            {"id": "opt_a", "text": "Instruction pipelining"},
                            {"id": "opt_b", "text": "Multi-word cache line prefetching"},
                            {"id": "opt_c", "text": "Branch prediction tables"},
                            {"id": "opt_d", "text": "Virtual memory page tables"}
                        ],
                        "correct_option_id": "opt_b",
                        "explanation": "Cache lines fetch contiguous memory blocks, improving access speed for nearby sequential data."
                    }
                ]
            },
            {
                "id": "les_cs101_03",
                "title": "Operating System Kernel & Trap Handlers",
                "duration_minutes": 45,
                "order": 3,
                "video_url": "/demo/videos/cs101_03.mp4",
                "description": "Privilege rings, context switches, software interrupts, and hardware timer signals.",
                "quiz": None
            },
            {
                "id": "les_cs101_04",
                "title": "Virtual Memory and Translation Lookaside Buffers",
                "duration_minutes": 50,
                "order": 4,
                "video_url": "/demo/videos/cs101_04.mp4",
                "description": "Page tables, multi-level paging, page faults, and TLB caching.",
                "quiz": None
            }
        ]
    },
    "course_ml201": {
        "id": "course_ml201",
        "title": "Behavioral Machine Learning & Anomaly Detection",
        "category": "Machine Learning",
        "difficulty": "Intermediate",
        "duration_hours": 18.0,
        "instructor": "Prof. Elena Rostova, AI & Biometrics Laboratory",
        "rating": 4.8,
        "review_count": 225,
        "price": 49.99,
        "is_free": False,
        "description": "Design supervised and unsupervised classifiers for behavioral biometric verification, pointer dynamics, typing rhythm analysis, and tree-based SHAP explainability.",
        "thumbnail_url": "/demo/thumbnails/ml201.jpg",
        "lesson_count": 3,
        "enrollment_count": 1410,
        "learning_objectives": [
            "Extract kinematic velocity, acceleration, and curvature features from motor streams",
            "Train gradient-boosted decision trees (XGBoost) for tabular behavioral biometrics",
            "Interpret model risk predictions using local TreeSHAP feature contributions"
        ],
        "prerequisites": [
            "Working knowledge of Python and NumPy/pandas",
            "Fundamental understanding of supervised classification and probability"
        ],
        "lessons": [
            {
                "id": "les_ml201_01",
                "title": "Feature Engineering on Interaction Dynamics",
                "duration_minutes": 50,
                "order": 1,
                "video_url": "/demo/videos/ml201_01.mp4",
                "description": "Transforming timestamped coordinate sequences into invariant statistical signals.",
                "quiz": [
                    {
                        "id": "q_ml201_01",
                        "question": "Why is cursor velocity variance generally higher for organic human users than deterministic scripts?",
                        "options": [
                            {"id": "opt_a", "text": "Humans execute motor corrections and micro-hesitations during navigation"},
                            {"id": "opt_b", "text": "Human mice have lower hardware DPI than virtual machines"},
                            {"id": "opt_c", "text": "Browsers throttle events more frequently for human sessions"},
                            {"id": "opt_d", "text": "Deterministic scripts always introduce random pauses"}
                        ],
                        "correct_option_id": "opt_a",
                        "explanation": "Human neuromuscular motor control exhibits natural velocity variance, sub-movements, and deceleration upon approaching visual targets."
                    }
                ]
            },
            {
                "id": "les_ml201_02",
                "title": "Gradient Boosted Trees & Decision Boundaries",
                "duration_minutes": 55,
                "order": 2,
                "video_url": "/demo/videos/ml201_02.mp4",
                "description": "Loss functions, shrinkage, tree regularization, and validation partitioning.",
                "quiz": None
            },
            {
                "id": "les_ml201_03",
                "title": "Model Interpretability with Exact TreeSHAP",
                "duration_minutes": 60,
                "order": 3,
                "video_url": "/demo/videos/ml201_03.mp4",
                "description": "Shapley values, cooperative game theory axioms, and local feature attribution.",
                "quiz": [
                    {
                        "id": "q_ml201_02",
                        "question": "What property guarantees that the sum of feature SHAP values equals the difference between model output and expected base value?",
                        "options": [
                            {"id": "opt_a", "text": "Efficiency / Additivity"},
                            {"id": "opt_b", "text": "Symmetry"},
                            {"id": "opt_c", "text": "Monotonicity"},
                            {"id": "opt_d", "text": "Null player property"}
                        ],
                        "correct_option_id": "opt_a",
                        "explanation": "The efficiency (local accuracy) axiom states that the sum of attributions across all features matches the total prediction shift."
                    }
                ]
            }
        ]
    },
    "course_sec301": {
        "id": "course_sec301",
        "title": "Modern Cybersecurity & Behavioral Biometrics",
        "category": "Cybersecurity",
        "difficulty": "Advanced",
        "duration_hours": 22.5,
        "instructor": "Marcus Brody, CISSP, Principal Security Architect",
        "rating": 4.9,
        "review_count": 420,
        "price": 79.99,
        "is_free": False,
        "description": "Counter advanced automated attacks, credential stuffing, headless puppeteering, and API replay fraud using cross-layer telemetry verification without storing PII.",
        "thumbnail_url": "/demo/thumbnails/sec301.jpg",
        "lesson_count": 3,
        "enrollment_count": 1670,
        "learning_objectives": [
            "Differentiate headless browser artifacts from authentic client runtime environments",
            "Correlate client motor biometrics with backend API sequence cadence",
            "Design privacy-preserving biometrics that reject raw keystroke strings"
        ],
        "prerequisites": [
            "Familiarity with HTTP/2, TLS, and browser security models",
            "Experience with API gateways and access tokens"
        ],
        "lessons": [
            {
                "id": "les_sec301_01",
                "title": "The Threat Landscape of Automated Web Agents",
                "duration_minutes": 45,
                "order": 1,
                "video_url": "/demo/videos/sec301_01.mp4",
                "description": "CDP automation, Puppeteer stealth evasion, and credential replay botnets.",
                "quiz": [
                    {
                        "id": "q_sec301_01",
                        "question": "Which of the following represents a structural inconsistency in automated API replay attacks?",
                        "options": [
                            {"id": "opt_a", "text": "API calls emitted with zero correlated prior browser pointer or focus events"},
                            {"id": "opt_b", "text": "API calls returning standard HTTP 200 OK headers"},
                            {"id": "opt_c", "text": "API calls utilizing gzip compression"},
                            {"id": "opt_d", "text": "API calls issued over encrypted TLS 1.3 tunnels"}
                        ],
                        "correct_option_id": "opt_a",
                        "explanation": "Headless replay scripts frequently dispatch transactional backend API endpoints without preceding cursor traversal or document dwell events."
                    }
                ]
            },
            {
                "id": "les_sec301_02",
                "title": "Cross-Layer Behavioral Integrity Verification",
                "duration_minutes": 55,
                "order": 2,
                "video_url": "/demo/videos/sec301_02.mp4",
                "description": "Binding client biometrics to backend API request timelines to measure discordance.",
                "quiz": None
            },
            {
                "id": "les_sec301_03",
                "title": "Privacy-by-Design in Biometric Systems",
                "duration_minutes": 50,
                "order": 3,
                "video_url": "/demo/videos/sec301_03.mp4",
                "description": "One-way cryptographic identifiers, keystroke timing vs character isolation, and GDPR compliance.",
                "quiz": None
            }
        ]
    },
    "course_web102": {
        "id": "course_web102",
        "title": "Full-Stack Web Engineering with Modern React",
        "category": "Web Development",
        "difficulty": "Beginner",
        "duration_hours": 16.0,
        "instructor": "Sarah Lin, Staff Frontend Architect",
        "rating": 4.7,
        "review_count": 190,
        "price": 0.0,
        "is_free": True,
        "description": "Master component architectures, reactive state hooks, TypeScript contracts, responsive layout styling with Tailwind CSS, and asynchronous API data fetching.",
        "thumbnail_url": "/demo/thumbnails/web102.jpg",
        "lesson_count": 3,
        "enrollment_count": 2100,
        "learning_objectives": [
            "Construct modular TypeScript interfaces and typed React components",
            "Manage asynchronous REST data flow with clean loading and error states",
            "Apply responsive Tailwind utilities and accessible semantic HTML5"
        ],
        "prerequisites": [
            "Basic HTML, CSS, and modern JavaScript (ES6+) fundamentals"
        ],
        "lessons": [
            {
                "id": "les_web102_01",
                "title": "Component Decomposition & State Principles",
                "duration_minutes": 40,
                "order": 1,
                "video_url": "/demo/videos/web102_01.mp4",
                "description": "Controlled components, single source of truth, and unidirectional data flow.",
                "quiz": [
                    {
                        "id": "q_web102_01",
                        "question": "What happens when React re-renders a parent component with updated state?",
                        "options": [
                            {"id": "opt_a", "text": "All child components re-render by default unless memoized"},
                            {"id": "opt_b", "text": "Only HTML input elements re-render"},
                            {"id": "opt_c", "text": "The entire browser page is refreshed"},
                            {"id": "opt_d", "text": "Child state is automatically destroyed"}
                        ],
                        "correct_option_id": "opt_a",
                        "explanation": "In standard React rendering cycles, updates in a parent component trigger re-rendering of child component trees unless optimization techniques like React.memo are applied."
                    }
                ]
            },
            {
                "id": "les_web102_02",
                "title": "Asynchronous Telemetry & API Integration",
                "duration_minutes": 45,
                "order": 2,
                "video_url": "/demo/videos/web102_02.mp4",
                "description": "Fetch error boundaries, abort controllers, and background event dispatchers.",
                "quiz": None
            },
            {
                "id": "les_web102_03",
                "title": "Tailwind Utility Systems & Design Consistency",
                "duration_minutes": 35,
                "order": 3,
                "video_url": "/demo/videos/web102_03.mp4",
                "description": "Design tokens, dark-mode color palettes, and glassmorphic surface overlays.",
                "quiz": None
            }
        ]
    },
    "course_dsa202": {
        "id": "course_dsa202",
        "title": "Advanced Data Structures & Algorithmic Analysis",
        "category": "Data Structures",
        "difficulty": "Intermediate",
        "duration_hours": 20.0,
        "instructor": "Dr. Devlin Hayes, Associate Professor of Algorithms",
        "rating": 4.8,
        "review_count": 310,
        "price": 39.99,
        "is_free": False,
        "description": "Dive deep into amortized complexity, self-balancing trees (AVL & Red-Black), disjoint set unions, graph shortest paths, and dynamic programming optimizations.",
        "thumbnail_url": "/demo/thumbnails/dsa202.jpg",
        "lesson_count": 3,
        "enrollment_count": 1350,
        "learning_objectives": [
            "Prove asymptotic bounds using Master Theorem and aggregate amortized analysis",
            "Implement balanced binary search trees and priority heaps",
            "Solve multi-stage decision problems via optimal substructure memoization"
        ],
        "prerequisites": [
            "Proficiency in basic data structures (arrays, linked lists, stacks, queues)",
            "Discrete mathematics and proof by induction"
        ],
        "lessons": [
            {
                "id": "les_dsa202_01",
                "title": "Self-Balancing Search Trees: AVL & Red-Black",
                "duration_minutes": 55,
                "order": 1,
                "video_url": "/demo/videos/dsa202_01.mp4",
                "description": "Tree rotations, balance factors, color invariants, and O(log n) worst-case lookup.",
                "quiz": [
                    {
                        "id": "q_dsa202_01",
                        "question": "What is the maximum permissible difference in height between subtrees of any node in an AVL tree?",
                        "options": [
                            {"id": "opt_a", "text": "1"},
                            {"id": "opt_b", "text": "0"},
                            {"id": "opt_c", "text": "2"},
                            {"id": "opt_d", "text": "log(n)"}
                        ],
                        "correct_option_id": "opt_a",
                        "explanation": "AVL trees require that for every node, the height difference between left and right subtrees (the balance factor) is strictly -1, 0, or 1."
                    }
                ]
            },
            {
                "id": "les_dsa202_02",
                "title": "Disjoint Set Unions & Minimum Spanning Trees",
                "duration_minutes": 50,
                "order": 2,
                "video_url": "/demo/videos/dsa202_02.mp4",
                "description": "Union by rank, path compression, Kruskal's algorithm, and inverse Ackermann bound.",
                "quiz": None
            },
            {
                "id": "les_dsa202_03",
                "title": "Dynamic Programming: Space Optimization & State Compression",
                "duration_minutes": 60,
                "order": 3,
                "video_url": "/demo/videos/dsa202_03.mp4",
                "description": "Top-down memoization, bottom-up tabulation, and bitmask state representation.",
                "quiz": None
            }
        ]
    },
    "course_cloud302": {
        "id": "course_cloud302",
        "title": "Cloud-Native Infrastructure & Microservices",
        "category": "Cloud Computing",
        "difficulty": "Advanced",
        "duration_hours": 24.0,
        "instructor": "Karan Patel, Principal Cloud Solutions Architect",
        "rating": 4.6,
        "review_count": 160,
        "price": 59.99,
        "is_free": False,
        "description": "Architect scalable containerized platforms with Kubernetes, Envoy sidecar proxies, event-driven message brokers, distributed tracing, and zero-trust mesh policies.",
        "thumbnail_url": "/demo/thumbnails/cloud302.jpg",
        "lesson_count": 3,
        "enrollment_count": 980,
        "learning_objectives": [
            "Configure container orchestration with declarative deployment manifests",
            "Implement distributed tracing with OpenTelemetry and correlation headers",
            "Enforce mutual TLS (mTLS) and identity-based ingress traffic routing"
        ],
        "prerequisites": [
            "Working knowledge of Linux CLI and Docker containers",
            "Basic understanding of microservice networking"
        ],
        "lessons": [
            {
                "id": "les_cloud302_01",
                "title": "Container Orchestration & Pod Networking",
                "duration_minutes": 50,
                "order": 1,
                "video_url": "/demo/videos/cloud302_01.mp4",
                "description": "CNI plugins, service cluster IPs, kube-proxy, and DNS service discovery.",
                "quiz": [
                    {
                        "id": "q_cloud302_01",
                        "question": "Which Kubernetes resource manages the desired replica count and rolling updates of stateless container pods?",
                        "options": [
                            {"id": "opt_a", "text": "Deployment"},
                            {"id": "opt_b", "text": "DaemonSet"},
                            {"id": "opt_c", "text": "ConfigMap"},
                            {"id": "opt_d", "text": "PersistentVolumeClaim"}
                        ],
                        "correct_option_id": "opt_a",
                        "explanation": "A Deployment provides declarative updates for Pods and ReplicaSets."
                    }
                ]
            },
            {
                "id": "les_cloud302_02",
                "title": "Service Meshes & Dynamic Traffic Shaping",
                "duration_minutes": 55,
                "order": 2,
                "video_url": "/demo/videos/cloud302_02.mp4",
                "description": "Envoy data planes, circuit breaking, fault injection, and canary deployments.",
                "quiz": None
            },
            {
                "id": "les_cloud302_03",
                "title": "Distributed Telemetry & Observability Pipelines",
                "duration_minutes": 45,
                "order": 3,
                "video_url": "/demo/videos/cloud302_03.mp4",
                "description": "Correlation identifiers, span propagation, structured metrics, and alerting.",
                "quiz": None
            }
        ]
    },
    "course_sec101": {
        "id": "course_sec101",
        "title": "Network Defense & Traffic Telemetry Analysis",
        "category": "Cybersecurity",
        "difficulty": "Beginner",
        "duration_hours": 14.0,
        "instructor": "Alex Rivera, Senior Threat Intelligence Analyst",
        "rating": 4.7,
        "review_count": 205,
        "price": 0.0,
        "is_free": True,
        "description": "Gain foundational expertise in network protocol analysis, TCP/IP handshake dynamics, packet dissection with Wireshark, and identifying unauthorized ingress scans.",
        "thumbnail_url": "/demo/thumbnails/sec101.jpg",
        "lesson_count": 3,
        "enrollment_count": 1940,
        "learning_objectives": [
            "Inspect IPv4/IPv6 packet headers and TCP flag states",
            "Identify SYN floods, port scans, and DNS amplification anomalies",
            "Configure firewall filtering rules and baseline behavioral allowances"
        ],
        "prerequisites": [
            "Basic understanding of IP addressing and network subnets"
        ],
        "lessons": [
            {
                "id": "les_sec101_01",
                "title": "The TCP Three-Way Handshake & State Machine",
                "duration_minutes": 40,
                "order": 1,
                "video_url": "/demo/videos/sec101_01.mp4",
                "description": "SYN, SYN-ACK, ACK sequences, sequence number randomization, and state tables.",
                "quiz": [
                    {
                        "id": "q_sec101_01",
                        "question": "What is the primary objective of TCP SYN Cookie defense against SYN flood exhaustion?",
                        "options": [
                            {"id": "opt_a", "text": "Avoid allocating server transmission control block (TCB) memory until ACK is received"},
                            {"id": "opt_b", "text": "Encrypt all incoming SYN packets with AES-256"},
                            {"id": "opt_c", "text": "Drop all client connections originating outside the local LAN"},
                            {"id": "opt_d", "text": "Automatically convert TCP traffic into UDP datagrams"}
                        ],
                        "correct_option_id": "opt_a",
                        "explanation": "SYN Cookies encode connection parameters into the initial sequence number, deferring server memory allocation until the client completes the handshake."
                    }
                ]
            },
            {
                "id": "les_sec101_02",
                "title": "DNS Telemetry & Tunneling Detection",
                "duration_minutes": 45,
                "order": 2,
                "video_url": "/demo/videos/sec101_02.mp4",
                "description": "High-entropy query domains, DNS over HTTPS/TLS, and exfiltration signatures.",
                "quiz": None
            },
            {
                "id": "les_sec101_03",
                "title": "Encrypted Traffic Analysis & Fingerprinting",
                "duration_minutes": 40,
                "order": 3,
                "video_url": "/demo/videos/sec101_03.mp4",
                "description": "TLS ClientHello cipher suites, JA3 hashes, packet sizing, and inter-arrival timing.",
                "quiz": None
            }
        ]
    }
}
