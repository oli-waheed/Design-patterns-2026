
# Facade Pattern — Smart Greenhouse

## 1. Purpose

The Facade pattern provides one simple interface to a more complex subsystem. It allows a client to perform an operation without coordinating all the internal components itself.

In the Smart Greenhouse application, the dashboard needs information about a location, its zones, assigned devices, latest readings, and automation. Without a Facade, the API handler or frontend would need to coordinate several operations. This would duplicate logic and make the application harder to maintain and test.

## 2. How the pattern works in this project

The Phase 7 Overview Facade provides a single operation:

`get_overview(location_id)`

The dashboard requests the overview through:

`GET /api/locations/{location_id}/overview`

The API handler calls the Facade and returns its response. The Facade coordinates the existing database and automation components and assembles an overview DTO containing:

- Location ID and name.
- Counts of assigned sensors and actuators.
- All zones belonging to the location, including empty zones.
- Assigned devices and their latest readings, when available.
- The saved automation strategy key.
- The latest recommendation calculated by the existing automation service.

The frontend uses this single response to display the Overview section. The location selector may use the existing locations list, while Refresh requests the overview again.

## 3. Responsibilities and separation of concerns

The Facade coordinates existing components, but it should not own every business rule.

- **Facade:** Coordinates the data needed for the overview and assembles the response.
- **Automation service and Strategy:** Make irrigation decisions using the existing automation logic.
- **Adapters:** Translate different sensor data formats into the application's common reading format.
- **Repositories and persistence:** Retrieve and store the application's data.
- **API handler:** Accepts the HTTP request, calls the Facade, and maps a missing location to HTTP 404.
- **React frontend:** Displays the overview response without rebuilding it from separate device, reading, and automation requests.

This separation makes the application easier to test and change.

## 4. Latest readings and the N+1 query problem

An N+1 query problem occurs when an application first retrieves a list of devices and then executes another database query for every device to retrieve its latest reading.

For example, if a location has 50 devices, this approach could require one device query plus 50 reading queries. That creates unnecessary database work.

The overview should retrieve the assigned devices in one query and retrieve the newest readings for those device IDs in a single additional query. A SQL window function such as `ROW_NUMBER()` partitioned by device ID can identify the newest reading for each device.

The overview should include readings regardless of whether they were produced by a manual read, the simulation sampler, or MQTT ingest, because these sources can write to the same reading history.

## 5. Recommendation is computed, not cached

The overview uses the saved strategy key and the existing automation evaluation service to calculate the recommendation when the overview is requested.

The recommendation is not saved in a new table or reused from an old cached result. This avoids displaying a stale recommendation after a new reading has been recorded or the strategy has changed.

When no strategy key has been saved, the endpoint should still return HTTP 200 with both `strategy_key` and `last_recommendation` set to `null`. It must not trigger the automation service in a way that silently saves a default strategy.

## 6. Why no new business table is needed

The information required for the overview already exists in the location, zone, device, reading, and automation-rule data from earlier phases.

The Facade composes this existing information into one read response. It does not need a new table to store a duplicate overview or a cached recommendation.

## 7. Benefits

The Facade provides several benefits:

- One API request supplies the dashboard overview.
- The HTTP handler stays simple.
- Data aggregation is separated from presentation.
- The frontend does not duplicate backend aggregation logic.
- Latest readings can be retrieved efficiently.
- Existing automation and adapter logic is reused instead of duplicated.
- The response can evolve internally without changing the route's responsibilities, provided the response contract remains stable.

## 8. Possible extension

A future extension could introduce a dedicated overview repository for the location, zone, device, and reading queries. This would keep SQL query logic in the persistence layer while allowing the Facade to focus on orchestration and response assembly.
