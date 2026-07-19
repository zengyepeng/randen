"""Randen Studio 应用核心——文件管理、配置、生命周期，无 HTTP 依赖。

大型操作逻辑（写作、审查、聊天、来源、导入、导出）委托至 routes._ops 模块。
"""

from __future__ import annotations
import os
import re
import tempfile
from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlparse
import yaml
from tools.novel_service import NovelApplicationService, NovelServiceError
from tools.novel_workspace import list_chapters, novel_root
from tools.version import __version__
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
_EMPTY_SNAPSHOT: dict[str, Any] = {
    "novel_id": "", "title": "新小说", "current_arc": "arc_001",
    "current_chapter": "ch_001", "stage": "discovery", "chapters": 0,
    "writing_units": 0, "target_units": 0, "characters": 0,
    "world_documents": 0, "pending_foreshadowing": 0, "total_tokens": 0,
    "reviewed_chapters": 0, "average_review_score": 0,
    "creative_focus": {"goal": "", "must_keep": [], "must_avoid": [], "notes": []},
    "readiness": {"author_intent": False, "background": False, "foundation": False,
                  "characters": False, "outline": False, "creative_focus": False},
    "next_actions": ["先创建小说项目"],
}


class StudioError(Exception):
    """Studio 业务异常。"""
    def __init__(self, message: str, status: int = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


class StudioApplication:
    """小说项目文件管理与写作执行核心。"""
    def __init__(
        self,
        project_root: Path,
        writer_executor: Callable[[Path, dict[str, Any]], dict[str, Any]] | None = None,
        review_executor: Callable[[Path, dict[str, Any]], dict[str, Any]] | None = None,
        chat_executor: Callable[[Path, str, str, str], dict[str, Any]] | None = None,
        source_executor: Callable[[Path, dict[str, Any]], dict[str, Any]] | None = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.config_path = self.project_root / "novel_config.yaml"
        self.initialized = self.config_path.exists()
        self.config = self._load_config() if self.initialized else {}
        self.novel_id = str(self.config.get("novel_id") or "")
        if self.initialized and not self.novel_id:
            raise StudioError("novel_config.yaml 缺少 novel_id")
        self.novel_root = (
            novel_root(self.project_root, self.novel_id).resolve()
            if self.initialized else self.project_root)
        self._writer_executor = writer_executor
        self._review_executor = review_executor
        self._chat_executor = chat_executor
        self._source_executor = source_executor
        self._write_lock = Lock()
        self._novel_service = self._build_novel_service() if self.initialized else None
    # ── 属性（供 routes.py 访问） ──────────────────────────────
    @property
    def chat_executor(self) -> Callable[[Path, str, str, str], dict[str, Any]] | None:
        return self._chat_executor
    @property
    def source_exec(self) -> Callable[[Path, dict[str, Any]], dict[str, Any]] | None:
        return self._source_executor
    @property
    def write_lock(self) -> Lock:
        return self._write_lock
    def service(self):
        self.require_project()
        if self._novel_service is None:
            self._novel_service = self._build_novel_service()
        return self._novel_service

    def _build_novel_service(self):
        return NovelApplicationService(
            self.project_root, writer_executor=self._writer_executor,
            review_executor=self._review_executor,
            source_executor=self._source_executor, task_lock=self._write_lock)

    # ── Workspace ──────────────────────────────────────────────

    def workspace(self) -> dict[str, Any]:
        if not self.initialized:
            return self._empty_workspace()
        self.config = self._load_config()
        return {
            "version": __version__, "initialized": True,
            "snapshot": self.service().workspace_snapshot(),
            "documents": self._document_groups(
                list_chapters(self.project_root, self.novel_id)),
            "model": self._model_info(),
            "operations": self.operation_status(),
        }

    def _empty_workspace(self) -> dict[str, Any]:
        return {
            "version": __version__, "initialized": False,
            "snapshot": dict(_EMPTY_SNAPSHOT),
            "documents": {"story": [], "characters": [], "world": [], "chapters": []},
            "model": self._model_info(),
            "operations": {"sync": {"needs_sync": False}, "source_packs": [],
                           "diagnostics": [{"name": "项目配置", "ok": False,
                                            "detail": "尚未创建"}]},
        }

    def _model_info(self) -> dict[str, Any]:
        return {"configured": bool(os.environ.get("LLM_API_KEY", "").strip()),
                "name": os.environ.get("LLM_MODEL", "").strip() or "未配置"}

    def operation_status(self) -> dict[str, Any]:
        sources_root = self.novel_root / "data" / "sources"
        source_packs: list[dict[str, Any]] = []
        if sources_root.exists():
            for path in sorted(sources_root.iterdir()):
                if not path.is_dir():
                    continue
                source_packs.append({"source_id": path.name,
                    "review_ready": (path / "source.md").exists(),
                    "style_ready": (path / "style").is_dir(),
                    "setting_ready": (path / "setting_profile.md").exists()})
        sync = self.service().sync_status()
        llm_ok = bool(os.environ.get("LLM_API_KEY", "").strip())
        llm_name = os.environ.get("LLM_MODEL", "").strip() or "未配置"
        needs_sync = bool(sync.get("needs_sync"))
        return {"sync": sync, "source_packs": source_packs, "diagnostics": [
            {"name": "项目配置", "ok": self.config_path.is_file() and bool(self.novel_id),
             "detail": self.novel_id},
            {"name": "模型连接", "ok": llm_ok, "detail": llm_name},
            {"name": "源文件同步", "ok": not needs_sync,
             "detail": "待同步" if needs_sync else "已同步"},
            {"name": "作品写入", "ok": os.access(self.novel_root, os.W_OK),
             "detail": "可写" if os.access(self.novel_root, os.W_OK) else "只读"}]}

    # ── Project lifecycle ──────────────────────────────────────

    def require_project(self) -> None:
        if not self.initialized:
            raise StudioError("请先创建小说项目", HTTPStatus.PRECONDITION_REQUIRED)

    def initialize_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.initialized:
            raise StudioError("当前目录已经是小说项目", HTTPStatus.CONFLICT)
        novel_id = str(payload.get("novel_id") or "").strip()
        title = str(payload.get("title") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,63}", novel_id):
            raise StudioError("小说 ID 需为 2-64 位字母、数字、横线或下划线")
        if not title or len(title) > 120:
            raise StudioError("书名不能为空且不能超过 120 字")
        try:
            NovelApplicationService.initialize(self.project_root, novel_id, title)
        except NovelServiceError as exc:
            raise self._translate_service_error(exc) from exc
        self.config = self._load_config()
        self.novel_id = novel_id
        self.novel_root = novel_root(self.project_root, novel_id).resolve()
        self.initialized = True
        self._novel_service = self._build_novel_service()
        return self.workspace()

    def configure_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        provider = str(payload.get("provider") or "openai").strip().lower()
        model = str(payload.get("model") or "").strip()
        base_url = str(payload.get("base_url") or "").strip()
        api_format = str(payload.get("api_format") or "chat").strip().lower()
        api_key = str(payload.get("api_key") or "").strip()
        if provider not in {"openai", "anthropic", "custom"}:
            raise StudioError("模型提供方无效")
        if api_format not in {"chat", "responses"}:
            raise StudioError("API 格式无效")
        if not model or len(model) > 120:
            raise StudioError("模型名称不能为空且不能超过 120 字")
        if base_url:
            parsed = urlparse(base_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise StudioError("Base URL 必须是有效的 HTTP(S) 地址")
        if not api_key and not os.environ.get("LLM_API_KEY", "").strip():
            raise StudioError("API Key 不能为空")
        for key, val in [("LLM_PROVIDER", provider), ("LLM_MODEL", model),
                         ("LLM_API_FORMAT", api_format)]:
            os.environ[key] = val
        if base_url:
            os.environ["LLM_BASE_URL"] = base_url
        if api_key:
            os.environ["LLM_API_KEY"] = api_key
        return self.workspace()

    def update_focus(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            self.service().update_focus(
                goal=str(payload.get("goal") or ""),
                must_keep=_string_list(payload.get("must_keep")),
                must_avoid=_string_list(payload.get("must_avoid")),
                notes=_string_list(payload.get("notes")))
        except NovelServiceError as exc:
            raise self._translate_service_error(exc) from exc
        return self.workspace()

    # ── Document I/O ───────────────────────────────────────────

    def read_document(self, relative_path: str) -> dict[str, Any]:
        path = self._resolve_document(relative_path, write=False)
        if not path.is_file():
            raise StudioError("文档不存在", HTTPStatus.NOT_FOUND)
        if path.stat().st_size > MAX_DOCUMENT_BYTES:
            raise StudioError("文档超过 2 MB，Studio 不直接打开",
                              HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        return {"path": self._relative(path), "title": _document_title(path),
                "content": path.read_text(encoding="utf-8"),
                "version": str(path.stat().st_mtime_ns)}

    def write_document(self, relative_path: str, content: str,
                       version: str | int | None, *, force: bool = False) -> dict[str, Any]:
        path = self._resolve_document(relative_path, write=True)
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_DOCUMENT_BYTES:
            raise StudioError("文档超过 2 MB，已拒绝保存",
                              HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        if "\x00" in content:
            raise StudioError("文档包含无效字符")
        with self._write_lock:
            if path.exists() and version is not None and not force:
                if str(path.stat().st_mtime_ns) != str(version):
                    raise StudioError("文档已在其他位置修改，请重新载入",
                                      HTTPStatus.CONFLICT)
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
                handle.write(content)
                temp_path = Path(handle.name)
            temp_path.replace(path)
        return self.read_document(self._relative(path))

    def create_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        kind = str(payload.get("kind") or "").strip()
        name = str(payload.get("name") or "").strip()
        description = str(payload.get("description") or "").strip()
        with self._write_lock:
            try:
                path = self.service().create_document(kind=kind, name=name,
                                                      description=description)
            except NovelServiceError as exc:
                raise self._translate_service_error(exc) from exc
        return {"document": self.read_document(self._relative(path)),
                "workspace": self.workspace()}

    def context_preview(self, chapter_id: str) -> dict[str, Any]:
        try:
            result = self.service().context_preview(chapter_id)
        except NovelServiceError as exc:
            raise self._translate_service_error(exc) from exc
        result.pop("packet", None)
        return result

    def continuity(self) -> dict[str, Any]:
        try:
            return self.service().continuity()
        except NovelServiceError as exc:
            raise self._translate_service_error(exc) from exc

    # ── 大型操作（委托至 handlers._ops 避免循环导入） ──────────

    def manage_foreshadowing(self, payload: dict[str, Any]) -> dict[str, Any]:
        from .handlers import _ops_manage_foreshadowing
        return _ops_manage_foreshadowing(self, payload)

    def write_next_chapter(self, payload: dict[str, Any]) -> dict[str, Any]:
        from .handlers import _ops_write_next_chapter
        return _ops_write_next_chapter(self, payload)

    def review_chapter(self, payload: dict[str, Any]) -> dict[str, Any]:
        from .handlers import _ops_review_chapter
        return _ops_review_chapter(self, payload)

    def sync_project(self) -> dict[str, Any]:
        from .handlers import _ops_sync_project
        return _ops_sync_project(self)

    def import_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        from .handlers import _ops_import_text
        return _ops_import_text(self, payload)

    def chat_turn(self, payload: dict[str, Any]) -> dict[str, Any]:
        from .handlers import _ops_chat_turn
        return _ops_chat_turn(self, payload)

    def source_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        from .handlers import _ops_source_action
        return _ops_source_action(self, payload)

    def export_download(self, format_name: str) -> tuple[str, bytes, str]:
        from .handlers import _ops_export_download
        return _ops_export_download(self, format_name)

    # ── 内部辅助 ───────────────────────────────────────────────

    def _load_config(self) -> dict[str, Any]:
        try:
            data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            raise StudioError(f"项目配置无法读取: {exc}") from exc
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _translate_service_error(exc: NovelServiceError) -> StudioError:
        status = {"PROJECT_BUSY": HTTPStatus.CONFLICT,
                  "CONFLICT": HTTPStatus.CONFLICT,
                  "NOT_FOUND": HTTPStatus.NOT_FOUND,
                  "INVALID_PROJECT": HTTPStatus.PRECONDITION_FAILED,
                  "INVALID_INPUT": HTTPStatus.BAD_REQUEST}.get(
                      exc.code, HTTPStatus.BAD_GATEWAY)
        return StudioError(str(exc), status)

    def _document_groups(self, chapters: list[Any]) -> dict[str, list[dict[str, Any]]]:
        src = self.novel_root / "src"
        groups = {
            "story": _collect_documents(src / "story", self.novel_root, recursive=False),
            "characters": _collect_documents(src / "characters", self.novel_root, recursive=False),
            "world": _collect_documents(src / "world", self.novel_root, recursive=True),
            "chapters": [self._chapter_summary(item) for item in chapters]}
        outline = src / "outline.md"
        if outline.exists():
            groups["story"].insert(0, _document_summary(outline, self.novel_root))
        return groups

    def _chapter_summary(self, item: Any) -> dict[str, Any]:
        review = self._load_review_result(item.chapter_id)
        subtitle = f"{item.chapter_id} · {item.writing_units:,} 字"
        if review:
            subtitle += f" · {float(review.get('score', 0)):.0f} 分"
        return {"path": self._relative(item.path), "title": item.title,
                "subtitle": subtitle, "review": review}

    def _load_review_result(self, chapter_id: str) -> dict[str, Any] | None:
        from tools.review_store import ReviewStore
        data = ReviewStore(self.project_root, self.novel_id).load(chapter_id)
        if data is None:
            return None
        return {"score": float(data.get("score") or 0),
                "passed": bool(data.get("passed")),
                "issues": int(data.get("issues") or 0),
                "reviewed_at": str(data.get("reviewed_at") or "")}

    def _resolve_document(self, relative_path: str, *, write: bool) -> Path:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise StudioError("缺少文档路径")
        candidate = (self.novel_root / relative_path).resolve()
        allowed_roots = [(self.novel_root / "src").resolve(),
                         (self.novel_root / "data" / "manuscript").resolve()]
        if not any(candidate == root or root in candidate.parents for root in allowed_roots):
            raise StudioError("文档路径不在 Studio 可访问范围", HTTPStatus.FORBIDDEN)
        if candidate.suffix.lower() != ".md":
            raise StudioError("Studio 仅编辑 Markdown 文档")
        if write and candidate.is_symlink():
            raise StudioError("不允许写入符号链接", HTTPStatus.FORBIDDEN)
        return candidate

    def _relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.novel_root).as_posix()


def _document_title(path: Path) -> str:
    try:
        head = path.read_text(encoding="utf-8")[:2000]
    except OSError:
        return path.stem
    match = re.search(r"^#\s+(.+?)\s*$", head, re.MULTILINE)
    return match.group(1).strip() if match else path.stem.replace("_", " ")


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        values = value.splitlines()
    elif isinstance(value, list):
        values = value
    else:
        return []
    return [str(item).strip().removeprefix("- ") for item in values if str(item).strip()]


def _collect_documents(root: Path, novel_root: Path, *, recursive: bool) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    iterator = root.rglob("*.md") if recursive else root.glob("*.md")
    return [_document_summary(path, novel_root) for path in sorted(iterator) if path.is_file()]


def _document_summary(path: Path, novel_root: Path) -> dict[str, Any]:
    return {"path": path.resolve().relative_to(novel_root).as_posix(),
            "title": _document_title(path),
            "subtitle": str(path.relative_to(novel_root).parent)}
