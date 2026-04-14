from bilibili_transcript.text_post import sanitize_filename_title


def test_basic():
    assert sanitize_filename_title("Hello World") == "Hello_World"


def test_special_chars():
    assert sanitize_filename_title('test:file*name?"yes"') == "test_file_name_yes"


def test_chinese_quotes_removed():
    assert sanitize_filename_title("「测试」标题") == "测试标题"


def test_max_len():
    long = "a" * 100
    result = sanitize_filename_title(long, max_len=10)
    assert len(result) == 10


def test_empty():
    assert sanitize_filename_title("") == "untitled"


def test_only_special():
    assert sanitize_filename_title("***") == "untitled"
