import pytest

from src.database.connection import Database
from src.database.model_registry import ModelRegistry
from src.models.dataset import ColumnRole, Dataset
from src.services.prediction.base_predictor import available_predictors, create_predictor
from src.services.prediction.prediction_service import PredictionService


@pytest.fixture
def service(tmp_path):
    db = Database(tmp_path / "test.db")
    yield PredictionService(ModelRegistry(db), tmp_path / "models")
    db.close()


@pytest.fixture
def dataset(sample_df):
    ds = Dataset(name="test", df=sample_df)
    ds.set_role("特性値", ColumnRole.TARGET)
    return ds


def test_xgboost_registered():
    assert "xgboost" in available_predictors()


def test_train_and_metrics(service, dataset):
    result = service.train(dataset, "特性値", ["温度", "圧力"])
    assert result.metrics["r2"] > 0.8
    assert set(result.importance.keys()) == {"温度", "圧力"}
    assert len(result.y_test) == len(result.y_pred)


def test_train_rejects_target_in_features(service, dataset):
    with pytest.raises(ValueError):
        service.train(dataset, "特性値", ["温度", "特性値"])


def test_save_and_load_roundtrip(service, dataset):
    result = service.train(dataset, "特性値", ["温度", "圧力"])
    info = service.save_model(result, "テストモデル")
    assert info.id is not None

    loaded_info, predictor = service.load_model(info.id)
    assert loaded_info.name == "テストモデル"
    pred = predictor.predict(dataset.df[["温度", "圧力"]])
    assert len(pred) == dataset.n_rows


def test_predictor_save_load_consistency(tmp_path, dataset):
    predictor = create_predictor("xgboost", {"n_estimators": 50})
    X, y = dataset.df[["温度", "圧力"]], dataset.df["特性値"]
    predictor.fit(X, y)
    before = predictor.predict(X)

    path = tmp_path / "m.joblib"
    predictor.save(path)
    restored = type(predictor).load(path)
    after = restored.predict(X)
    assert (before == after).all()
