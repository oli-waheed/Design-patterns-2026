# Abstract Factory Pattern

## Problem

The Smart Greenhouse needs to support different device families, such as `simulation` and `edge`.

Each family needs a coherent set of devices containing both sensors and actuators. The devices in each family can have different labels and configuration values.

Creating these devices separately could make it easy to accidentally mix devices from different families.

## Solution

The Abstract Factory pattern creates a complete family of related devices.

The project defines an abstract `DeviceFamilyFactory` with:

* `family_key`
* `create_device_set()`

There are two concrete factories:

* `SimulationDeviceFactory`
* `EdgeDeviceFactory`

Each factory creates four devices:

* Moisture sensor
* Light sensor
* Water pump
* Grow light

The simulation and edge factories use different family-specific configuration.

The existing Factory Method sensor creators are reused by the family factories for creating the moisture and light sensors.

The created devices are stored in the existing `devices` table with their `device_family` and `role`.

## Abstract Factory vs Factory Method

The Factory Method pattern is used to create one type of product.

In Phase 2, the sensor creators create individual sensor types, such as:

* Moisture sensor
* Light sensor

The Abstract Factory pattern creates a complete product family.

In Phase 3, a device family factory creates a complete set containing sensors and actuators that belong together.

In simple terms:

* Factory Method → creates an individual product.
* Abstract Factory → creates a related group of products.

## Where the Pattern Is Used

The main Abstract Factory implementation is in:

```text
backend/src/domain/devices/family_factory.py
```

The domain contains:

* `DeviceFamilyFactory`
* `SimulationDeviceFactory`
* `EdgeDeviceFactory`
* `get_family_factory()`

The application service uses the selected family factory to create and persist the device set.

The REST API exposes the functionality through:

```text
GET  /api/devices
POST /api/devices/provision?family=simulation
POST /api/devices/provision?family=edge
```

The frontend provides a family switcher and device list in the Devices dashboard section.

## Why Device Is Different from DeviceDto

`Device` is a domain entity. It belongs to the domain layer and represents a greenhouse device independently of HTTP or database technologies.

`DeviceDto` is an API data-transfer object. It defines the data structure returned by the REST API.

Keeping them separate prevents the domain model from depending on FastAPI or Pydantic.

The mapper in the application layer converts a domain `Device` into a `DeviceDto`.

This keeps the domain, application, infrastructure, and API responsibilities separated.

## Adding a Third Family

A third family could be added without changing the existing sensor Factory Method creators.

For example, a `cloud` family could be introduced by creating:

```text
CloudDeviceFactory
```

It would implement `DeviceFamilyFactory` and provide:

```text
family_key = "cloud"
```

Its `create_device_set()` method would create the sensors and actuators with cloud-specific configuration.

The new factory would then be added to the family factory lookup.

The existing repository, service, DTO, mapper, and general device API could continue to work with the new family.
