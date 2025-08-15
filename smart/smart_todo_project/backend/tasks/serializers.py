from rest_framework import serializers
from .models import Task, Category, ContextEntry, TaskContextLink
from ai_module.task_analyzer import TaskAnalyzer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'usage_count', 'created_at']

class ContextEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextEntry
        fields = [
            'id', 'content', 'source_type', 'sender', 'timestamp',
            'processed_insights', 'keywords', 'sentiment_score',
            'priority_indicators', 'created_at'
        ]
        read_only_fields = ['processed_insights', 'keywords', 'sentiment_score', 'priority_indicators']

class TaskContextLinkSerializer(serializers.ModelSerializer):
    context_entry = ContextEntrySerializer(read_only=True)
    
    class Meta:
        model = TaskContextLink
        fields = ['id', 'context_entry', 'relevance_score', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    related_contexts = TaskContextLinkSerializer(
        source='taskcontextlink_set', many=True, read_only=True
    )
    tags_list = serializers.SerializerMethodField()
    ai_suggested_tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'original_description',
            'category', 'category_name', 'priority', 'ai_priority_score',
            'status', 'deadline', 'ai_suggested_deadline',
            'estimated_duration', 'tags', 'tags_list',
            'ai_suggested_tags', 'ai_suggested_tags_list',
            'context_based_notes', 'created_at', 'updated_at',
            'completed_at', 'related_contexts'
        ]
    
    def get_tags_list(self, obj):
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
        return []
    
    def get_ai_suggested_tags_list(self, obj):
        if obj.ai_suggested_tags:
            return [tag.strip() for tag in obj.ai_suggested_tags.split(',') if tag.strip()]
        return []

class TaskCreateSerializer(serializers.ModelSerializer):
    use_ai_enhancement = serializers.BooleanField(default=True, write_only=True)
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'category', 'priority',
            'deadline', 'estimated_duration', 'tags', 'use_ai_enhancement'
        ]
    
    def create(self, validated_data):
        use_ai = validated_data.pop('use_ai_enhancement', True)
        task = Task(**validated_data)
        
        # Store original description
        task.original_description = task.description
        
        if use_ai:
            # Get AI analysis
            analyzer = TaskAnalyzer()
            
            # Get existing categories for suggestions
            existing_categories = list(Category.objects.values_list('name', flat=True))
            
            # Get recent context entries (last 7 days)
            from datetime import datetime, timedelta
            recent_contexts = ContextEntry.objects.filter(
                created_at__gte=datetime.now() - timedelta(days=7)
            )
            context_data = []
            for ctx in recent_contexts:
                context_data.append({
                    'content': ctx.content,
                    'keywords': ctx.keywords.split(',') if ctx.keywords else [],
                    'urgency_level': ctx.processed_insights.get('urgency_level', 1),
                    'sentiment_score': ctx.sentiment_score or 0.5
                })
            
            # Get comprehensive analysis
            analysis = analyzer.get_comprehensive_task_analysis(
                task.title,
                task.description,
                context_data,
                existing_categories
            )
            
            # Apply AI suggestions
            task.ai_priority_score = analysis['priority_score']
            task.ai_suggested_deadline = analysis['suggested_deadline']
            task.ai_suggested_tags = ','.join(analysis['suggested_tags'])
            
            # Enhance description if original is short
            if len(task.description or '') < 50:
                task.description = analysis['enhanced_description']
            
            task.context_based_notes = f"AI Analysis: Priority {analysis['priority_score']:.2f}, " \
                                     f"Suggested deadline: {analysis['suggested_deadline'].strftime('%Y-%m-%d')}"
            
            # Set or create category
            suggested_category = analysis['suggested_category']
            if suggested_category:
                category, created = Category.objects.get_or_create(
                    name=suggested_category,
                    defaults={'color': '#3B82F6'}
                )
                task.category = category
        
        task.save()
        return task

class TaskAIAnalysisSerializer(serializers.Serializer):
    task_title = serializers.CharField(max_length=200)
    task_description = serializers.CharField(required=False, allow_blank=True)
    current_workload = serializers.IntegerField(default=5, min_value=1, max_value=10)
    
    def validate(self, data):
        if not data.get('task_description'):
            data['task_description'] = ''
        return data