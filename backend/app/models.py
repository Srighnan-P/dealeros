from datetime import date
from decimal import Decimal

from sqlalchemy import (
    String,
    Date,
    Numeric,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Location(Base):
    __tablename__ = "locations"

    location_id: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )

    org_id: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )

    location_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )


class SystemARecord(Base):
    __tablename__ = "system_a_records"

    record_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )

    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.location_id"),
        nullable=False
    )

    event_date: Mapped[date] = mapped_column(Date)

    category_code: Mapped[str] = mapped_column(String(30))

    actor_id: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )

    base_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    adjustment: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    state: Mapped[str] = mapped_column(String(20))


class SystemBEntry(Base):
    __tablename__ = "system_b_entries"

    entry_id: Mapped[str] = mapped_column(
        String(40), primary_key=True
    )

    record_ref_raw: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    record_ref: Mapped[str | None] = mapped_column(
        String(30), nullable=True, index=True
    )

    location_id: Mapped[str] = mapped_column(
        ForeignKey("locations.location_id"),
        nullable=False
    )

    recorded_on: Mapped[date] = mapped_column(Date)

    value_raw: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    value: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )

    label: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )