from pathlib import Path
import pandas as pd
from .models import GroupRow

def load_groups(csv_path: str | Path) -> list[GroupRow]:
    df = pd.read_csv(csv_path)
    records = df.to_dict(orient="records")
    return [GroupRow(**record) for record in records]