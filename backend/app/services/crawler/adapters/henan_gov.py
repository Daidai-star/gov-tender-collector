from app.services.crawler.adapters.generic_gov import GenericGovernmentAdapter


class HenanProvincialAdapter(GenericGovernmentAdapter):
    DEFAULT_RULES = {
        **GenericGovernmentAdapter.DEFAULT_RULES,
        'list_link_selector': "a[href*='detail'],a[href*='content'],a[href*='article'],a",
        'detail_content_selector': 'article,.article,.content,.detail,.detail-content,.news-content,.ewb-article-info,body',
        'publish_time_selector': '.pub-time,.time,.date,.publish-time,.article-time',
        'max_seed_count': 260,
    }


class XinxiangGovProcurementAdapter(GenericGovernmentAdapter):
    DEFAULT_RULES = {
        **GenericGovernmentAdapter.DEFAULT_RULES,
        'list_link_selector': "a[href*='zfcg'],a[href*='gg'],a[href*='content'],a[href*='article'],a",
        'detail_content_selector': 'article,.article,.main-content,.content,.detail,.detail-content,body',
        'include_keywords': ['采购', '招标', '中标', '成交', '更正', '公告'],
        'max_seed_count': 240,
    }


class ZhengzhouPublicResourceAdapter(GenericGovernmentAdapter):
    DEFAULT_RULES = {
        **GenericGovernmentAdapter.DEFAULT_RULES,
        'list_link_selector': "a[href*='ggzy'],a[href*='jyxx'],a[href*='content'],a[href*='detail'],a",
        'detail_content_selector': 'article,.article,.content,.detail,.news-content,.main-article,body',
        'include_keywords': ['招标', '中标', '成交', '结果', '公告', '交易'],
        'max_seed_count': 260,
    }
