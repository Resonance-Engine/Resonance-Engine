%%{init: {'theme':'dark', 'themeVariables': { 'darkMode':'true', 'background':'#0a0a0a', 'primaryColor':'#1a1a2e', 'primaryTextColor':'#eee', 'primaryBorderColor':'#ff3333', 'lineColor':'#ff3333', 'secondaryColor':'#16213e', 'tertiaryColor':'#0f3460'}}}%%

graph TB
    subgraph External["EXTERNAL SOURCES"]
        EDGAR[SEC EDGAR]
        GDELT[GDELT]
        NewsAPI[NewsAPI]
        AlphaV[Alpha Vantage]
        Finnhub[Finnhub]
    end

    subgraph Ingestion["INGESTION LAYER"]
        Fetch[Fetch & Schedule]
        Normalize[Normalize]
        ChangeGate[Change Gate]
        AssignID[Assign IDs]
    end

    subgraph Agents["AGENTIC WORKFLOW                                                    "]
        IngAgent[1. Ingestion Agent]
        EntityAgent[2. Entity Resolution]
        EventAgent[3. Event Extraction]
        ImpactAgent[4. Impact Hypothesis<br/>RAG-Powered]
        RiskGate[5. Risk Gate]
        SignalStore[Signal Store]
        VectorStore[(Vector Store<br/>Pinecone/Qdrant<br/>Similarity Search)]
    end

    subgraph Storage["STORAGE"]
        Postgres[(PostgreSQL<br/>Events • Signals • Users)]
        Redis[(Redis<br/>Cache Layer)]
        S3[(S3<br/>Archives)]
    end

    subgraph API["API & UI"]
        REST[REST API<br/>FastAPI]
        WS[WebSocket Gateway<br/>Real-time Push]
        Frontend[React Frontend<br/>Event Cards + Dashboard]
    end

    subgraph Eval["EVALUATION & MONITORING"]
        Offline[Offline Metrics<br/>P/R/F1]
        Backtest[Backtest Harness<br/>Bias Checks]
        Live[Live Monitoring<br/>Accuracy]
        Drift[Drift Detection<br/>Alerts]
    end

    %% Connections
    EDGAR --> Fetch
    GDELT --> Fetch
    NewsAPI --> Fetch
    AlphaV --> Fetch
    Finnhub --> Fetch

    Fetch --> Normalize
    Normalize --> ChangeGate
    ChangeGate --> AssignID
    AssignID --> IngAgent

    IngAgent --> EntityAgent
    EntityAgent --> EventAgent
    EventAgent --> ImpactAgent
    ImpactAgent <-->|Embed & Retrieve| VectorStore
    ImpactAgent --> RiskGate
    RiskGate --> SignalStore

    SignalStore --> Postgres
    SignalStore --> Redis
    SignalStore --> S3
    VectorStore -.->|Embeddings| Postgres

    Postgres --> REST
    Postgres --> WS
    REST --> Frontend
    WS --> Frontend

    Postgres --> Offline
    Postgres --> Backtest
    Postgres --> Live
    Postgres --> Drift

    %% Styling
    classDef external fill:#1a1a2e,stroke:#ff3333,stroke-width:3px,color:#fff
    classDef ingestion fill:#16213e,stroke:#00d4ff,stroke-width:3px,color:#fff
    classDef agents fill:#0f3460,stroke:#00ff88,stroke-width:3px,color:#fff
    classDef storage fill:#2d1b2e,stroke:#ff006e,stroke-width:3px,color:#fff
    classDef api fill:#1e1e3f,stroke:#8338ec,stroke-width:3px,color:#fff
    classDef eval fill:#2e1a1a,stroke:#fb5607,stroke-width:3px,color:#fff

    class EDGAR,GDELT,NewsAPI,AlphaV,Finnhub external
    class Fetch,Normalize,ChangeGate,AssignID ingestion
    class IngAgent,EntityAgent,EventAgent,ImpactAgent,RiskGate,SignalStore,VectorStore agents
    class Postgres,Redis,S3 storage
    class REST,WS,Frontend api
    class Offline,Backtest,Live,Drift eval
