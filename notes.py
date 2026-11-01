"""Write Markdown only beneath an operator-selected directory (Linux)."""

from contextlib import ExitStack
import os
from pathlib import Path
import secrets
import stat


class NoteStore:
    def __init__(self, root: Path):
        # Do not resolve symlinks: the root itself must also pass O_NOFOLLOW.
        self.root = Path(os.path.abspath(root.expanduser()))

    def save_note(self, path: str, content: str) -> dict:
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError("path and content must be strings")
        parts = path.split("/")
        if (
            "\\" in path
            or "\0" in path
            or not path.endswith(".md")
            or any(not part or part.startswith(".") for part in parts)
        ):
            raise ValueError(
                "Use a relative .md path without hidden or traversal components"
            )
        data = content.encode("utf-8")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        with ExitStack() as stack:
            parent = os.open(self.root, flags)
            stack.callback(os.close, parent)
            for part in parts[:-1]:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=parent)
                except FileExistsError:
                    pass
                parent = os.open(part, flags, dir_fd=parent)
                stack.callback(os.close, parent)
            name = parts[-1]
            try:
                existing = os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                existing = None
            if existing is not None and (
                not stat.S_ISREG(existing.st_mode) or existing.st_nlink != 1
            ):
                raise ValueError("Destination must be a regular file without links")
            temporary = ".note-" + secrets.token_hex(16)
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=parent,
            )
            try:
                with os.fdopen(fd, "wb") as output:
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass
        return {"path": path, "bytes": len(data)}
