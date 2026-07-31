# Genesis

## Artificial Civilization Simulator

> A next-generation AI-powered civilization simulator where thousands of
> autonomous citizens create an emergent world with evolving societies,
> economies, politics, and history.

------------------------------------------------------------------------

# Vision

Genesis is not a game. It is a living simulation engine.

Every citizen is autonomous and possesses:

-   Identity
-   Personality
-   Goals
-   Skills
-   Career
-   Family
-   Relationships
-   Memories
-   Wealth
-   Health
-   Beliefs
-   Reputation

The world evolves continuously through interactions rather than scripted
events.

------------------------------------------------------------------------

# Core Objectives

-   Simulate believable civilizations
-   Demonstrate advanced software architecture
-   Showcase AI agent orchestration
-   Build an event-driven simulation engine
-   Run primarily with local models or Groq
-   Produce an exceptional portfolio project

------------------------------------------------------------------------

# Tech Stack

## Frontend

-   Next.js
-   React
-   TypeScript
-   TailwindCSS
-   Framer Motion
-   React Flow
-   Three.js (3D globe/city visualization)
-   Zustand
-   TanStack Query
-   Socket.IO Client

## Backend

-   FastAPI
-   Python
-   Pydantic
-   SQLAlchemy
-   Celery (optional)
-   Redis
-   WebSockets / Server-Sent Events

## Database

-   PostgreSQL
-   Neo4j Community (relationships)
-   ChromaDB (optional memory retrieval)

## AI

Provider abstraction:

-   Ollama
-   Groq
-   OpenAI (optional)
-   Anthropic (optional)

Models

-   Qwen
-   Gemma
-   Llama
-   DeepSeek

------------------------------------------------------------------------

# High-Level Architecture

``` text
User
 │
 ▼
Next.js Frontend
 │
 ▼
FastAPI API Gateway
 │
 ├── Simulation Engine
 ├── Citizen Engine
 ├── Economy Engine
 ├── Government Engine
 ├── Relationship Engine
 ├── AI Decision Service
 ├── Memory Service
 ├── Event Bus
 ├── Analytics
 └── WebSocket Stream
        │
        ▼
 PostgreSQL / Neo4j / ChromaDB
```

------------------------------------------------------------------------

# Simulation Modules

## Citizen Engine

Tracks

-   Birth
-   Death
-   Aging
-   Jobs
-   Education
-   Marriage
-   Divorce
-   Friendships
-   Mental health
-   Wealth
-   Religion
-   Happiness

Each citizen has:

-   UUID
-   DNA seed
-   Personality traits
-   Skills
-   Occupation
-   Current goals
-   Long-term goals
-   Memory timeline

------------------------------------------------------------------------

## Relationship Engine

Maintains

-   Parents
-   Children
-   Friends
-   Enemies
-   Romantic partners
-   Business partners

Stored as graph edges inside Neo4j.

------------------------------------------------------------------------

## Economy Engine

Simulates

-   Businesses
-   Salaries
-   Taxes
-   Inflation
-   Supply
-   Demand
-   Trade
-   Bankruptcy
-   Investments

------------------------------------------------------------------------

## Government Engine

Supports

-   Democracy
-   Monarchy
-   Dictatorship
-   Republic

Includes:

-   Elections
-   Laws
-   Budgets
-   Crime
-   Police
-   Courts

------------------------------------------------------------------------

## Environment Engine

Tracks

-   Weather
-   Seasons
-   Natural disasters
-   Disease outbreaks
-   Pollution

------------------------------------------------------------------------

## AI Decision Engine

Rule-based first.

AI only handles complex decisions.

Examples

-   Marriage proposal
-   Company strategy
-   Scientific discovery
-   Political speech
-   Peace treaty
-   War declaration

Provider selection

-   Ollama
-   Groq
-   Others

------------------------------------------------------------------------

# Event Bus

Everything is an event.

Examples

-   Birth
-   Death
-   Promotion
-   Marriage
-   Divorce
-   Company created
-   Election won
-   War started
-   Flood
-   Discovery

Events are immutable and replayable.

------------------------------------------------------------------------

# World Timeline

The simulation stores every event.

Users can:

-   Pause
-   Rewind
-   Compare years
-   Replay history

------------------------------------------------------------------------

# Dashboard

## Live Metrics

-   Population
-   GDP
-   Happiness
-   Inflation
-   Crime
-   Birth rate
-   Death rate
-   Average income
-   Employment

------------------------------------------------------------------------

# Interactive Views

-   Globe
-   City map
-   Family trees
-   Economy graph
-   Government dashboard
-   Event timeline
-   Relationship graph

------------------------------------------------------------------------

# Citizen Profile

Shows

-   Biography
-   Memories
-   Relationships
-   Income history
-   Health
-   Career
-   Decisions
-   Timeline

------------------------------------------------------------------------

# AI Workflow

1.  Tick simulation.
2.  Apply deterministic rules.
3.  Publish events.
4.  Trigger AI only for major decisions.
5.  Persist updates.
6.  Broadcast via WebSockets.

------------------------------------------------------------------------

# API Examples

## Citizens

GET /citizens

GET /citizens/{id}

POST /citizens

## World

GET /world

GET /timeline

POST /simulate

## Economy

GET /economy

## Government

GET /government

------------------------------------------------------------------------

# Folder Structure

``` text
genesis/
 ├── frontend/
 ├── backend/
 ├── simulation/
 ├── ai/
 ├── engines/
 │    ├── citizen
 │    ├── economy
 │    ├── government
 │    ├── relationship
 │    └── environment
 ├── events/
 ├── websocket/
 ├── database/
 ├── docs/
 └── docker/
```

------------------------------------------------------------------------

# Deployment

Development

-   Docker Compose
-   Ollama
-   PostgreSQL
-   Redis
-   Neo4j

Production

-   Next.js (Vercel)
-   FastAPI
-   PostgreSQL
-   Redis
-   Neo4j
-   Optional Groq API

------------------------------------------------------------------------

# Stretch Goals

-   Multiplayer worlds
-   Modding SDK
-   Plugin system
-   Voice interactions
-   Historical replay
-   AI-generated newspapers
-   AI-generated books
-   AI-generated TV/radio
-   Civilization export/import

------------------------------------------------------------------------

# Resume Impact

This project demonstrates:

-   Distributed architecture
-   Event-driven systems
-   AI orchestration
-   Local + cloud LLM integration
-   Graph databases
-   Full-stack engineering
-   Real-time streaming
-   Simulation design
-   Scalable backend architecture
