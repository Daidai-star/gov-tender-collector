from app.services.crawler.adapters.base import SiteAdapter
from app.services.crawler.adapters.generic_gov import GenericGovernmentAdapter
from app.services.crawler.adapters.henan_gov import (
    HenanProvincialAdapter,
    XinxiangGovProcurementAdapter,
    ZhengzhouPublicResourceAdapter,
)


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, SiteAdapter] = {
            'generic_html': GenericGovernmentAdapter(),
            'henan_hnsggzy': HenanProvincialAdapter(),
            'henan_xinxiang_zfcg': XinxiangGovProcurementAdapter(),
            'henan_zzggzy': ZhengzhouPublicResourceAdapter(),
        }

    def get(self, adapter_key: str) -> SiteAdapter:
        if adapter_key not in self._adapters:
            raise KeyError(f'unknown adapter: {adapter_key}')
        return self._adapters[adapter_key]


adapter_registry = AdapterRegistry()
