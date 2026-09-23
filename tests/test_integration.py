"""
tests/test_integration.py — Integration tests for tool combinations

Tests workflows that combine multiple tools to accomplish realistic tasks.
"""

import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.integrations import TOOL_REGISTRY


class TestFileWorkflows:
    """Test multi-tool workflows for file operations"""

    def test_create_analyze_read_workflow(self):
        """Workflow: Create file → Analyze code → Read back"""
        with TemporaryDirectory() as tmpdir:
            # Create a Python file
            test_file = Path(tmpdir) / "test.py"
            code = """
def hello(name):
    '''Say hello'''
    print(f'Hello {name}')

def add(a, b):
    return a + b
"""
            TOOL_REGISTRY['write_file'](str(test_file), code)

            # Analyze the file
            analysis = TOOL_REGISTRY['code_analyze'](str(test_file))
            assert analysis['functions'] == 2

            # Read it back
            content = TOOL_REGISTRY['read_file'](str(test_file))
            assert 'def hello' in content
            assert 'def add' in content

    def test_find_files_and_analyze(self):
        """Workflow: Find Python files → Analyze each"""
        with TemporaryDirectory() as tmpdir:
            # Create multiple Python files
            for i in range(3):
                test_file = Path(tmpdir) / f"file{i}.py"
                test_file.write_text(f"def func{i}():\n    pass\n")

            # Find all Python files
            files = TOOL_REGISTRY['find_files'](tmpdir, "*.py", max_results=10)
            assert len(files) == 3

            # Analyze each
            for fpath in files:
                analysis = TOOL_REGISTRY['code_analyze'](fpath)
                assert 'functions' in analysis
                assert analysis['functions'] >= 1

    def test_file_comparison_workflow(self):
        """Workflow: Create two files → Compare them"""
        with TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.py"
            file2 = Path(tmpdir) / "file2.py"

            file1.write_text("def function1():\n    pass")
            file2.write_text("def function2():\n    pass")

            # Compare files
            result = TOOL_REGISTRY['compare_files'](str(file1), str(file2))
            assert result['same'] is False
            assert result['diff_lines'] > 0


class TestDataAnalysisWorkflows:
    """Test multi-tool data analysis workflows"""

    def test_text_analysis_workflow(self):
        """Workflow: Analyze text → Extract URLs and emails"""
        text = """
        Check out https://example.com for more info.
        Contact us at support@example.com or sales@company.org
        Visit our site https://company.org today!
        """

        # Analyze text
        analysis = TOOL_REGISTRY['analyze_text'](text)
        assert analysis["word_count"] >= 15

        # Extract URLs
        urls = TOOL_REGISTRY['extract_urls'](text)
        assert len(urls) == 2

        # Extract emails
        emails = TOOL_REGISTRY['extract_emails'](text)
        assert len(emails) == 2

    def test_multi_source_research_workflow(self):
        """Workflow: Search → Research → Analyze"""
        # Search for topic
        search_results = TOOL_REGISTRY['web_search']('Python programming', num_results=3)

        # Should return list (may be empty without internet)
        assert isinstance(search_results, list)

        # Research topic
        research = TOOL_REGISTRY['cheetah_research']('Python', depth='light')
        assert isinstance(research, dict)
        assert 'sources' in research


class TestSecurityWorkflows:
    """Test security and analysis workflows"""

    def test_hash_verification_workflow(self):
        """Workflow: Hash text with different algorithms"""
        text = "test content"

        # SHA256
        sha256_result = TOOL_REGISTRY['hash_text'](text, "sha256")
        assert len(sha256_result['hash']) == 64

        # MD5
        md5_result = TOOL_REGISTRY['hash_text'](text, "md5")
        assert len(md5_result['hash']) == 32

        # SHA1
        sha1_result = TOOL_REGISTRY['hash_text'](text, "sha1")
        assert len(sha1_result['hash']) == 40

        # All should be different
        hashes = [
            sha256_result['hash'],
            md5_result['hash'],
            sha1_result['hash']
        ]
        assert len(set(hashes)) == 3

    def test_security_scan_workflow(self):
        """Workflow: Check SSL → DNS lookup → Port scan"""
        target = "localhost"

        # DNS lookup
        dns_result = TOOL_REGISTRY['dns_lookup'](target)
        assert 'hostname' in dns_result

        # Port scan (will likely fail on localhost:80 but shouldn't crash)
        port_result = TOOL_REGISTRY['port_scan'](target, ports="22,80,443")
        assert 'host' in port_result


class TestAutomationWorkflows:
    """Test automation workflows"""

    def test_task_to_execution_workflow(self):
        """Workflow: Decompose task → Check completion"""
        # Decompose complex task
        task = "Read the config file, parse JSON, and generate report"
        subtasks = TOOL_REGISTRY['task_decompose'](task)

        assert isinstance(subtasks, list)
        assert len(subtasks) >= 2

        # Each subtask should be a string
        for subtask in subtasks:
            assert isinstance(subtask, str)
            assert len(subtask) > 0

    def test_workflow_execution_with_memory(self):
        """Workflow: Execute task → Save to memory → Recall"""
        # Save task state
        task_id = "task_123"
        task_state = "In Progress: Analyzing files"

        TOOL_REGISTRY['memory_save'](task_id, task_state)

        # Simulate some processing...
        # Recall status
        recalled = TOOL_REGISTRY['memory_recall'](task_id)
        assert recalled == task_state

        # Update status
        new_state = "Completed: Analysis done"
        TOOL_REGISTRY['memory_save'](task_id, new_state)

        # Verify update
        recalled = TOOL_REGISTRY['memory_recall'](task_id)
        assert recalled == new_state


class TestComplexWorkflows:
    """Test complex multi-step workflows"""

    def test_code_quality_workflow(self):
        """Workflow: Analyze code → Review → Extract metrics"""
        with TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "complex.py"
            test_file.write_text("""
def process_data(data):
    '''Process and analyze data'''
    results = []
    for item in data:
        if item > 0:
            results.append(item * 2)
    return results

def validate(result):
    '''Validate results'''
    return len(result) > 0

# Main execution
if __name__ == '__main__':
    data = [1, 2, 3]
    results = process_data(data)
""")

            # Analyze
            analysis = TOOL_REGISTRY['code_analyze'](str(test_file))
            assert analysis['functions'] == 2

            # Review
            review = TOOL_REGISTRY['cheetah_code_review'](str(test_file))
            assert 'score' in review
            assert isinstance(review['score'], (int, float))

    def test_research_and_document_workflow(self):
        """Workflow: Research topic → Create document → Add metadata"""
        with TemporaryDirectory() as tmpdir:
            # Research
            research = TOOL_REGISTRY['cheetah_research']('AI safety', depth='light')
            assert 'sources' in research

            # Create document
            doc_path = Path(tmpdir) / "research.md"
            doc_content = f"""# AI Safety Research

## Summary
{research.get('summary', 'Research placeholder')}

## Sources
"""
            TOOL_REGISTRY['write_file'](str(doc_path), doc_content)

            # Analyze document
            analysis = TOOL_REGISTRY['code_analyze'](str(doc_path))
            assert analysis['total_lines'] > 0

            # Extract metadata
            metadata = TOOL_REGISTRY['extract_metadata'](str(doc_path))
            assert 'metadata' in metadata or 'error' in metadata


class TestErrorRecoveryWorkflows:
    """Test workflows with error handling"""

    def test_handle_missing_files(self):
        """Workflow: Try to process missing file → Handle gracefully"""
        # Try to read non-existent file
        result = TOOL_REGISTRY['read_file']('/nonexistent/file.txt')
        assert isinstance(result, str)
        assert 'not found' in result.lower() or 'error' in result.lower()

    def test_handle_invalid_directory(self):
        """Workflow: Try to find files in invalid dir → Handle gracefully"""
        result = TOOL_REGISTRY['find_files']('/nonexistent/directory')
        assert isinstance(result, list)
        # Should return empty list, not crash

    def test_handle_network_errors(self):
        """Workflow: Try web search without internet → Handle gracefully"""
        # Should not crash even without internet
        result = TOOL_REGISTRY['web_search']('test query', num_results=3)
        assert isinstance(result, list)


class TestCombinedAIACheetahWorkflows:
    """Test combining AIA and Cheetah tools"""

    def test_sentiment_analysis_workflow(self):
        """Workflow: Classify sentiment → Store result → Recall"""
        text1 = "This is absolutely amazing and wonderful!"
        text2 = "This is terrible and awful"
        text3 = "The weather is cloudy"

        # Classify each
        result1 = TOOL_REGISTRY['aia_ml_classify'](text1)
        result2 = TOOL_REGISTRY['aia_ml_classify'](text2)
        result3 = TOOL_REGISTRY['aia_ml_classify'](text3)

        # Verify classifications
        assert result1['classification'] == 'positive'
        assert result2['classification'] == 'negative'
        assert result3['classification'] == 'neutral'

        # Store results
        TOOL_REGISTRY['memory_save']('sentiment_results', str({
            'positive': result1['classification'],
            'negative': result2['classification'],
            'neutral': result3['classification']
        }))

        # Recall and verify
        recalled = TOOL_REGISTRY['memory_recall']('sentiment_results')
        assert 'positive' in recalled
        assert 'negative' in recalled

    def test_research_and_classify_workflow(self):
        """Workflow: Research → Classify sentiment → Store findings"""
        # Research
        research = TOOL_REGISTRY['cheetah_research']('Python', depth='light')
        summary = research.get('summary', 'Python is great')

        # Classify sentiment
        classification = TOOL_REGISTRY['aia_ml_classify'](summary)

        # Store findings
        findings = {
            'topic': 'Python',
            'sentiment': classification['classification'],
            'sources_count': len(research.get('sources', []))
        }
        TOOL_REGISTRY['memory_save']('research_findings', str(findings))

        # Verify stored
        recalled = TOOL_REGISTRY['memory_recall']('research_findings')
        assert 'Python' in recalled
        assert 'sentiment' in recalled


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
