import os
from freva_deployment.cli import main_cli

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
    for exe in ("cowsay", "cowsay.exe"):
        cow_exe = os.path.join(path, exe)
        if os.path.isfile(cow_exe):
            os.environ["ANSIBLE_COW_PATH"] = os.path.join(exe)
            break
    os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
    main_cli()
