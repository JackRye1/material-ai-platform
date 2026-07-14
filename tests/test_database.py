from src.database.connection import Database
from src.database.dataset_repo import DatasetRepo
from src.models.dataset import ColumnRole, Dataset


def test_migration_idempotent(tmp_path):
    path = tmp_path / "test.db"
    db1 = Database(path)
    db1.close()
    db2 = Database(path)  # 2回目の起動でもエラーにならない
    row = db2.conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
    assert row["v"] == 1
    db2.close()


def test_dataset_save_load_roundtrip(tmp_path, sample_df):
    db = Database(tmp_path / "test.db")
    repo = DatasetRepo(db)
    ds = Dataset(name="実験データ", df=sample_df)
    ds.set_role("特性値", ColumnRole.TARGET)

    dataset_id = repo.save(ds)
    loaded = repo.load(dataset_id)

    assert loaded.name == "実験データ"
    assert loaded.n_rows == ds.n_rows
    assert loaded.roles["特性値"] == ColumnRole.TARGET
    assert repo.load_latest().name == "実験データ"
    db.close()
