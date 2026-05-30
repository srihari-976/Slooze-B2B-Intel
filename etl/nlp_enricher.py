import logging
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    logger.warning("spaCy not installed. NLP enrichment will be skipped.")

class NLPEnricher:
    """Handles NLP-based keyword and entity extraction from product descriptions."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize the NLP enricher.
        
        Args:
            model_name: spaCy model to use for NLP processing
        """
        if not HAS_SPACY:
            logger.warning("spaCy not available — NLPEnricher will return data unchanged")
            self.nlp = None
            return
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"spaCy model '{model_name}' not found. Attempting to download...")
            try:
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", model_name], check=True)
                self.nlp = spacy.load(model_name)
            except Exception as e:
                logger.error(f"Failed to download spaCy model: {e}")
                raise RuntimeError(f"Could not load spaCy model '{model_name}'") from e
        
        # Add custom product-specific entity patterns if needed
        self._add_custom_patterns()
    
    def _add_custom_patterns(self):
        """Add custom entity patterns for product domain."""
        # Get the entity ruler
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        else:
            ruler = self.nlp.get_pipe("entity_ruler")
        
        # Define patterns for product attributes
        patterns = [
            {"label": "MATERIAL", "pattern": [{"LOWER": {"IN": ["steel", "aluminum", "plastic", "copper", "brass", "glass", "wood", "cotton", "polyester", "nylon"]}}]},
            {"label": "MEASUREMENT", "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["mm", "cm", "m", "kg", "g", "mg", "l", "ml", "inch", "inches", "ft", "feet", "yards"]}}]},
            {"label": "VOLTAGE", "pattern": [{"LIKE_NUM": True}, {"LOWER": "v"}, {"LOWER": {"IN": ["ac", "dc"]}, "OP": "?"}]},
            {"label": "POWER", "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["w", "kw", "hp"]}}]},
            {"label": "FREQUENCY", "pattern": [{"LIKE_NUM": True}, {"LOWER": {"IN": ["hz", "khz", "mhz"]}}]},
        ]
        
        ruler.add_patterns(patterns)
    
    def enrich_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a product with NLP-extracted keywords and entities.
        
        Args:
            product: Product dictionary to enrich
            
        Returns:
            Enriched product dictionary
        """
        if self.nlp is None:
            return product
        
        enriched = product.copy()
        
        # Extract keywords and entities from description
        description = product.get('description', '')
        if description:
            nlp_result = self._extract_keywords_and_entities(description)
            enriched.update(nlp_result)
        
        # Also extract from product name if description is short
        name = product.get('name', '')
        if name and len(description) < 50:  # If description is too short, supplement with name
            name_result = self._extract_keywords_and_entities(name)
            # Merge keywords, preferring existing ones
            existing_keywords = set(enriched.get('keywords', []))
            new_keywords = set(name_result.get('keywords', []))
            enriched['keywords'] = list(existing_keywords.union(new_keywords))
        
        return enriched
    
    def _extract_keywords_and_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract keywords and named entities from text.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary with extracted keywords and entities
        """
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract keywords (noun phrases, important nouns, adjectives)
        keywords = self._extract_keywords(doc)
        
        # Extract named entities
        entities = self._extract_entities(doc)
        
        return {
            'keywords': keywords,
            'entities': entities
        }
    
    def _extract_keywords(self, doc) -> List[str]:
        """
        Extract meaningful keywords from spaCy doc.
        
        Args:
            doc: Processed spaCy document
            
        Returns:
            List of keyword strings
        """
        keywords = set()
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            # Clean and normalize the noun phrase
            phrase = chunk.text.lower().strip()
            # Remove articles and determiners at the start
            phrase = re.sub(r'^(a|an|the|this|that|these|those)\s+', '', phrase)
            if len(phrase) > 2 and len(phrase.split()) <= 4:  # Reasonable length
                keywords.add(phrase)
        
        # Extract important single words (nouns, proper nouns, adjectives)
        for token in doc:
            if (token.pos_ in ["NOUN", "PROPN", "ADJ"] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.add(token.lemma_.lower())
        
        # Extract compound words (hyphenated terms)
        for token in doc:
            if '-' in token.text and token.pos_ in ["NOUN", "PROPN"]:
                keywords.add(token.text.lower())
        
        # Convert to list and sort by relevance (longer phrases first, then alphabetically)
        keyword_list = list(keywords)
        keyword_list.sort(key=lambda x: (-len(x), x))
        
        # Limit to reasonable number
        return keyword_list[:20]
    
    def _extract_entities(self, doc) -> List[Dict[str, str]]:
        """
        Extract named entities from spaCy doc.
        
        Args:
            doc: Processed spaCy document
            
        Returns:
            List of entity dictionaries with 'text' and 'label'
        """
        entities = []
        
        for ent in doc.ents:
            # Filter out very short entities or common false positives
            if len(ent.text.strip()) > 1:
                entities.append({
                    'text': ent.text.strip(),
                    'label': ent.label_
                })
        
        # Deduplicate entities (same text and label)
        seen = set()
        unique_entities = []
        for ent in entities:
            key = (ent['text'].lower(), ent['label'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(ent)
        
        return unique_entities
