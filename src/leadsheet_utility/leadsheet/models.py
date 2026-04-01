from dataclasses import dataclass, field


@dataclass
class ChordEvent:
    chord_symbol: str  # raw from file, e.g. "F:min7"
    root: str  # "F"
    quality: str  # "min7"
    extensions: list[str] = field(default_factory=list)  # e.g. ["b9"], ["#9"], []
    bass_note: str | None = None  # slash chord bass, or None
    start_beat: float = 0.0  # absolute beat position (0-indexed)
    end_beat: float = 0.0  # absolute beat position where chord ends
    duration_beats: float = 0.0  # end_beat - start_beat
    bar_number: int = 1  # derived: floor(start_beat / beats_per_bar) + 1
    beat_in_bar: float = 0.0  # derived: start_beat % beats_per_bar
    scale_notes: list[int] = field(default_factory=list)  # MIDI 21-108
    chord_tones: list[int] = field(default_factory=list)  # R, 3, 5, 7 (MIDI 21-108)
    guide_tones: list[int] = field(default_factory=list)  # 3rd and 7th (MIDI 21-108)
    available_tensions: list[int] = field(default_factory=list)  # scale non-chord-tones (MIDI 21-108)


@dataclass
class LeadSheet:
    title: str = "Unknown"
    composer: str = "Unknown"
    key: str = "C"
    time_signature: tuple[int, int] = (4, 4)
    default_tempo: int = 120
    form_repeats: int = 1
    chords: list[ChordEvent] = field(default_factory=list)
    total_beats: float = 0.0  # end_beat of the last chord
    total_bars: int = 0  # derived from total_beats / beats_per_bar
    guide_tone_line: list[int] = field(default_factory=list)  # voice-led guide tone per chord (MIDI)
