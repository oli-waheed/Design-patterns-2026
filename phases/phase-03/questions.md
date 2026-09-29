# Phase 3 — Abstract Factory questions

**Pattern / focus:** Abstract Factory.

## A. Pattern

### 1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a **family**?

Abstract Factory creates a group of related products that work together. Without it, different products can be selected independently and incompatible devices may be mixed.

### 2. Name the main participants (**abstract factory**, **concrete factory**, **abstract products**, **concrete products**, **client**). How does choosing a factory at the start **commit** the client to one family?

The main participants are the abstract factory, concrete factories, abstract products, concrete products, and client. In our application, `SimulationDeviceFactory` and `EdgeDeviceFactory` are concrete factories. Once the client chooses a factory, the whole device set belongs to that family.

### 3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?

Use Abstract Factory when several related products must belong to the same family. Skip it when only one product is needed or when mixing products from different families is safe.

## B. This phase of the application

### 4. In this lab, what is a **device family**, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?

A device family is a group of compatible devices, such as `simulation` or `edge`. `create_device_set()` returns four devices. Two sensors and two actuators. Simulation and edge devices have different configurations, so they should not be mixed.

### 5. Phase 2 Factory Method creators still exist. How does Abstract Factory **compose** them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?

The Abstract Factory reuses the Phase 2 sensor creators to create moisture and light sensors. It then adds the family-specific configuration. Without the creators, sensor creation would be duplicated inside the family factories.

### 6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?

We use the existing `devices` table because both sensors and actuators are devices. `device_family` tells us which family each device belongs to. The default or backfill keeps old Phase 2 rows valid. Without it, old sensors could have no family.

### 7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?

The UI needs family filtering so simulation and edge devices are not mixed. The old `/api/sensors` routes must still work because Phase 3 extends Phase 2. It does not replace it.

## C. Compare, contrast, and scenarios

### 8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which **one** product?” versus “which **product line**?” and mention that Abstract Factory often **uses** Factory Method–style methods inside.

Factory Method asks, **“Which one product?”** For example, a moisture sensor or a light sensor. Abstract Factory asks, **“Which product line?”** For example, a complete simulation or edge kit. Abstract Factory can use Factory Method inside it.

### 9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?

If the HTTP handler creates devices directly, it could mix simulation and edge configurations. It also duplicates business logic. The HTTP layer should call the service, and the service should use the family factory.

### 10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?

A god factory is a misuse because locations, readings, and devices are different concepts. Abstract Factory should create related products from one family. One huge factory would become difficult to maintain and extend.
