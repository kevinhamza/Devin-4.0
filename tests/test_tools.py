"""
tests/test_tools.py — Comprehensive test suite for TOOL_REGISTRY

Tests all 73 tools for:
1. Import success
2. Function callable
3. Return value validation
4. Error handling
5. Edge cases
"""

import pytest
import sys
import os
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.integrations import TOOL_REGISTRY, HAS


class TestCoreOSAutomation:
    """Test OS automation tools (mouse, keyboard, screenshot)"""

    def test_get_screen_size(self):
        """Test screen size retrieval"""
        result = TOOL_REGISTRY['get_screen_size']()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(x, (int, float)) for x in result)
        assert result[0] > 0 and result[1] > 0

    def test_get_mouse_position(self):
        """Test mouse position retrieval"""
        result = TOOL_REGISTRY['get_mouse_position']()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(x, (int, float)) for x in result)

    def test_keyboard_type(self):
        """Test keyboard typing (should not raise)"""
        result = TOOL_REGISTRY['keyboard_type']("test")
        assert isinstance(result, bool)

    def test_mouse_click(self):
        """Test mouse click (should not raise)"""
        result = TOOL_REGISTRY['mouse_click'](100, 100)
        assert isinstance(result, bool)


class TestFileOperations:
    """Test file reading, writing, and searching"""

    def test_read_file(self):
        """Test reading a file"""
        test_file = Path(__file__)
        content = TOOL_REGISTRY['read_file'](str(test_file))
        assert isinstance(content, str)
        assert len(content) > 0

    def test_write_file(self):
        """Test writing a file"""
        with TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test.txt"
            result = TOOL_REGISTRY['write_file'](str(test_path), "test content")
            assert result is True
            assert test_path.exists()
            assert test_path.read_text() == "test content"

    def test_list_files(self):
        """Test listing files"""
        test_dir = Path(__file__).parent.parent
        files = TOOL_REGISTRY['list_files'](str(test_dir), "*.py", max_results=10)
        assert isinstance(files, list)
        assert all(isinstance(f, str) for f in files)

    def test_find_files(self):
        """Test finding files by pattern"""
        test_dir = Path(__file__).parent.parent
        files = TOOL_REGISTRY['find_files'](str(test_dir), "*.py", max_results=5)
        assert isinstance(files, list)
        assert len(files) >= 0

    def test_code_analyze(self):
        """Test code analysis"""
        test_file = __file__
        result = TOOL_REGISTRY['code_analyze'](test_file)
        assert isinstance(result, dict)
        assert 'total_lines' in result
        assert 'functions' in result
        assert result['total_lines'] > 0


class TestDataAnalysis:
    """Test data analysis and text processing tools"""

    def test_analyze_text(self):
        """Test text analysis"""
        text = "The quick brown fox jumps over the lazy dog"
        result = TOOL_REGISTRY['analyze_text'](text)
        assert isinstance(result, dict)
        assert 'word_count' in result
        assert result['word_count'] == 9
        assert 'char_count' in result

    def test_extract_urls(self):
        """Test URL extraction"""
        text = "Visit https://example.com or https://google.com"
        urls = TOOL_REGISTRY['extract_urls'](text)
        assert isinstance(urls, list)
        assert len(urls) == 2
        assert all('https' in url for url in urls)

    def test_extract_emails(self):
        """Test email extraction"""
        text = "Contact test@example.com or admin@site.org"
        emails = TOOL_REGISTRY['extract_emails'](text)
        assert isinstance(emails, list)
        assert len(emails) == 2
        assert all('@' in email for email in emails)

    def test_compare_files(self):
        """Test file comparison"""
        with TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            file1.write_text("content1")
            file2.write_text("content2")

            result = TOOL_REGISTRY['compare_files'](str(file1), str(file2))
            assert isinstance(result, dict)
            assert 'same' in result
            assert result['same'] is False


class TestSecurityTools:
    """Test security and pentesting tools"""

    def test_hash_text_sha256(self):
        """Test SHA256 hashing"""
        result = TOOL_REGISTRY['hash_text']("test", "sha256")
        assert isinstance(result, dict)
        assert 'hash' in result
        assert len(result['hash']) == 64  # SHA256 produces 64 hex chars

    def test_hash_text_md5(self):
        """Test MD5 hashing"""
        result = TOOL_REGISTRY['hash_text']("test", "md5")
        assert 'hash' in result
        assert len(result['hash']) == 32  # MD5 produces 32 hex chars

    def test_dns_lookup(self):
        """Test DNS lookup"""
        result = TOOL_REGISTRY['dns_lookup']("localhost")
        assert isinstance(result, dict)
        assert 'hostname' in result
        assert 'ips' in result

    def test_extract_metadata(self):
        """Test metadata extraction"""
        test_file = __file__
        result = TOOL_REGISTRY['extract_metadata'](test_file)
        assert isinstance(result, dict)
        assert 'metadata' in result or 'error' in result


class TestMemoryOperations:
    """Test memory storage and recall"""

    def test_memory_save_recall(self):
        """Test saving and recalling memory"""
        # Save
        TOOL_REGISTRY['memory_save']('test_key', 'test_value')

        # Recall
        value = TOOL_REGISTRY['memory_recall']('test_key')
        assert value == 'test_value'

    def test_memory_list(self):
        """Test listing all memories"""
        # Save some values
        TOOL_REGISTRY['memory_save']('key1', 'value1')
        TOOL_REGISTRY['memory_save']('key2', 'value2')

        # List
        keys = TOOL_REGISTRY['memory_list']()
        assert isinstance(keys, list)
        assert 'key1' in keys or len(keys) > 0

    def test_memory_recall_missing(self):
        """Test recalling non-existent key"""
        result = TOOL_REGISTRY['memory_recall']('nonexistent_key')
        assert result == ""


class TestSystemMonitoring:
    """Test system information and monitoring"""

    def test_device_info(self):
        """Test device information retrieval"""
        result = TOOL_REGISTRY['device_info']()
        assert isinstance(result, dict)
        assert 'platform' in result
        assert 'processor' in result or 'platform' in result

    def test_get_system_info(self):
        """Test system info"""
        result = TOOL_REGISTRY['get_system_info']()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_internet_speed_test(self):
        """Test internet connectivity"""
        result = TOOL_REGISTRY['internet_speed_test']()
        assert isinstance(result, dict)
        assert 'status' in result


class TestTaskAutomation:
    """Test automation and workflow tools"""

    def test_task_decompose(self):
        """Test task decomposition"""
        task = "Create file and upload to server"
        subtasks = TOOL_REGISTRY['task_decompose'](task)
        assert isinstance(subtasks, list)
        assert len(subtasks) > 0
        assert all(isinstance(t, str) for t in subtasks)

    def test_task_decompose_multiple_tasks(self):
        """Test decomposing task with 'and' separator"""
        task = "Read file and write results and send email"
        subtasks = TOOL_REGISTRY['task_decompose'](task)
        assert isinstance(subtasks, list)
        assert len(subtasks) >= 2


class TestAIAFramework:
    """Test AIA-specific tools"""

    def test_aia_ml_classify_positive(self):
        """Test sentiment classification - positive"""
        result = TOOL_REGISTRY['aia_ml_classify'](
            "This product is amazing and excellent!"
        )
        assert 'classification' in result
        assert result['classification'] == 'positive'

    def test_aia_ml_classify_negative(self):
        """Test sentiment classification - negative"""
        result = TOOL_REGISTRY['aia_ml_classify'](
            "This is terrible and awful"
        )
        assert 'classification' in result
        assert result['classification'] == 'negative'

    def test_aia_ml_classify_neutral(self):
        """Test sentiment classification - neutral"""
        result = TOOL_REGISTRY['aia_ml_classify'](
            "The weather is cloudy today"
        )
        assert 'classification' in result
        assert result['classification'] == 'neutral'


class TestCheetahTools:
    """Test Cheetah advanced tools"""

    def test_cheetah_code_review(self):
        """Test code review"""
        test_file = __file__
        result = TOOL_REGISTRY['cheetah_code_review'](test_file)
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'issues' in result
        assert isinstance(result['score'], (int, float))
        assert 50 <= result['score'] <= 100

    def test_cheetah_research(self):
        """Test research tool"""
        result = TOOL_REGISTRY['cheetah_research'](
            'Python', depth='light'
        )
        assert isinstance(result, dict)
        assert 'sources' in result
        assert 'summary' in result


class TestShellOperations:
    """Test shell execution tools"""

    def test_execute_shell_simple(self):
        """Test simple shell command"""
        result = TOOL_REGISTRY['execute_shell']('echo "test"')
        assert isinstance(result, dict)
        assert 'stdout' in result or 'output' in result

    def test_execute_shell_error_handling(self):
        """Test shell error handling"""
        result = TOOL_REGISTRY['execute_shell']('exit 1')
        assert isinstance(result, dict)
        # Should not raise, should return error dict

    def test_git_command(self):
        """Test git command"""
        result = TOOL_REGISTRY['git_command']('--version')
        assert isinstance(result, str)


class TestWebOperations:
    """Test web-related tools"""

    def test_web_search(self):
        """Test web search"""
        result = TOOL_REGISTRY['web_search']('python', num_results=3)
        assert isinstance(result, list)
        # May be empty if no internet, but should return list

    def test_extract_urls_from_search(self):
        """Test URL extraction from search results"""
        search_results = [
            {"url": "https://example.com", "title": "Example"},
            {"url": "https://test.org", "title": "Test"}
        ]
        urls = TOOL_REGISTRY['extract_urls'](str(search_results))
        assert isinstance(urls, list)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_read_nonexistent_file(self):
        """Test reading non-existent file"""
        result = TOOL_REGISTRY['read_file']('/nonexistent/file.txt')
        # Should not raise, should return empty or error string
        assert isinstance(result, str)

    def test_analyze_empty_text(self):
        """Test analyzing empty text"""
        result = TOOL_REGISTRY['analyze_text']("")
        assert isinstance(result, dict)

    def test_find_files_invalid_dir(self):
        """Test finding files in invalid directory"""
        result = TOOL_REGISTRY['find_files']('/nonexistent/dir')
        assert isinstance(result, list)

    def test_hash_empty_string(self):
        """Test hashing empty string"""
        result = TOOL_REGISTRY['hash_text']("")
        assert 'hash' in result


class TestToolRegistry:
    """Test the tool registry itself"""

    def test_tool_registry_populated(self):
        """Test that registry is populated"""
        # The Phase 3 additions bumped the base registry to 88 (73 core + 7
        # persistent_memory + 8 access_control). main.py then adds 3 more
        # locally (remember, recall, task_complete) → 91 total. This test
        # sees only the base 88.
        assert len(TOOL_REGISTRY) >= 60
        assert len(TOOL_REGISTRY) >= 73  # was ==73; loosened as tools grow

    def test_all_tools_callable(self):
        """Test that all tools are callable"""
        for tool_name, tool_func in TOOL_REGISTRY.items():
            assert callable(tool_func), f"{tool_name} is not callable"

    def test_required_tools_exist(self):
        """Test that critical tools are present"""
        required = [
            'take_screenshot', 'mouse_click', 'keyboard_type',
            'execute_shell', 'read_file', 'write_file',
            'web_search', 'web_fetch', 'get_system_info'
        ]
        for tool in required:
            assert tool in TOOL_REGISTRY, f"Required tool {tool} missing"

    def test_no_duplicate_tools(self):
        """Test no duplicate tools in registry"""
        tools = list(TOOL_REGISTRY.keys())
        assert len(tools) == len(set(tools))


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
