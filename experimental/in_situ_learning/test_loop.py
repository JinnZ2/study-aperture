"""Pin the toy's printed results. CC0, stdlib. Run: python3 -m unittest test_loop.py"""
import os, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))


class Pinned(unittest.TestCase):
    def test_selftest(self):
        r = subprocess.run([sys.executable, "loop.py", "selftest"], cwd=HERE, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_physics_side(self):
        r = subprocess.run([sys.executable, "physics_side.py", "selftest"], cwd=HERE, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_sample_regenerates(self):
        r = subprocess.run([sys.executable, "loop.py"], cwd=HERE, capture_output=True, text=True)
        with open(os.path.join(HERE, "samples", "run.txt")) as f:
            self.assertEqual(r.stdout, f.read(),
                             "loop.py output changed; if deliberate, regenerate samples/run.txt "
                             "and update RESULTS.md")


if __name__ == "__main__":
    unittest.main()
