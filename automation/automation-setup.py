#!/usr/bin/env python3
import argparse
import asyncio
import hashlib
import os
import platform
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request as req
from functools import wraps
from getpass import getuser
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, List, Literal, Optional, ParamSpec, Type, TypeVar

F = TypeVar("F", bound=Callable)
P = ParamSpec("P")


def mock_decorator(func: Callable[P, F]) -> Callable[P, F]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> F:
        return func(*args, **kwargs)

    return wrapper


try:
    import appdirs
    import toml
    from prefect import flow, task
    from prefect.client.orchestration import get_client
    from prefect.client.schemas.filters import (
        DeploymentFilter,
        DeploymentFilterName,
    )
    from prefect.filesystems import LocalFileSystem

    bootstrap = False
except ImportError as error:
    print(f"[WARNING] Module not found: {error}")
    print("[WARNING] Boot strapping")
    bootstrap = True
    task = flow = mock_decorator


class BootstrapConda:
    """Install conda into the prefex location."""

    def call_from_bootstrap(self):
        """Call the script in a bootstrap env."""
        with tempfile.NamedTemporaryFile(suffix=".py") as temp_f:
            Path(temp_f.name).write_text(sys.stdin.read())
            cmd = [self.executable, temp_f.name]
            env = os.environ.copy()
            env.pop("_CALLED_FROM_BOOTSTRAP", None)
            subprocess.check_call(cmd, env=env)

    def __init__(
        self, prefix: Path, extra_pkgs: Optional[List[str]] = None
    ) -> None:
        extra_pkgs = extra_pkgs or []
        micromamba = prefix / "bin" / "micromamba"
        self.prefix = prefix
        pkgs = list(
            set(
                ["appdirs", "prefect", "caddy", "toml", "python=3.12", "git"]
                + extra_pkgs
            )
        )
        if not micromamba.is_file():
            self._setup_micromamba()
        conda_env = prefix / "conda"
        self.executable = str(prefix / "conda" / "bin" / "python")
        if not conda_env.is_dir():
            subprocess.check_call(
                [
                    f"{micromamba}",
                    "create",
                    "-y",
                    "-p",
                    f"{conda_env}",
                    "-c",
                    "conda-forge",
                    "--override-channels",
                ]
                + pkgs
            )
            subprocess.check_call([self.executable, "-m", "ensurepip"])

    def _setup_micromamba(self):
        system = platform.system().lower()
        plt = platform.machine()
        target = self.prefix / "bin" / "micromamba"
        if system != "linux":
            raise SystemExit("Only Linux based deployment is supported.")
        if plt.startswith("x86"):
            plt = "64"
        with NamedTemporaryFile(suffix=".tar") as temp_f:
            self._url_retrieve(
                f"https://micro.mamba.pm/api/micromamba/linux-{plt}/latest",
                temp_f.name,
            )
            with tarfile.open(temp_f.name, mode="r:bz2") as tar:
                member = tar.getmember("bin/micromamba")
                print("🔧 Extracting: bin/micromamba")
                tar.extract(member, path=str(self.prefix))
        target.chmod(0o755)

    def _url_retrieve(self, conda_url: str, target: str) -> None:
        print("Retrieving conda install script: {}".format(conda_url))
        req.urlretrieve(
            str(conda_url),
            filename=target,
        )


__version__ = "0.1.0"
SCRIPT_URL = "https://example.org/freva_setup.py"  # <- replace with real URL
SCRIPT_CHECKSUM = "REPLACE_WITH_ACTUAL_SHA256"

Steps = Literal["core", "freva-rest", "db", "web"]


def dump_cfg(paths: List[Path]) -> None:

    projects = {}
    cfg_file = Path(__file__).parent / ".freva-automation.toml"
    for path in paths:
        config = toml.load(path)
        project_name = config.get("project_name", "")
        if project_name:
            projects[project_name] = str(path)
    cfg_file.write_text(toml.dumps(projects))


def project_type() -> Type:

    try:
        import toml
    except ImportError:
        return Literal["freva"]
    cfg_file = Path(__file__).parent / ".freva-automation.toml"
    projects = list(toml.load(cfg_file).keys())
    return Literal[*projects]


@task
def update_deployment_software():
    subprocess.check_output(
        [sys.executable, "-m", "pip", "install", "-U", "freva-deployment"]
    )


@task
def run_deployment(
    config_file: Path,
    steps: List[Steps],
    gen_certs: bool = False,
):
    steps = steps or ["auto"]
    if "all" in steps:
        cmd = ["deploy", "cmd", "-c", str(config_file)]
    else:
        cmd = ["deploy-freva", "cmd", "-s", *steps, "-c", str(config_file)]
    if gen_certs:
        cmd.append("-g")
    subprocess.run(cmd, check=True)


@flow
def freva_deployment_flow(
    project: project_type(),
    steps: Optional[List[Steps]] = None,
    gen_certs: bool = False,
):
    """
    Apply the freva deployment for a Project.

    Args:
        project: The freva project that should be deployed.
        steps: The steps that should be run.
        gen_certs: Auto generate self signed keys.
    """
    update_deployment_software()
    steps = steps or ["auto"]
    run_deployment(project, steps, gen_certs)


def get_user_config_dir(appname: str) -> Path:
    if sys.platform.startswith("win"):
        base = os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    cfg_dir = Path(base) / appname
    cfg_dir.mkdir(exist_ok=True, parents=True)
    return cfg_dir


class PrefectServer:
    """Start the prefect server."""

    def __init__(self, log_dir: Path) -> None:

        self.caddy_bin = shutil.which(
            "caddy", path=str(Path(sys.executable).parent)
        )
        if not self.caddy_bin:
            raise SystemExit("Caddy bin not found.")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            self.port = s.getsockname()[1]
        self.prefect_api_url = f"http://127.0.0.1:{self.port}/api"

        log_dir.mkdir(exist_ok=True, parents=True)

        self.caddy_dir = Path(tempfile.mkdtemp(prefix="caddy-config-"))
        self.log_dir = log_dir
        self.server_log = (log_dir / "prefect-server.log").open("w")
        self.agent_log = (log_dir / "prefect-agent.log").open("w")
        self.caddy_log = (log_dir / "caddy.log").open("w")

    def linger(self) -> None:
        """Wait unitl the server gets terminated."""
        try:
            while True:
                server_status = self.server.poll()
                agent_status = self.agent.poll()
                if server_status is not None or agent_status is not None:
                    break
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            pass
        self.server.terminate()
        self.agent.terminate()
        self.server_log.close()
        self.agent_log.close()

    def prep_server(
        self, script_path: Path, user_var: Optional[str] = None
    ) -> None:
        """Perpare the server startup."""
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "freva-deployment"]
        )
        from freva_deployment.utils import config_file

        if user_var:
            config_dir = Path(appdirs.user_config_dir("freva")) / "deployment"
            config_dir.mkdir(exist_ok=True, parents=True)
            config = {"general": {}, "variables": {"USER": user_var}}
            config_file.write_text(toml.dumps(config))

        if not script_path.is_dir():
            print("[WARNING] Script path is not a directory.")
            return
        for path in script_path.glob("*.sh"):
            try:
                subprocess.run(
                    str(path.absolute()),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
            except subprocess.CalledProcessError as error:
                print(f"[WARNING] Failed to execute {path}: {error.stderr}")

    def start_caddy(
        self,
        port: int = 8443,
        cert_file: Optional[Path] = None,
        key_file: Optional[Path] = None,
    ) -> None:
        """Create and launch Caddy reverse proxy with basic auth."""
        username = os.getenv("FREVA_AUTOMATION_USERNAME")
        password = os.getenv("FREVA_AUTOMATION_PASSWORD")
        if not username or not password:
            raise SystemExit(
                "FREVA_AUTOMATION_USERNAME and FREVA_AUTOMATION_PASSWORD must be set"
            )
        if cert_file is None or key_file is None:
            keys = "internal"
        else:
            keys = f"{cert_file} {key_file}"
        # Generate bcrypt hash
        hashed_password = subprocess.check_output(
            [self.caddy_bin, "hash-password", "--plaintext", password], text=True
        ).strip()
        # Create temp dir for Caddy config
        caddyfile = self.caddy_dir / "Caddyfile"
        caddyfile.write_text(
            f"""
    http://localhost:{port} {{
        reverse_proxy 127.0.0.1:{self.port}
        tls {keys}
        basicauth / {{
        {username} {hashed_password}
    }}
}}
"""
        )
        self.caddy = subprocess.Popen(
            [
                self.caddy_bin,
                "run",
                "--config",
                str(caddyfile),
                "--adapter",
                "caddyfile",
            ],
            stdout=self.caddy_log,
            stderr=self.caddy_log,
        )
        print(
            "[INFO] Reverse proxy started visit: "
            f"https://{socket.gethostname()}:{port}"
        )

    def stop_server(self) -> None:
        """Stop all services."""
        self.server.terminate()
        self.server.terminate()
        for attr in ("server", "agent", "caddy"):
            proc = getattr(self, attr, None)
            if proc:
                proc.terminate()

        self.server_log.close()
        self.agent_log.close()
        self.caddy_log.close()

    def start_prefect(self) -> None:
        """Start the prefect server."""
        env = os.environ.copy()
        env["PREFECT_API_URL"] = self.prefect_api_url
        subprocess.check_call(
            [sys.executable, "-m", "prefect", "server", "stop"], env=env
        )
        print("[INFO] Starting Prefect server...")
        self.server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "prefect",
                "server",
                "start",
                "--port",
                f"{self.port}",
                "--host",
                "127.0.0.1",
            ],
            stdout=self.server_log,
            stderr=self.server_log,
            env=env,
        )
        time.sleep(10)
        print("[INFO] Starting Prefect agent...")
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "prefect",
                "work-pool",
                "create",
                "--overwrite",
                "--type",
                "process",
                "default-agent-pool",
            ],
            env=env,
        )
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "prefect",
                "block",
                "register",
                "-m",
                "prefect.filesystems",
            ],
            env=env,
        )
        self.agent = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "prefect",
                "worker",
                "start",
                "--pool",
                "default-agent-pool",
            ],
            env=env,
            stdout=self.agent_log,
            stderr=self.agent_log,
        )
        time.sleep(5)
        print(f"[INFO] Prefect web app started at: http://localhost:{self.port}")


# --- Functional helpers ---
def load_env_configs() -> List[Path]:
    env_var = "FREVA_DEPLOYMENT_CONFIG"
    return [
        Path(f.strip()) for f in os.getenv(env_var, "").split(",") if f.strip()
    ]


def write_config(config: dict, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as stream:
        toml.dump(config, stream)


def merge_config_files(default_path: Path, env_configs: List[Path]) -> List[Path]:
    try:
        config = toml.load(default_path)
    except FileNotFoundError:
        config = {}
    config.setdefault("configs", [])
    for cfg in env_configs:
        if cfg not in config["configs"]:
            config["configs"].append(str(cfg))
    write_config(config, default_path)
    return [f for f in map(Path, config["configs"]) if f.is_file()]


async def deployment_exists(name: str) -> bool:
    async with get_client() as client:
        deployments = await client.read_deployments(
            deployment_filter=DeploymentFilter(
                name=DeploymentFilterName(any_=[name])
            )
        )
        return len(deployments) > 0


def register_prefect_deployment(
    config_files: List[str],
    cron: Optional[str],
    name: str = "freva-deployment-instance",
) -> None:
    basepath = Path(__file__).parent.absolute()

    LocalFileSystem(
        basepath=str(basepath),
    ).save(name="freva-local", overwrite=True)
    LocalFileSystem.load("freva-local")

    dump_cfg(config_files)
    this_file = Path(__file__).name
    exists = asyncio.run(deployment_exists(name))
    if not exists:
        freva_deployment_flow.from_source(
            source=Path(__file__).parent,
            entrypoint=f"{this_file}:freva_deployment_flow",
        ).deploy(
            name=name,
            tags=["Deployment"],
            cron=cron,
            work_pool_name="default-agent-pool",
        )
    else:
        print(f"[INFO] Deployment '{name}' already exists. Skipping.")


# --- Self-update & checksum logic ---
def self_update(script_url: str, destination: Path):

    print(f"[INFO] Downloading latest script from: {script_url}")
    with req.urlopen(script_url) as response:
        content = response.read()
        destination.write_bytes(content)
    print(f"[INFO] Script updated at: {destination}")
    os.chmod(destination, 0o755)


def calculate_checksum(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# --- CLI
def main():
    parser = argparse.ArgumentParser(
        description="Prepare Freva config and register Prefect.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--prefix",
        "-p",
        help="The path where the automation should be deployed to.",
        type=Path,
        default=Path(
            os.getenv("FREVA_AUTOMATION_PREFIX_DIR") or Path(__file__).parent
        ),
    )
    parser.add_argument(
        "--config",
        "-c",
        nargs="*",
        help="Path(s) to the deployment files.",
        default=load_env_configs(),
    )
    parser.add_argument(
        "--version", action="store_true", help="Show script version and exit"
    )
    parser.add_argument(
        "--self-update",
        action="store_true",
        help="Fetch and replace script with latest version",
    )
    parser.add_argument(
        "--verify-checksum",
        action="store_true",
        help="Verify SHA256 checksum of script",
    )
    parser.add_argument(
        "-d",
        "--defaults",
        type=Path,
        default=os.getenv("FREVA_AUTOMATION_CONFIG")
        or os.path.join(
            get_user_config_dir("freva"), "deployment", "automation.toml"
        ),
        help="Path to the default TOML config file",
    )
    parser.add_argument(
        "--cron", type=str, default=None, help="Cron schedule (e.g. '0 3 * * *')"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=os.getenv("FREVA_AUTOMATION_SERVER_PORT", "4200"),
        help="Set the port to run the server.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=os.getenv("FREVA_AUTOMATION_LOG_DIR", "~/.cache/log"),
        help="Set the log dir for the automation service.",
    )
    parser.add_argument(
        "--extra-pkg",
        type=str,
        default=os.getenv("FREVA_AUTOMATION_EXTRA_PGKS") or None,
        help="Extra conda-forge packages that need to be installed. "
        "',' separated.",
    )
    parser.add_argument(
        "--script-directory",
        type=Path,
        default=os.getenv("FREVA_AUTOMATION_SCRIPT_DIR", "."),
        help="The direcotry that contains any pre-processing scripts "
        "that should be executed before launching the automation "
        "server.",
    )
    parser.add_argument(
        "--user",
        type=str,
        default=getuser(),
        help="If the deployment config file defines the `USER` variable. "
        "you can set the value of this variable here.",
    )
    parser.add_argument(
        "--cert-file",
        type=Path,
        default=os.getenv("FREVA_AUTOMATION_CERT_FILE") or None,
        help="Path to the web server certificate file.",
    )
    parser.add_argument(
        "--key-file",
        type=Path,
        default=os.getenv("FREVA_AUTOMATION_KEY_FILE") or None,
        help="Path to the web server private key file.",
    )

    args = parser.parse_args()
    port = int(args.port)
    script_path = Path(__file__).resolve()
    extra_pkgs = [
        pkg.strip() for pkg in (args.extra_pkg or "").split(",") if pkg.strip()
    ]
    if bootstrap or not (args.prefix / "conda" / "bin" / "prefect").is_file():
        b = BootstrapConda(args.prefix, extra_pkgs)
        print(sys._called_from_bootstrap)
        try:
            if not os.environ.get("_CALLED_FROM_BOOTSTRAP") :
                cmd = [b.executable] + list(sys.argv)
                subprocess.check_call(cmd)
            else:
                b.call_from_bootstrap()
        except subprocess.CalledProcessError:
            raise SystemExit(1)
        sys.exit(0)

    if args.version:
        print(f"freva_setup.py version {__version__}")
        return

    if args.verify_checksum:
        actual = calculate_checksum(script_path)
        expected = SCRIPT_CHECKSUM.lower()
        print(f"[INFO] SHA256: {actual}")
        if actual == expected:
            print("[INFO] Checksum verified.")
            return
        else:
            raise SystemExit("[ERROR] Checksum mismatch!")

    if args.self_update:
        self_update(SCRIPT_URL, script_path)
        sys.exit(0)

    if not args.defaults:
        parser.error("the following arguments are required: --defaults")

    # Main execution
    configs = args.config
    merged = merge_config_files(args.defaults, configs)
    if not merged:
        print("[WARNING]: no config files found.")
        return
    log_dir = Path(args.log_dir).expanduser().absolute()
    try:

        ps = PrefectServer(log_dir)
        ps.prep_server(args.script_directory.expanduser(), args.user)
        ps.start_prefect()
        register_prefect_deployment(
            config_files=merged,
            cron=args.cron,
        )
        ps.start_caddy(port, args.cert_file, args.key_file)
        ps.linger()
    finally:
        ps.stop_server()


if __name__ == "__main__":
    main()
