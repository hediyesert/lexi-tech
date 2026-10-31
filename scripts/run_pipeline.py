"""Pipeline'ı baştan sona çalıştırır: python scripts/run_pipeline.py

--from-step ile belirli bir adımdan başlanabilir. Adım sonuçları logs/ altına yazılır.
Pipeline sonunda otomatik kalite testleri çalışır.
"""
import argparse
import subprocess
import sys
from datetime import datetime

from common import path_of

STEPS = [
    "01_download.py",
    "02_extract.py",
    "02b_extract_legislation.py",
    "03_clean.py",
    "03b_clean_legislation.py",
    "04_deduplicate_exact.py",
    "05_build_domain_corpus.py",
    "06_filter_instruction.py",
    "07_build_instruction_set.py",
    "08_token_count.py",
    "09_statistics.py",
    "10_sample_quality_review.py",
    "11_quality_report.py",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-step", default=STEPS[0], help="Örn: 05_build_domain_corpus.py")
    arguments = parser.parse_args()

    log_dir = path_of("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log"

    with log_path.open("w", encoding="utf-8") as log:
        for step in STEPS[STEPS.index(arguments.from_step):]:
            started = datetime.now()
            print(f"[{started:%H:%M:%S}] {step}", flush=True)
            result = subprocess.run(
                [sys.executable, str(path_of("scripts", step))],
                cwd=path_of(),
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            if result.returncode != 0:
                sys.exit(f"Başarısız: {step}. Ayrıntı: {log_path}")
            print(f"  tamam ({datetime.now() - started})", flush=True)

        test = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q"],
            cwd=path_of(),
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    if test.returncode != 0:
        sys.exit(f"Testler başarısız. Ayrıntı: {log_path}")
    print("Pipeline ve testler başarılı. Log:", log_path)


if __name__ == "__main__":
    main()
