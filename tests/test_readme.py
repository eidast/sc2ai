from pathlib import Path


def test_readme_is_spanish_first_then_english():
    readme = Path("README.md").read_text(encoding="utf-8")

    spanish_index = readme.index("## Español")
    english_index = readme.index("## English")

    assert spanish_index < english_index
