from wilbito.pipelines.council import CouncilPipeline


def test_council_runs(tmp_path):
    diary = tmp_path / "diario"
    pipe = CouncilPipeline(str(diary))
    res = pipe.run("mejorar robustez", max_iter=2)
    assert isinstance(res, list) and len(res) == 1
    assert len(res[0]["iteraciones"]) == 2
