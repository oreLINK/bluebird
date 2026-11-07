"""Météo-France avalanche bulletins: parsing of the BRA XML.

``fixtures/meteofrance_bra_66.xml`` is a real answer of the API (Haute-Bigorre,
issued on 2026-11-07); the split cases follow the examples of the Météo-France
"Descriptif technique des informations du bulletin avalanche".
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from bluebird_pipeline.bronze import BronzeBatch, BronzeRecord
from bluebird_pipeline.config import Config
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.silver import TRANSFORMERS
from bluebird_pipeline.silver._avalanche import AVALANCHE_SCHEMA
from bluebird_pipeline.silver.transformer_meteofrance_bra import parse_bulletin
from bluebird_pipeline.storage import LocalStorage

REAL = (Path(__file__).parent / "fixtures" / "meteofrance_bra_66.xml").read_text(encoding="utf-8")


def bra(risk: str, *, number: int = 8) -> str:
    """A minimal bulletin with the given ``RISQUE`` attributes."""
    return (
        f'<BULLETINS_NEIGE_AVALANCHE TYPEBULLETIN="BRA" ID="{number}" MASSIF="Belledonne" '
        'DATEBULLETIN="2027-01-14T15:00:00" DATEVALIDITE="2027-01-15T18:00:00">'
        f"<CARTOUCHERISQUE><RISQUE {risk}/></CARTOUCHERISQUE></BULLETINS_NEIGE_AVALANCHE>"
    )


def test_a_real_bulletin_gives_its_day_and_the_trend_of_the_next() -> None:
    bulletin, trend = parse_bulletin(REAL)
    assert bulletin == {
        "massif_number": 66,
        "massif_name": "Haute-Bigorre",
        "issued_at": datetime(2026, 11, 7, 15, 0, tzinfo=UTC),  # 16:00 in Paris
        "valid_date": date(2026, 11, 8),
        "level_low": 1,
        "level_high": 1,
        "altitude_limit_m": None,
        "trend": False,
    }
    assert trend["valid_date"] == date(2026, 11, 9)
    assert (trend["level_low"], trend["level_high"], trend["trend"]) == (1, 1, True)


def test_an_elevation_split_keeps_both_levels_and_the_higher_over_the_day() -> None:
    # Descriptif example: below 2100 m limited (2), above considerable (3) going down to 2.
    (row, _) = parse_bulletin(
        bra(
            'RISQUE1="2" EVOLURISQUE1="" LOC1="&lt;2100" ALTITUDE="2100" RISQUE2="3" '
            'EVOLURISQUE2="2" LOC2="&gt;2100" RISQUEMAXI="3" RISQUEMAXIJ2="2" '
            'DATE_RISQUE_J2="2027-01-16T00:00:00"'
        )
    )
    assert (row["level_low"], row["level_high"], row["altitude_limit_m"]) == (2, 3, 2100)


def test_a_level_rising_during_the_day_counts() -> None:
    (row,) = parse_bulletin(bra('RISQUE1="2" EVOLURISQUE1="3" RISQUEMAXI="3"'))
    assert (row["level_low"], row["level_high"]) == (3, 3)


def test_a_geographic_split_keeps_the_higher_level() -> None:
    (row,) = parse_bulletin(
        bra('RISQUE1="2" LOC1="E" ALTITUDE="" RISQUE2="3" LOC2="O" RISQUEMAXI="3"')
    )
    assert (row["level_low"], row["level_high"], row["altitude_limit_m"]) == (3, 3, None)


@pytest.mark.parametrize("risk", ['RISQUE1=""', 'RISQUE1="9"', 'RISQUEMAXI="2"'])
def test_a_bulletin_without_a_valid_level_gives_nothing(risk: str) -> None:
    assert parse_bulletin(bra(risk)) == []


def test_records_without_bulletin_or_invalid_are_skipped(repo_config: Config, tmp_path) -> None:
    ctx = RunContext.create(
        repo_config, LocalStorage(tmp_path), now=datetime(2026, 11, 8, 5, 7, tzinfo=UTC)
    )
    source = next(s for s in repo_config.sources if s.id == "meteofrance_bra")

    def record(number: int, payload: str | None, status: int = 200) -> BronzeRecord:
        return BronzeRecord(
            source_id=source.id,
            url="https://public-api.meteofrance.fr/public/DPBRA/v1/massif/BRA",
            params={"id-massif": number, "format": "xml"},
            context={"massif_number": number},
            fetched_at=datetime(2026, 11, 8, 5, 7, tzinfo=UTC),
            status_code=status,
            payload=payload,
        )

    def batch(records: list[BronzeRecord]) -> BronzeBatch:
        return BronzeBatch(
            source_id=source.id, run_id=ctx.run_id, run_date=ctx.run_date, records=records
        )

    transformer = TRANSFORMERS.get("meteofrance_bra")(source)
    frame = transformer.transform(
        batch([record(66, REAL), record(65, None, 404), record(67, "<not xml")]), ctx
    )
    assert frame.schema == AVALANCHE_SCHEMA
    assert frame["massif_number"].to_list() == [66, 66]

    empty = transformer.transform(batch([record(66, None, 404)]), ctx)
    assert empty.is_empty() and empty.schema == AVALANCHE_SCHEMA
