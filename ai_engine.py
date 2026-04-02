"""
AI 引擎：支持 Kimi / Claude 双通道
OpenAI 兼容接口 (Kimi) + Anthropic 原生接口 (Claude)
"""

import threading
import json
from config import (
    KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL,
    CLAUDE_API_KEY, CLAUDE_MODEL,
    DEFAULT_AI_PROVIDER,
)


class AIEngine:
    """统一 AI 调用接口"""

    def __init__(self):
        self.provider = DEFAULT_AI_PROVIDER
        self._kimi_client = None
        self._claude_client = None
        self._init_clients()

    def _init_clients(self):
        if KIMI_API_KEY:
            try:
                from openai import OpenAI
                self._kimi_client = OpenAI(
                    api_key=KIMI_API_KEY,
                    base_url=KIMI_BASE_URL,
                )
            except ImportError:
                print("[WARN] openai 库未安装，Kimi 不可用。pip install openai")

        if CLAUDE_API_KEY:
            try:
                import anthropic
                self._claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            except ImportError:
                print("[WARN] anthropic 库未安装，Claude 不可用。pip install anthropic")

    @property
    def available_providers(self):
        providers = []
        if self._kimi_client:
            providers.append("kimi")
        if self._claude_client:
            providers.append("claude")
        return providers

    @property
    def is_available(self):
        return len(self.available_providers) > 0

    def set_provider(self, provider):
        if provider in self.available_providers:
            self.provider = provider

    def chat(self, messages, system_prompt=None, callback=None):
        """
        发送对话请求

        Args:
            messages: [{"role": "user"/"assistant", "content": "..."}]
            system_prompt: 系统提示词
            callback: 回调函数 callback(response_text, error)
        """
        if not self.is_available:
            if callback:
                callback(None, "没有可用的 AI 服务。请在 .env 中配置 API Key。")
            return

        def _do_request():
            try:
                if self.provider == "kimi" and self._kimi_client:
                    result = self._call_kimi(messages, system_prompt)
                elif self.provider == "claude" and self._claude_client:
                    result = self._call_claude(messages, system_prompt)
                else:
                    # fallback
                    if self._kimi_client:
                        result = self._call_kimi(messages, system_prompt)
                    elif self._claude_client:
                        result = self._call_claude(messages, system_prompt)
                    else:
                        result = None

                if callback:
                    callback(result, None)
            except Exception as e:
                if callback:
                    callback(None, str(e))

        thread = threading.Thread(target=_do_request, daemon=True)
        thread.start()

    def chat_sync(self, messages, system_prompt=None):
        """同步版本"""
        if not self.is_available:
            return None

        try:
            if self.provider == "kimi" and self._kimi_client:
                return self._call_kimi(messages, system_prompt)
            elif self.provider == "claude" and self._claude_client:
                return self._call_claude(messages, system_prompt)
        except Exception as e:
            return f"[AI Error] {e}"

    def _call_kimi(self, messages, system_prompt):
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)

        response = self._kimi_client.chat.completions.create(
            model=KIMI_MODEL,
            messages=api_messages,
            temperature=0.4,
        )
        return response.choices[0].message.content

    def _call_claude(self, messages, system_prompt):
        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self._claude_client.messages.create(**kwargs)
        return response.content[0].text
