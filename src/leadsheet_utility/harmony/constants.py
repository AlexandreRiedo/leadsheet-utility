"""Static data tables for the harmony analyzer."""

SCALES: dict[str, tuple[int, ...]] = {
    "ionian":           (0, 2, 4, 5, 7, 9, 11),
    "dorian":           (0, 2, 3, 5, 7, 9, 10),
    "phrygian":         (0, 1, 3, 5, 7, 8, 10),
    "lydian":           (0, 2, 4, 6, 7, 9, 11),
    "mixolydian":       (0, 2, 4, 5, 7, 9, 10),
    "aeolian":          (0, 2, 3, 5, 7, 8, 10),
    "locrian":          (0, 1, 3, 5, 6, 8, 10),
    "harmonic_minor":   (0, 2, 3, 5, 7, 8, 11),
    "locrian_nat6":     (0, 1, 3, 5, 6, 9, 10),
    "phrygian_dom":     (0, 1, 4, 5, 7, 8, 10),
    "melodic_minor":    (0, 2, 3, 5, 7, 9, 11),
    "locrian_nat9":     (0, 2, 3, 5, 6, 8, 10),
    "lydian_dominant":  (0, 2, 4, 6, 7, 9, 10),
    "altered":          (0, 1, 3, 4, 6, 8, 10),
    "half_whole_dim":   (0, 1, 3, 4, 6, 7, 9, 10),
    "whole_half_dim":   (0, 2, 3, 5, 6, 8, 9, 11),
    "whole_tone":       (0, 2, 4, 6, 8, 10),
}

NOTE_TO_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11,
}

# Semitone intervals from root for (root, 3rd, 5th, 7th).
# Triads have 3 entries (no 7th); 6th chords have the 6th in the 7th position.
CHORD_TONES: dict[str, tuple[int, ...]] = {
    # 7th chords
    "maj7":    (0, 4, 7, 11),
    "7":       (0, 4, 7, 10),
    "min7":    (0, 3, 7, 10),
    "hdim7":   (0, 3, 6, 10),
    "dim7":    (0, 3, 6, 9),
    "minmaj7": (0, 3, 7, 11),
    # Triads
    "maj":     (0, 4, 7),
    "min":     (0, 3, 7),
    "aug":     (0, 4, 8),
    # 6th chords (6 in "7th" position)
    "6":       (0, 4, 7, 9),
    "min6":    (0, 3, 7, 9),
    # Extended dominant (same chord tones as base dominant)
    "9":       (0, 4, 7, 10),
    # Extended major (same chord tones as maj7)
    "maj9":    (0, 4, 7, 11),
    "maj13":   (0, 4, 7, 11),
    "maj7#11": (0, 4, 7, 11),
    "maj69":   (0, 4, 7),
    # Extended minor (same chord tones as min7)
    "min9":    (0, 3, 7, 10),
    "min11":   (0, 3, 7, 10),
    "min13":   (0, 3, 7, 10),
    # Sus chords (sus note in "3rd" position; 7th only for 7sus4)
    "sus4":    (0, 5, 7),
    "sus2":    (0, 2, 7),
    "sus":     (0, 5, 7),
    "7sus4":   (0, 5, 7, 10),
}

# Layer 1: default quality → scale name fallback.
QUALITY_TO_SCALE: dict[str, str] = {
    "maj7":    "ionian",
    "maj":     "ionian",
    "6":       "ionian",
    "maj9":    "ionian",
    "maj13":   "ionian",
    "maj69":   "ionian",
    "maj7#11": "lydian",
    "7":       "mixolydian",
    "9":       "mixolydian",
    "sus4":    "mixolydian",
    "sus2":    "mixolydian",
    "sus":     "mixolydian",
    "7sus4":   "mixolydian",
    "min7":    "dorian",
    "min":     "dorian",
    "min6":    "dorian",
    "min9":    "dorian",
    "min11":   "dorian",
    "min13":   "dorian",
    "minmaj7": "melodic_minor",
    "hdim7":   "locrian_nat6",
    "dim7":    "whole_half_dim",
    "aug":     "whole_tone",
}

# Scale names considered dominant-function for contextual half-diminished checks.
DOMINANT_SCALES: set[str] = {"mixolydian", "lydian_dominant", "phrygian_dom", "altered"}
