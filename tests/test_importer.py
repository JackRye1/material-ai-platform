import pytest

from src.services.data.importer import DataImporter
from src.services.data.validator import DataValidator
from src.models.dataset import Dataset


def test_load_csv(tmp_path, sample_df):
    path = tmp_path / "sample.csv"
    sample_df.to_csv(path, index=False, encoding="utf-8-sig")
    ds = DataImporter().load(str(path))
    assert ds.name == "sample"
    assert ds.n_rows == len(sample_df)


def test_load_cp932_csv(tmp_path, sample_df):
    path = tmp_path / "sjis.csv"
    sample_df.to_csv(path, index=False, encoding="cp932")
    ds = DataImporter().load(str(path))
    assert "温度" in ds.df.columns


def test_load_excel(tmp_path, sample_df):
    path = tmp_path / "sample.xlsx"
    sample_df.to_excel(path, index=False)
    ds = DataImporter().load(str(path))
    assert ds.n_rows == len(sample_df)


def test_unsupported_extension(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("a,b\n1,2")
    with pytest.raises(ValueError):
        DataImporter().load(str(path))


def test_validator(sample_df):
    df = sample_df.copy()
    df.loc[0, "温度"] = None
    result = DataValidator().validate(Dataset(name="t", df=df))
    assert result.missing_by_column == {"温度": 1}
    assert result.completeness < 100
