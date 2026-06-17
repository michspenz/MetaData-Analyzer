from pathlib import Path
from analysis_utils import calculate_entropy, calculate_file_hashes


def test_hash_calculation(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world", encoding="utf-8")

    md5_hash, sha256_hash = calculate_file_hashes(sample)
    assert md5_hash == "5eb63bbbe01eeed093cb22bb8f5acdc3"
    assert sha256_hash == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_entropy_calculation(tmp_path: Path):
    sample = tmp_path / "random.bin"
    sample.write_bytes(bytes(range(256)))

    entropy = calculate_entropy(sample)
    assert isinstance(entropy, float)
    assert 0.0 <= entropy <= 8.0
