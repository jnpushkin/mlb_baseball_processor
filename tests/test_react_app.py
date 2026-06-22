import unittest

from baseball_processor.website.react_app import ReactComponents
from baseball_processor.website.templates import HTMLTemplate


class ReactAppTests(unittest.TestCase):
    def test_app_code_starts_with_shared_react_bindings(self):
        code = ReactComponents.get_app_code()

        self.assertTrue(code.startswith("const { useState"))

    def test_template_pins_babel_standalone_to_classic_runtime_version(self):
        html = HTMLTemplate.create_full_page({})

        self.assertIn("https://unpkg.com/@babel/standalone@7.28.5/babel.min.js", html)
        self.assertNotIn("https://unpkg.com/@babel/standalone/babel.min.js", html)


if __name__ == "__main__":
    unittest.main()
