# Phase 4 — Builder questions

**Pattern / focus:** Builder.

**Read first:** [Guide 04](../../materials/guides/04-builder.md) · [Requirements](requirements.md)

## How to answer

* Use your own wording. Do not paste teaching-example types (for example ramen orders) as if they were your greenhouse classes.
* When a question asks about *this application*, refer to locations, zones, `location_id`, and the configuration wizard from the lab.
* Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
* Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Builder in plain language. Why does construction of a complex object need **stepwise assembly** and **validation at the end** (`build()`), instead of a telescoping constructor or a half-filled dict written straight to the database?

> [!NOTE]
> ***Your Answer***
>
> Builder creates a complex object step by step. In our case, it builds a location with zones. `build()` checks that the whole configuration is valid before saving it.

2. Name the main participants (**product**, **builder**, **optional director**, **client**). Until `build()` succeeds, is the intermediate object a finished domain product? Why does that distinction matter?

> [!NOTE]
> ***Your Answer***
>
> The product is `LocationConfig`. The builder is `LocationConfigBuilder`. The application service is the client. We do not need a director. Before `build()`, it is not a finished product because it has not passed validation.

3. List at least three kinds of invalid configuration a location/zone `build()` should reject in **this** lab (name, zones, moisture thresholds). Why must those rules live in the **domain** builder, not only in the HTTP layer?

> [!NOTE]
> ***Your Answer***
>
> It should reject an empty location name, no zones, duplicate zone names, invalid thresholds, and low threshold greater than or equal to high threshold. These rules belong in the domain because they are business rules, not only API rules.

## B. This phase of the application

4. What aggregate does the builder produce (location plus zones)? Why does this course use **`location_id`** (and never `greenhouse_id`) as the name for that scope?

> [!NOTE]
> ***Your Answer***
>
> The builder creates a location with its zones. Zones use `location_id` to show which location they belong to. We use `location_id` because that is the required name in this phase.

5. Describe the path from API request to persistence: DTO → builder steps → `build()` → repository. What must **not** be persisted if `build()` raises `ConfigurationError` (or equivalent)? Why does assigning a device wait until the zone row exists, and why does the client send only `zone_id`?

> [!NOTE]
> ***Your Answer***
>
> The API receives a DTO. The service gives the data to the builder. `build()` validates it, and then the repository saves it. If validation fails, nothing should be saved. Device assignment waits until the zone has an ID. The client only sends `zone_id` because the server gets the correct `location_id` from the zone.

6. Saving a location and its zones must be **one transaction**. What goes wrong if the location row commits and a later zone insert fails? How does that relate to “no half-built aggregates in the database”?

> [!NOTE]
> ***Your Answer***
>
> We could end up with a location but only some of its zones. This creates incomplete data. One transaction makes sure everything is saved or everything is rolled back.

7. The configuration wizard UI collects fields in steps. How does that UI map to Builder without turning React (or the HTTP handler) into the place that owns domain validation?

> [!NOTE]
> ***Your Answer***
>
> The UI collects the location and zone information and sends it to the API. The application service passes it to the Builder. The Builder keeps the actual domain validation.

## C. Compare, contrast, and scenarios

8. Contrast Builder with Factory Method and with Abstract Factory. Which pattern answers “which type?”, which answers “which matching kit?”, and which answers “how do we assemble one **valid whole** in steps?

> [!NOTE]
> ***Your Answer***
>
> Factory Method answers “which type?”. Abstract Factory creates a matching group of objects. Builder answers “how do we build one valid object step by step?”

9. Fluent method chaining (`builder.add_zone(...).build()`) is a coding style. Why is a fluent interface **not** the same thing as the Builder pattern?

> [!NOTE]
> ***Your Answer***
>
> Fluent interface is just a way to chain method calls. Builder is about constructing and validating a complex object step by step.

10. A classmate validates thresholds only in FastAPI / Pydantic and leaves `build()` empty. Another mutates builder fields after `build()` while treating the product as immutable. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> API validation alone is not enough because other code could use the domain directly. The Builder must also validate. After `build()`, the product should stay immutable, so it should not be changed afterward.
