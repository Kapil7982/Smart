import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .ai_client import AIClient

class ContextProcessor:
    def __init__(self):
        self.ai_client = AIClient()
        self.priority_keywords = [
            'urgent', 'asap', 'immediately', 'deadline', 'due', 'important',
            'critical', 'priority', 'rush', 'emergency', 'today', 'tomorrow'
        ]
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Remove special characters and convert to lowercase
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Filter out common words and get meaningful keywords
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return list(set(keywords))[:10]  # Return top 10 unique keywords
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text (0-1, where 1 is most positive)"""
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'happy', 'excited', 'pleased', 'satisfied'
        ]
        negative_words = [
            'bad', 'terrible', 'awful', 'hate', 'dislike', 'angry', 'frustrated',
            'upset', 'annoyed', 'disappointed', 'worried', 'stressed', 'urgent'
        ]
        
        text_lower = text.lower()
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        total_score = positive_score + negative_score
        if total_score == 0:
            return 0.5  # Neutral
        
        return positive_score / total_score
    
    def detect_priority_indicators(self, text: str) -> List[str]:
        """Detect words/phrases that indicate priority"""
        found_indicators = []
        text_lower = text.lower()
        
        for keyword in self.priority_keywords:
            if keyword in text_lower:
                found_indicators.append(keyword)
        
        return found_indicators
    
    def extract_dates_and_times(self, text: str) -> List[str]:
        """Extract potential dates and times from text"""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'today|tomorrow|yesterday',
            r'monday|tuesday|wednesday|thursday|friday|saturday|sunday',
            r'next week|this week|next month',
            r'\d{1,2}:\d{2}\s*(am|pm)?'  # Time patterns
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            dates_found.extend(matches)
        
        return dates_found
    
    def process_context_entry(self, content: str, source_type: str) -> Dict[str, Any]:
        """Process a single context entry and extract insights"""
        insights = {
            'keywords': self.extract_keywords(content),
            'sentiment_score': self.analyze_sentiment(content),
            'priority_indicators': self.detect_priority_indicators(content),
            'dates_mentioned': self.extract_dates_and_times(content),
            'word_count': len(content.split()),
            'has_deadline_mention': any(word in content.lower() 
                                      for word in ['deadline', 'due', 'by']),
            'urgency_level': self._calculate_urgency(content)
        }
        
        # Use AI for deeper analysis if available
        try:
            ai_prompt = f"""
            Analyze this {source_type.lower()} message and extract key insights:
            
            Content: "{content}"
            
            Please identify:
            1. Main topic or subject
            2. Any mentioned deadlines or time constraints
            3. Priority level (1-10)
            4. Relevant project or category
            5. Action items mentioned
            
            Respond in JSON format with keys: topic, deadlines, priority, category, actions
            """
            
            ai_response = self.ai_client.analyze_with_ai(ai_prompt, 500)
            try:
                ai_insights = json.loads(ai_response)
                insights['ai_analysis'] = ai_insights
            except json.JSONDecodeError:
                insights['ai_analysis'] = {'raw_response': ai_response}
        except Exception as e:
            insights['ai_analysis'] = {'error': str(e)}
        
        return insights
    
    def _calculate_urgency(self, text: str) -> int:
        """Calculate urgency level 1-10 based on text content"""
        urgency_score = 1
        text_lower = text.lower()
        
        # High urgency indicators
        if any(word in text_lower for word in ['urgent', 'asap', 'immediately', 'emergency']):
            urgency_score += 4
        
        # Medium urgency indicators
        if any(word in text_lower for word in ['important', 'priority', 'deadline']):
            urgency_score += 2
        
        # Time-based urgency
        if any(word in text_lower for word in ['today', 'now', 'tonight']):
            urgency_score += 3
        elif any(word in text_lower for word in ['tomorrow', 'this week']):
            urgency_score += 2
        
        # Multiple exclamation marks
        urgency_score += min(text.count('!'), 2)
        
        return min(urgency_score, 10)
    
    def find_relevant_contexts(self, task_content: str, context_entries: List[Dict]) -> List[Dict]:
        """Find context entries relevant to a task"""
        task_keywords = set(self.extract_keywords(task_content))
        relevant_contexts = []
        
        for context in context_entries:
            context_keywords = set(context.get('keywords', []))
            
            # Calculate relevance score based on keyword overlap
            overlap = task_keywords.intersection(context_keywords)
            relevance_score = len(overlap) / max(len(task_keywords), 1)
            
            if relevance_score > 0.1:  # Minimum relevance threshold
                relevant_contexts.append({
                    'context': context,
                    'relevance_score': relevance_score,
                    'matching_keywords': list(overlap)
                })
        
        # Sort by relevance score
        relevant_contexts.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_contexts[:5]  # Return top 5 most relevant