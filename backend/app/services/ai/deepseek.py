from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """你是“政府招标文件分析助手”，面向企业投标团队。你的任务是基于给定招标公告与附件文本，输出可执行、可核查的投标分析结果。

要求：
1) 只基于输入文本，不得臆测；信息缺失请明确标注“未提及”。
2) 优先提取：项目名称、招标人、预算/控制价、报名与投标截止时间、开标时间、资格条件、评分办法、保证金、履约要求、废标风险点。
3) 输出必须是严格 JSON，不要输出任何额外文字。
4) 对时间、金额、比例等关键字段给出原文片段依据（evidence）。
5) 给出“行动清单”，按紧急程度排序（高/中/低）。

JSON Schema:
{
  "summary": "string",
  "basic_info": {
    "project_name": "string",
    "tenderer": "string",
    "budget": "string",
    "deadline_bid": "string",
    "open_time": "string",
    "region": "string"
  },
  "qualification_requirements": ["string"],
  "scoring_rules": ["string"],
  "risk_points": [
    {"level": "high|medium|low", "item": "string", "evidence": "string"}
  ],
  "action_checklist": [
    {"priority": "high|medium|low", "task": "string", "owner_suggestion": "string", "due_hint": "string"}
  ],
  "missing_info": ["string"]
}"""


class DeepSeekClient:
    def __init__(self) -> None:
        self.base_url = settings.deepseek_base_url.rstrip('/')
        self.api_key = settings.deepseek_api_key
        self.model = settings.deepseek_model

    def analyze(self, notice_text: str, attachment_texts: list[str]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError('DEEPSEEK_API_KEY is not configured')

        user_input = self._build_user_input(notice_text, attachment_texts)
        payload = {
            'model': self.model,
            'temperature': 0.1,
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_input},
            ],
        }
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

        response = httpx.post(
            f'{self.base_url}/chat/completions',
            headers=headers,
            json=payload,
            timeout=settings.deepseek_timeout_seconds,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return self._parse_json_content(content)

    def _build_user_input(self, notice_text: str, attachment_texts: list[str]) -> str:
        attachment_block = '\n\n'.join(
            f'【附件{i + 1}】\n{text[:12000]}' for i, text in enumerate(attachment_texts)
        )
        return f'【公告正文】\n{notice_text[:20000]}\n\n{attachment_block}'.strip()

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        stripped = content.strip()
        if stripped.startswith('```'):
            stripped = stripped.strip('`')
            if stripped.startswith('json'):
                stripped = stripped[4:]
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return {
                'summary': '模型返回非标准JSON，已回退保存原文。',
                'basic_info': {},
                'qualification_requirements': [],
                'scoring_rules': [],
                'risk_points': [],
                'action_checklist': [],
                'missing_info': ['模型返回格式异常'],
                '_raw_text': content,
            }
