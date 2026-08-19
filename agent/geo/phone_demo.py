from .phone_adapter import PhoneGeoAdapter
from .simulator import (
    MAX_ACCURACY_M,
    get_facility,
)


def main():
    facility = get_facility()

    print("=== TrustedPresence Phone GEO ===")
    print()
    print("Allowed facility:")
    print(f"  ID:     {facility['id']}")
    print(f"  Lat:    {facility['lat']}")
    print(f"  Lon:    {facility['lon']}")
    print(f"  Radius: {facility['radius_m']} m")
    print()

    print("Enter live location values from your phone.")
    print()

    lat = float(input("Latitude: ").strip())

    lon = float(input("Longitude: ").strip())

    accuracy = float(input("Accuracy (meters): ").strip())

    adapter = PhoneGeoAdapter()

    evidence = adapter.collect(
        lat=lat,
        lon=lon,
        accuracy_m=accuracy,
    )

    print()
    print("=== GeoEvidence ===")
    print(evidence.model_dump_json(indent=2))

    print()
    print("=== RESULT ===")

    if not evidence.fresh:
        print("DENIED: stale coordinates")

    elif evidence.accuracy_m > MAX_ACCURACY_M:
        print("DENIED: location accuracy is too low")

    elif evidence.inside:
        print("INSIDE")

    else:
        print("OUTSIDE")


if __name__ == "__main__":
    main()
