"""
Test cases for GUI main module functionality.
"""

import os
import sys
import unittest

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestGUIMainLaunchKwargs(unittest.TestCase):
    """Test cases for _build_launch_kwargs functionality in gui.gui module."""

    def test_build_launch_kwargs_with_both_params(self):
        """Test _build_launch_kwargs with both host and port."""
        from model_sentinel.gui.gui import _build_launch_kwargs

        result = _build_launch_kwargs(host="0.0.0.0", port=8080)
        expected = {"server_name": "0.0.0.0", "server_port": 8080}
        self.assertEqual(result, expected)

    def test_build_launch_kwargs_with_host_only(self):
        """Test _build_launch_kwargs with host only."""
        from model_sentinel.gui.gui import _build_launch_kwargs

        result = _build_launch_kwargs(host="0.0.0.0", port=None)
        expected = {"server_name": "0.0.0.0"}
        self.assertEqual(result, expected)

    def test_build_launch_kwargs_with_port_only(self):
        """Test _build_launch_kwargs with port only."""
        from model_sentinel.gui.gui import _build_launch_kwargs

        result = _build_launch_kwargs(host=None, port=8080)
        expected = {"server_port": 8080}
        self.assertEqual(result, expected)

    def test_build_launch_kwargs_with_neither(self):
        """Test _build_launch_kwargs with neither host nor port."""
        from model_sentinel.gui.gui import _build_launch_kwargs

        result = _build_launch_kwargs(host=None, port=None)
        expected = {}
        self.assertEqual(result, expected)

    def test_build_launch_kwargs_defaults(self):
        """Test _build_launch_kwargs with default parameters."""
        from model_sentinel.gui.gui import _build_launch_kwargs

        result = _build_launch_kwargs()
        expected = {}
        self.assertEqual(result, expected)


class TestGUIMainDynamicURL(unittest.TestCase):
    """Test cases for dynamic URL generation in gui.gui module."""

    def test_dynamic_url_with_custom_port(self):
        """Test dynamic URL generation with custom port."""
        host, port = None, 8080
        server_host = host if host is not None else "127.0.0.1"

        if port is not None:
            url = f"📍 URL: http://{server_host}:{port}"
            expected = "📍 URL: http://127.0.0.1:8080"
            self.assertEqual(url, expected)

    def test_dynamic_url_with_custom_host_and_port(self):
        """Test dynamic URL generation with custom host and port."""
        host, port = "0.0.0.0", 7860
        server_host = host if host is not None else "127.0.0.1"

        if port is not None:
            url = f"📍 URL: http://{server_host}:{port}"
            expected = "📍 URL: http://0.0.0.0:7860"
            self.assertEqual(url, expected)

    def test_url_fallback_message(self):
        """Test URL fallback message when port is None."""
        port = None

        if port is not None:
            url = f"📍 URL: http://127.0.0.1:{port}"
        else:
            url = "📍 URL: Check terminal output for Gradio server address"

        expected = "📍 URL: Check terminal output for Gradio server address"
        self.assertEqual(url, expected)


if __name__ == "__main__":
    unittest.main()
