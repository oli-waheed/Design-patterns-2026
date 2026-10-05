# Phase 5 — Adapter questions

**Pattern / focus:** Adapter.

**Read first:** [Guide 05](../../materials/guides/05-adapter.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a legacy XML calendar client) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensor ports, adapters, readings, and `sensor_readings` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol (odd field names, units, XML, status codes) directly?

> [!NOTE]
> ***Your Answer***
>
> Adapter makes different interfaces work together. It translates vendor-specific data into the format our application understands, so the main code does not need to handle vendor details.

2. Name the participants (**target / port**, **adaptee**, **adapter**, **client**). What does the adapter translate, and what must it **not** decide (business policy)?

> [!NOTE]
> ***Your Answer***
>
> The port is the interface the application expects, the adaptee is the external or vendor interface, and the adapter connects them. The adapter translates the data, but should not make business decisions.

3. GoF distinguishes an **object adapter** (composition) from a **class adapter** (inheritance). Which does modern code prefer, and why?

> [!NOTE]
> ***Your Answer***
>
> Object Adapter is usually preferred because it uses composition instead of inheritance. It is more flexible, and the application is less dependent on the adapted class.

## B. This phase of the application

4. What is `SensorPort` in this lab, and what normalized value type (for example `Reading`) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?

> [!NOTE]
> ***Your Answer***
>
> `SensorPort` is the common interface for sensors. Adapters return a normalized `Reading`. The application uses the port, so it does not need to know whether the sensor is simulation, vendor, or something else.

5. You need three translations onto the same normalized reading: a simulation adapter, a vendor stub, and an MQTT translator that accepts a payload dict. Why is the different raw shape the point of the exercise? How does `source` (`simulation`, `vendor`, or `mqtt`) show which adapter produced the reading, and why must the MQTT translator not open a broker in this phase? Phase 12 may deliver that same dict on a device HTTP route or through an optional broker — why must this phase still not open either transport?

> [!NOTE]
> ***Your Answer***
>
> The raw data can have different formats, that is why we need adapters. Each adapter converts its data into the same `Reading` format. The `source` shows where the reading came from. MQTT only translates the payload in this phase, it should not open a broker or HTTP connection.

6. Readings are **appended** to `sensor_readings` (history grows). Why not keep only the latest value in memory or overwrite a single row, and which later phase consumes this history? Why do a manual read, the simulation sampler, and (later) MQTT share **one** writer of that table? Why does the sampler skip devices with tracking off and MQTT devices, and why do sensor cards poll the latest stored reading until Phase 12?

> [!NOTE]
> ***Your Answer***
>
> Readings are stored as history, so previous values are not lost. This history will be useful in later phases, especially Strategy. Manual reads and the simulation sampler use the same writer, so readings are stored consistently. The sampler skips disabled and MQTT devices, and the frontend uses the latest stored reading until Phase 12.

7. `POST /api/sensors/{id}/read` runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?

> [!NOTE]
> ***Your Answer***
>
> If the device is missing, the API should return **404 Not Found**. If the adapter fails, it should return **500 Internal Server Error**. The router should use normal application types, not vendor-specific types.

## C. Compare, contrast, and scenarios

8. Contrast Adapter with **Facade**. Adapter changes the **shape** of an existing interface; Facade simplifies **how to use** a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).

> [!NOTE]
> ***Your Answer***
>
> Adapter changes the shape of an interface, so it fits the application. For example, a vendor sensor is converted into a normal `Reading`. Facade gives a simpler way to use a complicated subsystem, for example controlling several greenhouse devices through one service.

9. Contrast Adapter with **Decorator**. Both wrap an object. What is different about the interface they present to the client?

> [!NOTE]
> ***Your Answer***
>
> Adapter changes the interface, so the client can use it. Decorator keeps the same interface, but adds extra behavior, such as logging or safety checks.

10. A classmate puts irrigation policy (“if moisture &lt; 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?

> [!NOTE]
> ***Your Answer***
>
> The adapter should only translate the vendor data, it should not decide when to water. Irrigation decisions are business logic, so they should be handled later by Strategy. The adapter should stay responsible for translating the vendor data.