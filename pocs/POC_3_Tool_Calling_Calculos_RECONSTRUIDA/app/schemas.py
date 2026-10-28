from datetime import date, time

from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="Mensaje enviado al asistente",
    )


class ChatResponse(BaseModel):
    response: str


class ClaimsOccurrence(BaseModel):
    loss_dt: date | None = Field(
        default=None,
        description="ACORD LossDt. Fecha del siniestro.",
    )
    loss_time: time | None = Field(
        default=None,
        description="ACORD LossTime. Hora del siniestro.",
    )
    loss_cause_cd: str | None = Field(
        default=None,
        description=(
            "ACORD LossCauseCd. Código de causa cuando pueda "
            "determinarse de forma fiable."
        ),
    )
    loss_cause_desc: str | None = Field(
        default=None,
        description="ACORD LossCauseDesc. Descripción de la causa.",
    )
    loss_desc: str | None = Field(
        default=None,
        description="ACORD LossDesc. Descripción resumida de lo ocurrido.",
    )
    loss_location_desc: str | None = Field(
        default=None,
        description="Descripción del lugar del siniestro.",
    )


class VehInfo(BaseModel):
    veh_identification_number: str | None = Field(
        default=None,
        description="ACORD VehIdentificationNumber. Número VIN.",
    )
    vehicle_plate: str | None = Field(
        default=None,
        description="Matrícula o patente del vehículo.",
    )
    manufacturer: str | None = Field(
        default=None,
        description="Fabricante del vehículo.",
    )
    model: str | None = Field(
        default=None,
        description="Modelo del vehículo.",
    )
    model_year: int | None = Field(
        default=None,
        description="Año del vehículo.",
    )


class ClaimsDriverInfo(BaseModel):
    full_name: str | None = Field(
        default=None,
        description="Nombre del conductor involucrado.",
    )
    driver_license_number: str | None = Field(
        default=None,
        description="Número de licencia del conductor.",
    )


class ClaimsPartyInfo(BaseModel):
    party_role: str | None = Field(
        default=None,
        description="Rol de la parte involucrada.",
    )
    full_name: str | None = Field(
        default=None,
        description="Nombre de la parte involucrada.",
    )
    vehicle_plate: str | None = Field(
        default=None,
        description="Matrícula o patente del vehículo de la parte.",
    )


class ClaimData(BaseModel):
    claim_number: str | None = Field(
        default=None,
        description="ACORD ClaimNumber.",
    )
    claim_type_cd: str | None = Field(
        default=None,
        description="ACORD ClaimTypeCd.",
    )
    claim_status_cd: str | None = Field(
        default=None,
        description="ACORD ClaimStatusCd.",
    )
    policy_number: str | None = Field(
        default=None,
        description="ACORD PolicyNumber.",
    )
    claims_occurrence: ClaimsOccurrence = Field(
        default_factory=ClaimsOccurrence,
    )
    veh_info: VehInfo | None = None
    claims_driver_info: ClaimsDriverInfo | None = None
    claims_party_info: list[ClaimsPartyInfo] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_extracted_information(self):
        occurrence = self.claims_occurrence

        has_occurrence = any(
            [
                occurrence.loss_dt,
                occurrence.loss_time,
                occurrence.loss_cause_cd,
                occurrence.loss_cause_desc,
                occurrence.loss_desc,
                occurrence.loss_location_desc,
            ]
        )

        has_vehicle = (
            self.veh_info is not None
            and any(
                [
                    self.veh_info.veh_identification_number,
                    self.veh_info.vehicle_plate,
                    self.veh_info.manufacturer,
                    self.veh_info.model,
                    self.veh_info.model_year,
                ]
            )
        )

        has_data = any(
            [
                self.claim_number,
                self.claim_type_cd,
                self.claim_status_cd,
                self.policy_number,
                has_vehicle,
                self.claims_driver_info,
                self.claims_party_info,
                has_occurrence,
            ]
        )

        if not has_data:
            raise ValueError("No claim information could be extracted")

        return self


class ClaimExtractionRequest(BaseModel):
    description: str = Field(
        min_length=1,
        description="Descripción del siniestro en lenguaje natural.",
    )

from decimal import Decimal

class DeductibleCalculation(BaseModel):
    loss_amount: Decimal
    deductible_percentage: Decimal
    minimum_deductible: Decimal
    calculated_deductible: Decimal

class ReserveCalculation(BaseModel):
    estimated_loss_amount: Decimal
    deductible_amount: Decimal
    calculated_reserve: Decimal
