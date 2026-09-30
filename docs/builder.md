# Builder Pattern

## Purpose

The Builder pattern is used to create a valid location configuration step by step.

In this project, a location can contain one or more zones. The Builder collects the location name and zones, validates the complete configuration, and then creates the `LocationConfig`.

## Main Classes

- `LocationConfigBuilder` is the Builder.
- `LocationConfig` is the product.
- `Location` contains the location name and zones.
- `Zone` contains the zone configuration.
- `ConfigurationError` is raised when the configuration is invalid.

The application service acts as the client of the Builder.

We do not need a separate Director because the application service already controls the construction process.

## Construction Flow

The flow is:

1. The API receives the location configuration.
2. The application service creates a `LocationConfigBuilder`.
3. The location name is added to the Builder.
4. Zones are added to the Builder.
5. `build()` validates the complete configuration.
6. If validation succeeds, a `LocationConfig` is created.
7. The repository saves the location and all its zones in one transaction.

The Builder does not save anything to the database.

## Validation Rules

The Builder checks:

- Location name must not be empty.
- At least one zone is required.
- Zone names must be unique.
- Zone names must not be empty.
- Moisture thresholds must be between `0.0` and `1.0`.
- The low threshold must be less than the high threshold.

These are domain rules, so the validation belongs in the domain Builder.

## Persistence

The repository saves the location and all its zones in one database transaction.

If saving fails, the transaction is rolled back. This prevents a partially created location from being stored.

The Builder itself does not know about PostgreSQL, SQLAlchemy, FastAPI, or Pydantic.

## Device Assignment

Devices are not added through the Builder.

A location and its zones must first be saved so that the zones have database IDs. A separate device assignment operation can then assign a device to a zone.

When a device is assigned to a zone:

- `device.zone_id` is set to the selected zone.
- `device.location_id` is copied from the zone.

When a device is unassigned:

- `device.zone_id` is set to `NULL`.
- `device.location_id` is set to `NULL`.

## Why Builder Is Useful Here

The location configuration contains several related values and validation rules.

The Builder keeps the construction process clear and makes sure that an invalid configuration cannot be created through the domain API.

It also keeps domain validation separate from the API and database layers.

## Builder vs Other Patterns

### Builder vs Factory Method

Factory Method mainly answers:

> Which type of object should be created?

Builder answers:

> How should a complex object be constructed step by step?

### Builder vs Abstract Factory

Abstract Factory creates a related group of objects.

Builder constructs one complex object step by step.

### Builder vs Fluent Interface

A fluent interface allows method calls to be chained.

Builder is the construction pattern. A Builder can use a fluent interface, but they are not the same thing.

## Immutability

After `build()` creates the `LocationConfig`, the domain objects are immutable.

This makes the completed configuration safer to use because it cannot accidentally be changed after validation.