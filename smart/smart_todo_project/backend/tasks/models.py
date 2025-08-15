from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    original_description = models.TextField(blank=True)  # Store original before AI enhancement
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    ai_priority_score = models.FloatField(default=0.5)  # AI-calculated priority (0-1)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='TODO')
    deadline = models.DateTimeField(null=True, blank=True)
    ai_suggested_deadline = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.IntegerField(null=True, blank=True)  # in minutes
    tags = models.CharField(max_length=500, blank=True)  # Comma-separated tags
    ai_suggested_tags = models.CharField(max_length=500, blank=True)
    context_based_notes = models.TextField(blank=True)  # AI-generated context notes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # For multi-user support later
    
    class Meta:
        ordering = ['-ai_priority_score', '-created_at']
    
    def save(self, *args, **kwargs):
        if self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = datetime.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class ContextEntry(models.Model):
    SOURCE_CHOICES = [
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
        ('NOTES', 'Notes'),
        ('CALENDAR', 'Calendar'),
        ('OTHER', 'Other'),
    ]
    
    content = models.TextField()
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    sender = models.CharField(max_length=200, blank=True)  # Who sent the message/email
    timestamp = models.DateTimeField()
    processed_insights = models.JSONField(default=dict)  # Store AI-extracted insights
    keywords = models.CharField(max_length=500, blank=True)  # Extracted keywords
    sentiment_score = models.FloatField(null=True, blank=True)  # Sentiment analysis
    priority_indicators = models.JSONField(default=list)  # Words/phrases indicating priority
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.source_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class TaskContextLink(models.Model):
    """Links tasks to relevant context entries"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    context_entry = models.ForeignKey(ContextEntry, on_delete=models.CASCADE)
    relevance_score = models.FloatField(default=0.0)  # How relevant this context is to the task
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['task', 'context_entry']