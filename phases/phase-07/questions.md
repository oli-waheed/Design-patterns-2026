
# Phase 7 — Facade questions

**Pattern / focus:** Facade.

**Read first:** [Guide 07](../../materials/guides/07-facade.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a video publish pipeline) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the location overview, the facade, and the dashboard Overview page from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Facade in plain language. What problem appears when every HTTP handler (or every UI screen) repeats the same multi-step dance across repositories and services?

> [!NOTE]
> **_Your Answer_**
>
> Facade provides one simple interface to a more complex subsystem. In this project, the Overview Facade gathers location, zone, device, reading, and automation information. Without it, each HTTP handler would need to coordinate these operations separately, causing duplicated code and making the application harder to maintain and test.

2. A facade **orchestrates** collaborators. What should it **not** become (a god object that owns all domain logic)? Where should irrigation policy, sensor translation, and persistence stay instead?

> [!NOTE]
> **_Your Answer_**
>
> A Facade should coordinate existing components, not become a god object containing every business rule. Irrigation decisions belong in the Strategy and automation service, sensor translation belongs in the Adapter classes, and database operations belong in the persistence layer and repositories. The Facade combines their results for the overview response.

3. When should you use Facade, and when should you skip it (a single repository call is enough; or you actually need to **translate** a mismatched interface)?

> [!NOTE]
> **_Your Answer_**
>
> Facade is useful when a client needs information from several services or repositories through one simple operation. In this project, the overview needs location, zones, devices, readings, and automation information. If an operation needs only one simple repository call, a Facade may be unnecessary. If two interfaces have different data formats or methods, an Adapter is more suitable.

## B. This phase of the application

4. What does `GET /api/locations/{location_id}/overview` return? Name the main pieces of the overview DTO: location, assigned device counts, and `zones` (thresholds, assigned devices, and those devices’ latest readings, including `tracking_enabled` and `sampling_interval_seconds`), plus strategy key and last recommendation. Why may those reading rows come from the sampler or MQTT ingest, not only from `POST /read`? Why is overview scoped by `location_id`?

> [!NOTE]
> **_Your Answer_**
>
> The endpoint returns one overview DTO containing the location ID and name, counts of assigned sensors and actuators, and every zone with its moisture thresholds and assigned devices. Each zone also has a separate `latest_readings` collection containing the newest reading for each assigned device that has one. A reading summary includes `device_id`, `value`, `unit`, `recorded_at`, `tracking_enabled`, and `sampling_interval_seconds`. The response also includes the saved strategy key and the last recommendation calculated by the existing automation service.
>
> Readings can come from manual reads, the simulation sampler, or MQTT ingest because these sources can store readings in the same database. The overview is scoped by `location_id` because locations are the existing way to group zones and devices in this application.

5. Why does this phase **not** require a new business table? What already exists from Phases 2–6 that the facade only **composes**?

> [!NOTE]
> **_Your Answer_**
>
> No new business table is needed because the required information is already stored in the existing location, zone, device, reading, and automation-rule tables. These were developed in earlier phases. The Facade queries and combines this data into one response instead of duplicating it in a new table.

6. The overview HTTP handler should call **only** the facade, not reading/strategy/device repositories directly. Why? How does that help tests and later changes to the query shape?

> [!NOTE]
> **_Your Answer_**
>
> The handler should call only the Facade so that the API layer stays simple and does not depend on several repositories. This separates HTTP handling from data aggregation. The Facade can be tested independently, and its internal queries can change later without requiring changes to the route as long as the response contract remains the same.

7. The location selector may use the existing locations list. The Overview cards come from **one** overview fetch, and Refresh repeats that same fetch. Why must the React page not stitch device, reading, and automation calls together to build the same snapshot? How does a new reading or a saved strategy show up on overview without extra frontend glue?

> [!NOTE]
> **_Your Answer_**
>
> The React page should not combine separate device, reading, and automation requests because the backend Facade already assembles these details into one overview response. Multiple requests would duplicate logic and could return data from different moments. Selecting a location or pressing Refresh calls the overview endpoint again. The backend then reads the latest stored data and the saved strategy, so the updated information appears without extra frontend logic.

## C. Compare, contrast, and scenarios

8. Contrast Facade with **Adapter**. One makes an existing interface usable; the other makes a subsystem simpler to call. Which is which, and how do both appear in this greenhouse app (Phase 5 vs Phase 7)?

> [!NOTE]
> **_Your Answer_**
>
> An Adapter translates an existing interface or data format into the format expected by the application. In Phase 5, sensor adapters translate simulation, vendor, or MQTT data into a common reading format. A Facade provides a simpler entry point to several components. In Phase 7, the Overview Facade combines location, zone, device, reading, and automation information into one API response.

9. This phase mentions **N+1** queries. What is an N+1 problem in an overview that lists latest readings for many devices, and what can the facade (or its repository) do about it without putting SQL in the router?

> [!NOTE]
> **_Your Answer_**
>
> An N+1 problem happens when the application runs one query to get the devices and then an additional query for every device to find its latest reading. This becomes inefficient when there are many devices. The Facade or repository can retrieve the assigned devices in one query and use a single query with a window function or join to retrieve the latest readings for all those device IDs. SQL should stay out of the HTTP router.

10. A classmate hides every error behind a generic “overview failed,” so a missing location, a DB outage, and a strategy error look the same. Why is that a trap for a facade?

> [!NOTE]
> **_Your Answer_**
>
> Hiding every error behind one generic message makes it difficult to identify and fix the real problem. A missing location should return HTTP 404, while a database or automation failure should not be incorrectly reported as a missing location. The Facade should coordinate its collaborators without hiding important error information. The API layer should map known errors to appropriate HTTP responses.
