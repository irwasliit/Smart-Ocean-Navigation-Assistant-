"""
Enhanced Information Retrieval Service with NLP
Processes maritime bulletins, weather reports, and ocean data using advanced NLP techniques
"""

import asyncio
import aiohttp
import feedparser
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag
import spacy
from textblob import TextBlob
import requests
from urllib.parse import urljoin, urlparse
import hashlib

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

try:
    nltk.data.find('chunkers/maxent_ne_chunker')
except LookupError:
    nltk.download('maxent_ne_chunker')

try:
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('words')

@dataclass
class ProcessedDocument:
    """Represents a processed maritime document"""
    id: str
    title: str
    content: str
    summary: str
    source: str
    url: str
    published_date: datetime
    relevance_score: float
    keywords: List[str]
    entities: List[Dict[str, Any]]
    sentiment: Dict[str, float]
    category: str
    priority: str
    metadata: Dict[str, Any]

@dataclass
class MaritimeAlert:
    """Represents a maritime safety alert"""
    alert_id: str
    alert_type: str
    severity: str
    location: Dict[str, Any]
    description: str
    effective_date: datetime
    expiry_date: Optional[datetime]
    affected_areas: List[str]
    recommendations: List[str]
    source_document: str

class MaritimeNLPProcessor:
    """Advanced NLP processor for maritime content"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
        # Maritime-specific keywords and patterns
        self.maritime_keywords = {
            'weather': ['wind', 'wave', 'storm', 'hurricane', 'typhoon', 'cyclone', 'gale', 'squall', 'fog', 'visibility'],
            'navigation': ['course', 'bearing', 'heading', 'route', 'waypoint', 'GPS', 'chart', 'compass', 'navigation'],
            'safety': ['danger', 'hazard', 'warning', 'caution', 'emergency', 'distress', 'rescue', 'safety', 'risk'],
            'vessels': ['ship', 'boat', 'vessel', 'tanker', 'cargo', 'ferry', 'yacht', 'fishing', 'commercial'],
            'locations': ['port', 'harbor', 'anchorage', 'channel', 'strait', 'bay', 'coast', 'offshore', 'territorial'],
            'operations': ['loading', 'unloading', 'departure', 'arrival', 'docking', 'anchoring', 'transit', 'passage']
        }
        
        self.severity_indicators = {
            'critical': ['emergency', 'immediate', 'critical', 'urgent', 'severe', 'extreme'],
            'high': ['warning', 'danger', 'hazard', 'significant', 'important', 'serious'],
            'medium': ['caution', 'advisory', 'notice', 'moderate', 'attention'],
            'low': ['information', 'update', 'routine', 'normal', 'standard']
        }
        
        # Load spaCy model if available
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy English model not found. Some NLP features will be limited.")
            self.nlp = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        entities = []
        
        if self.nlp:
            # Use spaCy for entity extraction
            doc = self.nlp(text)
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.8  # spaCy doesn't provide confidence scores directly
                })
        else:
            # Fallback to NLTK
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags)
            
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    entity_text = ' '.join([token for token, pos in chunk])
                    entities.append({
                        'text': entity_text,
                        'label': chunk.label(),
                        'start': -1,  # NLTK doesn't provide character positions easily
                        'end': -1,
                        'confidence': 0.6
                    })
        
        # Extract maritime-specific entities using regex
        maritime_entities = self._extract_maritime_entities(text)
        entities.extend(maritime_entities)
        
        return entities
    
    def _extract_maritime_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract maritime-specific entities using patterns"""
        entities = []
        
        # Coordinate patterns
        coord_patterns = [
            r'\d+°\d+\'[NS]\s+\d+°\d+\'[EW]',  # 12°34'N 123°45'E
            r'\d+\.\d+°[NS]\s+\d+\.\d+°[EW]',  # 12.34°N 123.45°E
            r'\d+°\d+\.\d+\'[NS]\s+\d+°\d+\.\d+\'[EW]'  # 12°34.5'N 123°45.6'E
        ]
        
        for pattern in coord_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': 'COORDINATE',
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9
                })
        
        # Time patterns
        time_patterns = [
            r'\d{1,2}:\d{2}\s*(?:UTC|GMT|Z)',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': 'TIME',
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9
                })
        
        # Vessel identification patterns
        vessel_patterns = [
            r'IMO\s+\d{7}',
            r'MMSI\s+\d{9}',
            r'Call\s+Sign\s+[A-Z0-9]+',
            r'M/V\s+[\w\s]+',
            r'S/V\s+[\w\s]+',
            r'F/V\s+[\w\s]+'
        ]
        
        for pattern in vessel_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': 'VESSEL_ID',
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8
                })
        
        return entities
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of maritime content"""
        blob = TextBlob(text)
        
        # Get polarity and subjectivity
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Convert to maritime-relevant sentiment categories
        if polarity > 0.1:
            sentiment_category = "positive"
        elif polarity < -0.1:
            sentiment_category = "negative"
        else:
            sentiment_category = "neutral"
        
        # Calculate urgency based on negative sentiment and maritime keywords
        urgency_score = 0.0
        if polarity < 0:
            urgency_score += abs(polarity) * 0.5
        
        # Check for urgent/danger keywords
        urgent_words = ['emergency', 'danger', 'critical', 'immediate', 'urgent', 'severe']
        for word in urgent_words:
            if word.lower() in text.lower():
                urgency_score += 0.2
        
        urgency_score = min(1.0, urgency_score)
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'category': sentiment_category,
            'urgency': urgency_score,
            'confidence': 0.7
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract relevant keywords from text"""
        # Tokenize and remove stop words
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
        
        # Get frequency distribution
        freq_dist = nltk.FreqDist(tokens)
        
        # Get maritime-specific keywords
        maritime_keywords = []
        for category, keywords in self.maritime_keywords.items():
            for keyword in keywords:
                if keyword in tokens:
                    maritime_keywords.append(keyword)
        
        # Combine frequent words with maritime keywords
        frequent_words = [word for word, freq in freq_dist.most_common(max_keywords)]
        
        # Prioritize maritime keywords
        all_keywords = list(set(maritime_keywords + frequent_words))
        
        return all_keywords[:max_keywords]
    
    def categorize_content(self, text: str, title: str = "") -> str:
        """Categorize maritime content"""
        combined_text = (title + " " + text).lower()
        
        category_indicators = {
            'weather_alert': ['weather', 'storm', 'wind', 'wave', 'hurricane', 'gale', 'forecast'],
            'navigation_warning': ['navigation', 'warning', 'chart', 'buoy', 'lighthouse', 'channel'],
            'safety_bulletin': ['safety', 'accident', 'incident', 'rescue', 'emergency', 'distress'],
            'port_notice': ['port', 'harbor', 'berth', 'anchorage', 'terminal', 'docking'],
            'regulatory_update': ['regulation', 'rule', 'compliance', 'requirement', 'law', 'policy'],
            'traffic_advisory': ['traffic', 'vessel', 'congestion', 'routing', 'separation', 'scheme'],
            'environmental_notice': ['pollution', 'environment', 'protected', 'marine', 'conservation'],
            'general_information': []  # Default category
        }
        
        category_scores = {}
        for category, indicators in category_indicators.items():
            score = sum(1 for indicator in indicators if indicator in combined_text)
            category_scores[category] = score
        
        # Return category with highest score, or 'general_information' if tied at 0
        best_category = max(category_scores.items(), key=lambda x: x[1])
        return best_category[0] if best_category[1] > 0 else 'general_information'
    
    def determine_priority(self, text: str, sentiment: Dict[str, float]) -> str:
        """Determine priority level of maritime content"""
        text_lower = text.lower()
        
        # Check for critical indicators
        critical_count = sum(1 for word in self.severity_indicators['critical'] if word in text_lower)
        high_count = sum(1 for word in self.severity_indicators['high'] if word in text_lower)
        medium_count = sum(1 for word in self.severity_indicators['medium'] if word in text_lower)
        
        # Factor in sentiment urgency
        urgency = sentiment.get('urgency', 0)
        
        if critical_count > 0 or urgency > 0.8:
            return 'critical'
        elif high_count > 0 or urgency > 0.6:
            return 'high'
        elif medium_count > 0 or urgency > 0.3:
            return 'medium'
        else:
            return 'low'

class MaritimeContentSources:
    """Manages various maritime information sources"""
    
    def __init__(self):
        self.sources = {
            'noaa_weather': {
                'url': 'https://www.weather.gov/marine/',
                'rss_feeds': [
                    'https://www.weather.gov/source/crh/marine.xml'
                ]
            },
            'uscg_navwarn': {
                'url': 'https://www.navcen.uscg.gov/',
                'rss_feeds': [
                    'https://www.navcen.uscg.gov/rss/NavWarnings.xml'
                ]
            },
            'imo_circulars': {
                'url': 'https://www.imo.org/',
                'rss_feeds': [
                    'https://www.imo.org/en/MediaCentre/PressBriefings/pages/RSS.aspx'
                ]
            },
            'admiralty_notices': {
                'url': 'https://www.admiralty.co.uk/',
                'rss_feeds': []
            }
        }
    
    async def fetch_rss_content(self, url: str) -> List[Dict[str, Any]]:
        """Fetch content from RSS feeds"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        articles = []
                        for entry in feed.entries:
                            articles.append({
                                'title': entry.get('title', ''),
                                'content': entry.get('summary', entry.get('description', '')),
                                'url': entry.get('link', ''),
                                'published': self._parse_date(entry.get('published', '')),
                                'source': feed.feed.get('title', 'Unknown'),
                                'raw_entry': entry
                            })
                        
                        return articles
        except Exception as e:
            print(f"Error fetching RSS from {url}: {e}")
            return []
    
    async def fetch_web_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse web content"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Extract text content
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        text = soup.get_text()
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return {
                            'title': soup.title.string if soup.title else '',
                            'content': text,
                            'url': url,
                            'fetched': datetime.now()
                        }
        except Exception as e:
            print(f"Error fetching web content from {url}: {e}")
            return None
    
    def _parse_date(self, date_string: str) -> datetime:
        """Parse various date formats"""
        if not date_string:
            return datetime.now()
        
        try:
            # Try common formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # Fallback to current time
            return datetime.now()
        except:
            return datetime.now()

class EnhancedIRService:
    """Enhanced Information Retrieval Service"""
    
    def __init__(self):
        self.nlp_processor = MaritimeNLPProcessor()
        self.content_sources = MaritimeContentSources()
        self.processed_cache = {}  # Simple in-memory cache
        
    async def retrieve_and_process_content(self, sources: List[str] = None) -> List[ProcessedDocument]:
        """Retrieve and process content from multiple sources"""
        if sources is None:
            sources = ['noaa_weather', 'uscg_navwarn']
        
        all_documents = []
        
        for source_name in sources:
            if source_name in self.content_sources.sources:
                source_config = self.content_sources.sources[source_name]
                
                # Fetch RSS feeds
                for rss_url in source_config.get('rss_feeds', []):
                    articles = await self.content_sources.fetch_rss_content(rss_url)
                    
                    for article in articles:
                        processed_doc = await self._process_document(article, source_name)
                        if processed_doc:
                            all_documents.append(processed_doc)
        
        # Sort by relevance and recency
        all_documents.sort(key=lambda x: (x.relevance_score, x.published_date), reverse=True)
        
        return all_documents
    
    async def _process_document(self, raw_document: Dict[str, Any], source_name: str) -> Optional[ProcessedDocument]:
        """Process a single document using NLP"""
        try:
            content = raw_document.get('content', '')
            title = raw_document.get('title', '')
            
            if not content and not title:
                return None
            
            # Generate unique ID
            doc_id = hashlib.md5((title + content + source_name).encode()).hexdigest()
            
            # Check cache
            if doc_id in self.processed_cache:
                return self.processed_cache[doc_id]
            
            # Extract entities
            entities = self.nlp_processor.extract_entities(content)
            
            # Analyze sentiment
            sentiment = self.nlp_processor.analyze_sentiment(content)
            
            # Extract keywords
            keywords = self.nlp_processor.extract_keywords(content)
            
            # Categorize content
            category = self.nlp_processor.categorize_content(content, title)
            
            # Determine priority
            priority = self.nlp_processor.determine_priority(content, sentiment)
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(content, title, entities, keywords, sentiment)
            
            # Generate summary
            summary = self._generate_summary(content)
            
            processed_doc = ProcessedDocument(
                id=doc_id,
                title=title,
                content=content,
                summary=summary,
                source=source_name,
                url=raw_document.get('url', ''),
                published_date=raw_document.get('published', datetime.now()),
                relevance_score=relevance_score,
                keywords=keywords,
                entities=entities,
                sentiment=sentiment,
                category=category,
                priority=priority,
                metadata={
                    'processing_time': datetime.now(),
                    'content_length': len(content),
                    'entity_count': len(entities)
                }
            )
            
            # Cache the result
            self.processed_cache[doc_id] = processed_doc
            
            return processed_doc
            
        except Exception as e:
            print(f"Error processing document: {e}")
            return None
    
    def _calculate_relevance_score(self, content: str, title: str, entities: List[Dict], 
                                  keywords: List[str], sentiment: Dict[str, float]) -> float:
        """Calculate relevance score for maritime navigation"""
        score = 0.0
        
        # Base score for having content
        if content:
            score += 0.2
        
        if title:
            score += 0.1
        
        # Maritime keyword relevance
        maritime_count = 0
        for category, words in self.nlp_processor.maritime_keywords.items():
            for word in words:
                if word.lower() in content.lower() or word.lower() in title.lower():
                    maritime_count += 1
        
        # Normalize maritime keyword score
        score += min(0.4, maritime_count * 0.05)
        
        # Entity relevance
        relevant_entities = ['COORDINATE', 'TIME', 'VESSEL_ID', 'PERSON', 'GPE', 'ORG']
        entity_score = sum(0.02 for entity in entities if entity['label'] in relevant_entities)
        score += min(0.2, entity_score)
        
        # Urgency from sentiment
        urgency = sentiment.get('urgency', 0)
        score += urgency * 0.1
        
        # Recency bonus (documents from last 7 days get bonus)
        # This would need the published date, so we'll skip for now
        
        return min(1.0, score)
    
    def _generate_summary(self, content: str, max_sentences: int = 3) -> str:
        """Generate a summary of the content"""
        if not content:
            return ""
        
        sentences = sent_tokenize(content)
        
        if len(sentences) <= max_sentences:
            return content
        
        # Simple extractive summarization - take first, last, and middle sentences
        if len(sentences) >= 3:
            summary_sentences = [
                sentences[0],
                sentences[len(sentences) // 2],
                sentences[-1]
            ]
        else:
            summary_sentences = sentences[:max_sentences]
        
        return ' '.join(summary_sentences)
    
    async def search_content(self, query: str, documents: List[ProcessedDocument] = None, 
                           max_results: int = 10) -> List[ProcessedDocument]:
        """Search processed content using NLP"""
        if documents is None:
            documents = await self.retrieve_and_process_content()
        
        query_keywords = self.nlp_processor.extract_keywords(query)
        query_lower = query.lower()
        
        scored_documents = []
        
        for doc in documents:
            score = 0.0
            
            # Title match
            if any(keyword in doc.title.lower() for keyword in query_keywords):
                score += 0.3
            
            # Content match
            content_matches = sum(1 for keyword in query_keywords if keyword in doc.content.lower())
            score += min(0.4, content_matches * 0.1)
            
            # Keyword overlap
            keyword_overlap = len(set(query_keywords) & set(doc.keywords))
            score += min(0.2, keyword_overlap * 0.05)
            
            # Entity relevance
            for entity in doc.entities:
                if entity['text'].lower() in query_lower:
                    score += 0.1
            
            # Priority boost
            if doc.priority in ['critical', 'high']:
                score += 0.1
            
            if score > 0:
                scored_documents.append((doc, score))
        
        # Sort by score and return top results
        scored_documents.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_documents[:max_results]]
    
    async def extract_alerts(self, documents: List[ProcessedDocument] = None) -> List[MaritimeAlert]:
        """Extract maritime alerts from processed documents"""
        if documents is None:
            documents = await self.retrieve_and_process_content()
        
        alerts = []
        
        for doc in documents:
            if doc.priority in ['critical', 'high'] and doc.category in ['weather_alert', 'navigation_warning', 'safety_bulletin']:
                
                # Extract location from entities
                location = {}
                for entity in doc.entities:
                    if entity['label'] == 'COORDINATE':
                        location['coordinates'] = entity['text']
                    elif entity['label'] in ['GPE', 'LOC']:
                        location['name'] = entity['text']
                
                # Extract effective dates
                effective_date = doc.published_date
                expiry_date = None  # Would need more sophisticated date extraction
                
                # Generate recommendations based on content
                recommendations = self._extract_recommendations(doc.content)
                
                alert = MaritimeAlert(
                    alert_id=doc.id,
                    alert_type=doc.category,
                    severity=doc.priority,
                    location=location,
                    description=doc.summary,
                    effective_date=effective_date,
                    expiry_date=expiry_date,
                    affected_areas=[location.get('name', 'Unknown')],
                    recommendations=recommendations,
                    source_document=doc.id
                )
                
                alerts.append(alert)
        
        return alerts
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from content"""
        recommendations = []
        
        # Look for sentences containing recommendation keywords
        sentences = sent_tokenize(content)
        recommendation_keywords = ['recommend', 'advise', 'suggest', 'should', 'must', 'avoid', 'caution']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in recommendation_keywords):
                recommendations.append(sentence.strip())
        
        return recommendations[:5]  # Limit to 5 recommendations

# Singleton instance
enhanced_ir_service = EnhancedIRService()