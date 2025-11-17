"""
Azure OpenAI Integration for AI Avatar

This module demonstrates how to integrate Azure OpenAI for:
- Conversation generation
- Context-aware responses
- Personality consistency
- Streaming responses for real-time avatar
"""

import os
import json
from typing import List, Dict, AsyncIterator
from openai import AzureOpenAI
import asyncio

class AvatarAI:
    """
    AI brain for the avatar using Azure OpenAI
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_name: str = "gpt-4-turbo",
        api_version: str = "2024-02-15-preview"
    ):
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        self.deployment_name = deployment_name
        self.conversation_history: List[Dict] = []

        # Define avatar personality
        self.system_prompt = """
        You are Alex, a friendly and professional AI avatar assistant.

        Personality traits:
        - Professional yet warm and approachable
        - Patient and empathetic
        - Clear and concise in communication
        - Proactive in offering help
        - Maintains a positive, can-do attitude

        Guidelines:
        - Keep responses under 100 words for natural speech
        - Use simple, conversational language
        - Ask clarifying questions when needed
        - Admit when you don't know something
        - Show enthusiasm with words, not excessive punctuation
        - Be culturally sensitive and inclusive

        Format:
        - Break complex info into digestible chunks
        - Use "I" and "you" for personal connection
        - Avoid jargon unless user demonstrates expertise
        """

    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })

        # Keep only last 10 messages to manage context window
        if len(self.conversation_history) > 10:
            # Always keep system message, remove oldest user/assistant messages
            self.conversation_history = [self.conversation_history[0]] + \
                                       self.conversation_history[-9:]

    def generate_response(
        self,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 200
    ) -> Dict:
        """
        Generate a response from the AI avatar

        Returns:
            Dict with 'text', 'tokens_used', and 'finish_reason'
        """
        # Add user message to history
        self.add_message("user", user_message)

        # Prepare messages with system prompt
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95,
                frequency_penalty=0.5,  # Reduce repetition
                presence_penalty=0.5    # Encourage topic diversity
            )

            assistant_message = response.choices[0].message.content

            # Add assistant response to history
            self.add_message("assistant", assistant_message)

            return {
                "text": assistant_message,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason,
                "model": response.model
            }

        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return {
                "text": "I apologize, but I'm having trouble processing that right now. Could you please try again?",
                "tokens_used": 0,
                "finish_reason": "error"
            }

    async def stream_response(
        self,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 200
    ) -> AsyncIterator[str]:
        """
        Stream response in real-time for avatar lip-sync

        Yields chunks of text as they're generated
        """
        self.add_message("user", user_message)

        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            full_response = ""

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Add complete response to history
            self.add_message("assistant", full_response)

        except Exception as e:
            print(f"❌ Error streaming response: {e}")
            yield "I apologize, but I'm having trouble right now."

    def add_context(self, context: Dict):
        """
        Add external context to enhance responses

        Example: customer data, product info, ticket status
        """
        context_message = f"Context information: {json.dumps(context)}"
        self.conversation_history.insert(0, {
            "role": "system",
            "content": context_message
        })

    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🔄 Conversation history cleared")

    def get_conversation_summary(self) -> str:
        """
        Generate a summary of the conversation so far
        """
        if len(self.conversation_history) == 0:
            return "No conversation yet."

        summary_prompt = """
        Summarize the key points of this conversation in 2-3 bullet points.
        Focus on: main topics discussed, user's needs, and any actions taken.
        """

        messages = [
            {"role": "system", "content": summary_prompt}
        ] + self.conversation_history

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=0.3,
            max_tokens=150
        )

        return response.choices[0].message.content


# ============================================
# USAGE EXAMPLES
# ============================================

async def example_streaming():
    """Example: Streaming response for real-time avatar"""

    avatar = AvatarAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name="gpt-4-turbo"
    )

    print("🎬 Streaming response...")
    print("Avatar: ", end="", flush=True)

    async for chunk in avatar.stream_response("Tell me about your capabilities"):
        print(chunk, end="", flush=True)
        # In real app: send each chunk to TTS and avatar renderer
        await asyncio.sleep(0.01)  # Simulate processing time

    print("\n")


def example_conversation():
    """Example: Multi-turn conversation"""

    avatar = AvatarAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    # Add customer context
    avatar.add_context({
        "customer_name": "Sarah Johnson",
        "customer_tier": "Premium",
        "account_age_days": 450,
        "recent_orders": 5,
        "open_tickets": 0
    })

    # Conversation turns
    conversations = [
        "Hi, I need help with my recent order",
        "Order number is #12345",
        "When will it arrive?",
        "Thank you!"
    ]

    for user_msg in conversations:
        print(f"\n👤 User: {user_msg}")

        response = avatar.generate_response(user_msg)

        print(f"🤖 Avatar: {response['text']}")
        print(f"   ℹ️  Tokens used: {response['tokens_used']}")

    # Get conversation summary
    print("\n" + "="*50)
    print("📋 Conversation Summary:")
    print(avatar.get_conversation_summary())


def example_with_function_calling():
    """Example: Using function calling for external actions"""

    # Define available functions
    functions = [
        {
            "name": "get_order_status",
            "description": "Get the current status of a customer order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID, e.g., #12345"
                    }
                },
                "required": ["order_id"]
            }
        },
        {
            "name": "schedule_callback",
            "description": "Schedule a callback from customer service",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string"},
                    "preferred_time": {"type": "string"}
                },
                "required": ["phone_number"]
            }
        }
    ]

    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    messages = [
        {"role": "system", "content": "You are a helpful customer service avatar."},
        {"role": "user", "content": "Can you check the status of order #12345?"}
    ]

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        functions=functions,
        function_call="auto"
    )

    # Check if function should be called
    if response.choices[0].finish_reason == "function_call":
        function_call = response.choices[0].message.function_call
        print(f"🔧 Function to call: {function_call.name}")
        print(f"📋 Arguments: {function_call.arguments}")

        # Execute the function (simulated)
        if function_call.name == "get_order_status":
            # In real app: call your backend API
            order_status = {
                "order_id": "#12345",
                "status": "In Transit",
                "expected_delivery": "2025-11-20",
                "tracking_number": "1Z999AA10123456784"
            }

            # Send function result back to model
            messages.append({
                "role": "function",
                "name": "get_order_status",
                "content": json.dumps(order_status)
            })

            # Get final response
            final_response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages
            )

            print(f"\n🤖 Avatar: {final_response.choices[0].message.content}")


if __name__ == "__main__":
    print("🚀 Azure OpenAI Avatar Integration Examples\n")

    # Example 1: Simple conversation
    print("Example 1: Multi-turn Conversation")
    print("="*50)
    example_conversation()

    # Example 2: Streaming (requires async)
    print("\n\nExample 2: Streaming Response")
    print("="*50)
    asyncio.run(example_streaming())

    # Example 3: Function calling
    print("\n\nExample 3: Function Calling")
    print("="*50)
    example_with_function_calling()
