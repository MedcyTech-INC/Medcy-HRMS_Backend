from typing import Optional, NamedTuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.location import OfficeLocation
from app.utils.haversine import haversine_distance_meters


class GeofenceResult(NamedTuple):
    allowed: bool
    distance_meters: float
    nearest_office_name: Optional[str]
    accuracy_warning: bool


class GeofenceService:
    @staticmethod
    async def validate_location(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        accuracy_meters: Optional[float] = None
    ) -> GeofenceResult:
        """
        Server-side anti-spoofing geofence validation.
        Checks if given (lat, lng) falls within radius_meters of any active OfficeLocation.
        """
        accuracy_warning = accuracy_meters is not None and accuracy_meters > 100.0

        stmt = select(OfficeLocation).where(OfficeLocation.is_active == True)
        result = await db.execute(stmt)
        offices = result.scalars().all()

        if not offices:
            # If no office locations are configured in the system yet, default to allowed
            return GeofenceResult(
                allowed=True,
                distance_meters=0.0,
                nearest_office_name="Default Location",
                accuracy_warning=accuracy_warning,
            )

        min_distance = float("inf")
        nearest_office: Optional[OfficeLocation] = None
        within_geofence = False

        for office in offices:
            dist = haversine_distance_meters(latitude, longitude, float(office.latitude), float(office.longitude))
            if dist < min_distance:
                min_distance = dist
                nearest_office = office
            if dist <= float(office.radius_meters):
                within_geofence = True

        return GeofenceResult(
            allowed=within_geofence,
            distance_meters=round(min_distance, 2),
            nearest_office_name=nearest_office.name if nearest_office else None,
            accuracy_warning=accuracy_warning,
        )


geofence_service = GeofenceService()
