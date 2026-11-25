from typing import List, Optional
from pydantic import BaseModel, field_validator, model_validator


class SpikeSettings(BaseModel):
    species: List[str] = []
    normaliser: Optional[str] = None

    @model_validator(mode="after")
    def normaliser_is_spike_species(self):
        if self.normaliser and self.normaliser not in self.species:
            raise ValueError("normaliser must be one of the spike species")
        return self


class SpikeSpeciesAdd(BaseModel):
    species: str

    @field_validator("species")
    @classmethod
    def not_blank(cls, species: str) -> str:
        species = species.strip()
        if not species:
            raise ValueError("species must not be blank")
        return species


class SpikeSpeciesRemove(BaseModel):
    species: List[str]


class SpikeNormaliser(BaseModel):
    normaliser: Optional[str] = None
