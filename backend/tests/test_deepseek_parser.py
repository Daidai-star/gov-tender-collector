from app.services.ai.deepseek import DeepSeekClient


def test_parse_json_content_fallback():
    client = DeepSeekClient()
    out = client._parse_json_content('not json')
    assert out['summary']
    assert 'missing_info' in out
