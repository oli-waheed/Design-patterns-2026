# Phase 3 — Abstract Factory questions

**Pattern / focus:** Abstract Factory.

**Read first:** [Guide 03](../../materials/guides/03-abstract-factory.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example warrior/mage class kits) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to device families, provision, and the unified devices API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a **family**?

> [!NOTE]
> ***Your Answer***
>
> Abstract Factory creates a group of related products that work together. If products are chosen independently, different families can be mixed and incompatible devices may be created.

2. Name the main participants (**abstract factory**, **concrete factory**, **abstract products**, **concrete products**, **client**). How does choosing a factory at the start **commit** the client to one family?

> [!NOTE]
> ***Your Answer***
>
> The main participants are the abstract factory, concrete factories, abstract products, concrete products, and client. In this application, SimulationDeviceFactory and EdgeDeviceFactory are concrete factories. Choosing one factory commits the client to that device family.

3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?

> [!NOTE]
> ***Your Answer***
>
> Use Abstract Factory when several related products must belong to the same family. Skip it when only one product is needed or when mixing products from different families is valid.

## B. This phase of the application

4. In this lab, what is a **device family**, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?

> [!NOTE]
> ***Your Answer***
>
> A device family is a group of compatible devices, such as simulation or edge. create_device_set() returns four devices: two sensors and two actuators. The kits should not mix incompatible siblings because their configurations and protocols are different.

5. Phase 2 Factory Method creators still exist. How does Abstract Factory **compose** them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?

> [!NOTE]
> ***Your Answer***
>
> Abstract Factory reuses the Phase 2 sensor creators to create the moisture and light sensors, then adds the family-specific configuration. If the creators were deleted, sensor construction would be duplicated inside the family factories and the Factory Method design would be lost.

6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?

> [!NOTE]
> ***Your Answer***
>
> The existing devices table already represents both sensors and actuators, so device_family identifies which family each device belongs to. The default or backfill keeps old Phase 2 rows valid. Without it, old sensor rows could have no family and would not be consistent with the new model.

7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?

> [!NOTE]
> ***Your Answer***
>
> The UI needs family filtering so simulation and edge devices are not mixed. The Phase 2 /api/sensors routes must still work because Phase 3 extends the existing application rather than replacing the sensor API.

## C. Compare, contrast, and scenarios

8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which **one** product?” versus “which product **line**?” and mention that Abstract Factory often **uses** Factory Method–style methods inside.

> [!NOTE]
> ***Your Answer***
>
> Factory Method asks, “which one product?” For example, a moisture sensor or a light sensor. Abstract Factory asks, “which product line?” For example, a complete simulation or edge kit. Abstract Factory can use Factory Method-style methods inside it to create individual products.

9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?

> [!NOTE]
> ***Your Answer***
>
> If the HTTP handler creates simulation or edge devices directly, it can mix configurations from different families and duplicate business logic. The HTTP layer should call the service, and the service should use the selected family factory.

10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?

> [!NOTE]
> ***Your Answer***
>
> A god factory is a misuse because locations, readings, and devices are different concepts. Abstract Factory should create related products that belong to one family. One huge factory would become difficult to maintain and extend.
