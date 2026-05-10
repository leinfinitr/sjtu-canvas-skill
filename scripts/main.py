import os
import sys
import json
import re
import asyncclick
from pathlib import Path
from dotenv import load_dotenv, set_key
from rich.console import Console
from rich.table import Table
from .client import CanvasClient
from .cookie_utils import sanitize_filename
from .materials import extract_material_text, find_material_file
from .review_builder import build_study_note
from .video_client import SJTUVideoClient
from .workspace import get_workspace_cookie, load_workspace_env, resolve_workspace

# Load environment variables from project .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)

# Rich console for pretty printing
console = Console()


class FullCommandHelpGroup(asyncclick.Group):
    """Render complete command descriptions in top-level help output."""

    def format_commands(self, ctx, formatter):
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue
            help_text = cmd.short_help or cmd.help or ""
            commands.append((subcommand, help_text.strip()))

        if commands:
            with formatter.section("Commands"):
                formatter.write_dl(commands)


def _get_oc_cookie(workspace: str | Path | None = None) -> str:
    if workspace is not None:
        return get_workspace_cookie(workspace, fallback=os.environ.get("OC_COOKIE"))
    cookie = (os.environ.get("OC_COOKIE") or "").strip()
    if not cookie:
        raise RuntimeError(
            "OC_COOKIE is required for classroom video features. Put it in workspace .env or export OC_COOKIE."
        )
    return cookie


def derive_course_lesson_names(video_name: str) -> tuple[str, str]:
    """Derive human-friendly output path components from SJTU video title."""
    title = video_name.strip() or "未命名课程视频"
    lesson_match = re.search(r"[（(](第\s*\d+\s*讲)[）)]", title) or re.search(r"(第\s*\d+\s*讲)", title)
    lesson = re.sub(r"\s+", "", lesson_match.group(1)) if lesson_match else title
    course = title
    if lesson_match:
        course = title[: lesson_match.start()]
    course = re.sub(r"[（(][^）)]*[）)]\s*$", "", course).strip()
    course = course.rstrip("（(").strip()
    return course or "未命名课程", lesson or "未命名节次"


def write_transcript_files(
    *,
    out_dir: str | Path,
    course_name: str,
    lesson_name: str,
    course_id: int,
    video_id: str,
    cour_id: int | None,
    text: str,
    subtitle_items,
    metadata: dict,
) -> dict[str, str]:
    base = Path(out_dir) / sanitize_filename(course_name) / sanitize_filename(lesson_name)
    base.mkdir(parents=True, exist_ok=True)
    paths = {
        "txt": base / "transcript.txt",
        "metadata": base / "metadata.json",
    }
    paths["txt"].write_text(text, encoding="utf-8")
    paths["metadata"].write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


# Backwards-compatible alias for older tests/imports. It now writes only transcript artifacts.
def write_video_review_files(
    *,
    out_dir: str | Path,
    course_name: str,
    video_name: str,
    course_id: int,
    video_id: str,
    cour_id: int | None,
    srt: str = "",
    text: str,
    subtitle_items,
    metadata: dict,
) -> dict[str, str]:
    return write_transcript_files(
        out_dir=out_dir,
        course_name=course_name,
        lesson_name=video_name,
        course_id=course_id,
        video_id=video_id,
        cour_id=cour_id,
        text=text,
        subtitle_items=subtitle_items,
        metadata=metadata,
    )


async def _prompt_and_maybe_save_token(json_output: bool) -> str:
    """Prompt for TOKEN and optionally persist it to .env for future runs."""
    if not json_output:
        console.print(
            "[yellow]TOKEN not found in CLI args, environment, or .env.[/yellow]"
        )

    token = await asyncclick.prompt(
        "Please enter your Canvas API token", hide_input=True
    )
    token = token.strip()
    if not token:
        raise asyncclick.Abort()

    save_token = asyncclick.confirm(
        "Save TOKEN to project .env for future runs?", default=True
    )
    if save_token:
        set_key(str(ENV_FILE), "TOKEN", token, quote_mode="never")
        if not json_output:
            console.print(f"[green]Saved TOKEN to {ENV_FILE}[/green]")

    os.environ["TOKEN"] = token
    return token


@asyncclick.group(cls=FullCommandHelpGroup)
@asyncclick.option(
    "--token",
    envvar="TOKEN",
    help="Canvas API token. Can also be set with TOKEN environment variable.",
)
@asyncclick.option(
    "--base-url",
    envvar="BASE_URL",
    default="https://oc.sjtu.edu.cn",
    help="Canvas base URL. Can also be set with BASE_URL environment variable.",
)
@asyncclick.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output raw JSON instead of formatted tables.",
)
@asyncclick.pass_context
async def cli(ctx, token: str, base_url: str, json_output: bool):
    """
    A CLI tool for SJTU Canvas based on the Rust implementation.
    """
    token = (token or "").strip()
    if not token:
        if sys.stdin.isatty():
            token = await _prompt_and_maybe_save_token(json_output)
        else:
            if json_output:
                print(
                    json.dumps(
                        {
                            "status": "error",
                            "message": "TOKEN missing and stdin is non-interactive.",
                        }
                    )
                )
            else:
                console.print(
                    "[bold red]Error: TOKEN missing and stdin is non-interactive.[/bold red]"
                )
            raise asyncclick.Abort()

    if not base_url or not base_url.strip():
        console.print("[bold red]Error: BASE_URL is not set or is empty.[/bold red]")
        raise asyncclick.Abort()

    client = CanvasClient(base_url=base_url, token=token)
    client.json_output = json_output
    ctx.obj = client


@cli.command("list-courses")
@asyncclick.pass_obj
async def list_courses(client: CanvasClient):
    """Lists all active courses for the current user."""
    if not client.json_output:
        console.print("[bold cyan]Fetching courses...[/bold cyan]")
    try:
        courses = await client.get_courses()
        if client.json_output:
            active_courses = []
            for course in courses:
                if course.get("enrollment_state", "active") != "active":
                    continue
                active_courses.append(
                    {
                        "id": course.get("id"),
                        "name": course.get("name", "N/A"),
                        "course_code": course.get("course_code", "N/A"),
                        "term": course.get("term", {}).get("name", "N/A"),
                        "teachers": [
                            teacher.get("display_name", "N/A")
                            for teacher in course.get("teachers", [])
                        ],
                    }
                )
            print(json.dumps(active_courses, ensure_ascii=False))
            return
        if not courses:
            console.print("[yellow]No courses found.[/yellow]")
            return

        table = Table(title="Courses")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Course Code", style="cyan")
        table.add_column("Term", style="magenta")
        table.add_column("Teacher(s)", style="yellow")

        for course in courses:
            if course.get("enrollment_state", "active") == "active":
                teachers = ", ".join(
                    [
                        teacher.get("display_name", "N/A")
                        for teacher in course.get("teachers", [])
                    ]
                )
                term = course.get("term", {}).get("name", "N/A")
                table.add_row(
                    str(course["id"]),
                    course.get("name", "N/A"),
                    course.get("course_code", "N/A"),
                    term,
                    teachers,
                )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("list-assignments")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_obj
async def list_assignments(client: CanvasClient, course_id: int):
    """Lists all assignments for a given course ID."""
    if not client.json_output:
        console.print(
            f"[bold cyan]Fetching assignments for course {course_id}...[/bold cyan]"
        )
    try:
        assignments = await client.get_assignments(course_id)
        if client.json_output:
            compact_assignments = []
            for assign in assignments:
                due_at = assign.get("due_at", "N/A")
                if due_at and due_at != "N/A":
                    due_at = due_at.replace("T", " ").replace("Z", "")
                compact_assignments.append(
                    {
                        "id": assign.get("id"),
                        "name": assign.get("name", "N/A"),
                        "due_at": due_at,
                        "points_possible": assign.get("points_possible", "N/A"),
                    }
                )
            print(json.dumps(compact_assignments, ensure_ascii=False))
            return
        if not assignments:
            console.print("[yellow]No assignments found for this course.[/yellow]")
            return
        table = Table(title=f"Assignments for Course {course_id}")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Due At", style="magenta")
        table.add_column("Points Possible", style="cyan")
        for assign in assignments:
            due_at = assign.get("due_at", "N/A")
            if due_at and due_at != "N/A":
                due_at = due_at.replace("T", " ").replace("Z", "")
            table.add_row(
                str(assign["id"]),
                assign.get("name", "N/A"),
                due_at,
                str(assign.get("points_possible", "N/A")),
            )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("submit")
@asyncclick.argument("course_id", type=int)
@asyncclick.argument("assignment_id", type=int)
@asyncclick.argument("files", type=str, nargs=-1)
@asyncclick.option("--comment", "-c", help="Add a text comment to the submission.")
@asyncclick.pass_obj
async def submit(
    client: CanvasClient,
    course_id: int,
    assignment_id: int,
    files: list[str],
    comment: str,
):
    """Submits one or more files for an assignment."""
    if not files:
        if client.json_output:
            print(
                json.dumps({"error": "You must specify at least one file to submit."})
            )
        else:
            console.print(
                "[bold red]Error: You must specify at least one file to submit.[/bold red]"
            )
        return
    try:
        await client.submit_assignment(course_id, assignment_id, list(files), comment)
        if client.json_output:
            print(
                json.dumps(
                    {
                        "status": "success",
                        "message": "Assignment submitted successfully",
                    }
                )
            )
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(
                f"[bold red]An error occurred during submission: {e}[/bold red]"
            )
    finally:
        await client.close()


@cli.command("get-me")
@asyncclick.pass_obj
async def get_me(client: CanvasClient):
    """Gets the profile of the current user."""
    if not client.json_output:
        console.print("[bold cyan]Fetching user profile...[/bold cyan]")
    try:
        me = await client.get_me()
        if client.json_output:
            print(
                json.dumps(
                    {
                        "id": me.get("id"),
                        "name": me.get("name"),
                        "primary_email": me.get("primary_email", "N/A"),
                        "locale": me.get("locale", "N/A"),
                        "time_zone": me.get("time_zone", "N/A"),
                    },
                    ensure_ascii=False,
                )
            )
            return
        table = Table(title="My Profile")
        table.add_column("Attribute", style="bold green")
        table.add_column("Value", style="cyan")
        table.add_row("ID", str(me.get("id")))
        table.add_row("Name", me.get("name"))
        table.add_row("Primary Email", me.get("primary_email", "N/A"))
        table.add_row("Locale", me.get("locale", "N/A"))
        table.add_row("Time Zone", me.get("time_zone", "N/A"))
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("list-files")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_obj
async def list_files(client: CanvasClient, course_id: int):
    """Lists all files for a given course ID."""
    if not client.json_output:
        console.print(
            f"[bold cyan]Fetching files for course {course_id}...[/bold cyan]"
        )
    try:
        files = await client.get_files(course_id)
        if client.json_output:
            compact_files = []
            for f in files:
                compact_files.append(
                    {
                        "id": f.get("id"),
                        "name": f.get("display_name", "N/A"),
                        "size_kb": round(f.get("size", 0) / 1024, 2),
                        "content_type": f.get("content-type", "N/A"),
                        "url": f.get("url", "N/A"),
                    }
                )
            print(json.dumps(compact_files, ensure_ascii=False))
            return
        if not files:
            console.print("[yellow]No files found for this course.[/yellow]")
            return
        table = Table(title=f"Files for Course {course_id}")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Size (KB)", style="cyan")
        table.add_column("Content Type", style="magenta")
        table.add_column("URL", style="blue", overflow="fold")
        for f in files:
            size_kb = f.get("size", 0) / 1024
            table.add_row(
                str(f["id"]),
                f.get("display_name", "N/A"),
                f"{size_kb:.2f}",
                f.get("content-type", "N/A"),
                f.get("url", "N/A"),
            )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("list-folders")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_obj
async def list_folders(client: CanvasClient, course_id: int):
    """Lists all folders for a given course ID."""
    if not client.json_output:
        console.print(
            f"[bold cyan]Fetching folders for course {course_id}...[/bold cyan]"
        )
    try:
        folders = await client.get_folders(course_id)
        if client.json_output:
            compact_folders = []
            for folder in folders:
                compact_folders.append(
                    {
                        "id": folder.get("id"),
                        "name": folder.get("name", "N/A"),
                        "files_count": folder.get("files_count", "N/A"),
                        "full_name": folder.get("full_name", "N/A"),
                    }
                )
            print(json.dumps(compact_folders, ensure_ascii=False))
            return
        if not folders:
            console.print("[yellow]No folders found for this course.[/yellow]")
            return
        table = Table(title=f"Folders for Course {course_id}")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Files Count", style="cyan")
        table.add_column("Full Name", style="magenta")
        for folder in folders:
            table.add_row(
                str(folder["id"]),
                folder.get("name", "N/A"),
                str(folder.get("files_count", "N/A")),
                folder.get("full_name", "N/A"),
            )
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("download-file")
@asyncclick.argument("url")
@asyncclick.option("--path", default=".", help="The directory to save the file in.")
@asyncclick.pass_obj
async def download_file(client: CanvasClient, url: str, path: str):
    """Downloads a file from a specific URL."""
    try:
        if not client.json_output:
            console.print(f"[bold cyan]Downloading from {url}...[/bold cyan]")
        result = await client.download_file(url, path)
        if client.json_output:
            print(
                json.dumps(
                    {
                        "status": "success",
                        "filename": result["filename"],
                        "path": os.path.abspath(result["path"]),
                        "size": result["size"],
                    }
                )
            )
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(
                f"[bold red]An error occurred during download: {e}[/bold red]"
            )
    finally:
        await client.close()


@cli.command("list-videos")
@asyncclick.argument("course_id", type=int)
@asyncclick.pass_obj
async def list_videos(client: CanvasClient, course_id: int):
    """Lists classroom videos for a given course ID. Requires OC_COOKIE."""
    try:
        video_client = SJTUVideoClient(_get_oc_cookie(), base_url=client.base_url)
        videos = video_client.list_videos(course_id)
        rows = [
            {
                "video_id": video.video_id,
                "video_name": video.video_name,
                "course_begin_time": video.course_begin_time,
            }
            for video in videos
        ]
        if client.json_output:
            print(json.dumps(rows, ensure_ascii=False))
            return
        table = Table(title=f"Classroom Videos for Course {course_id}")
        table.add_column("Video ID", style="dim")
        table.add_column("Name", style="bold green")
        table.add_column("Begin Time", style="cyan")
        for row in rows:
            table.add_row(row["video_id"], row["video_name"], str(row["course_begin_time"] or "N/A"))
        console.print(table)
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("download-subtitle")
@asyncclick.argument("course_id", type=int)
@asyncclick.option("--video-id", required=True, help="Video ID from list-videos.")
@asyncclick.option("--out", "out_dir", default="./reviews", help="Output directory.")
@asyncclick.pass_obj
async def download_subtitle(client: CanvasClient, course_id: int, video_id: str, out_dir: str):
    """Downloads platform subtitles as SRT/TXT for a classroom video."""
    try:
        video_client = SJTUVideoClient(_get_oc_cookie(), base_url=client.base_url)
        video_client.launch_video_platform(course_id)
        info = video_client.get_video_info(video_id)
        items = video_client.get_subtitle(info.cour_id)
        if not items:
            raise RuntimeError("No platform subtitle found for this video")
        text = video_client.subtitle_to_text(items)
        videos = video_client.list_videos(course_id)
        selected_video = next((video for video in videos if video.video_id == video_id), None)
        video_name = selected_video.video_name if selected_video else f"video_{video_id}"
        course_name, lesson_name = derive_course_lesson_names(video_name)
        files = write_transcript_files(
            out_dir=out_dir,
            course_name=course_name,
            lesson_name=lesson_name,
            course_id=course_id,
            video_id=video_id,
            cour_id=info.cour_id,
            text=text,
            subtitle_items=items,
            metadata={
                "course_id": course_id,
                "video_id": video_id,
                "video_name": video_name,
                "course_name": course_name,
                "lesson_name": lesson_name,
                "video_info": info.raw,
            },
        )
        if client.json_output:
            print(json.dumps({"status": "success", "files": files}, ensure_ascii=False))
        else:
            console.print(f"[green]Saved transcript to {files['txt']}[/green]")
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


@cli.command("review-video")
@asyncclick.argument("course_id", type=int)
@asyncclick.option("--video-id", required=True, help="Video ID from list-videos.")
@asyncclick.option("--out", "out_dir", default="./reviews", help="Output directory.")
@asyncclick.pass_obj
async def review_video(client: CanvasClient, course_id: int, video_id: str, out_dir: str):
    """Creates a local Markdown review note from platform subtitles."""
    await download_subtitle.callback(client, course_id, video_id, out_dir)

@cli.command("study-note")
@asyncclick.argument("course_id", type=int)
@asyncclick.option("--video-id", required=True, help="Video ID from list-videos.")
@asyncclick.option("--material", "material_query", required=True, help="PPT/PDF filename or keyword for this lesson.")
@asyncclick.option("--workspace", "workspace_dir", default=".", help="Course workspace containing .env and materials.")
@asyncclick.option("--out", "out_dir", default=None, help="Output directory; defaults to workspace/reviews.")
@asyncclick.pass_obj
async def study_note(
    client: CanvasClient,
    course_id: int,
    video_id: str,
    material_query: str,
    workspace_dir: str,
    out_dir: str | None,
):
    """Builds an agent-ready study note from one course material and one video transcript."""
    try:
        workspace = resolve_workspace(workspace_dir)
        output_root = Path(out_dir).expanduser().resolve() if out_dir else workspace / "reviews"
        video_client = SJTUVideoClient(_get_oc_cookie(workspace), base_url=client.base_url)
        video_client.launch_video_platform(course_id)
        info = video_client.get_video_info(video_id)
        items = video_client.get_subtitle(info.cour_id)
        if not items:
            raise RuntimeError("No platform subtitle found for this video")
        text = video_client.subtitle_to_text(items)
        videos = video_client.list_videos(course_id)
        selected_video = next((video for video in videos if video.video_id == video_id), None)
        video_name = selected_video.video_name if selected_video else f"video_{video_id}"
        course_name, lesson_name = derive_course_lesson_names(video_name)
        transcript_files = write_transcript_files(
            out_dir=output_root,
            course_name=course_name,
            lesson_name=lesson_name,
            course_id=course_id,
            video_id=video_id,
            cour_id=info.cour_id,
            text=text,
            subtitle_items=items,
            metadata={
                "course_id": course_id,
                "video_id": video_id,
                "video_name": video_name,
                "course_name": course_name,
                "lesson_name": lesson_name,
                "video_info": info.raw,
            },
        )
        material_path = find_material_file(workspace, material_query)
        material = extract_material_text(material_path)
        note = build_study_note(
            course_name=course_name,
            lesson_name=lesson_name,
            material_name=str(material.path.relative_to(workspace)) if material.path.is_relative_to(workspace) else material.path.name,
            material_text=material.text,
            transcript_text=text,
        )
        note_path = Path(transcript_files["txt"]).parent / "study_note.md"
        note_path.write_text(note, encoding="utf-8")
        files = {**transcript_files, "study_note": str(note_path), "material": str(material.path)}
        if client.json_output:
            print(json.dumps({"status": "success", "files": files}, ensure_ascii=False))
        else:
            console.print(f"[green]Saved study note to {note_path}[/green]")
    except Exception as e:
        if client.json_output:
            print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        else:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    finally:
        await client.close()


def main():
    cli(_anyio_backend="asyncio")


if __name__ == "__main__":
    main()
