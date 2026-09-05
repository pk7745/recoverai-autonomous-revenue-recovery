from data.synthetic_generator import generate_synthetic_dataset, run_benchmark_simulation

def test_synthetic_dataset_generation():
    dataset = generate_synthetic_dataset(1000)
    assert dataset["total_count"] == 1000
    assert len(dataset["transactions"]) == 1000
    assert dataset["transactions"][0]["amount"] > 0

def test_benchmark_simulation_metrics():
    benchmark = run_benchmark_simulation(1000)
    assert benchmark["dataset_size"] == 1000
    assert benchmark["recoverai_strategy"]["recovery_rate"] > benchmark["baseline_strategy"]["recovery_rate"]
    assert benchmark["wasteful_retries_prevented"] >= 0
    assert benchmark["additional_revenue_recovered"] > 0
