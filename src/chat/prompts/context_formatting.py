#!/usr/bin/env python3
"""
Context formatting module for prompt engineering.

Provides different strategies for formatting retrieved literature context
for optimal AI comprehension and response generation.

Phase 1B: Enhanced context presentation for better AI understanding.
"""

from typing import List, Dict, Any

class ContextFormattingModule:
    """
    Module for formatting retrieved literature context.
    
    This module provides different strategies for presenting search results
    to the AI assistant in ways that maximize comprehension and enable
    accurate, well-sourced responses.
    """
    
    def get_context_formatting_instructions(self, style: str = "structured") -> str:
        """
        Get instructions for how AI should interpret and use context.
        
        Args:
            style: Formatting style ("simple", "structured", "advanced")
        
        Returns:
            Context formatting instructions for the AI
        """
        if style == "simple":
            return self._get_simple_context_instructions()
        elif style == "advanced":
            return self._get_advanced_context_instructions()
        else:  # structured (default)
            return self._get_structured_context_instructions()
    
    def _get_simple_context_instructions(self) -> str:
        """Simple context formatting instructions."""
        return """LITERATURE CONTEXT USAGE:
When provided with relevant literature context:
- Use the retrieved information to support your responses
- Cite sources when making specific claims
- Distinguish between information from the literature vs. your reasoning
- If context is insufficient, acknowledge limitations clearly"""
    
    def _get_structured_context_instructions(self) -> str:
        """Structured context formatting instructions."""
        return """LITERATURE CONTEXT INTEGRATION:
When literature context is provided, follow this systematic approach:

CONTEXT ANALYSIS:
- Identify the most relevant sources for the user's question
- Note the relevance score and source metadata for each result
- Consider the document section type (abstract, methods, results, discussion)
- Recognize when context covers different aspects of the question

INFORMATION SYNTHESIS:
- Synthesize information from multiple sources when available
- Identify areas of agreement and disagreement between sources
- Note the experimental or theoretical basis for different claims
- Consider the recency and authority of different sources

RESPONSE CONSTRUCTION:
- Ground your primary response in the most relevant literature
- Use specific citations for all factual claims: [Literature: filename.pdf]
- Indicate confidence levels based on source quality and consensus
- Acknowledge gaps where literature doesn't address the question
- Suggest specific papers for deeper exploration when appropriate

QUALITY INDICATORS:
- Prioritize results with higher similarity scores for core claims
- Use multiple sources to validate important statements
- Note when claims come from abstracts vs. detailed sections
- Consider the source type (research paper, review, user's work)"""
    
    def _get_advanced_context_instructions(self) -> str:
        """Advanced context formatting instructions."""
        return """ADVANCED LITERATURE INTEGRATION:
Employ sophisticated strategies for context utilization:

HIERARCHICAL CONTEXT PROCESSING:
- Primary sources: Direct experimental results and theoretical derivations
- Secondary sources: Review papers and theoretical overviews  
- Tertiary sources: Textbooks and general discussions
- User materials: Personal research and draft documents

CONTEXTUAL RELEVANCE ASSESSMENT:
- Evaluate relevance beyond similarity scores
- Consider methodological appropriateness for the question
- Assess temporal relevance (recent vs. historical perspective)
- Weight sources by experimental rigor and peer review status

MULTI-DIMENSIONAL SYNTHESIS:
- Theoretical perspective: What do the theories predict?
- Experimental evidence: What have measurements shown?
- Historical development: How has understanding evolved?
- Current consensus: What is widely accepted vs. disputed?
- Future directions: What questions remain open?

SOPHISTICATED CITATION STRATEGY:
- Primary citation: [Literature: Author_Year_Journal.pdf] for main claims
- Supporting citation: [Literature: filename.pdf] for corroborating evidence
- Contrasting citation: [Literature: filename.pdf] for alternative views
- Methodology citation: [Literature: filename.pdf] for experimental approaches
- Review citation: [Literature: filename.pdf] for comprehensive overviews

UNCERTAINTY AND CONFIDENCE:
- High confidence: Multiple consistent high-quality sources
- Medium confidence: Single authoritative source or consistent trends
- Low confidence: Limited sources or conflicting information
- Speculation: Clearly marked extrapolations beyond available literature

RESPONSE ARCHITECTURE:
1. Direct answer with primary source grounding
2. Supporting evidence from multiple sources
3. Alternative perspectives or limitations
4. Methodological considerations
5. Broader context and implications
6. Suggested literature for deeper investigation"""
    
    def format_search_results(self, 
                            search_results: List[Any], 
                            query: str,
                            style: str = "structured") -> str:
        """
        Format search results for inclusion in AI prompt.
        
        Args:
            search_results: List of search results from knowledge base
            query: Original user query
            style: Formatting style to use
        
        Returns:
            Formatted context string ready for prompt inclusion
        """
        if not search_results:
            return "No relevant literature found for this query."
        
        if style == "simple":
            return self._format_simple_context(search_results, query)
        elif style == "advanced":
            return self._format_advanced_context(search_results, query)
        else:  # structured
            return self._format_structured_context(search_results, query)
    
    def _format_simple_context(self, search_results: List[Any], query: str) -> str:
        """Format context in simple style."""
        context_parts = [f"LITERATURE CONTEXT FOR: {query}\n"]
        
        for i, result in enumerate(search_results, 1):
            chunk = result.chunk
            similarity = result.similarity_score
            
            context_parts.append(f"Source {i}: {chunk.file_name} (Relevance: {similarity:.2f})")
            context_parts.append(chunk.text)
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _format_structured_context(self, search_results: List[Any], query: str) -> str:
        """Format context in structured style."""
        context_parts = [
            f"LITERATURE CONTEXT FOR QUERY: {query}",
            f"Retrieved {len(search_results)} relevant sources:\n"
        ]
        
        for i, result in enumerate(search_results, 1):
            chunk = result.chunk
            similarity = result.similarity_score
            
            # Enhanced metadata display
            metadata_parts = [
                f"📄 SOURCE {i}: {chunk.file_name}",
                f"📊 Relevance Score: {similarity:.3f}",
                f"📍 Source Type: {chunk.source_type}",
                f"🔢 Chunk: {chunk.chunk_index + 1} of {chunk.total_chunks}"
            ]
            
            # Add enhanced metadata if available
            if hasattr(chunk, 'enhanced_metadata'):
                meta = chunk.enhanced_metadata
                if hasattr(meta, 'section_type') and meta.section_type:
                    metadata_parts.append(f"📝 Section: {meta.section_type}")
                if hasattr(meta, 'has_equations') and meta.has_equations:
                    metadata_parts.append("🧮 Contains equations")
                if hasattr(meta, 'has_citations') and meta.has_citations:
                    metadata_parts.append("📚 Contains citations")
                if hasattr(meta, 'confidence_score'):
                    metadata_parts.append(f"✅ Chunk quality: {meta.confidence_score:.2f}")
            
            context_parts.append("\n".join(metadata_parts))
            context_parts.append(f"\nCONTENT:\n{chunk.text}")
            context_parts.append("\n" + "="*50 + "\n")
        
        return "\n".join(context_parts)
    
    def _format_advanced_context(self, search_results: List[Any], query: str) -> str:
        """Format context in advanced style with sophisticated analysis."""
        # Group results by relevance tiers
        high_relevance = [r for r in search_results if r.similarity_score > 0.8]
        medium_relevance = [r for r in search_results if 0.6 <= r.similarity_score <= 0.8]
        low_relevance = [r for r in search_results if r.similarity_score < 0.6]
        
        context_parts = [
            f"COMPREHENSIVE LITERATURE ANALYSIS",
            f"Query: {query}",
            f"Sources retrieved: {len(search_results)} total\n"
        ]
        
        # Relevance summary
        if high_relevance:
            context_parts.append(f"🎯 HIGH RELEVANCE ({len(high_relevance)} sources): Direct answers expected")
        if medium_relevance:
            context_parts.append(f"📌 MEDIUM RELEVANCE ({len(medium_relevance)} sources): Supporting context")
        if low_relevance:
            context_parts.append(f"📎 LOW RELEVANCE ({len(low_relevance)} sources): Background information")
        
        context_parts.append("")
        
        # Format each tier
        for tier_name, tier_results in [
            ("HIGH RELEVANCE SOURCES", high_relevance),
            ("MEDIUM RELEVANCE SOURCES", medium_relevance),
            ("LOW RELEVANCE SOURCES", low_relevance)
        ]:
            if not tier_results:
                continue
                
            context_parts.append(f"═══ {tier_name} ═══")
            
            for i, result in enumerate(tier_results, 1):
                chunk = result.chunk
                similarity = result.similarity_score
                
                # Comprehensive metadata
                metadata = [
                    f"📄 {chunk.file_name}",
                    f"📊 Similarity: {similarity:.3f}",
                    f"📂 Type: {chunk.source_type}",
                    f"🔢 Position: {chunk.chunk_index + 1}/{chunk.total_chunks}"
                ]
                
                # Enhanced analysis
                if hasattr(chunk, 'enhanced_metadata'):
                    meta = chunk.enhanced_metadata
                    if hasattr(meta, 'section_type') and meta.section_type:
                        metadata.append(f"📝 Section: {meta.section_type}")
                    if hasattr(meta, 'has_equations') and meta.has_equations:
                        metadata.append("🧮 Mathematical content")
                    if hasattr(meta, 'has_citations') and meta.has_citations:
                        metadata.append("📚 Contains references")
                    if hasattr(meta, 'confidence_score'):
                        confidence = meta.confidence_score
                        confidence_desc = "excellent" if confidence > 0.9 else "good" if confidence > 0.7 else "fair"
                        metadata.append(f"✅ Chunk quality: {confidence:.2f} ({confidence_desc})")
                
                context_parts.append(f"\n【{tier_name[0]}{i}】 " + " | ".join(metadata))
                context_parts.append(f"\n{chunk.text}")
                context_parts.append("\n" + "─"*40)
            
            context_parts.append("")
        
        # Add analysis summary
        context_parts.extend([
            "💡 CONTEXT ANALYSIS NOTES:",
            f"• Total sources span {len(set(r.chunk.source_type for r in search_results))} different source types",
            f"• Coverage includes {len(set(r.chunk.file_name for r in search_results))} unique documents",
            "• Use high-relevance sources for primary claims, medium for support, low for background",
            "• Consider section types when assessing claim authority",
            "• Mathematical content may provide quantitative insights",
            "• Citation-rich sections may indicate comprehensive reviews"
        ])
        
        return "\n".join(context_parts)
    
    def analyze_context_quality(self, search_results: List[Any]) -> Dict[str, Any]:
        """
        Analyze the quality of retrieved context.
        
        Args:
            search_results: Search results to analyze
        
        Returns:
            Dictionary with context quality metrics
        """
        if not search_results:
            return {'quality': 'no_context'}
        
        similarities = [r.similarity_score for r in search_results]
        avg_similarity = sum(similarities) / len(similarities)
        max_similarity = max(similarities)
        
        # Count high-quality results
        high_quality = sum(1 for s in similarities if s > 0.8)
        medium_quality = sum(1 for s in similarities if 0.6 <= s <= 0.8)
        
        # Analyze source diversity
        unique_sources = len(set(r.chunk.file_name for r in search_results))
        source_types = set(r.chunk.source_type for r in search_results)
        
        # Enhanced metadata analysis
        enhanced_count = sum(1 for r in search_results if hasattr(r.chunk, 'enhanced_metadata'))
        
        quality_assessment = "excellent" if max_similarity > 0.9 and high_quality >= 2 else \
                           "good" if max_similarity > 0.8 or high_quality >= 1 else \
                           "fair" if max_similarity > 0.6 else "poor"
        
        return {
            'overall_quality': quality_assessment,
            'average_similarity': round(avg_similarity, 3),
            'max_similarity': round(max_similarity, 3),
            'high_quality_sources': high_quality,
            'medium_quality_sources': medium_quality,
            'unique_documents': unique_sources,
            'source_types': list(source_types),
            'enhanced_metadata_available': enhanced_count > 0,
            'total_sources': len(search_results)
        }