import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .ai_client import AIClient
from .context_processor import ContextProcessor

class TaskAnalyzer:
    def __init__(self):
        self.ai_client = AIClient()
        self.context_processor = ContextProcessor()
        
    def analyze_task_priority(self, task_title: str, task_description: str, 
                            context_data: List[Dict] = None) -> float:
        """Analyze task priority using AI and context"""
        context_info = ""
        if context_data:
            # Get recent high-priority contexts
            recent_contexts = [ctx for ctx in context_data 
                             if ctx.get('urgency_level', 0) > 5][:3]
            
            if recent_contexts:
                context_info = "\nRecent important context:\n"
                for ctx in recent_contexts:
                    context_info += f"- {ctx.get('content', '')[:100]}...\n"
        
        prompt = f"""
        Analyze the priority of this task on a scale of 0.0 to 1.0 (where 1.0 is highest priority):
        
        Task: {task_title}
        Description: {task_description}
        {context_info}
        
        Consider:
        1. Urgency and deadlines
        2. Impact and importance
        3. Dependencies and context
        4. Keywords indicating priority
        
        Respond with only a decimal number between 0.0 and 1.0
        """
        
        try:
            result = self.ai_client.analyze_with_ai(prompt, 100)
            # Extract number from response
            import re
            numbers = re.findall(r'0\.\d+|1\.0', result)
            if numbers:
                return float(numbers[0])
            else:
                return 0.5  # Default medium priority
        except:
            return self._calculate_fallback_priority(task_title, task_description)
    
    def suggest_deadline(self, task_title: str, task_description: str, 
                        current_workload: int = 5) -> datetime:
        """Suggest deadline based on task complexity and current workload"""
        prompt = f"""
        Suggest a realistic deadline for this task. Consider the complexity and current workload.
        
        Task: {task_title}
        Description: {task_description}
        Current workload (1-10): {current_workload}
        
        Based on the task complexity, suggest how many days from now this should be completed.
        Respond with only a number (days from now).
        """
        
        try:
            result = self.ai_client.analyze_with_ai(prompt, 100)
            # Extract number from response
            import re
            days = re.findall(r'\d+', result)
            if days:
                days_ahead = min(int(days[0]), 30)  # Cap at 30 days
                return datetime.now() + timedelta(days=days_ahead)
            else:
                return datetime.now() + timedelta(days=3)  # Default 3 days
        except:
            return self._calculate_fallback_deadline(task_description)
    
    def suggest_category(self, task_title: str, task_description: str, 
                        existing_categories: List[str] = None) -> str:
        """Suggest task category based on content"""
        categories_info = ""
        if existing_categories:
            categories_info = f"\nExisting categories: {', '.join(existing_categories)}"
        
        prompt = f"""
        Suggest the most appropriate category for this task:
        
        Task: {task_title}
        Description: {task_description}
        {categories_info}
        
        Choose from existing categories if possible, or suggest a new one.
        Respond with only the category name.
        """
        
        try:
            result = self.ai_client.analyze_with_ai(prompt, 50)
            return result.strip().title()
        except:
            return self._suggest_fallback_category(task_title, task_description)
    
    def suggest_tags(self, task_title: str, task_description: str) -> List[str]:
        """Suggest relevant tags for the task"""
        prompt = f"""
        Suggest 3-5 relevant tags for this task:
        
        Task: {task_title}
        Description: {task_description}
        
        Respond with comma-separated tags (no spaces after commas).
        """
        
        try:
            result = self.ai_client.analyze_with_ai(prompt, 100)
            tags = [tag.strip().lower() for tag in result.split(',')]
            return tags[:5]  # Limit to 5 tags
        except:
            return self._suggest_fallback_tags(task_title, task_description)
    
    def enhance_task_description(self, task_title: str, original_description: str,
                                relevant_contexts: List[Dict] = None) -> str:
        """Enhance task description with context-aware details"""
        context_info = ""
        if relevant_contexts:
            context_info = "\nRelevant context:\n"
            for ctx in relevant_contexts[:2]:  # Use top 2 relevant contexts
                context_info += f"- {ctx['context'].get('content', '')[:150]}...\n"
        
        prompt = f"""
        Enhance this task description with relevant details and context:
        
        Original Task: {task_title}
        Current Description: {original_description}
        {context_info}
        
        Provide an enhanced description that includes:
        1. Clear objectives
        2. Relevant context
        3. Potential steps or considerations
        
        Keep it concise but informative (max 200 words).
        """
        
        try:
            result = self.ai_client.analyze_with_ai(prompt, 300)
            return result.strip()
        except:
            return original_description or f"Complete the task: {task_title}"
    
    def get_comprehensive_task_analysis(self, task_title: str, task_description: str,
                                      context_entries: List[Dict] = None,
                                      existing_categories: List[str] = None,
                                      current_workload: int = 5) -> Dict[str, Any]:
        """Get comprehensive AI analysis for a task"""
        
        # Find relevant contexts
        relevant_contexts = []
        if context_entries:
            task_content = f"{task_title} {task_description}"
            relevant_contexts = self.context_processor.find_relevant_contexts(
                task_content, context_entries
            )
        
        # Run all analyses
        analysis = {
            'priority_score': self.analyze_task_priority(
                task_title, task_description, context_entries
            ),
            'suggested_deadline': self.suggest_deadline(
                task_title, task_description, current_workload
            ),
            'suggested_category': self.suggest_category(
                task_title, task_description, existing_categories
            ),
            'suggested_tags': self.suggest_tags(task_title, task_description),
            'enhanced_description': self.enhance_task_description(
                task_title, task_description, relevant_contexts
            ),
            'relevant_contexts': relevant_contexts,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return analysis
    
    def _calculate_fallback_priority(self, title: str, description: str) -> float:
        """Fallback priority calculation without AI"""
        priority_score = 0.5  # Default
        
        text = f"{title} {description}".lower()
        
        # High priority indicators
        if any(word in text for word in ['urgent', 'critical', 'asap', 'emergency']):
            priority_score = 0.9
        elif any(word in text for word in ['important', 'priority', 'deadline']):
            priority_score = 0.7
        elif any(word in text for word in ['meeting', 'call', 'presentation']):
            priority_score = 0.6
        
        return priority_score
    
    def _calculate_fallback_deadline(self, description: str) -> datetime:
        """Fallback deadline calculation without AI"""
        text = description.lower()
        
        if any(word in text for word in ['urgent', 'asap', 'today']):
            return datetime.now() + timedelta(days=1)
        elif any(word in text for word in ['tomorrow', 'soon']):
            return datetime.now() + timedelta(days=2)
        elif any(word in text for word in ['week', 'weekly']):
            return datetime.now() + timedelta(days=7)
        else:
            return datetime.now() + timedelta(days=3)
    
    def _suggest_fallback_category(self, title: str, description: str) -> str:
        """Fallback category suggestion without AI"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['meeting', 'call', 'discuss']):
            return 'Meetings'
        elif any(word in text for word in ['code', 'develop', 'program', 'bug', 'feature']):
            return 'Development'
        elif any(word in text for word in ['email', 'message', 'contact', 'reply']):
            return 'Communication'
        elif any(word in text for word in ['buy', 'purchase', 'shop', 'order']):
            return 'Shopping'
        elif any(word in text for word in ['health', 'doctor', 'exercise', 'medical']):
            return 'Health'
        elif any(word in text for word in ['clean', 'organize', 'home', 'house']):
            return 'Personal'
        else:
            return 'General'
    
    def _suggest_fallback_tags(self, title: str, description: str) -> List[str]:
        """Fallback tag suggestion without AI"""
        text = f"{title} {description}".lower()
        tags = []
        
        if any(word in text for word in ['urgent', 'asap', 'critical']):
            tags.append('urgent')
        if any(word in text for word in ['meeting', 'call']):
            tags.append('meeting')
        if any(word in text for word in ['work', 'office', 'project']):
            tags.append('work')
        if any(word in text for word in ['personal', 'home', 'family']):
            tags.append('personal')
        if any(word in text for word in ['follow-up', 'followup', 'follow']):
            tags.append('follow-up')
        
        # Add generic tag if no specific ones found
        if not tags:
            tags.append('task')
        
        return tags[:3]