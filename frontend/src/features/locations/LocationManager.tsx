import { useEffect, useState } from 'react'

import {
  addZone,
  createLocation,
  deleteLocation,
  deleteZone,
  getLocation,
  getLocations,
  renameLocation,
  updateZone,
  type LocationResponseDto,
  type LocationSummaryDto,
  type ZoneDto,
  type ZoneInput,
} from '../../services/api'

type ZoneForm = {
  name: string
  moisture_threshold_low: string
  moisture_threshold_high: string
}

const emptyZoneForm: ZoneForm = {
  name: '',
  moisture_threshold_low: '0.3',
  moisture_threshold_high: '0.7',
}

export default function LocationManager() {
  const [locations, setLocations] = useState<
    LocationSummaryDto[]
  >([])

  const [selectedLocation, setSelectedLocation] =
    useState<LocationResponseDto | null>(null)

  const [locationName, setLocationName] = useState('')

  const [newZone, setNewZone] =
    useState<ZoneForm>(emptyZoneForm)

  const [editingZoneId, setEditingZoneId] =
    useState<string | null>(null)

  const [editingZone, setEditingZone] =
    useState<ZoneForm>(emptyZoneForm)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadLocations()
  }, [])

  async function loadLocations() {
    try {
      setLoading(true)
      setError('')

      const data = await getLocations()
      setLocations(data)

      if (data.length === 0) {
        setSelectedLocation(null)
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load locations',
      )
    } finally {
      setLoading(false)
    }
  }

  async function selectLocation(
    locationId: string,
  ) {
    try {
      setLoading(true)
      setError('')

      const data = await getLocation(locationId)
      setSelectedLocation(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load location',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateLocation() {
    if (!locationName.trim()) {
      setError('Location name is required.')
      return
    }

    try {
      setLoading(true)
      setError('')

      const zone: ZoneInput = {
        name: 'Main Zone',
        moisture_threshold_low: 0.3,
        moisture_threshold_high: 0.7,
        schedule: {},
      }

      const created = await createLocation({
        location_name: locationName.trim(),
        zones: [zone],
      })

      setLocationName('')

      await loadLocations()
      setSelectedLocation(created)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to create location',
      )
    } finally {
      setLoading(false)
    }
  }

  const [renaming, setRenaming] = useState(false)
  const [newName, setNewName] = useState('')

  function startRename() {
    if (!selectedLocation) {
      return
    }

    setNewName(selectedLocation.location.name)
    setRenaming(true)
  }

  async function handleRename() {
    if (!selectedLocation || !newName.trim()) {
      return
    }

    try {
      setLoading(true)
      setError('')

      const updated = await renameLocation(
        selectedLocation.location.id,
        newName.trim(),
      )

      setSelectedLocation({
        ...selectedLocation,
        location: updated,
      })
      setLocations((current) =>
        current.map((location) =>
          location.id === updated.id ? updated : location,
        ),
      )
      setRenaming(false)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to rename location',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteLocation() {
    if (!selectedLocation) {
      return
    }

    const confirmed = window.confirm(
      `Delete "${selectedLocation.location.name}"?`,
    )

    if (!confirmed) {
      return
    }

    try {
      setLoading(true)
      setError('')

      await deleteLocation(
        selectedLocation.location.id,
      )

      setSelectedLocation(null)
      await loadLocations()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to delete location',
      )
    } finally {
      setLoading(false)
    }
  }

  function parseZoneForm(
    form: ZoneForm,
  ): ZoneInput | null {
    const low = Number(
      form.moisture_threshold_low,
    )

    const high = Number(
      form.moisture_threshold_high,
    )

    if (!form.name.trim()) {
      setError('Zone name is required.')
      return null
    }

    if (
      Number.isNaN(low) ||
      Number.isNaN(high)
    ) {
      setError('Thresholds must be numbers.')
      return null
    }

    if (
      low < 0 ||
      low > 1 ||
      high < 0 ||
      high > 1
    ) {
      setError(
        'Thresholds must be between 0 and 1.',
      )
      return null
    }

    if (low >= high) {
      setError(
        'Low threshold must be less than high threshold.',
      )
      return null
    }

    return {
      name: form.name.trim(),
      moisture_threshold_low: low,
      moisture_threshold_high: high,
      schedule: {},
    }
  }

  async function handleAddZone() {
    if (!selectedLocation) {
      return
    }

    const zone = parseZoneForm(newZone)

    if (!zone) {
      return
    }

    try {
      setLoading(true)
      setError('')

      await addZone(
        selectedLocation.location.id,
        zone,
      )

      setNewZone(emptyZoneForm)

      await selectLocation(
        selectedLocation.location.id,
      )
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to add zone',
      )
    } finally {
      setLoading(false)
    }
  }

  function startEditingZone(zone: ZoneDto) {
    setEditingZoneId(zone.id)

    setEditingZone({
      name: zone.name,
      moisture_threshold_low:
        String(zone.moisture_threshold_low),
      moisture_threshold_high:
        String(zone.moisture_threshold_high),
    })

    setError('')
  }

  function cancelEditingZone() {
    setEditingZoneId(null)
    setEditingZone(emptyZoneForm)
  }

  async function handleUpdateZone() {
    if (
      !selectedLocation ||
      !editingZoneId
    ) {
      return
    }

    const zone = parseZoneForm(editingZone)

    if (!zone) {
      return
    }

    try {
      setLoading(true)
      setError('')

      await updateZone(
        selectedLocation.location.id,
        editingZoneId,
        zone,
      )

      cancelEditingZone()

      await selectLocation(
        selectedLocation.location.id,
      )
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to update zone',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteZone(
    zoneId: string,
  ) {
    if (!selectedLocation) {
      return
    }

    if (selectedLocation.zones.length <= 1) {
      setError(
        'A location must have at least one zone.',
      )
      return
    }

    const confirmed = window.confirm(
      'Delete this zone?',
    )

    if (!confirmed) {
      return
    }

    try {
      setLoading(true)
      setError('')

      await deleteZone(
        selectedLocation.location.id,
        zoneId,
      )

      await selectLocation(
        selectedLocation.location.id,
      )
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to delete zone',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">
          Location Management
        </h2>

        <p className="text-sm text-slate-500">
          Create locations and manage their zones.
        </p>
      </div>

      {error && (
        <div className="alert-error">
          {error}
        </div>
      )}

      {/* Create location */}
      <div className="panel p-4">
        <h3 className="mb-3 font-medium">
          Create Location
        </h3>

        <div className="flex gap-2">
          <input
            value={locationName}
            onChange={(event) =>
              setLocationName(event.target.value)
            }
            placeholder="Location name"
            className="field flex-1"
          />

          <button
            type="button"
            onClick={handleCreateLocation}
            disabled={loading}
            className="btn btn-primary"
          >
            Create
          </button>
        </div>
      </div>

      {/* Location list */}
      <div className="panel p-4">
        <h3 className="mb-3 font-medium">
          Locations
        </h3>

        {locations.length === 0 ? (
          <p className="text-sm text-slate-500">
            No locations yet.
          </p>
        ) : (
          <div className="space-y-2">
            {locations.map((location) => (
              <button
                key={location.id}
                type="button"
                onClick={() =>
                  selectLocation(location.id)
                }
                className={`block w-full rounded border p-3 text-left ${
                  selectedLocation?.location.id ===
                  location.id
                    ? 'border-black'
                    : ''
                }`}
              >
                {location.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Selected location */}
      {selectedLocation && (
        <div className="panel space-y-6 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            {renaming ? (
              <form
                className="flex flex-1 flex-wrap items-center gap-2"
                onSubmit={(event) => {
                  event.preventDefault()
                  void handleRename()
                }}
              >
                <label htmlFor="rename-location" className="sr-only">
                  Location name
                </label>
                <input
                  id="rename-location"
                  value={newName}
                  onChange={(event) => setNewName(event.target.value)}
                  maxLength={128}
                  className="field min-w-0 flex-1"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={loading || !newName.trim()}
                  className="btn btn-primary btn-sm"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setRenaming(false)}
                  className="btn btn-secondary btn-sm"
                >
                  Cancel
                </button>
              </form>
            ) : (
              <div className="min-w-0">
                <h3 className="section-title truncate">
                  {selectedLocation.location.name}
                </h3>

                <p className="truncate text-xs text-slate-500">
                  ID: {selectedLocation.location.id}
                </p>
              </div>
            )}

            {!renaming && (
              <div className="flex shrink-0 gap-2">
                <button
                  type="button"
                  onClick={startRename}
                  disabled={loading}
                  className="btn btn-secondary btn-sm"
                >
                  Rename
                </button>
                <button
                  type="button"
                  onClick={handleDeleteLocation}
                  disabled={loading}
                  className="btn btn-danger btn-sm"
                >
                  Delete
                </button>
              </div>
            )}
          </div>

          {/* Add zone */}
          <div className="panel p-4">
            <h4 className="mb-3 font-medium">
              Add Zone
            </h4>

            <div className="grid gap-3 md:grid-cols-3">
              <input
                value={newZone.name}
                onChange={(event) =>
                  setNewZone({
                    ...newZone,
                    name: event.target.value,
                  })
                }
                placeholder="Zone name"
                className="field"
              />

              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={
                  newZone.moisture_threshold_low
                }
                onChange={(event) =>
                  setNewZone({
                    ...newZone,
                    moisture_threshold_low:
                      event.target.value,
                  })
                }
                placeholder="Low threshold"
                className="field"
              />

              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={
                  newZone.moisture_threshold_high
                }
                onChange={(event) =>
                  setNewZone({
                    ...newZone,
                    moisture_threshold_high:
                      event.target.value,
                  })
                }
                placeholder="High threshold"
                className="field"
              />
            </div>

            <button
              type="button"
              onClick={handleAddZone}
              disabled={loading}
              className="btn btn-primary mt-3"
            >
              Add Zone
            </button>
          </div>

          {/* Zones */}
          <div>
            <h4 className="mb-3 font-medium">
              Zones
            </h4>

            <div className="space-y-3">
              {selectedLocation.zones.map(
                (zone) => (
                  <div
                    key={zone.id}
                    className="panel p-4"
                  >
                    {editingZoneId === zone.id ? (
                      <div className="space-y-3">
                        <input
                          value={editingZone.name}
                          onChange={(event) =>
                            setEditingZone({
                              ...editingZone,
                              name: event.target.value,
                            })
                          }
                          className="field w-full"
                        />

                        <div className="grid gap-3 md:grid-cols-2">
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.01"
                            value={
                              editingZone.moisture_threshold_low
                            }
                            onChange={(event) =>
                              setEditingZone({
                                ...editingZone,
                                moisture_threshold_low:
                                  event.target.value,
                              })
                            }
                            className="field"
                          />

                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.01"
                            value={
                              editingZone.moisture_threshold_high
                            }
                            onChange={(event) =>
                              setEditingZone({
                                ...editingZone,
                                moisture_threshold_high:
                                  event.target.value,
                              })
                            }
                            className="field"
                          />
                        </div>

                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={
                              handleUpdateZone
                            }
                            disabled={loading}
                            className="btn btn-primary"
                          >
                            Save
                          </button>

                          <button
                            type="button"
                            onClick={
                              cancelEditingZone
                            }
                            className="btn btn-secondary"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <div className="font-medium">
                            {zone.name}
                          </div>

                          <div className="text-sm text-slate-500">
                            Moisture:{' '}
                            {zone.moisture_threshold_low}
                            {' – '}
                            {zone.moisture_threshold_high}
                          </div>
                        </div>

                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() =>
                              startEditingZone(zone)
                            }
                            className="btn btn-secondary"
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDeleteZone(
                                zone.id,
                              )
                            }
                            disabled={loading}
                            className="btn btn-danger"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ),
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}