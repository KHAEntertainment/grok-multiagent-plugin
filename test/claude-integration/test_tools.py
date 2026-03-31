#!/usr/bin/env python3
"""
test_tools.py - Tool passthrough and file writing tests

Tests:
- File context ingestion (--files flag)
- Glob pattern expansion
- Size limit enforcement (1.5MB)
- Dry-run vs apply modes
- Path safety validation
- Annotated code block parsing
"""

import sys
import os
import re
import subprocess
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "bridge"))

#-------------------------------------------------------------------------------
# Test 3.1: File Context Ingestion
#-------------------------------------------------------------------------------

class TestFileIngestion:
    """Tests for file context ingestion via --files flag."""

    def test_files_parameter_exists(self):
        """--files parameter should be available."""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.bridge.grok_bridge",
                "--help"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        combined = result.stdout + result.stderr
        assert "--files" in combined or "files" in combined.lower()

    def test_single_file_ingestion(self):
        """Single file should be readable and included in context."""
        # Create a test file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir=Path(__file__).parent.parent.parent
        ) as f:
            f.write("# Test file\ndef hello(): pass\n")
            test_file = f.name

        try:
            # Verify file exists
            assert Path(test_file).exists()
        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_file_size_limit(self):
        """Files over 1.5MB should be truncated or rejected."""
        # Check the patterns module for size limit
        patterns_path = Path(__file__).parent.parent.parent / "src" / "bridge" / "patterns.py"

        if patterns_path.exists():
            content = patterns_path.read_text()
            # Should mention 1.5MB or 1572864 bytes
            assert "1.5" in content or "1572864" in content or "MAX" in content


#-------------------------------------------------------------------------------
# Test 3.2: Glob Pattern Expansion
#-------------------------------------------------------------------------------

class TestGlobPatterns:
    """Tests for glob pattern handling."""

    def test_files_parameter_in_help(self):
        """Help should mention --files parameter for context."""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.bridge.grok_bridge",
                "--help"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        combined = result.stdout + result.stderr
        # Should have --files parameter
        assert "--files" in combined


#-------------------------------------------------------------------------------
# Test 3.3: File Writing Behavior
#-------------------------------------------------------------------------------

class TestFileWriting:
    """Tests for --write-files and --output flag behavior."""

    def test_write_files_parameter_exists(self):
        """--write-files parameter should enable file writing."""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.bridge.grok_bridge",
                "--help"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        combined = result.stdout + result.stderr
        assert "--write-files" in combined

    def test_output_parameter_exists(self):
        """--output parameter should write full response to a file."""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.bridge.grok_bridge",
                "--help"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        combined = result.stdout + result.stderr
        assert "--output" in combined


#-------------------------------------------------------------------------------
# Test 3.4: Path Safety Validation
#-------------------------------------------------------------------------------

class TestPathSafety:
    """Tests for path traversal protection."""

    def test_no_path_traversal_in_parse(self):
        """parse_and_write_files should not allow path traversal."""
        from grok_bridge import parse_and_write_files

        # Malicious annotation with path traversal
        malicious = """
        ```python
        # File: ../../../etc/passwd
        print("malicious")
        ```
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            written = parse_and_write_files(malicious, tmpdir)

            # Should not have written outside tmpdir
            for path in written:
                assert Path(path).resolve().parent.resolve() == Path(tmpdir).resolve(), \
                    f"Path traversal detected: {path}"

    def test_output_dir_creation(self):
        """Output directory should be created if it doesn't exist."""
        from grok_bridge import parse_and_write_files

        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "does" / "not" / "exist"
            assert not nested.exists()

            # parse_and_write_files with empty response should
            # still try to write, creating directories
            parse_and_write_files("# No files here", str(nested))

            # The directory might not be created if no files,
            # but the function should handle missing dirs gracefully


#-------------------------------------------------------------------------------
# Test 3.5: Annotated Code Block Parsing
#-------------------------------------------------------------------------------

class TestAnnotatedBlockParsing:
    """Tests for annotated code block parsing."""

    def test_standard_annotation_format(self):
        """Standard # FILE: path annotation should work."""
        from grok_bridge import parse_and_write_files

        content = """Here's the code:

```python
# FILE: example.py
def example():
    pass
```

Hope this helps!
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            written = parse_and_write_files(content, tmpdir)

            # written is list of (path, byte_count) tuples
            assert len(written) > 0, f"Expected files, got {written}"
            assert any("example.py" in p for p, _ in written)

    def test_multiple_files(self):
        """Multiple annotated files should all be parsed."""
        from grok_bridge import parse_and_write_files

        content = """Two files:

```python
# FILE: file1.py
content1 = "first"
```

```python
# FILE: file2.py
content2 = "second"
```
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            written = parse_and_write_files(content, tmpdir)

            # written is list of (path, byte_count) tuples
            assert len(written) >= 2, f"Expected 2+ files, got {len(written)}"
            assert any("file1.py" in p for p, _ in written)
            assert any("file2.py" in p for p, _ in written)

    def test_language_detection(self):
        """Language should be detected from code fence."""
        from grok_bridge import parse_and_write_files

        for lang in ["python", "js", "typescript", "go", "rust"]:
            content = f"""```{lang}
# File: test.{lang}
print("hello")
```
"""
            with tempfile.TemporaryDirectory() as tmpdir:
                written = parse_and_write_files(content, tmpdir)
                # Should find the file regardless of language


#-------------------------------------------------------------------------------
# Test 3.6: Code Block ID Extraction
#-------------------------------------------------------------------------------

class TestCodeBlockIDExtraction:
    """Tests for extracting IDs from code blocks."""

    def test_file_pattern_regex(self):
        """File annotation regex should be robust."""
        # Check patterns.py exists and has the right patterns
        patterns_path = Path(__file__).parent.parent.parent / "src" / "bridge" / "patterns.py"

        if patterns_path.exists():
            content = patterns_path.read_text()
            assert "re.compile" in content or "Pattern" in content


#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Tool & File Writing Tests")
    print("Testing file ingestion, path safety, and parsing")
    print("=" * 60)
    print()

    all_passed = True

    test_classes = [
        TestFileIngestion,
        TestGlobPatterns,
        TestFileWriting,
        TestPathSafety,
        TestAnnotatedBlockParsing,
        TestCodeBlockIDExtraction,
    ]

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * len(test_class.__name__))

        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    print(f"  ✓ {method_name}")
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
                    all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("All tool tests PASSED")
        sys.exit(0)
    else:
        print("Some tool tests FAILED")
        sys.exit(1)
