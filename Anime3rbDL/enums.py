"""
Data models and enums for Anime3rbDL.

This module defines structured representations of:
- Anime metadata (series, episodes, search results, contributors, etc.)
- Download information (resolutions, sizes, direct links)
- Mapping of Arabic genres/roles to English equivalents (TranslateArabic)
- Enums for schema.org types and application-level object typing

These models are used throughout the parser to store, organize, and retrieve
parsed anime data in a consistent way.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime
import uuid

# ---------------- Translation ---------------- #
TranslateArabic = {
    "قيد البث":"Currently Airing",
    "منتهي":"Ended",
    "الاستديو": "studio",
    "المخرج": "director",
    "المؤلف": "creator",
    "أكشن": "action",
    "كوميدي": "comedy",
    "خيال": "fantasy",
    "مغامرة": "adventure",
    "دراما": "drama",
    "شونين": "shounen",
    "مدرسي": "school",
    "رومانسي": "romance",
    "خيال علمي": "sci-fi",
    "خارق للطبيعة": "supernatural",
    "سينين": "seinen",
    "غموض": "mystery",
    "إيتشي": "ecchi",
    "تاريخي": "historical",
    "بطولة راشدين": "adult-cast",
    "الحياة اليومية": "slice-of-life",
    "ميكا": "mecha",
    "قوى خارقة": "super-power",
    "حريم": "harem",
    "عسكري": "military",
    "رياضي": "sports",
    "تشويق": "suspense",
    "شوچو": "shoujo",
    "إيسيكاي": "isekai",
    "أساطير": "mythology",
    "نفسي": "psychological",
    "رعب": "horror",
    "موسيقى": "music",
    "دموي": "gore",
    "قتالي": "martial-arts",
    "ساخر": "parody",
    "فضاء": "space",
    "بوليسي": "detective",
    "حائز على جوائز": "award-winning",
    "كيوت": "cgdct",
    "رياضات جماعية": "team-sports",
    "للأطفال": "kids",
    "إياشيكي": "iyashikei",
    "كوميديا حركية": "gag-humor",
    "خيال حضري": "urban-fantasy",
    "عمل": "workplace",
    "مصاصي دماء": "vampire",
    "فتاة ساحرة": "mahou-shoujo",
    "ساموراي": "samurai",
    "أنثروبولوجي": "anthropomorphic",
    "تناسخ و إعادة إحياء": "reincarnation",
    "چوسي": "josei",
    "سفر عبر الزمن": "time-travel",
    "استراتيجي": "strategy-game",
    "حب متعدد الأطراف": "love-polygon",
    "ثقافة الأوتاكو": "otaku-culture",
    "أيدول إناث": "idols-female",
    "جريمة منظمة": "organized-crime",
    "ألعاب فيديو": "video-game",
    "نجاة": "survival",
    "طعام": "gourmet",
    "فنون استعراضية": "performing-arts",
    "سباق": "racing",
    "عكس حريم": "reverse-harem",
    "حب فتيات": "girls-love",
    "ابتكاري": "avant-garde",
    "رياضات قتالية": "combat-sports",
    "رعاية أطفال": "childcare",
    "فنون بصرية": "visual-arts",
    "ألعاب عالية المخاطر": "high-stakes-game",
    "حالة حب": "love-status-quo",
    "جانحون": "delinquents",
    "أيدول ذكور": "idols-male",
    "حيوانات أليفة": "pets",
    "طبي": "medical",
    "تنكر في ملابس الجنس الآخر": "crossdressing",
    "حب فتيان": "boys-love",
    "تبديل جنسي سحري": "magical-sex-shift",
    "صناعة الترفيه": "showbiz",
    "ايروتيكا": "erotica",
    "تعليمية": "educational",
    "شريرة": "villainess",
}

# ---------------- Enums ---------------- #


class CustomTypes(Enum):
    """
    Enumeration of schema.org-like object types found in anime metadata.
    """

    SERIES = "TVSeries"
    EPISODE = "Episode"
    MOVIE = "Movie"
    ORGANIZATION = "Organization"
    VIDEO_OBJECT = "VideoObject"
    AGGRATE_RATING = "AggregateRating"
    ITEM_LIST = "ItemList"
    NEWEST_EPISODES = "أحدث الحلقات"
    LAST_ADDED_ANIMES = "Latest Added Animes"
    FIXED_WORKS = "الأعمال المثبتة"


# ---------------- Data Models ---------------- #


@dataclass
class TotalSizeEnum:
    """
    Accumulator for total download size per resolution.
    """

    Low: int = 0
    Mid: int = 0
    High: int = 0
    UnKnown: int = 0
    FLow: str = None
    FMid: str = None
    FHigh: str = None
    FUnKnown: str = None

    def getByVal(self, res: str):
        """
        Get resolution data by resolution string.

        Args:
            res (str): Resolution name ("low", "mid", "high", "480p", "720p", "1080p").

        Returns:
            ResoultionData: Resolution data object.
        """
        res = str(res).lower()
        if res == "low" or res == "480p":
            return self.Low, self.FLow
        if res == "mid" or res == "720p":
            return self.Mid, self.FMid
        if res == "high" or res == "1080p":
            return self.High, self.FHigh
        return self.UnKnown, self.FUnKnown


@dataclass
class ResoultionData:
    """
    Metadata for a specific resolution download.
    """

    Size: int = 0
    FormatedSize: str = ""
    DownloadLink: str = ""
    DirectLink: str = ""
    FileName: str = ""
    Index: int = 0

@dataclass
class ResolutionURLs:
    """
    Container for download information across multiple resolutions.
    """
    Low: ResoultionData = field(default_factory=ResoultionData)
    Mid: ResoultionData = field(default_factory=ResoultionData)
    High: ResoultionData = field(default_factory=ResoultionData)
    UnKnown: ResoultionData = field(default_factory=ResoultionData)
    TotalSize: TotalSizeEnum = field(default_factory=TotalSizeEnum)

    
    def getByVal(self, res: str):
        """
        Get resolution data by resolution string.

        Args:
            res (str): Resolution name ("low", "mid", "high", "480p", "720p", "1080p").

        Returns:
            ResoultionData: Resolution data object.
        """
        res = str(res).lower()
        if res == "low" or res == "480p":
            return self.Low
        if res == "mid" or res == "720p":
            return self.Mid
        if res == "high" or res == "1080p":
            return self.High
        return self.UnKnown


@dataclass
class VideoObjectEnum:
    """
    Representation of a single episode or video object.
    """

    Html: Optional[bytes] = None
    Type: CustomTypes = CustomTypes.EPISODE
    PageName: Optional[str] = None
    PageURL: Optional[str] = None
    PublishedDate: Optional[str] = None
    PublishYear: Optional[str] = None
    Language: Optional[str] = None
    PageDescription: Optional[str] = None
    Name: Optional[str] = None
    ThumbnailUrl: Optional[str] = None
    EmbedUrl: Optional[str] = None
    PlayerType: Optional[str] = None
    Description: Optional[str] = None
    UploadDate: Optional[datetime] = None
    IsFamilyFriendly: Optional[bool] = None
    Duration: Optional[str] = None
    DownloadData: ResolutionURLs = field(default_factory=ResolutionURLs)
    IsPartOf: Optional[str] = None
    EpisodesCount: int = 1


@dataclass
class EpisodeEnum:
    """
    Representation of an episode entry in a series.
    """

    Id: Optional[str] = None
    Type: Optional[CustomTypes] = None
    Index: Optional[int] = None
    Name: Optional[str] = None
    Title: Optional[str] = None
    Description: Optional[str] = None
    Url: Optional[str] = None
    PublishedDate: Optional[str] = None
    PublishYear: Optional[str] = None
    Video: Optional[VideoObjectEnum] = None


@dataclass
class ContributorEnum:
    """
    Contributor information for an anime (director, studio, etc.).
    """

    name: Optional[str] = None
    url: Optional[str] = None
    role: Optional[str] = None


@dataclass
class TargetAnimeEnum:
    """
    Representation of an entire anime (series).
    """

    Html: Optional[bytes] = None
    Type: Optional[CustomTypes] = None
    Title: Optional[str] = None
    ClearTitle: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    Url: Optional[str] = None
    PublishDate: Optional[datetime] = None
    TrialersUrls: list[str] = field(default_factory=list)
    BannerURL: Optional[str] = None
    Language: Optional[str] = None
    Genres: list[str] = field(default_factory=list)
    AlternateNames: list[str] = field(default_factory=list)
    Contributors: list[ContributorEnum] = field(default_factory=list)
    Rate: Optional[float] = None
    Status: Optional[str] = None
    EpisodesCount: Optional[int] = None
    EpisodesURLs: list[str] = field(default_factory=list)
    Episodes: list[EpisodeEnum] = field(default_factory=list, init=False, repr=False)

    def Add(
        self,
        index,
        title,
        name,
        desc,
        url,
        date,
        _html,
        lang,
        real_name,
        thumb_url,
        embed_url,
        player_type,
        vid_desc,
        upload_date,
        isfamily,
        duration,
        qualities,
        is_part_of,
    ):
        """
        Add an episode to this anime.

        Returns:
            EpisodeEnum: Created episode object.
        """
        _obj = EpisodeEnum(
            uuid.uuid4().hex,
            CustomTypes.SERIES,
            index,
            name,
            title,
            desc,
            url,
            date,
            date.year,
            VideoObjectEnum(
                _html,
                CustomTypes.EPISODE,
                name,
                url,
                date,
                date.year,
                lang,
                desc,
                real_name,
                thumb_url,
                embed_url,
                player_type,
                vid_desc,
                upload_date,
                isfamily,
                duration,
                qualities,
                is_part_of,
            ),
        )
        self.Episodes.append(_obj)
        return _obj

    def getByVal(self, _source: str | int) -> Optional[TinySearchEnum]:
        """
        Retrieve episode by index, Id, Name, or Url.

        Args:
            _source (str | int): Lookup key.

        Returns:
            EpisodeEnum | None: Matching episode if found.
        """
        if isinstance(_source, int):
            return self.Episodes[_source]
        for _ in self.Episodes:
            if _.Id == _source or _.Name == _source or _.Url == _source:
                return _
        return None


@dataclass
class SearchEnum:
    """
    Representation of a detailed search result entry.
    """

    Id: Optional[str] = None
    Type: Optional[CustomTypes] = None
    Title: Optional[str] = None
    Name: Optional[str] = None
    url: Optional[str] = None
    Language: Optional[str] = None
    BannerLink: Optional[str] = None
    Descripion: Optional[str] = None
    NumberOfEpisodes: Optional[int] = 1
    Genres: list[str] = field(default_factory=list)
    PuplishedDate: Optional[datetime] = None
    PublishYear: Optional[int] = None
    Rate: Optional[float] = None


@dataclass
class SearchResultEnum:
    """
    Container for detailed search results.
    """

    Results: list[SearchEnum] = field(default_factory=list, repr=False)

    @property
    def Count(self):
        return len(self.Results)

    def Add(
        self, _type, title, name, url, lang, image, desc, count, genres, date, rate
    ):
        """
        Add a new search result entry.
        """
        self.Results.append(
            SearchEnum(
                uuid.uuid4().hex,
                CustomTypes(_type),
                title,
                name,
                url,
                lang,
                image,
                desc,
                int(count),
                genres,
                date,
                date.year,
                rate,
            )
        )

    def getByVal(self, _source: str | int) -> Optional[TinySearchEnum]:
        """
        Retrieve search result by index, Id, Name, or Url.
        """
        if isinstance(_source, int):
            return self.Results[_source]
        for _ in self.Results:
            if _.Id == _source or _.Name == _source or _.url == _source:
                return _
        return None


@dataclass
class TinySearchEnum:
    """
    Lightweight search result entry (title, rating, year, etc.).
    """

    Id: Optional[str] = None
    Type: Optional[CustomTypes] = None
    Title: Optional[str] = None
    Name: Optional[str] = None
    Rate: Optional[float] = None
    NumberOfEpisodes: Optional[int] = None
    PublishYear: Optional[int] = None
    url: Optional[str] = None
    BannerLink: Optional[str] = None
    Description: Optional[str] = None


@dataclass
class TinySearchResultEnum:
    """
    Container for lightweight search results.
    """

    Results: list[TinySearchEnum] = field(default_factory=list, repr=False)

    @property
    def Count(self):
        return len(self.Results)

    def Add(self, title, name, link, image, desc, rate, count, year):
        """
        Add a tiny search result entry.
        """
        self.Results.append(
            TinySearchEnum(
                uuid.uuid4().hex,
                CustomTypes.ITEM_LIST,
                title,
                name,
                rate,
                count,
                year,
                link,
                image,
                desc,
            )
        )

    def getByVal(self, _source: str | int) -> Optional[TinySearchEnum]:
        """
        Retrieve search result by index, Id, Name, or Url.
        """
        if isinstance(_source, int):
            return self.Results[_source]
        for _ in self.Results:
            if _.Id == _source or _.Name == _source or _.url == _source:
                return _
        return None


@dataclass
class LatestAddedDataEnum:
    """Data model for latest added anime with episode tracking.

    Tracks anime metadata and maintains list of added episode numbers.
    Used to associate episodes with their parent series in latest updates.
    """

    Id: Optional[str] = None
    Type: Optional[CustomTypes] = None
    Title: Optional[str] = None
    Name: Optional[str] = None
    Rate: Optional[float] = None
    NumberOfEpisodes: Optional[int] = None
    PublishYear: Optional[int] = None
    Genres: list[str] = field(default_factory=list, repr=False)
    url: Optional[str] = None
    BannerLink: Optional[str] = None
    Description: Optional[str] = None
    LastAdded: list[int] = field(default_factory=list, repr=False)

    @property
    def LastAddedStr(self):
        return ",".join([str(f) for f in self.LastAdded])

    def Add(self, value: int = 1):
        self.LastAdded.append(value)
        self.LastAdded = list(set(self.LastAdded))
        self.LastAdded.sort()
        self.NumberOfEpisodes = self.LastAdded[-1]

@dataclass
class LatestAddedAnimeResultsEnum:
    """
    Container for lightweight Latest Added Anime results.
    """

    Results: list[LatestAddedDataEnum] = field(default_factory=list, repr=False)

    @property
    def Count(self):
        return len(self.Results)

    def Add(self, type, title, name, link, image, genres, desc, rate, date):
        """
        Add data about last added anime result entry.
        """
        self.Results.append(LatestAddedDataEnum(uuid.uuid4().hex,type,title,name,rate,-1,date.year,genres,link,image,desc,[],))

    def Remove(self,id):
        self.Results.remove(id)

    def getByVal(self, _source: str | int):
        """
        Retrieve search result by index, Id, Name, or Url.
        """
        if isinstance(_source, int):
            return self.Results[_source]
        _source = _source.lower()
        if _source.startswith("http"):
            _source = _source.split("/")[-1]
        
        for result in self.Results:
            if result.Id == _source or result.Title.lower() == _source or result.Name.lower() == _source or result.url == _source or result.url.split("/")[-1] == _source:
                return result
        return None

@dataclass
class LastAddedEpisodeDataEnum:
    """
    Representation of a single episode entry in the latest added episodes list.
    """
    Id: Optional[str] = None
    Type: Optional[CustomTypes] = None
    url: Optional[str] = None
    image: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    index: Optional[int] = None
    
@dataclass
class LastAddedEpisodesResutlsEnum:
    
    """
    Container for lightweight Latest Added Anime results.
    """

    Results: list[LastAddedEpisodeDataEnum] = field(default_factory=list, repr=False)

    @property
    def Count(self):
        return len(self.Results)

    def Add(self, type, title, name, link, image, index):
        """
        Add data about last added anime result entry.
        """
        existing = self.getByVal(link)
        if existing:
            existing.index = max(index, existing.index)
            return
        
        self.Results.append(
            LastAddedEpisodeDataEnum(uuid.uuid4().hex, type, link, image, name, title, index)
        )

    def getByVal(self, _source: str | int):
        """
        Retrieve search result by index, Id, Name, or Url.
        """
        if isinstance(_source, int):
            return self.Results[_source]
        _source = _source.lower()
        if _source.startswith("http"):
            _source = _source.split("/")[-1]
        
        for result in self.Results:
            if result.Id == _source or result.title.lower() == _source or result.name.lower() == _source or result.url == _source or result.url.split("/")[-1] == _source:
                return result
        return None

    
@dataclass
class ResponseFileInfo:
    """HTTP response metadata for downloaded files.

    Stores file information extracted from HTTP headers and content.
    Used for tracking download progress and file validation.
    """

    filename: Optional[str] = None
    filesize: Optional[int] = None
    fileext: Optional[str] = None
    ETag: Optional[str] = None
    AcceptRange: Optional[bool] = None


class AppTypes(Enum):
    """
    Application-level type classification for data models.
    """

    IsSeries = TargetAnimeEnum
    IsEpisode = EpisodeEnum
    IsDeepSearch = SearchResultEnum
    IsSearch = TinySearchResultEnum

    def __eq__(self, other):
        """
        Compare AppTypes enum with a class type.
        """
        if isinstance(other, type):
            return self.value == other
        return Enum.__eq__(self, other)
