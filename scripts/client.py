import os
import sys
import socket
import asyncio
import aiohttp
import urllib.parse
from rich.progress import Progress
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List, Optional
from yarl import URL


class _SystemResolver(aiohttp.abc.AbstractResolver):
    """Resolver that uses the OS resolver instead of aiodns.

    On this Windows/MSYS setup, aiohttp's aiodns resolver can time out against
    the IPv6 DNS server while socket.getaddrinfo and curl work. This keeps the
    CLI aligned with the system resolver.
    """

    async def resolve(self, host, port=0, family=socket.AF_INET):
        infos = await asyncio.to_thread(
            socket.getaddrinfo, host, port, family, socket.SOCK_STREAM
        )
        return [
            {
                "hostname": host,
                "host": address[0],
                "port": address[1],
                "family": addr_family,
                "proto": proto,
                "flags": 0,
            }
            for addr_family, _socktype, proto, _canonname, address in infos
        ]

    async def close(self):
        return None


def _connector_kwargs() -> Dict[str, Any]:
    if sys.platform.startswith("win"):
        return {"resolver": _SystemResolver(), "family": socket.AF_INET}
    return {}


class CanvasClient:
    """A client for interacting with the Canvas API."""

    def __init__(self, base_url: str, token: str):
        if not base_url or not token:
            raise ValueError("BASE_URL and TOKEN must be set")
        self.base_url = base_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.client: Optional[aiohttp.ClientSession] = None
        self.json_output = False

    async def get_client(self) -> aiohttp.ClientSession:
        """Lazily create the HTTP session inside a running async context."""
        if self.client is None or self.client.closed:
            self.client = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30.0),
                connector=aiohttp.TCPConnector(**_connector_kwargs()),
            )
        return self.client

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> aiohttp.ClientResponse:
        """Make a GET request."""
        url = f"{self.base_url}{path}"
        client = await self.get_client()
        try:
            res = await client.get(url, params=params, **kwargs)
            res.raise_for_status()
            return res
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error occurred: {e.status} {e.message}")
            raise

    async def _post(
        self,
        url: str,  # Note: this now takes a full URL
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> aiohttp.ClientResponse:
        """Make a POST request."""
        client = await self.get_client()
        try:
            # Use the provided URL directly
            res = await client.post(
                url, data=data, json=json, headers=headers, **kwargs
            )
            res.raise_for_status()
            return res
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error occurred: {e.status} {e.message} for URL {url}")
            raise

    async def _put(
        self, path: str, data: Optional[Dict[str, Any]] = None
    ) -> aiohttp.ClientResponse:
        """Make a PUT request."""
        url = f"{self.base_url}{path}"
        client = await self.get_client()
        try:
            res = await client.put(url, data=data)
            res.raise_for_status()
            return res
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error occurred: {e.status} {e.message}")
            raise

    async def _delete(self, path: str) -> aiohttp.ClientResponse:
        """Make a DELETE request."""
        url = f"{self.base_url}{path}"
        client = await self.get_client()
        try:
            res = await client.delete(url)
            res.raise_for_status()
            return res
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error occurred: {e.status} {e.message}")
            raise

    async def list_items(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """List all items from a paginated API endpoint."""
        url = f"{self.base_url}{path}"
        client = await self.get_client()
        items = []
        if params is None:
            params = {}
        params.setdefault("per_page", 100)

        while url:
            try:
                async with client.get(url, params=params) as res:
                    res.raise_for_status()
                    data = await res.json()
                    if isinstance(data, list):
                        items.extend(data)

                    # Canvas API pagination
                    if "next" in res.links:
                        url = res.links["next"]["url"]
                        params = None  # params are already in the next url
                    else:
                        url = None
            except aiohttp.ClientResponseError as e:
                print(f"HTTP error occurred: {e.status} {e.message}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
        return items

    async def get_courses(self) -> List[Dict[str, Any]]:
        """Fetch all active courses for the current user."""
        return await self.list_items(
            "/api/v1/courses", params={"include[]": ["term", "teachers"]}
        )

    async def get_assignments(self, course_id: int) -> List[Dict[str, Any]]:
        """Fetch all assignments for a given course ID."""
        return await self.list_items(f"/api/v1/courses/{course_id}/assignments")

    async def get_me(self) -> Dict[str, Any]:
        """Fetch the profile of the current user."""
        res = await self._get("/api/v1/users/self")
        return await res.json()

    async def get_files(self, course_id: int) -> List[Dict[str, Any]]:
        """Fetch all files for a given course ID."""
        return await self.list_items(f"/api/v1/courses/{course_id}/files")

    async def get_folders(self, course_id: int) -> List[Dict[str, Any]]:
        """Fetch all folders for a given course ID."""
        return await self.list_items(f"/api/v1/courses/{course_id}/folders")

    async def submit_assignment(
        self,
        course_id: int,
        assignment_id: int,
        file_paths: List[str],
        comment: Optional[str] = None,
    ):
        """Submits files for an assignment."""
        client = await self.get_client()
        uploaded_file_ids = []

        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            if not self.json_output:
                print(f"Step 1: Preparing to upload '{file_name}'...")
            prep_url = f"{self.base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/self/files"
            prep_payload = {"name": file_name, "size": file_size}
            async with client.post(prep_url, data=prep_payload) as prep_response:
                prep_response.raise_for_status()
                prep_data = await prep_response.json()

            if "upload_url" not in prep_data:
                raise Exception(f"Failed to get upload URL. Response: {prep_data}")

            upload_url = prep_data["upload_url"]
            upload_params = prep_data["upload_params"]

            if not self.json_output:
                print(f"Step 2: Uploading '{file_name}'...")
            form_data = aiohttp.FormData()
            for key, value in upload_params.items():
                form_data.add_field(key, str(value))

            with open(file_path, "rb") as f:
                form_data.add_field("file", f, filename=file_name)
                async with aiohttp.ClientSession() as upload_session:
                    async with upload_session.post(
                        upload_url, data=form_data, allow_redirects=False
                    ) as upload_response:
                        if upload_response.status >= 400:
                            body = await upload_response.text()
                            raise Exception(
                                f"File upload failed. Status: {upload_response.status}. Body: {body}"
                            )
                        location_url = upload_response.headers.get("Location")
                        if not location_url:
                            raise Exception(
                                f"Upload confirmation URL not found in redirect. Status: {upload_response.status}"
                            )

            async with client.get(location_url) as confirm_response:
                confirm_response.raise_for_status()
                final_file_data = await confirm_response.json()
            uploaded_file_ids.append(final_file_data["id"])
            if not self.json_output:
                print(
                    f"Successfully uploaded '{file_name}' with file ID: {final_file_data['id']}"
                )

        if not self.json_output:
            print(
                f"Step 3: Submitting assignment with file IDs: {uploaded_file_ids}..."
            )
        submit_url = f"{self.base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions"

        submit_payload = [("submission[submission_type]", "online_upload")]
        for fid in uploaded_file_ids:
            submit_payload.append(("submission[file_ids][]", str(fid)))
        if comment:
            submit_payload.append(("comment[text_comment]", comment))

        await self._post(submit_url, data=submit_payload)
        if not self.json_output:
            print("Assignment submitted successfully!")

    async def download_file(self, url: str, save_path: str) -> Dict[str, Any]:
        """Downloads a file from a URL with a progress bar."""
        client = await self.get_client()
        async with client.get(url, allow_redirects=False) as response:
            response.raise_for_status()
            download_url = response.headers.get("Location")
            if response.status in (301, 302, 303, 307, 308) and download_url:
                final_url = download_url
            else:
                final_url = str(response.url)

        # Encode to avoid issues with special characters in URLs
        download_url = URL(final_url, encoded=True)
        download_client = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30.0),
            connector=aiohttp.TCPConnector(**_connector_kwargs()),
        )

        try:
            async with download_client.get(
                download_url, allow_redirects=False
            ) as response:
                response.raise_for_status()
                final_url = str(response.url)
                content_disp = response.headers.get("content-disposition", "")
                filename = "out_file"

                query_params = parse_qs(urlparse(final_url).query)
                query_disposition = query_params.get(
                    "response-content-disposition", [""]
                )[0]
                if query_disposition:
                    content_disp = urllib.parse.unquote(query_disposition)

                if not content_disp:
                    filename = (
                        os.path.basename(urlparse(final_url).path) or "downloaded_file"
                    )
                if content_disp:
                    parts = [p.strip() for p in content_disp.split(";")]
                    for part in parts:
                        if part.lower().startswith("filename*="):
                            value = part.split("=", 1)[1].strip().strip('"')
                            if "''" in value:
                                value = value.split("''", 1)[1]
                            filename = urllib.parse.unquote(value)
                            break
                    else:
                        for part in parts:
                            if part.lower().startswith("filename="):
                                filename = part[len("filename=") :].strip('"')
                                break

                file_size = int(response.headers.get("content-length", 0))
                full_path = os.path.join(save_path, filename)
                os.makedirs(save_path, exist_ok=True)

                with Progress(disable=self.json_output) as progress:
                    task = progress.add_task(
                        f"[cyan]Downloading {filename}", total=file_size
                    )
                    with open(full_path, "wb") as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
        finally:
            await download_client.close()

        if not self.json_output:
            print(f"Downloaded '{filename}' to '{full_path}'")

        return {
            "filename": filename,
            "size": file_size,
            "path": full_path,
            "url": final_url,
        }

    async def close(self):
        """Close the HTTP client."""
        if self.client and not self.client.closed:
            await self.client.close()
