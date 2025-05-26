import os
import openai
from typing import List, Dict, Any, Optional
from config import config

class TeacherAgent:
    """
    Teacher Agent specialized in educational support and explanations.
    Provides clear, structured learning content and adapts to different learning levels.
    """
    
    def __init__(self):
        self.name = "Teacher"
        self.role = "Educational Assistant"
        self.system_prompt = """You are an experienced and patient teacher. Your role is to:

1. Explain concepts clearly and systematically
2. Break down complex topics into digestible parts
3. Provide examples and analogies to aid understanding
4. Encourage questions and critical thinking
5. Adapt your teaching style to the student's level
6. Offer additional resources and practice suggestions

Always be encouraging, patient, and supportive. Use a warm, professional tone that makes learning enjoyable."""

    async def process_message(self, message: str, history: List[Dict], user_context: Any) -> str:
        """Process a message with educational focus"""
        # Check if demo mode is enabled
        if config.DEMO_MODE:
            return self._get_demo_response(message)
        
        try:
            # Prepare conversation context with educational focus
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add relevant history for context
            for entry in history[-3:]:  # Last 3 conversations for context
                if entry.get("agent") == "teacher":  # Only include teacher conversations
                    messages.append({"role": "user", "content": entry["user"]})
                    messages.append({"role": "assistant", "content": entry["assistant"]})
            
            # Enhance the current message with educational context
            enhanced_message = self._enhance_educational_message(message, user_context)
            messages.append({"role": "user", "content": enhanced_message})
            
            # Get response from OpenAI
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                max_tokens=600,
                temperature=0.7
            )
            
            return self._format_educational_response(response.choices[0].message.content)
            
        except openai.RateLimitError:
            return "🚫 **Teacher's Note:** The AI service is currently busy. Please wait a moment and ask your question again."
        except openai.AuthenticationError:
            return "🔑 **Teacher's Note:** There's a technical issue with our AI service. Please contact support."
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "insufficient_quota" in error_msg:
                return "💳 **Teacher's Note:** Our AI service quota has been exceeded. Please contact support to resolve this issue."
            elif "429" in error_msg:
                return "⏳ **Teacher's Note:** Too many students are asking questions right now. Please wait a moment and try again."
            else:
                return f"👨‍🏫 **Teacher's Note:** I encountered a technical issue while preparing your lesson. Let's try a different approach to your question.\n\nTechnical details: {str(e)}"

    def _enhance_educational_message(self, message: str, user_context: Any) -> str:
        """Enhance the message with educational context"""
        enhanced = f"Student question: {message}\n\n"
        
        # Add context based on user tier for personalization
        if user_context and user_context.tier:
            if user_context.tier == "premium":
                enhanced += "Note: This is a premium user, provide detailed explanations with advanced examples.\n"
            elif user_context.tier == "enterprise":
                enhanced += "Note: This is an enterprise user, include professional applications and industry examples.\n"
        
        enhanced += "Please provide a clear, educational response that helps the student understand the concept thoroughly."
        
        return enhanced

    def _format_educational_response(self, response: str) -> str:
        """Format the response with educational structure"""
        # Add teacher emoji and structure if not already present
        if not response.startswith("👨‍🏫"):
            response = f"👨‍🏫 **Teacher's Explanation:**\n\n{response}"
        
        # Add learning tips if the response is substantial
        if len(response) > 200:
            response += "\n\n💡 **Learning Tip:** Try to explain this concept in your own words to reinforce your understanding!"
        
        return response

    def _get_demo_response(self, message: str) -> str:
        """Generate demo educational responses"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['explain', 'what is', 'how does', 'define']):
            return """👨‍🏫 **Teacher's Demo Explanation:**

I'd be happy to explain that concept! In full mode with AI access, I would:

📚 **Break down the topic** into digestible parts
🔍 **Provide clear examples** and analogies  
📝 **Give step-by-step explanations**
💡 **Suggest practice exercises**
📖 **Recommend additional resources**

*This is a demo response showcasing the Teacher agent's educational approach. With OpenAI API access, I'd provide detailed, personalized explanations!*

💡 **Learning Tip:** Try to explain concepts in your own words to reinforce understanding!"""
        
        elif any(word in message_lower for word in ['homework', 'assignment', 'study']):
            return """👨‍🏫 **Teacher's Study Guidance:**

Let me help you with your studies! In full mode, I would:

📋 **Analyze your assignment** requirements
⏰ **Create a study schedule** 
📚 **Break tasks** into manageable steps
🎯 **Provide focused guidance** for each topic
✅ **Help you track** your progress

*This is a demo response. With full AI access, I'd provide personalized study plans and detailed academic support!*

💡 **Learning Tip:** Start with the most challenging topics when your mind is fresh!"""
        
        else:
            return f"""👨‍🏫 **Teacher's Demo Response:**

You asked: "{message}"

As your educational assistant, I would normally provide:
- Clear, structured explanations
- Step-by-step guidance  
- Relevant examples and analogies
- Practice suggestions
- Additional learning resources

*Currently in demo mode. With OpenAI API access, I'd give you detailed, personalized educational support!*

💡 **Learning Tip:** Active learning through questions like yours is the key to mastery!"""

    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "Explain complex concepts clearly",
            "Provide step-by-step tutorials",
            "Create learning plans",
            "Suggest practice exercises",
            "Adapt to different learning styles",
            "Offer educational resources"
        ]

    def get_specializations(self) -> List[str]:
        """Return list of subject specializations"""
        return [
            "Mathematics",
            "Science",
            "Programming",
            "Language Arts",
            "History",
            "General Education"
        ] 