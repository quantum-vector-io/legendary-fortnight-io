from io import BytesIO
import pandas as pd


class UnsupportedFormatError(ValueError):
    pass


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df.dropna(how="all")


def load_rate_card(file_name: str, file_content: bytes) -> pd.DataFrame:
    ext = file_name.lower().split(".")[-1]
    if ext in {"csv", "txt"}:
        return _normalize_dataframe(pd.read_csv(BytesIO(file_content)))
    if ext in {"xlsx", "xlsm", "xls"}:
        return _normalize_dataframe(pd.read_excel(BytesIO(file_content)))
    if ext == "pdf":
        try:
            import pdfplumber
        except ImportError as exc:
            raise UnsupportedFormatError("Install optional dependency: pdfplumber") from exc

        rows = []
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    rows.extend(table)
        if not rows:
            raise UnsupportedFormatError("PDF did not contain an extractable table")
        header, *body = rows
        return _normalize_dataframe(pd.DataFrame(body, columns=header))

    raise UnsupportedFormatError(f"Unsupported format: .{ext}")
