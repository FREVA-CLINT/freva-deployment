import os
from freva_deployment.cli import main_cli

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
    from pathlib import Path

    print(list(Path(path).rglob("*")))
    os.environ["ANSIBLE_COW_PATH"] = os.path.join(path, "cowsay")
    os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
    main_cli()
