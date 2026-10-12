# {{name}}

A Python service: the package in `src/{{module}}/`, its tests in `tests/`.

    uv sync              # installs it, with the dev tools
    uv run pytest        # the tests
    codecrew check .     # every check the agents are held to
