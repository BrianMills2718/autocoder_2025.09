#!/usr/bin/env python3
"""Test direct LiteLLM to verify it's working"""

from litellm import completion
from dotenv import load_dotenv

load_dotenv()

# Test direct LiteLLM call
response = completion(
    model="gemini/gemini-2.5-flash",
    messages=[
        {"role": "user", "content": "Say hello in exactly one word"}
    ],
    timeout=30
)

print(f"Response: {response}")
print(f"Content: {response.choices[0].message.content}")
print(f"Type: {type(response.choices[0].message.content)}")