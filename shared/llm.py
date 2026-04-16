"""Shared Bedrock LLM client with automatic fallback to simulated mode.

Usage:
    from shared.llm import LLM
    llm = LLM()                          # auto-detects Bedrock or falls back
    llm = LLM(mode="bedrock")            # force Bedrock (fails if no creds)
    llm = LLM(mode="simulated")          # force simulated

    response = llm.invoke("What is 2+2?", system="You are a math tutor.")
    print(llm.mode)  # "bedrock" or "simulated"
"""
import json, os

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "eu-west-1"))

class LLM:
    def __init__(self, mode="auto"):
        self.mode = mode
        self._client = None
        if mode in ("auto", "bedrock"):
            try:
                import boto3
                self._client = boto3.client("bedrock-runtime", region_name=REGION)
                # Validate creds with a real API call (lightweight)
                boto3.client("bedrock", region_name=REGION).list_foundation_models(maxResults=1)
                self.mode = "bedrock"
            except Exception:
                if mode == "bedrock":
                    raise
                self.mode = "simulated"
        else:
            self.mode = "simulated"

    @property
    def is_live(self):
        return self.mode == "bedrock"

    def invoke(self, prompt, system=None, max_tokens=1024, fallback=None):
        """Call Bedrock or return fallback in simulated mode."""
        if self.mode == "bedrock":
            return self._call_bedrock(prompt, system, max_tokens)
        if fallback is not None:
            return fallback
        return f"[SIMULATED] Response to: {prompt[:80]}..."

    def _call_bedrock(self, prompt, system, max_tokens):
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        kwargs = {
            "modelId": MODEL_ID,
            "messages": messages,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.7},
        }
        if system:
            kwargs["system"] = [{"text": system}]
        resp = self._client.converse(**kwargs)
        return resp["output"]["message"]["content"][0]["text"]

    def invoke_multi_turn(self, messages, system=None, max_tokens=1024, fallback=None):
        """Multi-turn conversation. messages = [{"role":"user"|"assistant","content":"..."}]"""
        if self.mode == "bedrock":
            formatted = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in messages]
            kwargs = {
                "modelId": MODEL_ID,
                "messages": formatted,
                "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.7},
            }
            if system:
                kwargs["system"] = [{"text": system}]
            resp = self._client.converse(**kwargs)
            return resp["output"]["message"]["content"][0]["text"]
        if fallback is not None:
            return fallback
        return "[SIMULATED] Multi-turn response"
