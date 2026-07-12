"""Media filename metadata extraction utilities."""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum

import opencc

from app.utils.numeral import cn_to_int


class EpisodeKind(StrEnum):
    """Provider-independent kinds of episodic media."""

    REGULAR = "regular"
    SPECIAL = "special"
    OVA = "ova"
    OAD = "oad"
    ONA = "ona"
    NCOP = "ncop"
    NCED = "nced"
    PV = "pv"
    TRAILER = "trailer"
    CM = "cm"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class EpisodeRef:
    """A canonical episode reference parsed from a media name."""

    kind: EpisodeKind
    number: Decimal
    absolute_number: Decimal | None = None

    @property
    def canonical_number(self) -> str:
        """Return a stable, non-exponential representation of the number."""
        return _canonical_decimal(self.number)


@dataclass(frozen=True, slots=True)
class ParsedMediaName:
    """Structured metadata extracted from a media or release name."""

    raw_name: str
    title: str
    normalized_title: str
    year: int | None
    season: int | None
    episodes: tuple[EpisodeRef, ...]
    release_version: int | None
    is_batch: bool
    context_source: str
    confidence: str


_T2S_CONVERTER = opencc.OpenCC("t2s.json")

# pattern to match common separators: dot, underscore, hyphen, space, star
_SEPARATOR_PATTERN = re.compile(r"[._\-\s★☆]+")

# pattern to match the leading noise prefix like [SubGroup], (SiteName), 【字幕组】 etc.
_PREFIX_PATTERN = re.compile(r"^[\[\(【][^\]\)】]*[\]\)】]\s*")

# pattern to match a leading metadata prefix after the release group
_LEADING_META_PREFIX_PATTERN = re.compile(
    r"""
    ^(?:
        [\[\(【]
        (?:
            [^\]\)】]*
            (?:粵語|粤语|國語|国语|日語|日语|英語|英语|雙語|双语|無字幕|无字幕|字幕)
            [^\]\)】]*
            | ANi
            | アニメ
            | 国漫
        )
        [\]\)】]\s*
    )+
    """,
    re.VERBOSE,
)

# pattern to strip unbracketed subtitle group prefixes like 字幕組★Title
_LEADING_STAR_PREFIX_PATTERN = re.compile(r"^[^★☆]{1,40}(?:字幕组|字幕組)[^★☆]*[★☆]\s*")

# pattern to match leading seasonal broadcast markers like ★04月新番★
_LEADING_BROADCAST_MARKER_PATTERN = re.compile(r"^[★☆]\s*\d{1,2}\s*月\s*新番\s*[★☆]\s*")

# pattern to merge adjacent bracketed title segments, e.g. [中文][English]
_BRACKET_BOUNDARY_PATTERN = re.compile(r"[\]\)】]\s*[\[\(【]")

# pattern to strip episode titles after a bracketed episode and before an air date
_BRACKETED_EPISODE_TITLE_SUFFIX_PATTERN = re.compile(
    r"""
    \[
    (?!0*(?:19|20)\d{2}\])
    0*\d{1,4}
    \]
    [^\[\]]+
    \[(?:19|20)\d{2}[._-]\d{1,2}[._-]\d{1,2}\]
    .*$
    """,
    re.VERBOSE,
)

# year pattern: a 4-digit year between 1900 and 2099, excluding dimensions
_YEAR_PATTERN = re.compile(
    r"(?:^|(?<=[._\-\s\]\)】]))[\(\[（]?(?P<year>(?:19|20)\d{2})"
    r"(?!\d|[xX]\d{3,4}|[A-Za-z])[\)\]）]?"
)

# season pattern: S01, S01E01, s1, Season 1, 第1季, 第二季, 第二期 etc.
_SEASON_PATTERN = re.compile(
    r"""
    (?:
        [Ss]eason[._\-\s]*(\d{1,3})
        | (?<![A-Za-z0-9])
          (first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)
          [._\-\s]*[Ss]eason\b
        | (?<![A-Za-z0-9])(\d{1,3})(?:[Ss][Tt]|[Nn][Dd]|[Rr][Dd]|[Tt][Hh])
          [._\-\s]*[Ss]eason\b
        | (?<![A-Za-z0-9])[Ss](\d{1,3})(?:[Ee]\d{1,4}|\b)
        | 第\s*(\d{1,3})\s*[季期]
        | 第\s*([零一二三四五六七八九十百千]+)\s*[季期]
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# episode pattern: E01, ep1, [01], 第1集, 第一话 etc.
_EPISODE_PATTERN = re.compile(
    r"""
    (?:
        [Ss]\d{1,3}[Ee]0*(\d{1,4})
        | (?<![A-Za-z0-9])[Ee][Pp]?\.?0*(\d{1,4})(?!\d)
          (?:\s*[Ee][Nn][Dd]\b)?
          (?:\s*[\[\(【][^\]\)】]*[\]\)】])?
        | \s-\s(?!0*(?:19|20)\d{2}\b)0*(\d{1,4})\s*
          (?:[Ee][Nn][Dd]\b\s*)?(?:-|[\[\(]|$)
        | \[(?!(?:19|20)\d{2}\])0*(\d{1,4})
          (?:[Vv]\d+|\s*-\s*(?:\d{1,4}|[总總]第\s*(?:\d{1,4}|[零一二三四五六七八九十百千]+)))?\]
        | 第\s*(\d{1,4})\s*[集话話回](?=$|[\s\]\)】\[\(【._-])
        | 第\s*([零一二三四五六七八九十百千]+)\s*[集话話回](?=$|[\s\]\)】\[\(【._-])
    )
    """,
    re.VERBOSE,
)

# collection range pattern, e.g. "| 01-12", "[01-12 合集]", "第01-11話"
_COLLECTION_RANGE_PATTERN = re.compile(
    r"""
    (?:
        \s*\|\s*(?!0*(?:19|20)\d{2}\b)0*\d{1,4}\s*[-~～]\s*
        (?!0*(?:19|20)\d{2}\b)0*\d{1,4}(?:\+[Ss][Pp]x\d+)?(?=\s*(?:[\[\(]|$))
        | \s*[★☆]\s*(?!0*(?:19|20)\d{2}\b)0*\d{1,4}\s*[-~～]\s*
          (?!0*(?:19|20)\d{2}\b)0*\d{1,4}
          (?:[\(（]\s*(?:完|[Ee][Nn][Dd]|[Ff]in)\s*[\)）])?(?=\s*[★☆])
        | \s*第\s*0*\d{1,4}\s*[-~～]\s*0*\d{1,4}\s*[集话話回](?=\s*(?:[\[\(]|$))
        | \s*[\[\(【]\s*合集\s*[\]\)】]\s*[\[\(【]\s*
          0*\d{1,4}\s*[~～]\s*0*\d{1,4}\s*[\]\)】]
        | \s*[\[\(【]\s*0*\d{1,4}\s*[-~～]\s*0*\d{1,4}
          (?:\s*[集话話回])?(?:\s*合集)?\s*[\]\)】]
        | \s*[\[\(【]\s*[总總]第\s*0*\d{1,4}\s*[-~～]\s*
          0*\d{1,4}\s*[\]\)】]
        | \s+(?:\d{1,3}(?:[Ss][Tt]|[Nn][Dd]|[Rr][Dd]|[Tt][Hh])\s*)?
          -\s*0*\d{1,4}\s*[~～]\s*0*\d{1,4}(?=\]\s*(?:[\[\(【]|$))
    )
    """,
    re.VERBOSE,
)

# pattern to match common video tags and everything after them
_VIDEO_TAGS_PATTERN = re.compile(
    r"""
    [\.\s\[\(\-_★☆]   # leading separator
    (?:
        # resolution
        \d{3,4}[pPiI]
        | \d{3,4}x\d{3,4}
        | 4[kK]
        | UHD
        # source
        | BluRay | Blu-Ray | BDRip | DLRip | BDRemux | BD | BDMV
        | WEB-DL | WEBRip | WEBDL | WEB
        | DVDRip | DVD
        | HD(?:TV|CAM)?
        | AMZN | NF | DSNP | HMAX | ATVP | IQIYI | ViuTV | ABEMA | Baha
        | B-Global(?:\s+Donghua)?
        | (?-i:CR) | (?-i:iT)
        # encoding
        | [Hh]\.?26[45] | HEVC | AVC | x26[45] | xvid | divx
        | HDR(?:10(?:\+|Plus)?)?| DV | DoVi | SDR
        | 10[Bb]it | 8[Bb]it
        # audio
        | DTS(?:-HD|-MA|-X)? | TrueHD | Atmos | DD\+? | AAC | AC3 | FLAC | MP3 | OPUS
        | [257]\.1
        # language/subtitle markers
        | (?:(?:zh|cn|jp|en|fr|es|ru)[-_]?){1,3}(?:sub|dub)?\b
        | (?:CHS|CHT|ENG|JPN|KOR|GB|BIG5)
          (?:[._+](?:CHS|CHT|ENG|JPN|KOR|GB|BIG5))*
        | [简簡繁](?:[简簡繁])?(?:日|中)?(?:[内內][嵌封](?:字幕)?|字幕)
        | (?:[简簡繁粵粤國国日英中]+(?:語|语)|[简簡繁粵粤國国日英中]+[雙双]語)
          (?:\+(?:[无無]字幕|[内內][嵌封](?:[简簡繁](?:体|體)?(?:中|日)?文?)?字幕))*
        | [内內][嵌封](?:[简簡繁](?:体|體)?(?:中|日)?文?)?字幕
        | [无無]字幕
        | [Ss]ub(?:bed)?
        # misc
        | PROPER | REPACK | REMUX | EXTENDED | THEATRICAL | DIRECTORS\.CUT
        | Pre-Air
        | [Ss]eason\s*\d+
    )
    (?=[\.\s\]\)\-_★☆]|$)  # tag must be complete, not a word prefix
    [\.\s\]\)\-_★☆]?  # trailing separator
    .*$             # consume the rest
    """,
    re.VERBOSE | re.IGNORECASE,
)

# map of English ordinal season words to integers
_ENGLISH_ORDINAL_NUMBERS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}

_DECIMAL_TOKEN = r"\d{1,4}(?:\.\d{1,2}(?!\d))?"
_NUMBER_SUFFIX_GUARD = r"(?![\dA-Za-z])"

_ABSOLUTE_EPISODE_PATTERN = re.compile(
    rf"(?P<local>{_DECIMAL_TOKEN})\s*-\s*[总總]\s*第?\s*"
    rf"(?P<absolute>{_DECIMAL_TOKEN}){_NUMBER_SUFFIX_GUARD}",
    re.IGNORECASE,
)
_TYPED_EPISODE_PATTERN = re.compile(
    rf"""
    (?<![A-Za-z0-9])
    (?P<label>
        NCOP|NCED|OVA|OAD|ONA|SP|SPECIAL|PV|TRAILER|CM|OP|ED
        | 特别篇|特別篇|特典|番外(?:篇)?|总集篇|總集篇
    )
    (?=$|[^A-Za-z]|\d)
    (?:[\s._\-\[\]()【】]*
       (?P<start>{_DECIMAL_TOKEN})(?![\dA-Za-z]))?
    (?:\s*[-~～]\s*(?:(?P=label)[\s._\-]*)?
       (?P<end>{_DECIMAL_TOKEN})(?![\dA-Za-z]))?
    """,
    re.IGNORECASE | re.VERBOSE,
)
_SEASON_EPISODE_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9])[Ss](?P<season>\d{{1,3}})[Ee]"
    rf"(?P<start>{_DECIMAL_TOKEN})(?!\d)"
    rf"(?:\s*[-~～]\s*[Ee]?(?P<end>{_DECIMAL_TOKEN})(?!\d)"
    rf"|[Ee](?P<next>{_DECIMAL_TOKEN})(?!\d))?",
    re.IGNORECASE,
)
_EXPLICIT_EPISODE_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9])[Ee][Pp]?\.?\s*"
    rf"(?P<start>{_DECIMAL_TOKEN})(?!\d)"
    rf"(?:\s*[-~～]\s*[Ee]?[Pp]?\.?(?P<end>{_DECIMAL_TOKEN})(?!\d))?"
    rf"(?:\s*(?:END|FIN)\b)?"
    rf"(?:\s*[\[【(][^\]】)]*[\]】)])?",
    re.IGNORECASE,
)
_CHINESE_EPISODE_PATTERN = re.compile(
    rf"第\s*(?P<start>{_DECIMAL_TOKEN})\s*"
    rf"(?:[-~～]\s*(?P<end>{_DECIMAL_TOKEN})\s*)?[集话話回]",
)
_BRACKET_EPISODE_PATTERN = re.compile(
    rf"[\[【(]\s*(?P<start>{_DECIMAL_TOKEN})"
    rf"(?:\s*[-~～]\s*(?P<end>{_DECIMAL_TOKEN}))?"
    rf"(?:[Vv](?P<version>\d+))?\s*(?:合集)?\s*[\]】)]",
    re.IGNORECASE,
)
_DASH_EPISODE_PATTERN = re.compile(
    rf"\s-\s(?P<start>{_DECIMAL_TOKEN})(?!\d)"
    rf"(?:\s*[-~～]\s*(?P<end>{_DECIMAL_TOKEN})(?!\d))?"
    rf"(?=\s*(?:END\b|FIN\b|[\[【(]|-|$))",
    re.IGNORECASE,
)
_PIPE_RANGE_PATTERN = re.compile(
    rf"\|\s*(?P<start>{_DECIMAL_TOKEN})\s*[-~～]\s*"
    rf"(?P<end>{_DECIMAL_TOKEN})(?!\d)",
)
_RELEASE_VERSION_PATTERN = re.compile(r"(?<![A-Za-z])[Vv](\d+)(?!\d)")
_BATCH_PATTERN = re.compile(r"合集|全集|全\s*\d+\s*[集话話回]|\b(?:batch|complete)\b", re.I)
_END_MARKER_PATTERN = re.compile(r"\b(?:END|FIN)\b", re.IGNORECASE)

_TYPE_LABELS = {
    "sp": EpisodeKind.SPECIAL,
    "special": EpisodeKind.SPECIAL,
    "特别篇": EpisodeKind.SPECIAL,
    "特別篇": EpisodeKind.SPECIAL,
    "特典": EpisodeKind.SPECIAL,
    "番外": EpisodeKind.SPECIAL,
    "番外篇": EpisodeKind.SPECIAL,
    "总集篇": EpisodeKind.SPECIAL,
    "總集篇": EpisodeKind.SPECIAL,
    "ova": EpisodeKind.OVA,
    "oad": EpisodeKind.OAD,
    "ona": EpisodeKind.ONA,
    "ncop": EpisodeKind.NCOP,
    "op": EpisodeKind.NCOP,
    "nced": EpisodeKind.NCED,
    "ed": EpisodeKind.NCED,
    "pv": EpisodeKind.PV,
    "trailer": EpisodeKind.TRAILER,
    "cm": EpisodeKind.CM,
}


def _canonical_decimal(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _parse_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value).normalize()
    except InvalidOperation:
        return None


def _episode_values(start: Decimal, end: Decimal | None) -> tuple[Decimal, ...]:
    if end is None or end == start:
        return (start,)
    if start == start.to_integral() and end == end.to_integral():
        step = 1 if end > start else -1
        values = range(int(start), int(end) + step, step)
        return tuple(Decimal(value) for value in values)
    # Decimal episode numbers are labels, not an arithmetic sequence.
    return (start, end)


def _structured_episodes(name: str) -> tuple[EpisodeRef, ...]:
    episodes: dict[tuple[EpisodeKind, Decimal], EpisodeRef] = {}

    def add(
        kind: EpisodeKind,
        start_text: str | None,
        end_text: str | None = None,
        *,
        absolute_text: str | None = None,
    ) -> None:
        start = _parse_decimal(start_text)
        if start is None:
            start = Decimal(1)
        end = _parse_decimal(end_text)
        absolute = _parse_decimal(absolute_text)
        for offset, number in enumerate(_episode_values(start, end)):
            absolute_number = absolute
            if absolute is not None and number == number.to_integral():
                absolute_number = absolute + offset
            key = (kind, number)
            current = episodes.get(key)
            if current is None or (
                current.absolute_number is None and absolute_number is not None
            ):
                episodes[key] = EpisodeRef(kind, number, absolute_number)

    for match in _ABSOLUTE_EPISODE_PATTERN.finditer(name):
        add(
            EpisodeKind.REGULAR,
            match.group("local"),
            absolute_text=match.group("absolute"),
        )

    for match in _TYPED_EPISODE_PATTERN.finditer(name):
        label = match.group("label").casefold()
        add(
            _TYPE_LABELS.get(label, EpisodeKind.OTHER),
            match.group("start"),
            match.group("end"),
        )

    for pattern in (
        _SEASON_EPISODE_PATTERN,
        _EXPLICIT_EPISODE_PATTERN,
        _CHINESE_EPISODE_PATTERN,
        _BRACKET_EPISODE_PATTERN,
        _DASH_EPISODE_PATTERN,
        _PIPE_RANGE_PATTERN,
    ):
        for match in pattern.finditer(name):
            start = match.groupdict().get("start")
            looks_like_year = (
                start
                and len(start.split(".", 1)[0]) == 4
                and start.startswith(("19", "20"))
            )
            if looks_like_year:
                continue
            end = match.groupdict().get("end") or match.groupdict().get("next")
            add(EpisodeKind.REGULAR, start, end)

    # An explicit regular token (for example S01E00 Special) is stronger than
    # an unnumbered descriptive extra label.
    if any(ref.kind == EpisodeKind.REGULAR for ref in episodes.values()):
        for match in _TYPED_EPISODE_PATTERN.finditer(name):
            if match.group("start") is None:
                label = match.group("label").casefold()
                kind = _TYPE_LABELS.get(label, EpisodeKind.OTHER)
                episodes.pop((kind, Decimal(1)), None)

    return tuple(episodes.values())


def normalize_series_title(title: str) -> str:
    """Normalize a local series title without fuzzy or provider-based matching."""
    normalized = unicodedata.normalize("NFKC", title)
    normalized = _T2S_CONVERTER.convert(normalized).casefold()
    chars = [ch if ch.isalnum() else " " for ch in normalized]
    return " ".join("".join(chars).split())


def parse_media_name(
    name: str,
    *,
    series_title: str | None = None,
    year: int | None = None,
    season: int | None = None,
) -> ParsedMediaName:
    """Parse a media name into provider-independent structured metadata."""
    context_name = series_title if series_title is not None else name
    parsed_title = extract_title(context_name)
    parsed_year = year if year is not None else extract_year(context_name)
    parsed_season = season if season is not None else extract_season(context_name)
    if parsed_season is None and series_title is not None:
        parsed_season = extract_season(name)

    versions = [
        int(match.group(1)) for match in _RELEASE_VERSION_PATTERN.finditer(name)
    ]
    provided_context = series_title is not None
    episodes = _structured_episodes(name)
    return ParsedMediaName(
        raw_name=name,
        title=parsed_title,
        normalized_title=normalize_series_title(parsed_title),
        year=parsed_year,
        season=parsed_season,
        episodes=episodes,
        release_version=max(versions, default=None),
        is_batch=bool(_BATCH_PATTERN.search(name)) or len(episodes) > 1,
        context_source="provided" if provided_context else "inferred",
        confidence="high" if provided_context else "low",
    )


def build_local_episode_keys(parsed: ParsedMediaName) -> tuple[str, ...]:
    """Build deterministic local episode keys from structured parsed metadata."""
    if not parsed.normalized_title:
        return ()
    year = str(parsed.year) if parsed.year is not None else "_"
    payload = f"title={parsed.normalized_title}|year={year}"
    series_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    season = str(parsed.season) if parsed.season is not None else "_"
    return tuple(
        f"local:v1:{series_hash}:s{season}:{episode.kind.value}:"
        f"{episode.canonical_number}"
        for episode in parsed.episodes
    )


def extract_year(name: str) -> int | None:
    """Extract the release year from a media file name.

    Args:
        name: The raw file name or path stem string.

    Returns:
        The four-digit year as an integer, or None if not found.
    """
    match = _YEAR_PATTERN.search(name)
    if match:
        return int(match.group("year"))
    return None


def extract_season(name: str) -> int | None:
    """Extract the season number from a media file name.

    Args:
        name: The raw file name or path stem string.

    Returns:
        The season number as an integer, or None if not found.
    """
    match = _SEASON_PATTERN.search(name)
    if match:
        value = next(g for g in match.groups() if g is not None)
        if value.isdigit():
            return int(value)
        english_number = _ENGLISH_ORDINAL_NUMBERS.get(value.lower())
        return english_number if english_number is not None else cn_to_int(value)
    return None


def extract_episode(name: str) -> int | None:
    """Extract the episode number from a media file name.

    Args:
        name: The raw file name or path stem string.

    Returns:
        The episode number as an integer, or None if not found.
    """
    for episode in _structured_episodes(name):
        if episode.kind != EpisodeKind.REGULAR:
            continue
        if episode.number != episode.number.to_integral():
            return None
        return int(episode.number)

    match = _EPISODE_PATTERN.search(name)
    if match:
        value = next(g for g in match.groups() if g is not None)
        return int(value) if value.isdigit() else cn_to_int(value)
    return None


def extract_title(name: str) -> str:
    """Extract a clean title string from a media file name.

    Strips common prefix noise (sub-group tags, download-site labels) and
    suffix noise (year, season/episode markers, video quality/codec tags,
    etc.) from the input string.

    Args:
        name: The raw file name or path stem string.

    Returns:
        A cleaned title string suitable for media scraping.
    """
    # strip the leading bracketed prefix (sub-group / site label)
    title = _PREFIX_PATTERN.sub("", name).strip()
    title = _LEADING_META_PREFIX_PATTERN.sub("", title).strip()
    title = _LEADING_STAR_PREFIX_PATTERN.sub("", title).strip()
    title = _LEADING_BROADCAST_MARKER_PATTERN.sub("", title).strip()
    title = _BRACKETED_EPISODE_TITLE_SUFFIX_PATTERN.sub("", title).strip()

    # remove standalone year token before video tags
    title = _YEAR_PATTERN.sub(" ", title)

    # remove collection ranges before their component episode tokens
    title = _COLLECTION_RANGE_PATTERN.sub(" ", title)

    # remove structured episode markers, including decimals and typed extras
    for pattern in (
        _ABSOLUTE_EPISODE_PATTERN,
        _TYPED_EPISODE_PATTERN,
        _SEASON_EPISODE_PATTERN,
        _EXPLICIT_EPISODE_PATTERN,
        _CHINESE_EPISODE_PATTERN,
        _BRACKET_EPISODE_PATTERN,
        _DASH_EPISODE_PATTERN,
        _PIPE_RANGE_PATTERN,
    ):
        title = pattern.sub(" ", title)
    title = _RELEASE_VERSION_PATTERN.sub(" ", title)
    title = _END_MARKER_PATTERN.sub(" ", title)

    # remove collection episode ranges before technical tags truncate context
    title = _COLLECTION_RANGE_PATTERN.sub(" ", title)

    # remove trailing technical tags and everything after them
    title = _VIDEO_TAGS_PATTERN.sub("", title)

    # remove any collection episode ranges exposed by technical tag cleanup
    title = _COLLECTION_RANGE_PATTERN.sub(" ", title)

    # remove season and episode markers
    title = _SEASON_PATTERN.sub(" ", title)
    title = _EPISODE_PATTERN.sub(" ", title)

    # replace common separators with spaces and collapse whitespace
    title = _SEPARATOR_PATTERN.sub(" ", title).strip()
    title = _BRACKET_BOUNDARY_PATTERN.sub(" ", title).strip()

    # unwrap a single surrounding bracket pair left after stripping the prefix
    title = re.sub(r"^[\[\(【](.*?)[\]\)】]$", r"\1", title).strip()

    # fallback to original name if nothing survives
    if not title:
        title = _SEPARATOR_PATTERN.sub(" ", name).strip()

    return title
