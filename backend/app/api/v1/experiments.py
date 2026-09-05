import app.core.path_setup  # Ensure sys.path includes project root
from fastapi import APIRouter, Query
from app.schemas.experiment import BenchmarkComparisonResponse
from data.synthetic_generator import run_benchmark_simulation

router = APIRouter(prefix="/experiments", tags=["Experiments & Benchmarks"])

# Cache the standard 10,000 transaction benchmark
_CACHED_BENCHMARK = run_benchmark_simulation(10000)

@router.get("/benchmark", response_model=BenchmarkComparisonResponse)
async def get_benchmark_comparison():
    return _CACHED_BENCHMARK

@router.post("/run", response_model=BenchmarkComparisonResponse)
async def run_benchmark(dataset_size: int = Query(10000, ge=100, le=50000)):
    global _CACHED_BENCHMARK
    _CACHED_BENCHMARK = run_benchmark_simulation(dataset_size)
    return _CACHED_BENCHMARK
