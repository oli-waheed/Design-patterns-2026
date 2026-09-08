# Phase 1 - Skeleton Questions

## A. Pattern

### 1. In your own words, what is a design pattern? What is it not?

A design pattern is a reusable approach to solving a common software design problem. It provides a way to structure code when a similar problem occurs.

It is not ready-made code or a library, and it is not something that should be used for every problem.

### 2. Name the three GoF pattern families. For each family, give one-sentence: what kind of design problem it addresses. Then place Factory Method and Strategy into the correct family.

- Creational - concerns how objects are created.
- Structural - concerns how classes and objects are combined.
- Behavioral - concerns how objects communicate and how their behavior is organized.

Factory Method -> Creational

Strategy -> Behavioral

### 3. A teammate wants to add a pattern "because it is on the course list," even though the feature is small and unlikely to grow. When should you skip a pattern? What risk do you take if you apply one too early?

I would skip a pattern when the feature is simple, has little variation, and is unlikely to change. Simple code is better when there is no real problem for the pattern to solve.

Using a pattern too early can add unnecessary abstraction and make the code harder to understand. It can also mean designing for changes that may never happen.

## B. This phase of the application

### 4. Why does Phase 1 ship a vertical slice that does almost no greenhouse business logic? What does "empty but running" prove that a folder of unimplemented classes would not?

Phase 1 establishes the basic application structure before adding greenhouse functionality. The running skeleton shows that the main parts of the system can work together, rather than only showing that folders and files exist.

### 5. List the four backend layer packages used in this course (domain, application, infrastructure, interfaces/api). For each, state what belongs there and give one example of something that must not live in domain.

- domain - business concepts and rules. It should not contain FastAPI routes or other framework-specific code.
- application - application use cases and coordination.
- infrastructure - technical concerns such as settings and database connectivity.
- interfaces/api - FastAPI application, HTTP routes, CORS and Scalar.

The domain layer must remain independent of technologies such as FastAPI and SQLAlchemy.

### 6. What does GET /health return, and why does it check the database instead of only reporting that the HTTP process is up? Why is API documentation served at /scalar, and why is /docs disabled?

GET /health returns:

{"status": "ok", "db": "ok"}

or, if the database check fails:

{"status": "degraded", "db": "fail"}

The database check confirms that the backend can actually reach PostgreSQL, rather than only confirming that the HTTP server is running.

Scalar provides the API reference required for this project. /docs is disabled so that the project has one defined API documentation endpoint instead of two documentation interfaces.

### 7. Phase 1 requires Alembic (or equivalent) with a baseline migration and no business tables such as devices. Why introduce the migration toolchain before any product schema? What would go wrong if you created tables by hand in Postgres and only added migrations later?

Introducing Alembic first establishes a consistent and reproducible way to manage database changes. The baseline also proves that the migration system can work with the PostgreSQL database.

If tables were created manually first, the actual database and migration history could become inconsistent. Later migrations could then be harder to apply or reproduce on another developer's database.

## C. Compare, contrast, and scenarios

### 8. Explain dependency direction in this skeleton: which layers may import which? Why must domain code not import FastAPI, SQLAlchemy, or Pydantic models used as HTTP schemas?

The dependency direction is generally from the outer layers toward the core: interfaces/api uses application logic, and application logic uses the domain. Infrastructure provides technical implementations such as database access.

The domain should not import FastAPI, SQLAlchemy or HTTP-specific Pydantic models because this would couple the business logic to particular technologies. Keeping it independent makes it easier to test and change.

### 9. The frontend cannot show a healthy badge. A classmate blames "the patterns." What should you check first (stack, CORS/proxy, health JSON), and why is that a Phase 1 concern rather than a later pattern concern?

I would first check that PostgreSQL and the backend are running. Then I would check the frontend API URL and CORS configuration, and finally verify that /health returns the expected JSON.

This is a Phase 1 integration issue because the health badge depends on the basic frontend-backend-database connection, not on a design pattern.

### 10. Course completion is at Phase 12, not Phase 1. What is still missing after a successful skeleton, and how do later phases add behaviour without rewriting the foundations you laid here?

After Phase 1, the project still lacks the actual greenhouse business functionality, such as devices, sensors and automation.

Later phases can add these through the existing layers, database migrations, API routes and frontend structure. This allows the application to grow without needing to restructure the whole project.