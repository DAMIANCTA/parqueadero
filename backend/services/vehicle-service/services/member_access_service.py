from fastapi import HTTPException

from repositories.biometric_repository import BiometricEvidenceRepository
from repositories.face_service_repository import FaceServiceRepository
from repositories.member_repository import MemberRepository
from schemas.members import (
    FaceEnrollMemberRequest,
    FaceProfileListResponse,
    FaceProfileResponse,
    MemberAccessValidationRequest,
    MemberAccessValidationResponse,
    MemberCreateRequest,
    MemberListResponse,
    MemberResponse,
    MonthlyPermitCreateRequest,
    MonthlyPermitListResponse,
    MonthlyPermitResponse,
    PermitLookupResponse,
    VehicleAuthorizationRequest,
    VehicleAuthorizationResponse,
    VehicleCreateRequest,
    VehicleListResponse,
    VehicleLookupResponse,
    VehicleResponse,
)


class MemberAccessService:
    def __init__(self) -> None:
        self.repository = MemberRepository()
        self.biometric_repository = BiometricEvidenceRepository()
        self.face_service = FaceServiceRepository()

    def create_member(self, payload: MemberCreateRequest) -> MemberResponse:
        record = self.repository.create_member(payload.model_dump())
        return MemberResponse(**record)

    def list_members(self, university_id: str | None = None) -> MemberListResponse:
        items = [MemberResponse(**item) for item in self.repository.list_members(university_id)]
        return MemberListResponse(total=len(items), items=items)

    def get_member(self, member_id: str) -> MemberResponse:
        record = self.repository.get_member(member_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Member not found")
        return MemberResponse(**record)

    def create_vehicle(self, payload: VehicleCreateRequest) -> VehicleResponse:
        if self.repository.get_vehicle_by_plate(payload.plate_text):
            raise HTTPException(status_code=409, detail="Vehicle plate is already registered")
        record = self.repository.create_vehicle(payload.model_dump())
        return VehicleResponse(**record)

    def list_vehicles(self, university_id: str | None = None) -> VehicleListResponse:
        items = [VehicleResponse(**item) for item in self.repository.list_vehicles(university_id)]
        return VehicleListResponse(total=len(items), items=items)

    def get_vehicle_by_plate(self, plate_text: str) -> VehicleLookupResponse:
        vehicle = self.repository.get_vehicle_by_plate(plate_text)
        if vehicle is None:
            return VehicleLookupResponse(found=False, message="Vehicle plate is not registered")
        people = [MemberResponse(**item) for item in self.repository.get_authorized_people_for_vehicle(vehicle["id"])]
        return VehicleLookupResponse(
            found=True,
            message="Vehicle plate is registered",
            vehicle=VehicleResponse(**vehicle),
            authorized_people=people,
        )

    def authorize_person(self, vehicle_id: str, payload: VehicleAuthorizationRequest) -> VehicleAuthorizationResponse:
        vehicle = self.repository.get_vehicle(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        member = self.repository.get_member(payload.person_id)
        if member is None:
            raise HTTPException(status_code=404, detail="Member not found")
        record = self.repository.authorize_person(vehicle_id, payload.person_id, payload.is_owner, payload.status)
        return VehicleAuthorizationResponse(**record)

    def enroll_face(self, member_id: str, payload: FaceEnrollMemberRequest) -> FaceProfileResponse:
        member = self.repository.get_member(member_id)
        if member is None:
            raise HTTPException(status_code=404, detail="Member not found")

        image_reference = self.biometric_repository.get_image_reference(payload.face_image_id)
        if image_reference is None:
            raise HTTPException(status_code=404, detail="Face image evidence not found")

        enrollment = self.face_service.enroll_face(
            university_id=member["university_id"],
            person_id=member_id,
            image_reference=image_reference,
            quality_score_hint=payload.quality_score_hint,
        )
        record = self.repository.create_face_profile(
            {
                "university_id": member["university_id"],
                "person_id": member_id,
                "face_image_id": payload.face_image_id,
                "template_id": enrollment["template_id"],
                "provider": enrollment.get("model_name") or payload.provider_hint or "face-service",
                "status": "ACTIVE",
            }
        )
        return FaceProfileResponse(**record)

    def list_face_profiles(self, university_id: str | None = None) -> FaceProfileListResponse:
        items = [FaceProfileResponse(**item) for item in self.repository.list_face_profiles(university_id)]
        return FaceProfileListResponse(total=len(items), items=items)

    def create_monthly_permit(self, payload: MonthlyPermitCreateRequest) -> MonthlyPermitResponse:
        member = self.repository.get_member(payload.person_id)
        if member is None:
            raise HTTPException(status_code=404, detail="Member not found")
        vehicle = self.repository.get_vehicle(payload.vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        record = self.repository.create_monthly_permit(payload.model_dump())
        return MonthlyPermitResponse(**record)

    def list_monthly_permits(self, university_id: str | None = None) -> MonthlyPermitListResponse:
        items = [MonthlyPermitResponse(**item) for item in self.repository.list_monthly_permits(university_id)]
        return MonthlyPermitListResponse(total=len(items), items=items)

    def get_permit_by_plate(self, plate_text: str) -> PermitLookupResponse:
        permit = self.repository.get_permit_by_plate(plate_text)
        if permit is None:
            return PermitLookupResponse(found=False, message="No valid monthly permit found for this plate")
        return PermitLookupResponse(
            found=True,
            plate_text=permit["plate_text"],
            permit_status=permit["status"],
            person_id=permit["person_id"],
            person_name=permit["person_name"],
            role_type=permit["role_type"],
            vehicle_id=permit["vehicle_id"],
            start_date=permit["start_date"],
            end_date=permit["end_date"],
            message="Valid monthly permit found",
        )

    def validate_member_access(self, payload: MemberAccessValidationRequest) -> MemberAccessValidationResponse:
        normalized_plate = self.repository.normalize_plate(payload.plate_text)
        vehicle = self.repository.get_vehicle_by_plate(normalized_plate)
        if vehicle is None or vehicle["status"] != "ACTIVE":
            return MemberAccessValidationResponse(
                authorized=False,
                vehicle_registered=False,
                plate_text=normalized_plate,
                message="Vehicle plate is not registered as a university member vehicle",
            )

        authorized_people = self.repository.get_authorized_people_for_vehicle(vehicle["id"])
        if not authorized_people:
            return MemberAccessValidationResponse(
                authorized=False,
                vehicle_registered=True,
                vehicle_id=vehicle["id"],
                plate_text=normalized_plate,
                message="Vehicle does not have authorized people",
                warnings=["NO_AUTHORIZED_PEOPLE"],
            )

        session_person = None
        if payload.session_person_id:
            session_person = next((person for person in authorized_people if person["id"] == payload.session_person_id), None)
            if session_person is not None:
                authorized_people = [session_person] + [person for person in authorized_people if person["id"] != payload.session_person_id]

        best_match: dict | None = None
        warnings: list[str] = []
        permit_failure = False
        for person in authorized_people:
            permit = self.repository.get_valid_permit(person_id=person["id"], vehicle_id=vehicle["id"])
            if permit is None:
                permit_failure = True
                warnings.append(f"PERMIT_NOT_VALID:{person['id']}")
                continue

            profiles = self.repository.get_face_profiles_by_person(person["id"])
            if not profiles:
                warnings.append(f"FACE_PROFILE_NOT_FOUND:{person['id']}")
                continue

            for profile in profiles:
                try:
                    comparison = self.face_service.compare_images(
                        university_id=payload.university_id,
                        source_image_id=profile["face_image_id"],
                        target_image_id=payload.face_image_id,
                    )
                except Exception:
                    warnings.append(f"FACE_COMPARE_FAILED:{person['id']}")
                    continue

                similarity = float(comparison.get("similarity") or 0.0)
                match = bool(comparison.get("match"))
                candidate = {
                    "person": person,
                    "permit": permit,
                    "profile": profile,
                    "comparison": comparison,
                    "similarity": similarity,
                    "match": match,
                }
                if best_match is None or similarity > best_match["similarity"]:
                    best_match = candidate
                if match:
                    return MemberAccessValidationResponse(
                        authorized=True,
                        vehicle_registered=True,
                        person_id=person["id"],
                        person_name=person["full_name"],
                        role_type=person["role_type"],
                        vehicle_id=vehicle["id"],
                        plate_text=normalized_plate,
                        permit_status=permit["status"],
                        face_match=True,
                        similarity=similarity,
                        template_id=profile["template_id"],
                        provider=comparison.get("provider"),
                        message="Member access authorized",
                        warnings=comparison.get("warnings", []),
                    )

        if best_match is not None:
            return MemberAccessValidationResponse(
                authorized=False,
                vehicle_registered=True,
                person_id=best_match["person"]["id"],
                person_name=best_match["person"]["full_name"],
                role_type=best_match["person"]["role_type"],
                vehicle_id=vehicle["id"],
                plate_text=normalized_plate,
                permit_status=best_match["permit"]["status"],
                face_match=False,
                similarity=best_match["similarity"],
                template_id=best_match["profile"]["template_id"],
                provider=best_match["comparison"].get("provider"),
                message="Face verification failed for the authorized member",
                warnings=(best_match["comparison"].get("warnings", []) + warnings),
            )

        return MemberAccessValidationResponse(
            authorized=False,
            vehicle_registered=True,
            vehicle_id=vehicle["id"],
            plate_text=normalized_plate,
            permit_status="EXPIRED" if permit_failure else None,
            message="Permission is not valid" if permit_failure else "No authorized member with valid permit and enrolled face was found",
            warnings=warnings,
        )
