"""Entity schema — represents a resolved company/organization."""

from pydantic import BaseModel


class Entity(BaseModel):
    """A resolved entity (company) with canonical identifiers."""

    ticker: str
    cik: str | None = None
    name: str
    sic_code: str | None = None
