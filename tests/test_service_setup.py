import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "setup",
    "start",
    "stop",
    "restart",
    "status",
    "logs",
)


class ServiceSetupTest(unittest.TestCase):
    def test_scripts_have_valid_bash_syntax_and_are_executable(self) -> None:
        script_paths = [PROJECT_ROOT / "scripts" / name for name in SCRIPTS]

        subprocess.run(
            ["bash", "-n", PROJECT_ROOT / "scripts" / "_common.sh", *script_paths],
            check=True,
        )
        for script_path in script_paths:
            self.assertTrue(os.access(script_path, os.X_OK), script_path)

    def test_unit_templates_do_not_assume_a_clone_location_or_user(self) -> None:
        systemd_directory = PROJECT_ROOT / "deploy" / "systemd"
        control = (systemd_directory / "workshop-control.service.in").read_text()
        ustreamer = (
            systemd_directory / "workshop-ustreamer.service.in"
        ).read_text()

        self.assertIn("User=@WORKSHOP_USER@", control)
        self.assertIn("WorkingDirectory=@WORKSHOP_ROOT@", control)
        self.assertIn("ExecStart=@WORKSHOP_PYTHON@", control)
        self.assertIn("User=@WORKSHOP_USER@", ustreamer)
        self.assertIn("--static=@WORKSHOP_ROOT@/public", ustreamer)
        self.assertNotIn("/home/pi/", control + ustreamer)

    def test_target_starts_both_project_services(self) -> None:
        target = (
            PROJECT_ROOT / "deploy" / "systemd" / "workshop.target"
        ).read_text()

        self.assertIn(
            "Requires=workshop-control.service workshop-ustreamer.service",
            target,
        )
        self.assertIn("Wants=pigpiod.service", target)

    def test_start_script_recovers_each_service(self) -> None:
        start_script = (PROJECT_ROOT / "scripts" / "start").read_text()

        for service in (
            "pigpiod.service",
            "workshop-control.service",
            "workshop-ustreamer.service",
        ):
            self.assertIn(service, start_script)

    @unittest.skipUnless(shutil.which("systemd-analyze"), "systemd is unavailable")
    def test_rendered_systemd_units_are_valid(self) -> None:
        systemd_directory = PROJECT_ROOT / "deploy" / "systemd"
        replacements = {
            "@WORKSHOP_ROOT@": str(PROJECT_ROOT),
            "@WORKSHOP_USER@": "root",
            "@WORKSHOP_PYTHON@": sys.executable,
            "@USTREAMER@": "/usr/bin/true",
        }

        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            unit_directory = Path(directory)
            for source_name, destination_name in (
                ("workshop-control.service.in", "workshop-control.service"),
                ("workshop-ustreamer.service.in", "workshop-ustreamer.service"),
            ):
                content = (systemd_directory / source_name).read_text()
                for placeholder, value in replacements.items():
                    content = content.replace(placeholder, value)
                destination = unit_directory / destination_name
                destination.write_text(content)
                destination.chmod(0o644)

            shutil.copy(
                systemd_directory / "workshop.target",
                unit_directory / "workshop.target",
            )
            (unit_directory / "workshop.target").chmod(0o644)
            pigpiod = unit_directory / "pigpiod.service"
            pigpiod.write_text(
                "[Service]\nExecStart=/usr/bin/true\n"
            )
            pigpiod.chmod(0o644)

            environment = os.environ.copy()
            environment["SYSTEMD_UNIT_PATH"] = os.pathsep.join(
                (
                    directory,
                    "/usr/local/lib/systemd/system",
                    "/usr/lib/systemd/system",
                    "/lib/systemd/system",
                )
            )
            subprocess.run(
                [
                    "systemd-analyze",
                    "verify",
                    "workshop.target",
                    "workshop-control.service",
                    "workshop-ustreamer.service",
                ],
                check=True,
                env=environment,
            )


if __name__ == "__main__":
    unittest.main()
