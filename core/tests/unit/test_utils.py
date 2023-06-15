"""File loading tests.
"""

from dk.utils import find_files_weighted_by_path

FILES_ROOT = './tests/resources/unit/test_utils_files'


def test_find_files() -> None:
    """Tests if file loading works.
    """
    files_expected = [['./tests/resources/unit/test_utils_files', 'test_file1.dk.env'],
                      ['./tests/resources/unit/test_utils_files/deeper_dir', 'test_file2.dk.env']]
    files = find_files_weighted_by_path('*.dk.env', {}, FILES_ROOT)
    assert files == files_expected, "List of files that supposed to be gathered doesn't match."


def test_find_files_weight() -> None:
    """Tests if prioritization by weight during files loading works correctly.
    """
    files_expected = [['./tests/resources/unit/test_utils_files/deeper_dir', 'test_file2.dk.env'],
                      ['./tests/resources/unit/test_utils_files', 'test_file1.dk.env']]
    files = find_files_weighted_by_path('*.dk.env', {
        FILES_ROOT: 10,
    }, FILES_ROOT)
    assert files == files_expected, "Prioritized file is not last."
