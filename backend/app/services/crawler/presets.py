HENAN_SEED_SITES = [
    {
        'name': '河南省公共资源交易中心',
        'base_url': 'https://hnsggzyjy.henan.gov.cn/',
        'province': '河南省',
        'city': '省级',
        'adapter_key': 'henan_hnsggzy',
        'crawl_enabled': True,
        'rate_limit': 4,
        'schedule_group': 'default',
        'parser_rules': {
            'list_pages': [
                'https://hnsggzyjy.henan.gov.cn/',
            ],
            'include_keywords': ['招标', '中标', '结果', '公告', '采购'],
            'exclude_keywords': ['办事指南', '政策法规', '首页', '下一页'],
            'max_seed_count': 300,
        },
    },
    {
        'name': '新乡市政府采购网',
        'base_url': 'https://xinxiang.zfcg.henan.gov.cn/',
        'province': '河南省',
        'city': '新乡市',
        'adapter_key': 'henan_xinxiang_zfcg',
        'crawl_enabled': True,
        'rate_limit': 4,
        'schedule_group': 'default',
        'parser_rules': {
            'list_pages': [
                'https://xinxiang.zfcg.henan.gov.cn/',
            ],
            'include_keywords': ['采购', '招标', '成交', '中标', '公告'],
            'exclude_keywords': ['联系我们', '网站地图', '首页', '下一页'],
            'max_seed_count': 240,
        },
    },
    {
        'name': '郑州市公共资源交易中心',
        'base_url': 'https://zzggzy.zhengzhou.gov.cn/',
        'province': '河南省',
        'city': '郑州市',
        'adapter_key': 'henan_zzggzy',
        'crawl_enabled': True,
        'rate_limit': 4,
        'schedule_group': 'default',
        'parser_rules': {
            'list_pages': [
                'https://zzggzy.zhengzhou.gov.cn/',
            ],
            'include_keywords': ['招标', '中标', '成交', '结果', '公告'],
            'exclude_keywords': ['网站首页', '办事指南', '首页', '下一页'],
            'max_seed_count': 260,
        },
    },
]
