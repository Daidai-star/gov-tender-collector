from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.models.entities import Site
from app.services.crawler.adapters.base import SiteAdapter
from app.services.crawler.types import NoticeSeed, ParsedAttachment, ParsedNotice
from app.services.utils import normalize_url

settings = get_settings()


class GenericGovernmentAdapter(SiteAdapter):
    """
    Generic parser for mostly static government pages.

    parser_rules supports:
    - list_link_selector (default: "a")
    - list_pages: optional list of list page urls
    - include_keywords / exclude_keywords
    - max_seed_count
    - detail_content_selector (default: "body")
    - attachment_selector (default: "a")
    - publish_time_selector (optional)
    - tender_type_keywords (mapping tender_type -> [keywords])
    """

    DEFAULT_RULES: dict = {
        'list_link_selector': 'a',
        'detail_content_selector': 'body',
        'attachment_selector': "a[href*='.pdf'],a[href*='.doc'],a[href*='.docx'],a[href*='.xls'],a[href*='.xlsx']",
        'include_keywords': ['招标', '采购', '中标', '成交', '公告', '结果'],
        'exclude_keywords': ['上一页', '下一页', '首页', '尾页'],
        'max_seed_count': 200,
    }

    def _request(self, url: str) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(settings.crawl_retry_times):
            try:
                resp = httpx.get(url, timeout=settings.crawl_timeout_seconds, follow_redirects=True)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPError(f'transient status={resp.status_code}')
                resp.raise_for_status()
                return resp
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        if last_error is None:
            raise RuntimeError('unexpected request failure')
        raise last_error

    def _request_with_playwright(self, url: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError('playwright is not installed, please install and run playwright install') from exc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=settings.crawl_timeout_seconds * 1000, wait_until='networkidle')
            html = page.content()
            browser.close()
            return html

    def _fetch_html(self, site: Site, url: str) -> str:
        use_browser = bool(self._rules(site).get('use_browser', False))
        if use_browser:
            return self._request_with_playwright(url)
        return self._request(url).text

    def list_notices(self, site: Site, tender_types: list[str] | None = None) -> list[NoticeSeed]:
        rules = self._rules(site)
        link_selector = rules.get('list_link_selector', 'a')
        include_keywords = tuple(rules.get('include_keywords', []))
        exclude_keywords = tuple(rules.get('exclude_keywords', []))
        max_seed_count = int(rules.get('max_seed_count', 200))
        list_pages = rules.get('list_pages') or [site.base_url]

        seeds: list[NoticeSeed] = []
        seen_urls: set[str] = set()

        for list_page in list_pages:
            html = self._fetch_html(site, list_page)
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.select(link_selector)

            for link in links:
                text = (link.get_text() or '').strip()
                href = (link.get('href') or '').strip()
                if not text or not href:
                    continue
                if len(text) < 6:
                    continue
                if include_keywords and not any(keyword in text for keyword in include_keywords):
                    continue
                if exclude_keywords and any(keyword in text for keyword in exclude_keywords):
                    continue
                if tender_types and not self._match_tender_type(text, tender_types, site):
                    continue
                detail_url = normalize_url(list_page, href)
                if detail_url in seen_urls:
                    continue
                seen_urls.add(detail_url)
                seeds.append(
                    NoticeSeed(
                        title=text,
                        detail_url=detail_url,
                        publish_time=self._extract_time_from_text(text),
                    )
                )
                if len(seeds) >= max_seed_count:
                    return seeds
        return seeds

    def parse_notice(self, site: Site, seed: NoticeSeed, tender_types: list[str] | None = None) -> ParsedNotice | None:
        html = self._fetch_html(site, seed.detail_url)
        soup = BeautifulSoup(html, 'html.parser')
        rules = self._rules(site)

        content_selector = rules.get('detail_content_selector', 'body')
        node = soup.select_one(content_selector)
        content_text = (node.get_text('\n', strip=True) if node else soup.get_text('\n', strip=True)).strip()
        if len(content_text) < 30:
            content_text = f"{seed.title}\n\n正文抓取不完整，请点击原文链接查看。\n原文地址：{seed.detail_url}"

        attachments = self._parse_attachments(site, soup, seed.detail_url, rules.get('attachment_selector', 'a'))
        tender_type = self._guess_tender_type(seed.title + '\n' + content_text, tender_types)
        publish_time = self._extract_publish_time(soup, rules.get('publish_time_selector')) or seed.publish_time

        return ParsedNotice(
            title=seed.title,
            source_url=seed.detail_url,
            publish_time=publish_time,
            tender_type=tender_type,
            content_text=content_text,
            source_notice_id=seed.source_notice_id,
            attachments=attachments,
        )

    def download_attachment(self, site: Site, source_url: str) -> tuple[bytes, str]:
        resp = self._request(source_url)
        content_type = resp.headers.get('content-type', 'application/octet-stream')
        return resp.content, content_type

    def normalize(self, parsed: ParsedNotice) -> ParsedNotice:
        parsed.content_text = self._clean_content_text(parsed.content_text)
        return parsed

    def _parse_attachments(self, site: Site, soup: BeautifulSoup, page_url: str, selector: str) -> list[ParsedAttachment]:
        allowed = ('.pdf', '.doc', '.docx', '.xls', '.xlsx')
        items: list[ParsedAttachment] = []
        for link in soup.select(selector):
            href = (link.get('href') or '').strip()
            if not href:
                continue
            lower_href = href.lower()
            if not any(ext in lower_href for ext in allowed):
                continue
            source_url = normalize_url(page_url, href)
            file_name = (link.get_text() or source_url.split('/')[-1]).strip()
            if '.' not in file_name:
                file_name = source_url.split('/')[-1]
            ext = file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else 'bin'
            items.append(ParsedAttachment(file_name=file_name, source_url=source_url, file_type=ext))
        return items[:20]

    def _match_tender_type(self, text: str, tender_types: list[str], site: Site) -> bool:
        tender_map = self._rules(site).get('tender_type_keywords', {})
        text_lower = text.lower()
        for tender_type in tender_types:
            keywords = tender_map.get(tender_type, [tender_type])
            if any(keyword.lower() in text_lower for keyword in keywords):
                return True
        return False

    def _guess_tender_type(self, text: str, tender_types: list[str] | None) -> str:
        text_lower = text.lower()
        if tender_types:
            for tender_type in tender_types:
                if tender_type.lower() in text_lower:
                    return tender_type
        keywords: dict[str, Iterable[str]] = {
            '公开招标': ('公开招标', '招标公告'),
            '竞争性谈判': ('竞争性谈判',),
            '竞争性磋商': ('竞争性磋商',),
            '单一来源': ('单一来源',),
        }
        for tender_type, keys in keywords.items():
            if any(key in text for key in keys):
                return tender_type
        return '未分类'

    def _extract_publish_time(self, soup: BeautifulSoup, selector: str | None) -> datetime | None:
        text = ''
        if selector:
            node = soup.select_one(selector)
            if node:
                text = (node.get_text() or '').strip()
        if not text:
            text = soup.get_text(' ', strip=True)[:1000]
        return self._extract_time_from_text(text)

    def _extract_time_from_text(self, text: str) -> datetime | None:
        matches = re.findall(r'(20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:\s+\d{1,2}:\d{1,2}(?::\d{1,2})?)?)', text)
        if not matches:
            return None
        candidate = matches[0].replace('年', '-').replace('月', '-').replace('日', '')
        candidate = candidate.replace('/', '-').replace('.', '-').strip()
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                return datetime.strptime(candidate[:19], fmt)
            except ValueError:
                continue
        return None

    def _rules(self, site: Site) -> dict:
        rules = dict(self.DEFAULT_RULES)
        rules.update(site.parser_rules or {})
        return rules

    def _clean_content_text(self, text: str) -> str:
        raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not raw_lines:
            return text

        noise_patterns = [
            r'^您当前的位置',
            r'^当前位置',
            r'^首页$',
            r'^>$',
            r'^信息来源[:：]?$',
            r'^打印$',
            r'^关闭窗口$',
        ]

        lines: list[str] = []
        fragment_buffer = ''
        for line in raw_lines:
            if any(re.search(pattern, line) for pattern in noise_patterns):
                continue

            # Merge fragmented one-char/short lines caused by broken HTML extraction.
            if (
                len(line) <= 2
                and re.match(r'^[\u4e00-\u9fffA-Za-z0-9（）()【】《》\-—]+$', line)
            ):
                fragment_buffer += line
                continue

            if fragment_buffer:
                line = f'{fragment_buffer}{line}'
                fragment_buffer = ''

            line = re.sub(r'\s+', ' ', line).strip()
            lines.append(line)

        if fragment_buffer:
            lines.append(fragment_buffer)

        merged: list[str] = []
        heading_pattern = re.compile(
            r'^(一、|二、|三、|四、|五、|六、|七、|八、|九、|十、|项目概况|资格条件|时间安排|评分办法|采购需求|联系方式)'
        )
        for line in lines:
            if not merged:
                merged.append(line)
                continue
            if heading_pattern.match(line):
                merged.append(line)
                continue
            prev = merged[-1]
            if (
                len(line) < 18
                and not re.search(r'[。！？；：:]$', prev)
                and not heading_pattern.match(prev)
            ):
                merged[-1] = f'{prev}{line}'
            else:
                merged.append(line)

        return '\n'.join(merged)
