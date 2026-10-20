from typing import List, Optional
from pydantic import BaseModel, model_validator


class SpikeSettings(BaseModel):
    species: List[str] = []
    normaliser: Optional[str] = None

    @model_validator(mode="after")
    def normaliser_is_spike_species(self):
        if self.normaliser and self.normaliser not in self.species:
            raise ValueError("normaliser must be one of the spike species")
        return self
