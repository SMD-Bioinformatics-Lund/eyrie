from typing import List, Optional
from pydantic import BaseModel, field_validator, model_validator


def strip_species(species: str) -> str:
    species = species.strip()
    if not species:
        raise ValueError("species must not be blank")
    return species


class SpikeSettings(BaseModel):
    species: List[str] = []
    normaliser: Optional[str] = None

    @field_validator("species")
    @classmethod
    def unique_species(cls, species: List[str]) -> List[str]:
        species = [strip_species(name) for name in species]
        if len({name.casefold() for name in species}) != len(species):
            raise ValueError("species must not be listed more than once, ignoring case")
        return species

    @model_validator(mode="after")
    def normaliser_is_spike_species(self):
        if self.normaliser:
            key = self.normaliser.strip().casefold()
            match = next((name for name in self.species if name.casefold() == key), None)
            if match is None:
                raise ValueError("normaliser must be one of the spike species")
            self.normaliser = match
        return self


class SpikeSpeciesAdd(BaseModel):
    species: str

    @field_validator("species")
    @classmethod
    def not_blank(cls, species: str) -> str:
        return strip_species(species)


class SpikeSpeciesRemove(BaseModel):
    species: List[str]


class SpikeNormaliser(BaseModel):
    normaliser: Optional[str] = None
