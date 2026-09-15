# Phase 2 — Factory Method questions

Pattern / focus: Factory Method.

Read first: [Guide 02](./guided-check.md) · [Requirements](./requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example courier notifiers) as if they were your greenhouse classes.
- When a question asks about this application, refer to sensors, creators, the `devices` table, and the sensors API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching Your Answer note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

### 1. State the intent of Factory Method in plain language. What problem appears when callers scatter `new` / constructors (or a growing `if type == ...`) across the application?

Factory Method moves object creation away from the callers. Otherwise, every part of the application may start using constructors or `if/elif` checks. As types grow, that becomes harder to maintain and extend.

### 2. Name the main participants of Factory Method (product, concrete product, creator, concrete creator, client). For each, give one sentence: what it is responsible for.

- Product - `Sensor`, the common object used by the application.
- Concrete product - The actual sensor variant, such as moisture or light.
- Creator - `SensorCreator`, which defines how a sensor is created.
- Concrete creator - `MoistureSensorCreator` or `LightSensorCreator`, each providing its own sensor details.
- Client - `SensorService`, which requests a sensor without handling its creation details.

### 3. How do you add a new product variant when creators are polymorphic (new class + registry entry) versus when creation lives in one shared `if/elif` function? Why does that difference matter for extension?

With polymorphic creators, I add a new creator class and a registry entry. The existing service can stay unchanged. With one `if/elif` function, I must keep modifying the same function, which becomes harder to manage as variants increase.

## B. This phase of the application

### 4. In this lab, what is the product and what are the concrete creators? Why must the API handler (or sensor service) go through a creator/registry instead of constructing `MoistureSensor` / `LightSensor` itself?

The product is the `Sensor` domain object. The concrete creators are `MoistureSensorCreator` and `LightSensorCreator`. The service uses them because sensor-specific defaults belong to the creators, not to the API handler.

### 5. `POST /api/sensors` accepts a short `type` key such as `"moisture"` or `"light"`, while the stored/returned field is `device_type` (for example `moisture_sensor`). Why are those two fields different? Who decides the stored `device_type` and `default_config`?

`type` is a short API key, used to select the creator, for example `"moisture"`. `device_type` is the stored sensor identity, for example `"moisture_sensor"`. The concrete creator decides both `device_type` and `default_config`.

### 6. Why is there a single `devices` table with `role="sensor"` instead of a dedicated `sensors` table? What later phase does that choice prepare for?

A single `devices` table gives the system a common place for different device roles. `role="sensor"` identifies the devices used in this phase. It also prepares the database for later device types, such as actuators.

### 7. What should happen when the client posts an unknown `type`? Where should that rejection be decided (registry/service vs router constructing a concrete class anyway)?

An unknown type should be rejected with HTTP 400. The registry should decide whether the type exists, not the router. In our implementation, `get_creator()` rejects the type, and the API converts that error into a 400 response.

## C. Compare, contrast, and scenarios

### 8. Contrast Factory Method with a simple factory (one function full of `if type == ...`). When is the simple factory “good enough,” and why does this phase still want polymorphic creators?

A simple factory is fine when creation is small and unlikely to change. Factory Method separates creation into different creators. This phase uses that approach because adding another sensor should not make one central `if/elif` function increasingly complicated.

### 9. Contrast Factory Method with Abstract Factory (Phase 3). Factory Method answers which question? Abstract Factory answers which different question? Why is Factory Method enough for Phase 2 sensors?

Factory Method focuses on creating one product, here a sensor. Abstract Factory focuses on creating a family of related products. Phase 2 only needs individual sensors, so Factory Method is enough.

### 10. A classmate puts SQLAlchemy session commits (or FastAPI request parsing) inside a concrete creator. Why is that a trap? Where should persistence and HTTP stay instead?

That would mix responsibilities. The creator should create and configure the sensor, nothing more. Database work belongs in the repository, HTTP parsing belongs in the API layer. This separation also makes the creator easier to test.