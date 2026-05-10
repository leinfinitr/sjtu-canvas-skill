from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qsl, quote, urlparse

import requests
from bs4 import BeautifulSoup

from .cookie_utils import parse_cookie_string

OIDC_LOGIN_URL = "https://v.sjtu.edu.cn/jy-application-canvas-sjtu/oidc/login_initiations"
LTI_AUTH_URL = "https://v.sjtu.edu.cn/jy-application-canvas-sjtu/lti3/lti3Auth/ivs"
TOKEN_URL = "https://v.sjtu.edu.cn/jy-application-canvas-sjtu/lti3/getAccessTokenByTokenId"
VIDEO_LIST_URL = "https://v.sjtu.edu.cn/jy-application-canvas-sjtu/directOnDemandPlay/findVodVideoList"
VIDEO_INFO_URL = "https://v.sjtu.edu.cn/jy-application-canvas-sjtu/directOnDemandPlay/getVodVideoInfos"
SUBTITLE_URL = "https://v.sjtu.edu.cn/jy-application-canvas-sjtu/transfer/translate/detail"
VIDEO_REFERER = "https://v.sjtu.edu.cn/jy-application-canvas-sjtu-ui/"


@dataclass
class VideoSession:
    canvas_course_id: str
    token: str


@dataclass
class CanvasVideo:
    video_id: str
    video_name: str
    course_begin_time: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoInfo:
    cour_id: int
    video_play_response_vo_list: List[Dict[str, Any]]
    raw: Dict[str, Any]


@dataclass
class SubtitleItem:
    bg: int
    ed: int
    res: str
    en: Optional[str] = None
    zh: Optional[str] = None


def parse_redirect_params(url: str | None) -> Dict[str, str]:
    if not url:
        return {}
    parsed = urlparse(url)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if "?" in parsed.fragment:
        _, _, fragment_query = parsed.fragment.partition("?")
        params.update(parse_qsl(fragment_query, keep_blank_values=True))
    return params


def get_nested_value(obj: Any, *path: str) -> Any:
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def extract_video_records(payload: Any) -> Optional[List[Dict[str, Any]]]:
    if isinstance(payload, list):
        return payload
    candidates = (
        ("data", "records"),
        ("data", "list"),
        ("data", "rows"),
        ("data", "items"),
        ("data", "page", "records"),
        ("data", "page", "list"),
        ("body", "list"),
        ("body",),
        ("data",),
    )
    for path in candidates:
        value = get_nested_value(payload, *path)
        if isinstance(value, list):
            return value
    return None


def extract_video_detail(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, dict):
        for path in (("data",), ("body",)):
            value = get_nested_value(payload, *path)
            if isinstance(value, dict):
                return value
        if "courId" in payload or "videoPlayResponseVoList" in payload:
            return payload
    return None


def format_srt_time(milliseconds: int) -> str:
    milliseconds = max(0, int(milliseconds))
    hours, rem = divmod(milliseconds, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def format_text_time(milliseconds: int) -> str:
    milliseconds = max(0, int(milliseconds))
    hours, rem = divmod(milliseconds, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, _ = divmod(rem, 1_000)
    if hours:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return f"{minutes:02}:{seconds:02}"


class SJTUVideoClient:
    def __init__(self, oc_cookie: str, base_url: str = "https://oc.sjtu.edu.cn"):
        if not oc_cookie or not oc_cookie.strip():
            raise ValueError("OC_COOKIE is required for SJTU classroom video features")
        self.base_url = base_url.rstrip("/")
        self.oc_cookie = oc_cookie
        self.cookies = parse_cookie_string(oc_cookie)
        self.session = requests.Session()
        self.session.cookies.update(self.cookies)
        self.video_session: Optional[VideoSession] = None

    @staticmethod
    def extract_external_tool_id(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        root = soup.find("div", attrs={"id": "main"}) or soup
        for anchor in root.find_all("a"):
            text = anchor.get_text(strip=True)
            if text.startswith("课堂视频") and not text.endswith("旧版"):
                href = anchor.get("href", "")
                tool_id = href.rstrip("/").rpartition("/")[-1]
                if tool_id:
                    return tool_id
        raise RuntimeError("未找到新版课堂视频入口，可能是课程未开放课堂视频或页面结构已变化。")

    @staticmethod
    def extract_form_inputs(html: str, action: str) -> Dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form", attrs={"action": action})
        if form is None:
            raise RuntimeError(f"未找到表单: {action}")
        data: Dict[str, str] = {}
        for item in form.find_all("input"):
            name = item.get("name")
            if name:
                data[name] = item.get("value", "")
        return data

    def get_external_tool_id(self, course_id: int) -> str:
        resp = self.session.get(f"{self.base_url}/courses/{course_id}")
        resp.raise_for_status()
        return self.extract_external_tool_id(resp.text)

    def launch_video_platform(self, course_id: int) -> VideoSession:
        external_tool_id = self.get_external_tool_id(course_id)
        resp = self.session.get(
            f"{self.base_url}/courses/{course_id}/external_tools/{external_tool_id}"
        )
        resp.raise_for_status()
        oidc_data = self.extract_form_inputs(resp.text, OIDC_LOGIN_URL)

        oidc_resp = self.session.post(OIDC_LOGIN_URL, data=oidc_data, allow_redirects=True)
        oidc_resp.raise_for_status()
        auth_data = self.extract_form_inputs(oidc_resp.text, LTI_AUTH_URL)

        auth_resp = self.session.post(LTI_AUTH_URL, data=auth_data, allow_redirects=False)
        auth_resp.raise_for_status()
        params = parse_redirect_params(auth_resp.headers.get("location"))
        token_id = params.get("tokenId")
        if not token_id:
            raise RuntimeError(f"未能从视频平台跳转中解析 tokenId，当前返回字段: {sorted(params)}")

        token_resp = self.session.get(TOKEN_URL, params={"tokenId": token_id})
        token_resp.raise_for_status()
        token_payload = token_resp.json().get("data") or {}
        token = token_payload.get("token")
        if not token:
            raise RuntimeError("视频平台未返回 access token")
        access_params = token_payload.get("params") or {}
        canvas_course_id = (
            access_params.get("courId")
            or access_params.get("canvasCourseId")
            or access_params.get("courseId")
            or params.get("courId")
            or params.get("canvasCourseId")
            or str(course_id)
        )
        self.video_session = VideoSession(canvas_course_id=str(canvas_course_id), token=str(token))
        return self.video_session

    def ensure_video_session(self, course_id: int) -> VideoSession:
        if self.video_session is None:
            return self.launch_video_platform(course_id)
        return self.video_session

    def list_videos(self, course_id: int) -> List[CanvasVideo]:
        video_session = self.ensure_video_session(course_id)
        payload = self._post_video_list(video_session.canvas_course_id, video_session.token)
        records = extract_video_records(payload)
        if records is None:
            raise RuntimeError("视频列表接口未返回可识别的数据")
        videos: List[CanvasVideo] = []
        for item in records:
            video_id = str(item.get("videoId") or item.get("id") or "")
            video_name = str(item.get("videoName") or item.get("name") or item.get("courName") or video_id)
            videos.append(
                CanvasVideo(
                    video_id=video_id,
                    video_name=video_name,
                    course_begin_time=item.get("courseBeginTime") or item.get("beginTime"),
                    raw=item,
                )
            )
        return videos

    def _post_video_list(self, canvas_course_id: str, token: str) -> Any:
        resp = self.session.post(
            VIDEO_LIST_URL,
            json={"canvasCourseId": quote(str(canvas_course_id), safe="")},
            headers={"token": token, "Referer": VIDEO_REFERER},
        )
        resp.raise_for_status()
        return resp.json()

    def get_video_info(self, video_id: str, course_id: int | None = None) -> VideoInfo:
        video_session = self.video_session
        if video_session is None:
            if course_id is None:
                raise RuntimeError("get_video_info requires an active video session or course_id")
            video_session = self.launch_video_platform(course_id)
        resp = self.session.post(
            VIDEO_INFO_URL,
            data={"playTypeHls": "true", "id": video_id, "isAudit": "true"},
            headers={"token": video_session.token},
        )
        resp.raise_for_status()
        detail = extract_video_detail(resp.json())
        if detail is None:
            raise RuntimeError("视频详情接口未返回可识别的数据")
        cour_id = int(detail.get("courId") or detail.get("courseId"))
        plays = detail.get("videoPlayResponseVoList") or []
        return VideoInfo(cour_id=cour_id, video_play_response_vo_list=plays, raw=detail)

    def get_subtitle(self, cour_id: int) -> List[SubtitleItem]:
        video_session = self.video_session
        if video_session is None:
            raise RuntimeError("get_subtitle requires an active video session")
        resp = self.session.post(
            SUBTITLE_URL,
            json={"courseId": cour_id},
            headers={"token": video_session.token},
        )
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data") or payload.get("body")
        if not isinstance(data, dict):
            return []
        raw_items = data.get("beforeAssemblyList") or data.get("before_assembly_list") or []
        return [
            SubtitleItem(
                bg=int(item.get("bg", 0)),
                ed=int(item.get("ed", item.get("bg", 0))),
                res=str(item.get("res", "")),
                en=item.get("en"),
                zh=item.get("zh"),
            )
            for item in raw_items
            if item.get("res")
        ]

    @staticmethod
    def subtitle_to_srt(items: Iterable[SubtitleItem]) -> str:
        item_list = list(items)
        blocks = []
        for index, item in enumerate(item_list, start=1):
            end = item.ed if index == len(item_list) else item_list[index].bg
            blocks.append(
                f"{index}\n{format_srt_time(item.bg)} --> {format_srt_time(end)}\n{item.res}\n"
            )
        return "\n".join(blocks)

    @staticmethod
    def subtitle_to_text(items: Iterable[SubtitleItem]) -> str:
        return "\n".join(f"[{format_text_time(item.bg)}] {item.res}" for item in items)
