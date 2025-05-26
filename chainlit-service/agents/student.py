import os
import openai
from typing import List, Dict, Any, Optional
from config import config

class StudentAgent:
    """
    Student Agent that acts as a learning companion and study partner.
    Provides peer-level support, study strategies, and collaborative learning.
    """
    
    def __init__(self):
        self.name = "Student"
        self.role = "Learning Companion"
        self.system_prompt = """You are an enthusiastic and supportive study partner. Your role is to:

1. Act as a peer learner who understands the challenges of studying
2. Share study strategies and techniques that work
3. Help break down overwhelming tasks into manageable steps
4. Provide motivation and encouragement during difficult topics
5. Suggest collaborative learning approaches
6. Share relatable experiences and study tips
7. Help with practice problems and review sessions

Use a friendly, encouraging tone that feels like talking to a supportive classmate. Be enthusiastic about learning and share the excitement of discovery."""

    async def process_message(self, message: str, history: List[Dict], user_context: Any) -> str:
        """Process a message with peer learning focus"""
        # Check if demo mode is enabled
        if config.DEMO_MODE:
            return self._get_demo_response(message)
        
        try:
            # Prepare conversation context with student perspective
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add relevant history for context
            for entry in history[-3:]:  # Last 3 conversations for context
                if entry.get("agent") == "student":  # Only include student conversations
                    messages.append({"role": "user", "content": entry["user"]})
                    messages.append({"role": "assistant", "content": entry["assistant"]})
            
            # Enhance the message with peer learning context
            enhanced_message = self._enhance_peer_message(message, user_context)
            messages.append({"role": "user", "content": enhanced_message})
            
            # Get response from OpenAI
            client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                max_tokens=600,
                temperature=0.8  # Slightly higher temperature for more conversational tone
            )
            
            return self._format_peer_response(response.choices[0].message.content)
            
        except openai.RateLimitError:
            return "🚫 **Study Buddy:** The AI service is swamped right now! Let's take a quick study break and try again in a few minutes."
        except openai.AuthenticationError:
            return "🔑 **Study Buddy:** There's a tech issue on our end. Let me know if this keeps happening!"
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "insufficient_quota" in error_msg:
                return "💳 **Study Buddy:** Looks like we've hit our AI service limit. Time to contact support - they'll sort this out!"
            elif "429" in error_msg:
                return "⏳ **Study Buddy:** Whoa, lots of students studying right now! Let's wait a moment and try again."
            else:
                return f"👨‍🎓 **Study Buddy:** I hit a technical snag, but don't worry! Let's figure this out together. Can you try rephrasing your question?\n\nTech details: {str(e)}"

    def _enhance_peer_message(self, message: str, user_context: Any) -> str:
        """Enhance the message with peer learning context"""
        enhanced = f"Study buddy question: {message}\n\n"
        
        # Add context based on user tier for personalization
        if user_context and user_context.tier:
            if user_context.tier == "premium":
                enhanced += "Note: This user has access to premium features, suggest advanced study techniques.\n"
            elif user_context.tier == "enterprise":
                enhanced += "Note: This user might be studying for professional development, include career-relevant tips.\n"
        
        enhanced += "Respond as a supportive study partner who understands the challenges of learning and can offer practical, peer-level advice."
        
        return enhanced

    def _format_peer_response(self, response: str) -> str:
        """Format the response with peer learning structure"""
        # Add student emoji and structure if not already present
        if not response.startswith("👨‍🎓"):
            response = f"👨‍🎓 **Study Buddy:**\n\n{response}"
        
        # Add motivational elements for longer responses
        if len(response) > 200:
            motivational_tips = [
                "\n\n🎯 **Study Tip:** Take breaks every 25-30 minutes to keep your brain fresh!",
                "\n\n📚 **Remember:** Every expert was once a beginner. You've got this!",
                "\n\n⭐ **Pro Tip:** Try teaching this concept to someone else - it really helps solidify your understanding!",
                "\n\n🚀 **Motivation:** Each question you ask is a step closer to mastery!",
                "\n\n💪 **Keep Going:** The fact that you're asking questions shows you're actively learning!"
            ]
            import random
            response += random.choice(motivational_tips)
        
        return response

    def _get_demo_response(self, message: str) -> str:
        """Generate demo peer learning responses"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['stressed', 'overwhelmed', 'difficult', 'hard']):
            return """👨‍🎓 **Study Buddy:**

Hey, I totally get it! We've all been there. In full mode, I'd help you:

😤 **Break down** what's overwhelming you
🎯 **Prioritize** the most important tasks
⏰ **Create a manageable** study schedule
🧘 **Find stress-relief** techniques that work
👥 **Connect** with study groups or resources

*This is a demo response showing how I'd support you as a study partner. With AI access, I'd give personalized advice based on your specific situation!*

🚀 **Motivation:** Remember, every expert was once a beginner. You've got this!"""
        
        elif any(word in message_lower for word in ['study tips', 'how to study', 'study better']):
            return """👨‍🎓 **Study Buddy's Tips:**

Great question! Here are some study strategies I'd share:

🍅 **Pomodoro Technique** - 25 min study, 5 min break
📝 **Active Recall** - Test yourself instead of just re-reading
🔄 **Spaced Repetition** - Review material at increasing intervals
🗺️ **Mind Maps** - Visual connections between concepts
👥 **Study Groups** - Explain concepts to each other

*In full mode with AI access, I'd customize these strategies based on your learning style and specific subjects!*

💪 **Keep Going:** The fact that you're asking about study tips shows you're committed to improvement!"""
        
        else:
            return f"""👨‍🎓 **Study Buddy:**

You said: "{message}"

As your learning companion, I'd normally help with:
- Study motivation and encouragement
- Breaking down complex topics
- Sharing effective study techniques
- Practice problem solving
- Exam preparation strategies

*Currently in demo mode! With full AI access, I'd be your enthusiastic study partner, ready to tackle any academic challenge together!*

⭐ **Pro Tip:** Teaching someone else what you've learned is one of the best ways to solidify your own understanding!"""

    def get_study_strategies(self) -> List[str]:
        """Return list of study strategies this agent can help with"""
        return [
            "Pomodoro Technique",
            "Active Recall",
            "Spaced Repetition",
            "Mind Mapping",
            "Practice Testing",
            "Collaborative Study",
            "Note-taking Methods",
            "Time Management"
        ]

    def get_support_areas(self) -> List[str]:
        """Return list of areas where this agent provides support"""
        return [
            "Study motivation",
            "Exam preparation",
            "Assignment planning",
            "Concept review",
            "Practice problems",
            "Study group coordination",
            "Learning difficulties",
            "Academic stress management"
        ]

    def get_learning_styles(self) -> List[str]:
        """Return learning styles this agent can adapt to"""
        return [
            "Visual Learning",
            "Auditory Learning", 
            "Kinesthetic Learning",
            "Reading/Writing Learning",
            "Social Learning",
            "Solitary Learning"
        ] 