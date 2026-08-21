from pathlib import Path
from evaluation.run_evaluation import EvaluationRunner

def test_full_evaluation_suite():
    runner = EvaluationRunner()
    base_dir = Path(__file__).resolve().parent.parent
    visible_file = base_dir / "evaluation" / "visible-cases.json"
    custom_file = base_dir / "evaluation" / "custom-cases.json"
    success = runner.run_all([visible_file, custom_file])
    assert success is True
