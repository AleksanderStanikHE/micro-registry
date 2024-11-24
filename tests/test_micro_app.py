import os
import subprocess
import sys
import unittest


class TestMicroApp(unittest.TestCase):

    def test_run_without_registry_directory(self):
        # Paths setup
        micro_app_path = os.path.join(os.path.dirname(__file__), "..", "micro_app.py")
        config_path = os.path.join(os.path.dirname(__file__), "test_config.yaml")
        test_module_path = os.path.join(os.path.dirname(__file__), "test_module.py")
        test_module_dir = os.path.dirname(test_module_path)

        # Create config file and test_module.py as before

        # Prepare environment variables
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [test_module_dir, env.get("PYTHONPATH", "")]
        )

        # Run the micro_app.py script with unbuffered output
        process = subprocess.Popen(
            [sys.executable, "-u", micro_app_path, "-c", config_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=os.path.dirname(micro_app_path),
        )

        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        output = stdout.decode()
        errors = stderr.decode()

        # Print process return code
        print(f"Process return code: {process.returncode}")

        # Output errors for debugging
        print(f"STDOUT:\n{output}")
        print(f"STDERR:\n{errors}")

        # # Clean up
        # os.remove(config_path)
        # os.remove(test_module_path)

        # Check that the application started without errors
        self.assertIn("Application is running. Press Ctrl+C to stop.", output)
        self.assertEqual(errors, "")


if __name__ == "__main__":
    unittest.main()
