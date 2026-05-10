from scripts.video_client import (
    SJTUVideoClient,
    extract_video_records,
    parse_redirect_params,
)


def test_get_external_tool_id_prefers_new_classroom_video_link():
    html = """
    <div id="main">
      <a href="/courses/1/external_tools/9487">课堂视频 旧版</a>
      <a href="/courses/1/external_tools/8329">课堂视频</a>
    </div>
    """
    assert SJTUVideoClient.extract_external_tool_id(html) == "8329"


def test_extract_form_inputs_by_action():
    html = """
    <form action="https://example.test/submit">
      <input name="a" value="1" />
      <input name="b" value="hello" />
      <input name="no_value" />
    </form>
    """
    assert SJTUVideoClient.extract_form_inputs(html, "https://example.test/submit") == {
        "a": "1",
        "b": "hello",
        "no_value": "",
    }


def test_parse_redirect_params_reads_query_and_fragment_query():
    params = parse_redirect_params("https://x.test/cb?tokenId=abc#/path?courId=123")
    assert params["tokenId"] == "abc"
    assert params["courId"] == "123"


def test_extract_video_records_supports_data_records():
    payload = {"data": {"records": [{"videoId": "v1"}]}}
    assert extract_video_records(payload) == [{"videoId": "v1"}]


def test_extract_video_records_supports_body_list():
    payload = {"body": {"list": [{"videoId": "v2"}]}}
    assert extract_video_records(payload) == [{"videoId": "v2"}]
