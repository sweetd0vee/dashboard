# Architecture Documentation
## AIOps Dashboard Project

This document describes the system architecture, components, data flow, and deployment structure of the AIOps Dashboard application.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Database Schema](#database-schema)
6. [Deployment Architecture](#deployment-architecture)
7. [Technology Stack](#technology-stack)

---

## System Overview

The AIOps Dashboard is a full-stack application for monitoring and forecasting server metrics. It consists of:

- **Backend API**: FastAPI-based REST API for data access and forecasting
- **Frontend UI**: Streamlit-based interactive dashboard
- **Database**: PostgreSQL for time-series metrics storage
- **Forecasting Engine**: Prophet-based time series forecasting
- **Authentication**: Keycloak integration (configured but not fully implemented)
- **Reverse Proxy**: Apache HTTPd for routing and SSL termination

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
    end
    
    subgraph "Reverse Proxy Layer"
        HTTPd[Apache HTTPd<br/>Port 80/443]
    end
    
    subgraph "Application Layer"
        API[FastAPI Backend<br/>Port 8000]
        UI[Streamlit Frontend<br/>Port 8501]
    end
    
    subgraph "Service Layer"
        Auth[Keycloak<br/>Port 8087]
        LLM[LLaMA Server<br/>Port 8080]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL<br/>Port 5432)]
        Models[Model Storage<br/>File System]
    end
    
    Browser -->|HTTPS/HTTP| HTTPd
    HTTPd -->|/api/*| API
    HTTPd -->|/dashboard-ui/*| UI
    HTTPd -->|/keycloak/*| Auth
    
    API -->|Read/Write| DB
    API -->|Load/Save| Models
    UI -->|API Calls| API
    UI -->|Direct| DB
    
    Auth -->|User Data| DB
    API -.->|Auth Check| Auth
    
    style Browser fill:#e1f5ff
    style HTTPd fill:#fff4e1
    style API fill:#e8f5e9
    style UI fill:#e8f5e9
    style DB fill:#f3e5f5
    style Models fill:#f3e5f5
    style Auth fill:#fff9c4
    style LLM fill:#fff9c4
```

---

## Component Architecture

### Backend API Components

```mermaid
graph LR
    subgraph "API Layer"
        Main[main.py<br/>FastAPI App]
        Router[api/endpoints.py<br/>REST Routes]
    end
    
    subgraph "Business Logic"
        CRUD[dbcrud.py<br/>Data Access]
        Forecaster[forecaster.py<br/>Prophet ML]
        Anomaly[anomaly_detector.py<br/>Anomaly Detection]
    end
    
    subgraph "Data Models"
        Models[models.py<br/>SQLAlchemy ORM]
        Schemas[schemas.py<br/>Pydantic Models]
    end
    
    subgraph "Infrastructure"
        Conn[connection.py<br/>DB Connection]
        Logger[base_logger.py<br/>Logging]
    end
    
    Main --> Router
    Router --> CRUD
    Router --> Forecaster
    Router --> Anomaly
    CRUD --> Models
    CRUD --> Conn
    Forecaster --> Models
    Forecaster --> Conn
    Models --> Conn
    Main --> Logger
    
    style Main fill:#4caf50
    style Router fill:#81c784
    style CRUD fill:#66bb6a
    style Forecaster fill:#ff9800
    style Anomaly fill:#ff9800
    style Models fill:#2196f3
    style Schemas fill:#2196f3
    style Conn fill:#9e9e9e
    style Logger fill:#9e9e9e
```

### Frontend UI Components

```mermaid
graph TB
    subgraph "UI Entry Point"
        MainUI[main.py<br/>Streamlit App]
    end
    
    subgraph "Pages"
        Fact[pages/fact.py<br/>Fact Metrics]
        Forecast[pages/forecast.py<br/>Forecasting]
        Analysis[pages/analysis.py<br/>Analysis]
    end
    
    subgraph "Components"
        Header[components/header.py]
        Sidebar[components/sidebar.py]
        Footer[components/footer.py]
    end
    
    subgraph "Utilities"
        DataGen[utils/data_generator.py]
        Alerts[utils/alert_rules.py]
        Analyzer[utils/alert_analyzer.py]
    end
    
    MainUI --> Fact
    MainUI --> Forecast
    MainUI --> Analysis
    MainUI --> Header
    MainUI --> Sidebar
    MainUI --> Footer
    
    Fact --> DataGen
    Fact --> Alerts
    Forecast --> DataGen
    Analysis --> Analyzer
    
    style MainUI fill:#ff6b6b
    style Fact fill:#ff8787
    style Forecast fill:#ff8787
    style Analysis fill:#ff8787
    style Header fill:#ffa8a8
    style Sidebar fill:#ffa8a8
    style Footer fill:#ffa8a8
```

### Forecasting Module Components

```mermaid
graph TB
    subgraph "Forecasting Module"
        Forecaster[forecaster.py<br/>Main Interface]
        
        subgraph "Data Processing"
            Prep[data_preparation.py<br/>Data Prep]
            Utils[utils.py<br/>Helpers]
        end
        
        subgraph "Model Management"
            Train[model_training.py<br/>Training]
            Tune[model_tuning.py<br/>Hyperparameter Tuning]
            Predict[model_prediction.py<br/>Prediction]
            Storage[storage.py<br/>Model Storage]
        end
        
        subgraph "Evaluation"
            Eval[evaluation.py<br/>Metrics]
        end
        
        Config[config.py<br/>Configuration]
    end
    
    Forecaster --> Prep
    Forecaster --> Train
    Forecaster --> Tune
    Forecaster --> Predict
    Forecaster --> Storage
    
    Train --> Prep
    Train --> Eval
    Tune --> Train
    Predict --> Storage
    Prep --> Utils
    
    Config --> Forecaster
    Config --> Train
    Config --> Tune
    
    style Forecaster fill:#9c27b0
    style Train fill:#ba68c8
    style Tune fill:#ba68c8
    style Predict fill:#ba68c8
    style Storage fill:#ba68c8
    style Prep fill:#ce93d8
    style Eval fill:#ce93d8
```

---

## Data Flow Diagrams

### Metrics Retrieval Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant CRUD as DBCRUD
    participant DB as PostgreSQL
    
    User->>UI: Select VM & Metric
    UI->>API: GET /api/v1/metrics?vm=X&metric=Y
    API->>CRUD: get_latest_metrics(vm, metric, hours)
    CRUD->>DB: SELECT query with filters
    DB-->>CRUD: Result set
    CRUD-->>API: List[ServerMetricsFact]
    API-->>UI: JSON response
    UI->>UI: Render charts/graphs
    UI-->>User: Display metrics
```

### Forecasting Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant Forecaster as ProphetForecaster
    participant CRUD as DBCRUD
    participant DB as PostgreSQL
    participant Storage as Model Storage
    
    User->>UI: Request Forecast
    UI->>API: POST /api/v1/predict
    API->>Forecaster: generate_forecast(vm, metric)
    
    alt Model Exists
        Forecaster->>Storage: load_model(vm, metric)
        Storage-->>Forecaster: Prophet Model
    else Model Not Found
        Forecaster->>CRUD: get_historical_metrics()
        CRUD->>DB: SELECT historical data
        DB-->>CRUD: Time series data
        CRUD-->>Forecaster: DataFrame
        Forecaster->>Forecaster: train_model()
        Forecaster->>Storage: save_model()
    end
    
    Forecaster->>Forecaster: predict(periods=48)
    Forecaster->>CRUD: save_prediction()
    CRUD->>DB: INSERT predictions
    DB-->>CRUD: Success
    CRUD-->>Forecaster: Confirmation
    Forecaster-->>API: Forecast results
    API-->>UI: JSON with predictions
    UI->>UI: Render forecast chart
    UI-->>User: Display forecast
```

### Data Ingestion Flow

```mermaid
sequenceDiagram
    participant External as External System
    participant API as FastAPI
    participant CRUD as DBCRUD
    participant DB as PostgreSQL
    participant Anomaly as AnomalyDetector
    
    External->>API: POST /api/v1/metrics/batch
    API->>API: Validate input (Pydantic)
    API->>CRUD: create_historical_metric()
    
    loop For each metric
        CRUD->>DB: INSERT INTO server_metrics_fact
        DB-->>CRUD: Success
    end
    
    CRUD-->>API: Created metrics
    API->>Anomaly: detect_realtime_anomaly()
    Anomaly->>CRUD: get_latest_metrics()
    CRUD->>DB: SELECT recent data
    DB-->>CRUD: Historical values
    CRUD-->>Anomaly: Data
    Anomaly->>Anomaly: Calculate anomaly score
    alt Anomaly Detected
        Anomaly-->>API: Alert
        API->>API: Log/Notify
    end
    API-->>External: 201 Created
```

---

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    ServerMetricsFact ||--o{ ServerMetricsPredictions : "related"
    
    ServerMetricsFact {
        uuid id PK
        string vm
        datetime timestamp
        string metric
        decimal value
        datetime created_at
    }
    
    ServerMetricsPredictions {
        uuid id PK
        string vm
        datetime timestamp
        string metric
        decimal value_predicted
        decimal lower_bound
        decimal upper_bound
        datetime created_at
    }
```

### Table Structure

#### server_metrics_fact
- **Purpose**: Stores actual/historical server metrics
- **Primary Key**: `id` (UUID)
- **Unique Constraint**: `(vm, timestamp, metric)`
- **Indexes**: 
  - `idx_vm_timestamp_metric` on `(vm, timestamp, metric)`
  - Individual indexes on `vm`, `timestamp`, `value`
- **Constraints**: 
  - `chk_timestamp_not_future`: Ensures timestamps are not in the future

#### server_metrics_predictions
- **Purpose**: Stores forecasted/predicted metrics
- **Primary Key**: `id` (UUID)
- **Unique Constraint**: `(vm, timestamp, metric)`
- **Indexes**: 
  - `idx_vm_timestamp_metric_pred` on `(vm, timestamp, metric)`
  - Individual indexes on `vm`, `timestamp`
- **Fields**: Includes confidence intervals (`lower_bound`, `upper_bound`)

---

## Deployment Architecture

### Docker Compose Deployment

```mermaid
graph TB
    subgraph "Docker Network: servers-network"
        subgraph "Web Layer"
            HTTPd[Apache HTTPd<br/>Container: httpd-proxy<br/>Ports: 80, 443]
        end
        
        subgraph "Application Containers"
            API_Container[FastAPI App<br/>Container: dashboard<br/>Port: 8000]
            UI_Container[Streamlit UI<br/>Container: dashboard-ui<br/>Port: 8501]
        end
        
        subgraph "Service Containers"
            Keycloak[Keycloak<br/>Container: keycloak<br/>Port: 8087]
            LLaMA[LLaMA Server<br/>Container: llama-server<br/>Port: 8080]
        end
        
        subgraph "Data Containers"
            Postgres[PostgreSQL<br/>Container: postgres<br/>Port: 5432<br/>Volume: postgres-data]
        end
    end
    
    subgraph "Host Volumes"
        ModelStorage[Model Storage<br/>./notebooks/models]
        PostgresData[Postgres Data<br/>~/docker-share/postgres-data-server]
        SSL_Certs[SSL Certificates<br/>./docker/httpd/data/letsencrypt]
    end
    
    HTTPd -->|Route /api/*| API_Container
    HTTPd -->|Route /dashboard-ui/*| UI_Container
    HTTPd -->|Route /keycloak/*| Keycloak
    
    API_Container -->|Connect| Postgres
    UI_Container -->|API Calls| API_Container
    Keycloak -->|Connect| Postgres
    
    API_Container -->|Read/Write| ModelStorage
    Postgres -->|Persist| PostgresData
    HTTPd -->|SSL Certs| SSL_Certs
    
    style HTTPd fill:#ff9800
    style API_Container fill:#4caf50
    style UI_Container fill:#4caf50
    style Postgres fill:#2196f3
    style Keycloak fill:#ffc107
    style LLaMA fill:#ffc107
```

### Container Structure

```mermaid
graph LR
    subgraph "docker/app"
        AppDockerfile[Dockerfile<br/>Python 3.12-slim]
        AppCompose[docker-compose.yaml]
    end
    
    subgraph "docker/ui"
        UIDockerfile[Dockerfile<br/>Python 3.12-slim]
        UICompose[docker-compose.yaml]
    end
    
    subgraph "docker/postgres"
        PGDockerfile[Dockerfile<br/>Postgres 16.9]
        PGInit[01-init-dbs.sh]
    end
    
    subgraph "docker/httpd"
        HTTPdDockerfile[Dockerfile<br/>Apache 2.4]
        HTTPdConf[httpd.conf<br/>proxy-*.conf]
    end
    
    subgraph "docker/keycloak"
        KCDockerfile[Dockerfile<br/>Keycloak 26.4.6]
        KCRealm[realm-export.json]
    end
    
    style AppDockerfile fill:#e8f5e9
    style UIDockerfile fill:#e8f5e9
    style PGDockerfile fill:#e3f2fd
    style HTTPdDockerfile fill:#fff3e0
    style KCDockerfile fill:#fff9c4
```

---

## Technology Stack

### Backend Stack
```
┌─────────────────────────────────────┐
│         FastAPI 0.104.1            │
│  - REST API Framework               │
│  - Async support                    │
│  - Auto-generated OpenAPI docs      │
└─────────────────────────────────────┘
           │
           ├─── SQLAlchemy 2.0.23
           │    - ORM for PostgreSQL
           │
           ├─── Pydantic 2.5.0
           │    - Data validation
           │
           ├─── Prophet 1.1.5
           │    - Time series forecasting
           │
           └─── Uvicorn 0.24.0
                - ASGI server
```

### Frontend Stack
```
┌─────────────────────────────────────┐
│      Streamlit 1.29.0               │
│  - Interactive dashboard             │
│  - Real-time updates                 │
└─────────────────────────────────────┘
           │
           ├─── Plotly 5.18.0
           │    - Interactive charts
           │
           ├─── Pandas 2.1.4
           │    - Data manipulation
           │
           └─── NumPy 1.26.2
                - Numerical operations
```

### Infrastructure Stack
```
┌─────────────────────────────────────┐
│         Docker & Docker Compose     │
│  - Containerization                  │
│  - Multi-service orchestration       │
└─────────────────────────────────────┘
           │
           ├─── PostgreSQL 16.9
           │    - Time-series database
           │
           ├─── Apache HTTPd 2.4
           │    - Reverse proxy
           │    - SSL termination
           │
           ├─── Keycloak 26.4.6
           │    - Identity management
           │
           └─── LLaMA Server
                - AI/ML capabilities
```

---

## Module Dependencies

### Backend Dependencies Graph

```mermaid
graph TD
    main[main.py] --> endpoints[api/endpoints.py]
    main --> connection[connection.py]
    main --> models[models.py]
    
    endpoints --> dbcrud[dbcrud.py]
    endpoints --> connection
    
    dbcrud --> models
    dbcrud --> connection
    
    forecaster[forecaster.py] --> dbcrud
    forecaster --> connection
    forecaster --> storage[storage.py]
    
    anomaly[anomaly_detector.py] --> dbcrud
    
    models --> connection
    
    style main fill:#4caf50
    style endpoints fill:#81c784
    style dbcrud fill:#66bb6a
    style forecaster fill:#ff9800
    style models fill:#2196f3
    style connection fill:#9e9e9e
```

### Forecast Module Dependencies

```mermaid
graph TD
    forecaster[forecaster.py] --> config[config.py]
    forecaster --> data_prep[data_preparation.py]
    forecaster --> train[model_training.py]
    forecaster --> tune[model_tuning.py]
    forecaster --> predict[model_prediction.py]
    forecaster --> storage[storage.py]
    forecaster --> utils[utils.py]
    
    train --> data_prep
    train --> eval[evaluation.py]
    tune --> train
    predict --> storage
    data_prep --> utils
    
    style forecaster fill:#9c27b0
    style train fill:#ba68c8
    style tune fill:#ba68c8
    style predict fill:#ba68c8
    style storage fill:#ba68c8
```

---

## API Endpoints Structure

```mermaid
graph LR
    API[FastAPI App<br/>/api/v1] --> Metrics[GET /metrics<br/>GET /latest_metrics]
    
    Metrics --> Query[Query Params:<br/>vm, metric, days,<br/>start_date, end_date]
    
    style API fill:#4caf50
    style Metrics fill:#81c784
    style Query fill:#c8e6c9
```

**Current Endpoints:**
- `GET /api/v1/latest_metrics` - Get latest 24 hours of metrics
- `GET /api/v1/metrics` - Get metrics with flexible date range

**Planned/Commented Endpoints:**
- `POST /api/v1/metrics/` - Create single metric
- `POST /api/v1/metrics/batch/` - Batch create metrics
- `POST /api/v1/predict/` - Generate forecast
- `POST /api/v1/train/` - Train model

---

## Data Processing Pipeline

```mermaid
graph LR
    Raw[Raw Data<br/>CSV/Excel] --> Prep[Data Preparation<br/>utils/prepare_data.py]
    Prep --> Load[Data Loader<br/>utils/data_loader.py]
    Load --> DB[(PostgreSQL<br/>server_metrics_fact)]
    DB --> Query[CRUD Operations<br/>dbcrud.py]
    Query --> Forecast[Forecasting<br/>forecaster.py]
    Forecast --> Predictions[(Predictions<br/>server_metrics_predictions)]
    Predictions --> UI[Dashboard<br/>Streamlit]
    
    style Raw fill:#ffeb3b
    style Prep fill:#ffc107
    style Load fill:#ff9800
    style DB fill:#2196f3
    style Query fill:#4caf50
    style Forecast fill:#9c27b0
    style Predictions fill:#2196f3
    style UI fill:#f44336
```

---

## Security Architecture (Planned)

```mermaid
graph TB
    Client[Client Browser] --> HTTPd[Apache HTTPd]
    HTTPd -->|SSL/TLS| HTTPS[HTTPS Termination]
    HTTPS --> Auth[Keycloak<br/>Authentication]
    Auth -->|JWT Token| API[FastAPI API]
    API -->|Validate Token| Auth
    API -->|Authorized Request| DB[(Database)]
    
    style Client fill:#e1f5ff
    style HTTPd fill:#fff4e1
    style Auth fill:#fff9c4
    style API fill:#e8f5e9
    style DB fill:#f3e5f5
```

**Note:** Authentication is configured but not fully implemented in the current codebase.

---

## File Structure Overview

```
dashboard/
├── src/
│   ├── app/              # FastAPI Backend
│   │   ├── api/         # API endpoints
│   │   ├── models.py    # Database models
│   │   ├── schemas.py   # Pydantic schemas
│   │   ├── dbcrud.py    # Database operations
│   │   └── main.py      # FastAPI app
│   │
│   └── ui/              # Streamlit Frontend
│       ├── pages/       # Page components
│       ├── components/  # UI components
│       └── utils/       # UI utilities
│
├── forecast/            # Forecasting module
│   ├── forecaster.py    # Main interface
│   ├── model_training.py
│   ├── model_tuning.py
│   └── ...
│
├── docker/              # Docker configurations
│   ├── app/            # API container
│   ├── ui/             # UI container
│   ├── postgres/       # Database container
│   └── httpd/          # Reverse proxy
│
├── notebooks/          # Jupyter notebooks
└── data/              # Data files
    ├── source/        # Raw data
    └── processed/     # Processed data
```

---

## Performance Considerations

### Current Architecture
- **Synchronous database operations** (SQLAlchemy ORM)
- **No caching layer** (Redis/Memcached)
- **Direct database queries** from UI (should go through API)
- **File-based model storage** (could use object storage)

### Recommended Improvements
1. **Add Redis** for caching frequently accessed data
2. **Implement async database operations** (async SQLAlchemy)
3. **Add API gateway** for rate limiting
4. **Use object storage** (S3/MinIO) for model files
5. **Implement connection pooling** optimization
6. **Add database read replicas** for scaling

---

## Monitoring & Observability (Planned)

```mermaid
graph TB
    App[Application] --> Logs[Logging<br/>base_logger.py]
    App --> Metrics[Prometheus<br/>Metrics]
    Metrics --> Grafana[Grafana<br/>Dashboards]
    Logs --> ELK[ELK Stack<br/>Log Aggregation]
    
    style App fill:#4caf50
    style Logs fill:#ff9800
    style Metrics fill:#2196f3
    style Grafana fill:#9c27b0
    style ELK fill:#f44336
```

**Current State:**
- Basic file-based logging implemented
- No metrics collection
- No distributed tracing

---

## Conclusion

This architecture provides a solid foundation for an AIOps dashboard with time-series forecasting capabilities. The modular design allows for independent scaling of components and clear separation of concerns.

**Key Strengths:**
- Clear separation between frontend and backend
- Modular forecasting engine
- Containerized deployment
- Well-structured database schema

**Areas for Improvement:**
- Add caching layer
- Implement full authentication
- Add comprehensive monitoring
- Optimize for async operations
- Add API versioning

---

*Last Updated: 2025-01-27*

