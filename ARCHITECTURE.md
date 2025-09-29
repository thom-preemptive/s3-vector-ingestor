# agent2_ingestor - Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                             agent2_ingestor                                        │
│                        Cloud-Ready Multi-User Architecture                          │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  CLIENT LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                      │
│  │   Web Browser   │  │   Mobile App    │  │   API Client    │                      │
│  │   (React SPA)   │  │   (Future)      │  │   (CLI/SDK)     │                      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                      │
│           │                     │                     │                             │
│           └─────────────────────┼─────────────────────┘                             │
│                                 │                                                   │
└─────────────────────────────────┼───────────────────────────────────────────────────┘
                                  │
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        AWS AMPLIFY HOSTING                                     │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │ │
│  │  │  Upload Page    │  │  Dashboard      │  │  Jobs Monitor   │                 │ │
│  │  │  - PDF Upload   │  │  - System Health│  │  - Real-time    │                 │ │
│  │  │  - URL Input    │  │  - Queue Stats  │  │  - Job Status   │                 │ │
│  │  │  - Drag & Drop  │  │  - Worker Info  │  │  - Progress     │                 │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │ │
│  │                                                                                │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │ │
│  │  │ Approval Page   │  │  Admin Panel    │  │  User Profile   │                 │ │
│  │  │ - Pending Items │  │  - User Mgmt    │  │  - Settings     │                 │ │
│  │  │ - Review Docs   │  │  - System Config│  │  - Activity Log │                 │ │
│  │  │ - Approve/Reject│  │  - Monitoring   │  │  - Preferences  │                 │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ REST API
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               API GATEWAY                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        AWS API GATEWAY                                         │ │
│  │  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │ │
│  │  │  Authentication  │  │  Rate Limiting  │  │   CORS Setup    │                │ │
│  │  │  - JWT Validation│  │  - Throttling   │  │   - Origins     │                │ │
│  │  │  - Token Refresh │  │  - Quotas       │  │   - Headers     │                │ │
│  │  └──────────────────┘  └─────────────────┘  └─────────────────┘                │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Forward to FastAPI
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                          FASTAPI BACKEND                                       │ │
│  │                                                                                │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │ │
│  │  │   main.py       │  │ dashboard_api.py│  │   API Routes    │                 │ │
│  │  │   - Core API    │  │ - System Health │  │   - /auth/*     │                 │ │
│  │  │   - Routing     │  │ - Queue Metrics │  │   - /upload/*   │                 │ │
│  │  │   - Middleware  │  │ - Worker Status │  │   - /process/*  │                 │ │
│  │  └─────────────────┘  └─────────────────┘  │   - /jobs/*     │                 │ │
│  │                                            │   - /queue/*    │                 │ │
│  │                                            │   - /dashboard/*│                 │ │
│  │                                            └─────────────────┘                 │ │
│  │                                                                                │ │
│  │  ┌───────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │                           SERVICE LAYER                                   │ │ │
│  │  │                                                                           │ │ │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐           │ │ │
│  │  │  │  aws_services   │  │  queue_service  │  │document_processor│           │ │ │
│  │  │  │  - S3Service    │  │  - JobQueue     │  │  - PDF Process   │           │ │ │
│  │  │  │  - DynamoDB     │  │  - Priority Mgmt│  │  - URL Scraping  │           │ │ │
│  │  │  │  - Cognito      │  │  - Retry Logic  │  │  - OCR Extract   │           │ │ │
│  │  │  └─────────────────┘  └─────────────────┘  └──────────────────┘           │ │ │
│  │  │                                                                           │ │ │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐           │ │ │
│  │  │  │approval_service │  │orchestration    │  │   Future         │           │ │ │
│  │  │  │ - Workflow Mgmt │  │ - EventBridge   │  │   Services       │           │ │ │
│  │  │  │ - User Tracking │  │ - Lambda Coord  │  │   - Analytics    │           │ │ │
│  │  │  │ - Activity Log  │  │ - Event Routing │  │   - Notifications│           │ │ │
│  │  │  └─────────────────┘  └─────────────────┘  └──────────────────┘           │ │ │
│  │  └───────────────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Event-Driven Communication
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            ORCHESTRATION LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         AWS EVENTBRIDGE                                        │ │
│  │                                                                                │ │
│  │    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐       │ │
│  │    │   Job Events    │      │  System Events  │      │  User Events    │       │ │
│  │    │ - Job Created   │      │ - Health Alerts │      │ - Login/Logout  │       │ │
│  │    │ - Job Completed │      │ - Queue Backlog │      │ - Activity Log  │       │ │
│  │    │ - Job Failed    │      │ - Worker Status │      │ - Approval Req  │       │ │
│  │    └─────────────────┘      └─────────────────┘      └─────────────────┘       │ │
│  │                                       │                                        │ │
│  │                            Event Bus Routing                                   │ │
│  │                                       │                                        │ │
│  │    ┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐      │ │
│  │    │   Lambda        │      │   SNS Topics     │      │   Future        │      │ │
│  │    │   Triggers      │      │   - Alerts       │      │   Integrations  │      │ │
│  │    │                 │      │   - Notifications│      │   - Webhooks    │      │ │
│  │    └─────────────────┘      └──────────────────┘      └─────────────────┘      │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Job Processing
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                             PROCESSING LAYER                                         │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           JOB QUEUE SYSTEM                                      │ │
│  │                                                                                 │ │
│  │    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐        │ │
│  │    │   Document      │      │   Approval      │      │   Maintenance   │        │ │
│  │    │   Processing    │      │   Workflow      │      │   Tasks         │        │ │
│  │    │   Queue (SQS)   │      │   Queue (SQS)   │      │   Queue (SQS)   │        │ │
│  │    │                 │      │                 │      │                 │        │ │
│  │    │ ┌─────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │        │ │
│  │    │ │ Priorities  │ │      │ │ Priorities  │ │      │ │ Priorities  │ │        │ │
│  │    │ │ 1-Low       │ │      │ │ 1-Low       │ │      │ │ 1-Low       │ │        │ │
│  │    │ │ 2-Normal    │ │      │ │ 2-Normal    │ │      │ │ 2-Normal    │ │        │ │
│  │    │ │ 3-High      │ │      │ │ 3-High      │ │      │ │ 3-High      │ │        │ │
│  │    │ │ 4-Urgent    │ │      │ │ 4-Urgent    │ │      │ │ 4-Urgent    │ │        │ │
│  │    │ └─────────────┘ │      │ └─────────────┘ │      │ └─────────────┘ │        │ │
│  │    └─────────────────┘      └─────────────────┘      └─────────────────┘        │ │
│  │                                       │                                         │ │
│  │                                Dead Letter Queues                               │ │
│  │    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐        │ │
│  │    │   Failed Jobs   │      │   Failed        │      │   Failed        │        │ │
│  │    │   (PDF/URL)     │      │   Approvals     │      │   Maintenance   │        │ │
│  │    └─────────────────┘      └─────────────────┘      └─────────────────┘        │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           LAMBDA WORKERS                                        │ │
│  │                                                                                 │ │
│  │    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐        │ │
│  │    │   Document      │      │   Document      │      │   Approval      │        │ │
│  │    │   Orchestrator  │      │   Processor     │      │   Handler       │        │ │
│  │    │   Lambda        │      │   Lambda        │      │   Lambda        │        │ │
│  │    │                 │      │                 │      │                 │.       │ │
│  │    │ - Event Routing │      │ - PDF Processing│      │ - Workflow Mgmt │        │ │
│  │    │ - Job Dispatch  │      │ - URL Scraping  │      │ - Notifications │        │ │
│  │    │ - Status Update │      │ - OCR with      │      │ - Status Update │        │ │
│  │    │ - Error Handling│      │   Textract      │      │ - User Tracking │        │ │
│  │    │                 │      │ - Embeddings    │      │                 │        │ │
│  │    │                 │      │ - S3 Upload     │      │                 │        │ │
│  │    └─────────────────┘      └─────────────────┘      └─────────────────┘        │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Data Persistence
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                               DATA LAYER                                             │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                            STORAGE SERVICES                                     │ │
│  │                                                                                 │ │
│  │  ┌─────────────────┐  ┌───────────────────┐  ┌─────────────────┐                │ │
│  │  │   Amazon S3     │  │   Amazon          │  │   Amazon        │                │ │
│  │  │   Document      │  │   DynamoDB        │  │   DynamoDB      │                │ │
│  │  │   Storage       │  │   Job Tracking.   │  │   Queue Jobs    │                │ │
│  │  │                 │  │                   │  │                 │                │ │
│  │  │ ┌─────────────┐ │  │ ┌───────────────┐ │  │ ┌─────────────┐ │                │ │
│  │  │ │ Processed   │ │  │ │ Jobs Table    │ │  │ │ Queue Table │ │                │ │
│  │  │ │ Documents   │ │  │ │ - job_id      │ │  │ │ - job_id    │ │                │ │
│  │  │ │ - Markdown  │ │  │ │ - user_id     │ │  │ │ - user_id   │ │                │ │
│  │  │ │ - Vector    │ │  │ │ - status      │ │  │ │ - queue_type│ │                │ │
│  │  │ │   Sidecars  │ │  │ │ - metadata.   │ │  │ │ - status    │ │                │ │
│  │  │ │             │ │  │ │               │ │  │ │ - priority  │ │                │ │
│  │  │ └─────────────┘ │  │ └───────────────┘ │  │ └─────────────┘ │                │ │
│  │  │                 │  │                   │  │                 │                │ │
│  │  │ ┌─────────────┐ │  │ ┌───────────────┐ │  │ ┌─────────────┐ │                │ │
│  │  │ │ Raw Files   │ │  │ │ Approvals     │ │  │ │ GSI Indexes │ │                │ │
│  │  │ │ - PDFs      │ │  │ │ Table         │ │  │ │ - UserJobs  │ │                │ │
│  │  │ │ - Images    │ │  │ │ - approval_id │ │  │ │ - QueueType │ │                │ │
│  │  │ │ - Temp      │ │  │ │ - job_id      │ │  │ │ - Status    │ │                │ │
│  │  │ │   Files     │ │  │ │ - approver    │ │  │ │             │ │                │ │
│  │  │ └─────────────┘ │  │ └───────────────┘ │  │ └─────────────┘ │                │ │
│  │  │                 │  │                   │  │                 │                │ │
│  │  │ ┌─────────────┐ │  │ ┌───────────────┐ │  │                 │                │ │
│  │  │ │ Manifest    │ │  │ │ User          │ │  │                 │                │ │
│  │  │ │ - Central   │ │  │ │ Activity      │ │  │                 │                │ │
│  │  │ │   Index     │ │  │ │ Logs          │ │  │                 │                │ │
│  │  │ │ - Metadata  │ │  │ │               │ │  │                 │                │ │
│  │  │ └─────────────┘ │  │ └───────────────┘ │  │                 │                │ │
│  │  └─────────────────┘  └───────────────────┘  └─────────────────┘                │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           AUTHENTICATION                                        │ │
│  │                                                                                 │ │
│  │  ┌───────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │ │
│  │  │   Amazon          │  │   User Groups   │  │   JWT Tokens    │                │ │
│  │  │   Cognito         │  │   - admin       │  │   - Access      │                │ │
│  │  │   User Pool       │  │   - user        │  │   - ID          │                │ │
│  │  │                   │  │   - viewer      │  │   - Refresh     │                │ │
│  │  │ ┌───────────────┐ │  │                 │  │                 │                │ │
│  │  │ │ User Mgmt     │ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │                │ │
│  │  │ │ - Registration│ │  │ │ Permissions │ │  │ │ Token       │ │                │ │
│  │  │ │ - Login       │ │  │ │ - Read      │ │  │ │ Validation  │ │                │ │
│  │  │ │ - Password    │ │  │ │ - Write     │ │  │ │ - Expiry    │ │                │ │
│  │  │ │   Reset       │ │  │ │ - Admin     │ │  │ │ - Refresh   │ │                │ │
│  │  │ └───────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │                │ │
│  │  └───────────────────┘  └─────────────────┘  └─────────────────┘                │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ ML/AI Services
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AI/ML LAYER                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           AWS AI SERVICES                                      │ │
│  │                                                                                │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │ │
│  │  │   Amazon        │  │   Amazon        │  │   Amazon        │                 │ │
│  │  │   Textract      │  │   Bedrock       │  │   Comprehend    │                 │ │
│  │  │   (OCR)         │  │   (Embeddings)  │  │   (Future)      │                 │ │
│  │  │                 │  │                 │  │                 │                 │ │
│  │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │                 │ │
│  │  │ │ PDF Text    │ │  │ │ Titan       │ │  │ │ Entity      │ │                 │ │
│  │  │ │ Extraction  │ │  │ │ Embeddings  │ │  │ │ Extraction  │ │                 │ │
│  │  │ │             │ │  │ │ Model       │ │  │ │             │ │                 │ │
│  │  │ │ - Tables    │ │  │ │             │ │  │ │ - Keywords  │ │                 │ │
│  │  │ │ - Forms     │ │  │ │ - Vector    │ │  │ │ - Sentiment │ │                 │ │
│  │  │ │ - Text      │ │  │ │   Generation│ │  │ │ - Topics    │ │                 │ │
│  │  │ │ - Layouts   │ │  │ │ - Similarity│ │  │ │             │ │                 │ │
│  │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │                 │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Monitoring & Observability
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            MONITORING LAYER                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                         AWS CLOUDWATCH                                          ││
│  │                                                                                 ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  ││
│  │  │   Metrics       │  │   Logs          │  │   Alarms        │                  ││
│  │  │   - Queue Depth │  │   - Lambda Logs │  │   - DLQ Messages│                  ││
│  │  │   - Processing  │  │   - API Logs    │  │   - High Latency│                  ││
│  │  │     Time        │  │   - Error Logs  │  │   - Error Rate  │                  ││
│  │  │   - Success Rate│  │   - Audit Trail │  │   - Queue       │                  ││
│  │  │   - Error Rate  │  │                 │  │     Backlog     │                  ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  ││
│  │                                                                                 ││
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐                 ││
│  │  │   Dashboards    │  │   SNS Topics     │  │   X-Ray Tracing │                 ││
│  │  │   - System      │  │   - DLQ Alerts   │  │   - Request     │                 ││
│  │  │     Health      │  │   - Backlog      │  │     Tracing     │                 ││
│  │  │   - Queue       │  │     Alerts       │  │   - Performance │                 ││
│  │  │     Status      │  │   - Error        │  │     Analysis    │                 ││
│  │  │   - Performance │  │     Notifications│  │                 │                 ││
│  │  └─────────────────┘  └──────────────────┘  └─────────────────┘                 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  User Upload/URL ──► FastAPI ──► Queue Service ──► SQS ──► Lambda Workers           │
│                                     │                         │                     │
│                                     ▼                         ▼                     │
│                            DynamoDB Job Track    ────►    S3 Storage                │
│                                     │                         │                     │
│                                     ▼                         ▼                     │
│                            EventBridge Events   ────►    Manifest Update            │
│                                     │                         │                     │
│                                     ▼                         ▼                     │
│                            Dashboard Updates   ────►    Vector Sidecars             │
│                                     │                         │                     │
│                                     ▼                         ▼                     │
│                            User Notifications ────►    AI/ML Ready Output           │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Key Architecture Components

### 1. **Frontend Layer (React + AWS Amplify)**

- Single Page Application with TypeScript
- Material-UI components for consistent design
- Real-time dashboard with WebSocket connections
- Responsive design for mobile and desktop
- AWS Amplify hosting with CDN distribution

### 2. **API Gateway & Load Balancing**

- AWS API Gateway for REST API management
- Rate limiting and throttling
- CORS configuration
- JWT token validation
- Request/response transformation

### 3. **Application Layer (FastAPI)**

- Python FastAPI framework for high performance
- Async/await support for concurrent processing
- Automatic API documentation (OpenAPI/Swagger)
- Modular service architecture
- Comprehensive error handling

### 4. **Event-Driven Orchestration**

- AWS EventBridge for event routing
- Decoupled service communication
- Event-driven scaling
- Custom event patterns
- Integration with external systems

### 5. **Job Queue System**

- Multi-queue SQS architecture
- Priority-based job processing
- Dead letter queues for failed jobs
- Retry logic with exponential backoff
- Real-time job status tracking

### 6. **Serverless Processing**

- AWS Lambda for scalable processing
- Event-triggered execution
- Auto-scaling based on queue depth
- Cost-effective pay-per-use model
- Built-in monitoring and logging

### 7. **Data Storage**

- S3 for document and vector storage
- DynamoDB for job and user data
- Global Secondary Indexes for queries
- Point-in-time recovery
- Encryption at rest and in transit

### 8. **Authentication & Authorization**

- AWS Cognito User Pools
- JWT token-based authentication
- Role-based access control
- Multi-factor authentication support
- Social identity provider integration

### 9. **AI/ML Integration**

- AWS Textract for OCR processing
- AWS Bedrock Titan for embeddings
- Vector sidecar generation
- Future: AWS Comprehend for NLP
- Scalable ML inference

### 10. **Monitoring & Observability**

- CloudWatch metrics and logs
- Real-time dashboards
- Automated alerting
- Performance monitoring
- Audit trails and compliance

## Data Flow Process

1. **Document Ingestion**: User uploads PDF or submits URL
2. **Authentication**: Cognito validates user and permissions
3. **Job Creation**: FastAPI creates job record in DynamoDB
4. **Queue Processing**: Job placed in appropriate SQS queue with priority
5. **Worker Processing**: Lambda workers process jobs from queues
6. **Document Processing**: OCR extraction, text cleaning, markdown conversion
7. **Vector Generation**: Bedrock Titan creates embeddings
8. **Storage**: Documents and vectors stored in S3
9. **Manifest Update**: Central manifest updated with new documents
10. **Event Notification**: EventBridge publishes completion events
11. **Dashboard Update**: Real-time dashboard reflects current status
12. **User Notification**: Optional notifications sent to users

## Scalability Features

- **Auto-scaling Lambda workers** based on queue depth
- **DynamoDB on-demand scaling** for variable workloads
- **S3 unlimited storage** with intelligent tiering
- **EventBridge high throughput** event processing
- **CloudWatch metrics** for performance optimization
- **Multi-AZ deployment** for high availability

## Security Features

- **End-to-end encryption** for data in transit and at rest
- **IAM roles and policies** with least privilege access
- **VPC isolation** for Lambda functions
- **API Gateway throttling** to prevent abuse
- **CloudTrail auditing** for compliance
- **Secret Manager** for API keys and credentials

This architecture provides a robust, scalable, and secure foundation for emergency document processing with comprehensive monitoring and real-time operational visibility.