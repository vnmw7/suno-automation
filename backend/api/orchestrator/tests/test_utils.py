"""
System: Suno Automation
Module: Orchestrator CDN Tests
File URL: backend/api/orchestrator/tests/test_utils.py
Purpose: Validate CDN download helper and hybrid workflow behaviour.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

# Setup path for local imports (required before module imports)  # noqa: E402
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # noqa: E402
BACKEND_ROOT = PROJECT_ROOT / 'backend'  # noqa: E402
for sys_path in (PROJECT_ROOT, BACKEND_ROOT):  # noqa: E402
    sys_path_str = str(sys_path)  # noqa: E402
    if sys_path_str not in sys.path:  # noqa: E402
        sys.path.append(sys_path_str)  # noqa: E402

from api.orchestrator.utils import (  # noqa: E402
    downloadSongsFromCdn,
    download_both_songs,
)


@pytest.mark.asyncio
async def test_downloadSongsFromCdn_success(tmp_path: Path) -> None:
    async def handler(request: web.Request) -> web.Response:
        return web.Response(body=b"ID3-test-audio")

    app = web.Application()
    app.router.add_get("/song-success.mp3", handler)

    async with TestServer(app) as server:
        base_url = str(server.make_url(""))[:-1]
        result = await downloadSongsFromCdn(
            song_id="song-success",
            download_dir=str(tmp_path),
            base_url=base_url,
        )

    assert result["success"] is True
    downloaded_file = Path(result["file_path"])
    assert downloaded_file.exists()
    assert downloaded_file.read_bytes().startswith(b"ID3-test-audio")


@pytest.mark.asyncio
async def test_downloadSongsFromCdn_not_found(tmp_path: Path) -> None:
    app = web.Application()

    async with TestServer(app) as server:
        base_url = str(server.make_url(""))[:-1]
        result = await downloadSongsFromCdn(
            song_id="missing",
            download_dir=str(tmp_path),
            base_url=base_url,
        )

    assert result["success"] is False
    assert "HTTP 404" in result["error"]


@pytest.mark.asyncio
async def test_downloadSongsFromCdn_server_error(tmp_path: Path) -> None:
    async def handler(request: web.Request) -> web.Response:
        return web.Response(status=500, text="fail")

    app = web.Application()
    app.router.add_get("/song-error.mp3", handler)

    async with TestServer(app) as server:
        base_url = str(server.make_url(""))[:-1]
        result = await downloadSongsFromCdn(
            song_id="song-error",
            download_dir=str(tmp_path),
            base_url=base_url,
        )

    assert result["success"] is False
    assert "HTTP 500" in result["error"]


@pytest.mark.asyncio
async def test_downloadSongsFromCdn_timeout(tmp_path: Path) -> None:
    async def handler(request: web.Request) -> web.Response:
        await asyncio.sleep(2)
        return web.Response(body=b"ID3-late-audio")

    app = web.Application()
    app.router.add_get("/song-slow.mp3", handler)

    async with TestServer(app) as server:
        base_url = str(server.make_url(""))[:-1]
        result = await downloadSongsFromCdn(
            song_id="song-slow",
            download_dir=str(tmp_path),
            base_url=base_url,
            timeout_seconds=1,
        )

    assert result["success"] is False
    assert "timed out" in result["error"]
    assert not any(tmp_path.iterdir())


@pytest.mark.asyncio
async def test_downloadSongsFromCdn_invalid_mp3(tmp_path: Path) -> None:
    async def handler(request: web.Request) -> web.Response:
        return web.Response(body=b"NOT-MP3")

    app = web.Application()
    app.router.add_get("/song-bad.mp3", handler)

    async with TestServer(app) as server:
        base_url = str(server.make_url(""))[:-1]
        result = await downloadSongsFromCdn(
            song_id="song-bad",
            download_dir=str(tmp_path),
            base_url=base_url,
        )

    assert result["success"] is False
    assert "Invalid MP3 header" in result["error"]
    assert not any(tmp_path.iterdir())


@pytest.mark.asyncio
async def test_download_both_songs_hybrid_flow(monkeypatch, tmp_path: Path) -> None:
    async def good_handler(request: web.Request) -> web.Response:
        return web.Response(body=b"ID3-good-audio")

    async def bad_handler(request: web.Request) -> web.Response:
        return web.Response(status=500)

    app = web.Application()
    app.router.add_get("/song-good.mp3", good_handler)
    app.router.add_get("/song-bad.mp3", bad_handler)

    async with TestServer(app) as server:
        base_url = str(server.make_url(""))[:-1]

        monkeypatch.setattr(
            "api.orchestrator.utils.CDN_BASE_URL",
            base_url,
        )

        async def fake_download_song_v2(
            strTitle: str,
            intIndex: int,
            download_path: str,
            song_id: str = None,
        ) -> Dict[str, Any]:
            fallback_path = Path(download_path) / f"fallback_{intIndex}.mp3"
            fallback_path.write_bytes(b"ID3-fallback-audio")
            return {
                "success": True,
                "file_path": str(fallback_path),
                "song_id": song_id or f"index_{intIndex}",
            }

        monkeypatch.setattr(
            "utils.download_song_v2.download_song_v2",
            fake_download_song_v2,
        )

        result = await download_both_songs(
            title="Hybrid Test",
            temp_dir=str(tmp_path),
            song_ids=["song-good", "song-bad"],
        )

    assert result["success"] is True
    assert len(result["downloads"]) == 2
    file_paths = {entry["song_id"]: Path(entry["file_path"]) for entry in result["downloads"]}
    assert "song-good" in file_paths and file_paths["song-good"].exists()
    assert "song-bad" in file_paths and file_paths["song-bad"].exists()
