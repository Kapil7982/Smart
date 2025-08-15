import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class AIClient:
    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
        
    def call_lm_studio(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call LM Studio local API"""
        try:
            response = requests.post(
                f"{self.lm_studio_url}/completions",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stop": ["\n\n"]
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('choices', [{}])[0].get('text', '').strip()
            else:
                return self._fallback_analysis(prompt)
        except Exception as e:
            print(f"LM Studio error: {e}")
            return self._fallback_analysis(prompt)
    
    def call_openai(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call OpenAI API"""
        if not self.openai_key:
            return self.call_lm_studio(prompt, max_tokens)
        
        try:
            import openai
            openai.api_key = self.openai_key
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI error: {e}")
            return self.call_lm_studio(prompt, max_tokens)
    
    def _fallback_analysis(self, prompt: str) -> str:
        """Fallback analysis when AI services are unavailable"""
        if "priority" in prompt.lower():
            return "0.7"  # Default medium-high priority
        elif "deadline" in prompt.lower():
            future_date = datetime.now() + timedelta(days=3)
            return future_date.strftime("%Y-%m-%d")
        elif "category" in prompt.lower():
            return "General"
        elif "tags" in prompt.lower():
            return "task, general"
        else:
            return "Analysis unavailable - using defaults"

    def analyze_with_ai(self, prompt: str, max_tokens: int = 1000) -> str:
        """Main method to call AI services with fallback"""
        # Try LM Studio first (recommended)
        result = self.call_lm_studio(prompt, max_tokens)
        
        # If LM Studio fails, try OpenAI
        if "Analysis unavailable" in result and self.openai_key:
            result = self.call_openai(prompt, max_tokens)
        
        return result