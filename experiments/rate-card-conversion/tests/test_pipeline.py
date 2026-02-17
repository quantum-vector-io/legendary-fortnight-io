import pandas as pd

from app.pipeline import convert_dataframe


def test_convert_dataframe_maps_and_validates_rows():
    df = pd.DataFrame(
        [
            {
                "Carrier": "CarrierA",
                "Origin": "Shanghai",
                "Destination": "Rotterdam",
                "Base Rate": "2500",
                "Fuel Surcharge %": "12%",
                "Valid From": "2025-01-01",
                "Valid To": "2025-12-31",
                "Transit Days": "28",
            },
            {
                "Carrier": "CarrierB",
                "Origin": "Busan",
                "Destination": "LA",
                "Base Rate": "-1",
            },
        ]
    )

    result = convert_dataframe(df)

    assert len(result.rows) == 1
    assert result.rejected_rows == 1
    assert result.rows[0].lane_origin == "Shanghai"
    assert result.rows[0].rate_value == 2500.0
    assert result.rows[0].surcharge_fuel_pct == 12.0


def test_convert_dataframe_flags_missing_required_fields():
    df = pd.DataFrame([{"Carrier": "X", "Foo": "bar"}])

    result = convert_dataframe(df)

    assert any("Missing required canonical field mapping: lane_origin" in w for w in result.warnings)
    assert any("Missing required canonical field mapping: lane_destination" in w for w in result.warnings)
