"""
Simplified Enhanced Information Retrieval Service
Basic implementation without complex NLP dependencies for immediate functionality
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
import json
import requests
from urllib.parse import urljoin, urlparse

# Set up minimal logging - Only errors and warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMaritimeNLPProcessor:
    """Simplified maritime content processor without heavy NLP dependencies"""
    
    def __init__(self):
        self.maritime_keywords = [
            'storm', 'hurricane', 'gale', 'wind', 'wave', 'sea', 'ocean',
            'ship', 'vessel', 'boat', 'navigation', 'maritime', 'coast',
            'harbor', 'port', 'safety', 'weather', 'warning', 'alert'
        ]
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract maritime keywords from text"""
        text_lower = text.lower()
        found_keywords = []
        for keyword in self.maritime_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        return found_keywords
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Simple sentiment analysis"""
        # Basic sentiment analysis using keyword counting
        positive_words = ['safe', 'calm', 'clear', 'good', 'favorable']
        negative_words = ['danger', 'warning', 'storm', 'rough', 'hazard', 'risk']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return {'positive': 0.5, 'negative': 0.5, 'neutral': 0.5}
        
        return {
            'positive': positive_count / total if total > 0 else 0,
            'negative': negative_count / total if total > 0 else 0,
            'neutral': 1 - (positive_count + negative_count) / total if total > 0 else 0.5
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Simple entity extraction"""
        # Basic pattern matching for locations and dates
        entities = {
            'locations': [],
            'dates': [],
            'organizations': []
        }
        
        # Simple location patterns (coastal areas, seas, etc.)
        location_patterns = [
            r'[A-Z][a-z]+ (Bay|Sea|Ocean|Coast|Harbor|Port)',
            r'(Atlantic|Pacific|Indian|Arctic) Ocean',
            r'Gulf of [A-Z][a-z]+'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            entities['locations'].extend(matches)
        
        # Simple date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            entities['dates'].extend(matches)
        
        return entities
    
    def categorize_content(self, text: str, title: str = "") -> str:
        """Categorize maritime content"""
        combined_text = (title + " " + text).lower()
        
        if any(word in combined_text for word in ['warning', 'alert', 'danger']):
            return 'warning'
        elif any(word in combined_text for word in ['forecast', 'prediction', 'outlook']):
            return 'forecast'
        elif any(word in combined_text for word in ['news', 'report', 'incident']):
            return 'news'
        elif any(word in combined_text for word in ['regulation', 'rule', 'law']):
            return 'regulation'
        else:
            return 'general'

class SimpleEnhancedIRService:
    """Simplified Enhanced Information Retrieval Service"""
    
    def __init__(self):
        self.nlp_processor = SimpleMaritimeNLPProcessor()
        self.content_sources = [
            {
                'name': 'NOAA Marine Weather',
                'url': 'https://marine.weather.gov/',
                'type': 'rss',
                'active': True
            },
            {
                'name': 'Coast Guard News',
                'url': 'https://www.uscg.mil/news/',
                'type': 'web',
                'active': True
            }
        ]
        
        logger.info("Simple Enhanced IR Service initialized")
    
    async def search_maritime_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for maritime content with basic processing"""
        try:
            # Simulate content search with mock data for now
            mock_results = [
                {
                    'title': f'Maritime Weather Update - {query}',
                    'content': f'Current maritime conditions related to {query}. Weather patterns show moderate conditions.',
                    'source': 'NOAA Marine Weather',
                    'url': 'https://marine.weather.gov/forecast',
                    'published': datetime.now().isoformat(),
                    'relevance_score': 0.8,
                    'category': 'forecast',
                    'keywords': self.nlp_processor.extract_keywords(query),
                    'sentiment': self.nlp_processor.analyze_sentiment(f'Maritime conditions for {query}')
                },
                {
                    'title': f'Safety Notice - {query} Area',
                    'content': f'Safety information for maritime operations in {query} region. Current conditions are generally favorable.',
                    'source': 'Coast Guard',
                    'url': 'https://www.uscg.mil/safety',
                    'published': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'relevance_score': 0.7,
                    'category': 'safety',
                    'keywords': self.nlp_processor.extract_keywords(query),
                    'sentiment': self.nlp_processor.analyze_sentiment(f'Safety information for {query}')
                }
            ]
            
            return mock_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching maritime content: {e}")
            return []
    
    async def process_document(self, content: str, title: str = "", source: str = "") -> Dict[str, Any]:
        """Process a maritime document with basic NLP"""
        try:
            processed = {
                'original_content': content,
                'title': title,
                'source': source,
                'processed_at': datetime.now().isoformat(),
                'keywords': self.nlp_processor.extract_keywords(content),
                'sentiment': self.nlp_processor.analyze_sentiment(content),
                'entities': self.nlp_processor.extract_entities(content),
                'category': self.nlp_processor.categorize_content(content, title),
                'word_count': len(content.split()),
                'summary': content[:200] + "..." if len(content) > 200 else content
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'original_content': content,
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
    
    async def get_latest_maritime_bulletins(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get latest maritime bulletins with basic processing"""
        try:
            # Mock maritime bulletins for now
            bulletins = [
                {
                    'title': 'Marine Weather Forecast',
                    'content': 'Current marine weather conditions show moderate seas with winds from the southeast at 10-15 knots.',
                    'issued': datetime.now().isoformat(),
                    'valid_until': (datetime.now() + timedelta(hours=24)).isoformat(),
                    'priority': 'normal',
                    'category': 'forecast'
                },
                {
                    'title': 'Navigation Safety Notice',
                    'content': 'Mariners are advised of ongoing construction work in harbor area. Exercise caution.',
                    'issued': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'valid_until': (datetime.now() + timedelta(days=7)).isoformat(),
                    'priority': 'high',
                    'category': 'safety'
                }
            ]
            
            # Process each bulletin
            processed_bulletins = []
            for bulletin in bulletins[:limit]:
                processed = await self.process_document(
                    bulletin['content'], 
                    bulletin['title'], 
                    'Maritime Authority'
                )
                processed.update(bulletin)
                processed_bulletins.append(processed)
            
            return processed_bulletins
            
        except Exception as e:
            logger.error(f"Error fetching maritime bulletins: {e}")
            return []
    
    async def analyze_content_relevance(self, content: str, context: Dict[str, Any]) -> float:
        """Analyze content relevance to given context"""
        try:
            relevance_score = 0.5  # Base score
            
            # Check for location matches
            if 'location' in context:
                location_keywords = context['location'].lower().split()
                content_lower = content.lower()
                for keyword in location_keywords:
                    if keyword in content_lower:
                        relevance_score += 0.1
            
            # Check for weather-related keywords
            weather_keywords = ['weather', 'wind', 'wave', 'storm', 'forecast']
            content_lower = content.lower()
            for keyword in weather_keywords:
                if keyword in content_lower:
                    relevance_score += 0.05
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error analyzing content relevance: {e}")
            return 0.5

# Create global instance
simple_enhanced_ir_service = SimpleEnhancedIRService()