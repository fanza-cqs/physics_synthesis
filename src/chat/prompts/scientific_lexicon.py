#!/usr/bin/env python3
"""
Scientific lexicon module for prompt engineering.

Provides guidance for appropriate scientific terminology, precision,
and communication standards in physics research contexts.

Phase 1B: Enhanced scientific communication for AI responses.
"""

class ScientificLexiconModule:
    """
    Module for scientific terminology and communication guidance.
    
    This module provides different levels of scientific precision and
    terminology guidance for AI responses in physics contexts.
    """
    
    def get_lexicon_guidance(self, level: str = "precise") -> str:
        """
        Get scientific lexicon guidance for specified precision level.
        
        Args:
            level: Precision level ("basic", "precise", "technical")
        
        Returns:
            Scientific lexicon guidance section
        """
        if level == "basic":
            return self._get_basic_lexicon_guidance()
        elif level == "technical":
            return self._get_technical_lexicon_guidance()
        else:  # precise (default)
            return self._get_precise_lexicon_guidance()
    
    def _get_basic_lexicon_guidance(self) -> str:
        """Basic scientific communication guidance."""
        return """SCIENTIFIC COMMUNICATION:
- Use clear, accurate physics terminology
- Define technical terms when first introduced
- Maintain consistency in notation and units
- Distinguish between theoretical models and experimental reality
- Acknowledge approximations and their limitations"""
    
    def _get_precise_lexicon_guidance(self) -> str:
        """Precise scientific lexicon guidance."""
        return """SCIENTIFIC PRECISION & TERMINOLOGY:

PHYSICS LANGUAGE STANDARDS:
- Use precise physics terminology with correct technical meanings
- Distinguish carefully between related but distinct concepts
- Employ standard notation and conventions consistently
- Reference appropriate units (SI system preferred)
- Use proper mathematical notation and symbols

CONCEPTUAL PRECISION:
- Distinguish between "theory" (well-established framework) and "hypothesis" (proposed explanation)
- Differentiate "model" (simplified representation) from "reality" (actual physical system)
- Separate "measurement" (experimental observation) from "calculation" (theoretical prediction)
- Clarify "correlation" vs. "causation" in physical relationships
- Distinguish "exact" solutions from "approximate" or "numerical" results

QUANTITATIVE COMMUNICATION:
- Provide orders of magnitude when giving numerical estimates
- Include appropriate significant figures based on measurement precision
- Note uncertainty ranges when discussing experimental results
- Distinguish between systematic and statistical uncertainties
- Use appropriate mathematical language (e.g., "proportional to" vs. "depends on")

TEMPORAL AND SPATIAL SCALES:
- Specify relevant time scales (femtoseconds to cosmological ages)
- Indicate spatial scales (subatomic to astronomical)
- Use appropriate energy scales (meV to TeV)
- Reference temperature ranges with proper context
- Note pressure and density regimes where applicable

THEORETICAL FRAMEWORKS:
- Identify the theoretical level (classical, quantum, relativistic)
- Specify approximations and their validity ranges
- Note when results are model-dependent
- Distinguish between fundamental principles and derived results
- Indicate the experimental basis for theoretical claims"""
    
    def _get_technical_lexicon_guidance(self) -> str:
        """Technical/expert-level lexicon guidance."""
        return """ADVANCED SCIENTIFIC COMMUNICATION:

EXPERT-LEVEL TERMINOLOGY:
- Employ field-specific technical vocabulary with precision
- Use advanced mathematical terminology appropriately
- Reference specific experimental techniques and methodologies
- Utilize proper names for effects, theorems, and phenomena
- Apply correct group theory and symmetry language

THEORETICAL SOPHISTICATION:
- Distinguish between effective theories and fundamental theories
- Specify gauge choices and their implications
- Note regularization and renormalization schemes
- Identify symmetries and their breaking mechanisms
- Discuss phase spaces and statistical mechanical ensembles

EXPERIMENTAL PRECISION:
- Reference specific detector technologies and their capabilities
- Discuss systematic uncertainties and their mitigation
- Note calibration procedures and their limitations
- Specify data analysis techniques and their assumptions
- Distinguish between online and offline data processing

MATHEMATICAL RIGOR:
- Use proper functional analysis terminology
- Apply group theory concepts correctly
- Employ differential geometry language appropriately
- Reference topological concepts with precision
- Use statistical and probabilistic terminology accurately

ADVANCED PHYSICS CONCEPTS:
- Renormalization group language and scaling behavior
- Quantum field theory terminology (correlation functions, Green's functions)
- Many-body physics concepts (quasiparticles, collective modes)
- General relativity language (manifolds, curvature, geodesics)
- Statistical mechanics (partition functions, phase transitions)

RESEARCH METHODOLOGY:
- Distinguish between ab initio and phenomenological approaches
- Note computational complexity and scaling behavior
- Reference standard algorithms and their implementations
- Discuss convergence criteria and numerical stability
- Identify benchmarking and validation procedures"""
    
    def get_domain_specific_lexicon(self, domain: str) -> str:
        """
        Get lexicon guidance for specific physics domains.
        
        Args:
            domain: Physics domain ("quantum", "condensed_matter", etc.)
        
        Returns:
            Domain-specific lexicon guidance
        """
        domain_lexicons = {
            "quantum": self._get_quantum_lexicon(),
            "condensed_matter": self._get_condensed_matter_lexicon(),
            "particle": self._get_particle_physics_lexicon(),
            "cosmology": self._get_cosmology_lexicon(),
            "atomic": self._get_atomic_physics_lexicon()
        }
        
        return domain_lexicons.get(domain, self._get_precise_lexicon_guidance())
    
    def _get_quantum_lexicon(self) -> str:
        """Quantum physics specific terminology."""
        return """QUANTUM PHYSICS LEXICON:
- State vectors vs. wavefunctions vs. density matrices
- Unitary evolution vs. measurement vs. decoherence
- Entanglement vs. superposition vs. interference
- Quantum correlations vs. classical correlations
- Coherence vs. purity vs. mixedness
- Observable vs. operator vs. expectation value
- Basis states vs. eigenstates vs. coherent states
- Quantum gates vs. quantum circuits vs. quantum algorithms"""
    
    def _get_condensed_matter_lexicon(self) -> str:
        """Condensed matter physics terminology."""
        return """CONDENSED MATTER LEXICON:
- Lattice vs. crystal vs. unit cell vs. primitive cell
- Band structure vs. density of states vs. Fermi surface
- Metal vs. insulator vs. semiconductor vs. semimetal
- Phase vs. phase transition vs. critical point vs. order parameter
- Correlation function vs. structure factor vs. response function
- Quasiparticle vs. collective mode vs. elementary excitation
- Symmetry breaking vs. spontaneous symmetry breaking
- Topological order vs. topological phase vs. topological invariant"""
    
    def _get_particle_physics_lexicon(self) -> str:
        """Particle physics terminology."""
        return """PARTICLE PHYSICS LEXICON:
- Fundamental particles vs. composite particles vs. resonances
- Gauge bosons vs. matter fermions vs. scalar bosons
- Strong interaction vs. electromagnetic vs. weak vs. gravitational
- Cross section vs. decay rate vs. branching ratio
- Invariant mass vs. transverse momentum vs. pseudorapidity
- Standard Model vs. beyond Standard Model vs. effective theory
- Symmetry vs. gauge symmetry vs. global symmetry
- Renormalization vs. regularization vs. dimensional analysis"""
    
    def _get_cosmology_lexicon(self) -> str:
        """Cosmology and astrophysics terminology."""
        return """COSMOLOGY LEXICON:
- Universe vs. observable universe vs. cosmic horizon
- Dark matter vs. dark energy vs. baryonic matter
- Expansion vs. acceleration vs. inflation vs. Big Bang
- Cosmic microwave background vs. primordial fluctuations
- Structure formation vs. galaxy formation vs. reionization
- Redshift vs. proper distance vs. comoving distance
- Critical density vs. density parameter vs. equation of state
- Flatness problem vs. horizon problem vs. monopole problem"""
    
    def _get_atomic_physics_lexicon(self) -> str:
        """Atomic physics terminology."""
        return """ATOMIC PHYSICS LEXICON:
- Electronic configuration vs. term symbol vs. quantum numbers
- Fine structure vs. hyperfine structure vs. Zeeman effect
- Transition vs. selection rules vs. forbidden transitions
- Laser cooling vs. magnetic trapping vs. optical molasses
- Coherent state vs. squeezed state vs. entangled state
- Stimulated emission vs. spontaneous emission vs. absorption
- Rabi frequency vs. detuning vs. Rabi oscillations
- Cold atoms vs. ultracold atoms vs. quantum degenerate gases"""
    
    def get_uncertainty_language(self) -> str:
        """Get language guidance for expressing scientific uncertainty."""
        return """EXPRESSING SCIENTIFIC UNCERTAINTY:

CONFIDENCE LEVELS:
- "Established" or "well-established": Strong consensus, multiple confirmations
- "Widely accepted": Broad agreement, some remaining questions
- "Supported by evidence": Good evidence, but not yet consensus
- "Preliminary evidence suggests": Early results, needs confirmation
- "Speculative" or "hypothetical": Proposed ideas, limited evidence

MEASUREMENT PRECISION:
- "Precisely measured": High precision, small error bars
- "Accurately determined": Good agreement with theory/other measurements
- "Approximately": Order-of-magnitude estimate
- "On the order of": Factor of few uncertainty
- "Roughly" or "about": Significant uncertainty

THEORETICAL STATUS:
- "Predicted by theory": Solid theoretical foundation
- "Consistent with theory": Agreement within uncertainties
- "Theory suggests": Theoretical indication, not definitive
- "Models predict": Model-dependent result
- "Phenomenological": Empirical description, limited theoretical basis

EXPERIMENTAL STATUS:
- "Observed": Direct experimental confirmation
- "Measured": Quantitative experimental determination
- "Detected": Experimental evidence, possibly indirect
- "Inferred": Conclusion drawn from observations
- "No evidence for": Searches have found no signal"""
    
    def get_comparison_language(self) -> str:
        """Get language guidance for scientific comparisons."""
        return """SCIENTIFIC COMPARISON LANGUAGE:

QUANTITATIVE COMPARISONS:
- "X times larger/smaller": Precise factor known
- "Orders of magnitude": Factors of 10 difference
- "Significantly larger/smaller": Statistically significant difference
- "Comparable to": Within factor of few
- "Much larger/smaller": Factor of 10+ difference

ACCURACY COMPARISONS:
- "More accurate": Smaller systematic uncertainties
- "More precise": Smaller statistical uncertainties
- "Better resolution": Finer discrimination capability
- "Higher sensitivity": Can detect smaller signals
- "More reliable": Less susceptible to systematic errors

THEORETICAL COMPARISONS:
- "More fundamental": Fewer assumptions, broader applicability
- "More complete": Includes more physical effects
- "More sophisticated": Uses advanced techniques
- "More phenomenological": More empirical, less fundamental
- "Complementary approaches": Different methods, similar goals"""