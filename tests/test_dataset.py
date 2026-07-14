from src.models.dataset import ColumnRole, Dataset


def test_infer_roles(sample_df):
    ds = Dataset(name="test", df=sample_df)
    assert ds.roles["サンプルID"] == ColumnRole.ID
    assert ds.roles["温度"] == ColumnRole.FEATURE
    assert ds.roles["備考"] == ColumnRole.META


def test_set_role_and_selectors(sample_df):
    ds = Dataset(name="test", df=sample_df)
    ds.set_role("特性値", ColumnRole.TARGET)
    assert ds.target_names == ["特性値"]
    assert "特性値" not in ds.feature_names
    assert ds.features().shape[1] == 2


def test_roles_roundtrip(sample_df):
    ds = Dataset(name="test", df=sample_df)
    ds.set_role("特性値", ColumnRole.TARGET)
    restored = Dataset.roles_from_dict(ds.roles_as_dict())
    assert restored == ds.roles
