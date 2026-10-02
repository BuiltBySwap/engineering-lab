# Production app architecture (generic)

!!! note "Fill this in from memory"
    This page is a skeleton. Replace the labels with how a real production app you worked on is structured — **generic names only**: no company code, no internal URLs, no keys, no private data. Delete this note when done.

## Layers

```mermaid
flowchart TD
    UI["UI layer — Jetpack Compose screens"] -->|"user intent"| VM["ViewModel (MVI): State · Intent · Effect"]
    VM -->|"state"| UI
    VM --> UC["Use cases (domain)"]
    UC --> REPO["Repository interfaces (domain)"]
    REPO --> DATA["Data layer — repository implementations"]
    DATA --> NET["Network: Retrofit + OkHttp"]
    DATA --> DB["Local storage: Room / DataStore"]
    DATA --> CLOUD["Cloud and realtime: Firestore, sockets"]
```

## One screen, end to end

```mermaid
sequenceDiagram
    participant U as User
    participant S as Compose screen
    participant V as ViewModel
    participant C as UseCase
    participant R as Repository
    U->>S: taps "Refresh"
    S->>V: Intent.Refresh
    V->>C: invoke()
    C->>R: getItems()
    R-->>C: items
    C-->>V: result
    V-->>S: new State
    S-->>U: updated UI
```

## Key decisions

| Decision | Why | What I gave up |
|---|---|---|
| MVI instead of MVVM | One immutable state per screen; predictable | More boilerplate |
| Single navigation entry point | All deep links in one place | Extra indirection |
| _add yours_ | | |

## What I would change today

-
