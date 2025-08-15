from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from datetime import datetime, timedelta
from .models import Task, Category, ContextEntry, TaskContextLink
from .serializers import (
    TaskSerializer, TaskCreateSerializer, CategorySerializer,
    ContextEntrySerializer, TaskAIAnalysisSerializer
)
from ai_module.task_analyzer import TaskAnalyzer
from ai_module.context_processor import ContextProcessor

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.annotate(
            task_count=Count('task')
        ).order_by('-usage_count', 'name')

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer
    
    def get_queryset(self):
        queryset = Task.objects.select_related('category').prefetch_related(
            'taskcontextlink_set__context_entry'
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Search in title and description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        # Sort by priority score and creation date
        return queryset.order_by('-ai_priority_score', '-created_at')
    
    @action(detail=False, methods=['post'])
    def ai_analysis(self, request):
        """Get AI analysis for task data without creating a task"""
        serializer = TaskAIAnalysisSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Get recent context for analysis
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
            
            # Get existing categories
            existing_categories = list(Category.objects.values_list('name', flat=True))
            
            # Run AI analysis
            analyzer = TaskAnalyzer()
            analysis = analyzer.get_comprehensive_task_analysis(
                data['task_title'],
                data['task_description'],
                context_data,
                existing_categories,
                data['current_workload']
            )
            
            # Format response
            response_data = {
                'priority_score': analysis['priority_score'],
                'priority_level': self._get_priority_level(analysis['priority_score']),
                'suggested_deadline': analysis['suggested_deadline'].isoformat(),
                'suggested_category': analysis['suggested_category'],
                'suggested_tags': analysis['suggested_tags'],
                'enhanced_description': analysis['enhanced_description'],
                'relevant_contexts_count': len(analysis['relevant_contexts']),
                'analysis_timestamp': analysis['analysis_timestamp']
            }
            
            return Response(response_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reanalyze(self, request, pk=None):
        """Re-run AI analysis on existing task"""
        task = self.get_object()
        
        # Get recent context
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
        
        # Get existing categories
        existing_categories = list(Category.objects.values_list('name', flat=True))
        
        # Run AI analysis
        analyzer = TaskAnalyzer()
        analysis = analyzer.get_comprehensive_task_analysis(
            task.title,
            task.original_description or task.description,
            context_data,
            existing_categories
        )
        
        # Update task with new analysis
        task.ai_priority_score = analysis['priority_score']
        task.ai_suggested_deadline = analysis['suggested_deadline']
        task.ai_suggested_tags = ','.join(analysis['suggested_tags'])
        task.description = analysis['enhanced_description']
        task.context_based_notes = f"Re-analyzed on {datetime.now().strftime('%Y-%m-%d %H:%M')}: " \
                                  f"Priority {analysis['priority_score']:.2f}"
        
        # Update category if suggested
        if analysis['suggested_category']:
            category, created = Category.objects.get_or_create(
                name=analysis['suggested_category'],
                defaults={'color': '#3B82F6'}
            )
            task.category = category
        
        task.save()
        
        # Link relevant contexts
        for rel_ctx in analysis['relevant_contexts']:
            try:
                context_entry = ContextEntry.objects.get(
                    id=rel_ctx['context']['id']
                )
                TaskContextLink.objects.update_or_create(
                    task=task,
                    context_entry=context_entry,
                    defaults={'relevance_score': rel_ctx['relevance_score']}
                )
            except ContextEntry.DoesNotExist:
                continue
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get task statistics"""
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status='COMPLETED').count()
        pending_tasks = Task.objects.filter(status__in=['TODO', 'IN_PROGRESS']).count()
        high_priority_tasks = Task.objects.filter(ai_priority_score__gte=0.7).count()
        overdue_tasks = Task.objects.filter(
            deadline__lt=datetime.now(),
            status__in=['TODO', 'IN_PROGRESS']
        ).count()
        
        # Category distribution
        category_stats = Category.objects.annotate(
            task_count=Count('task')
        ).values('name', 'task_count')
        
        return Response({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'high_priority_tasks': high_priority_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'category_distribution': list(category_stats)
        })
    
    def _get_priority_level(self, score):
        """Convert priority score to level"""
        if score >= 0.8:
            return 'URGENT'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'

class ContextEntryViewSet(viewsets.ModelViewSet):
    queryset = ContextEntry.objects.all()
    serializer_class = ContextEntrySerializer
    
    def get_queryset(self):
        queryset = ContextEntry.objects.all()
        
        # Filter by source type
        source_type = self.request.query_params.get('source_type')
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=from_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=to_date)
            except ValueError:
                pass
        
        return queryset.order_by('-timestamp')
    
    def perform_create(self, serializer):
        """Process context entry with AI when created"""
        context_entry = serializer.save()
        
        # Process with AI
        processor = ContextProcessor()
        insights = processor.process_context_entry(
            context_entry.content,
            context_entry.source_type
        )
        
        # Update the entry with processed insights
        context_entry.processed_insights = insights
        context_entry.keywords = ','.join(insights['keywords'])
        context_entry.sentiment_score = insights['sentiment_score']
        context_entry.priority_indicators = insights['priority_indicators']
        context_entry.save()
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple context entries at once"""
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of context entries'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_entries = []
        processor = ContextProcessor()
        
        for entry_data in request.data:
            serializer = self.get_serializer(data=entry_data)
            if serializer.is_valid():
                context_entry = serializer.save()
                
                # Process with AI
                insights = processor.process_context_entry(
                    context_entry.content,
                    context_entry.source_type
                )
                
                # Update with insights
                context_entry.processed_insights = insights
                context_entry.keywords = ','.join(insights['keywords'])
                context_entry.sentiment_score = insights['sentiment_score']
                context_entry.priority_indicators = insights['priority_indicators']
                context_entry.save()
                
                created_entries.append(context_entry)
        
        serializer = self.get_serializer(created_entries, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def insights_summary(self, request):
        """Get summary of context insights"""
        # Get recent context entries (last 30 days)
        recent_contexts = ContextEntry.objects.filter(
            created_at__gte=datetime.now() - timedelta(days=30)
        )
        
        total_entries = recent_contexts.count()
        if total_entries == 0:
            return Response({'message': 'No recent context entries found'})
        
        # Calculate averages and distributions
        avg_sentiment = recent_contexts.aggregate(
            avg_sentiment=models.Avg('sentiment_score')
        )['avg_sentiment'] or 0.5
        
        # Source type distribution
        source_distribution = recent_contexts.values('source_type').annotate(
            count=Count('id')
        )
        
        # Most common keywords
        all_keywords = []
        for entry in recent_contexts:
            if entry.keywords:
                all_keywords.extend(entry.keywords.split(','))
        
        from collections import Counter
        common_keywords = Counter(all_keywords).most_common(10)
        
        # High priority entries
        high_priority_count = sum(
            1 for entry in recent_contexts
            if entry.processed_insights.get('urgency_level', 1) > 6
        )
        
        return Response({
            'total_entries': total_entries,
            'average_sentiment': avg_sentiment,
            'source_distribution': list(source_distribution),
            'common_keywords': common_keywords,
            'high_priority_entries': high_priority_count,
            'analysis_period': '30 days'
        })