import os


def test_env_example_exists():
    project_root = os.path.dirname(os.path.dirname(__file__))
    env_example_path = os.path.join(project_root, ".env.example")
    assert os.path.isfile(env_example_path), ".env.example is missing"


def test_env_example_contains_required_vars():
    project_root = os.path.dirname(os.path.dirname(__file__))
    env_example_path = os.path.join(project_root, ".env.example")
    with open(env_example_path) as f:
        content = f.read()

    required_vars = [
        "SC2AI_LLM_API_KEY",
        "SC2AI_LLM_MODEL",
        "SC2AI_LLM_BASE_URL",
        "SC2AI_LLM_MAX_TOKENS",
        "SC2AI_LLM_REASONING_EFFORT",
        "SC2AI_LLM_TEMPERATURE",
    ]
    for var in required_vars:
        assert var in content, f"Missing variable: {var}"
