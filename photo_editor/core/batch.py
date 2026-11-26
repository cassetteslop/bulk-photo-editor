"""Background batch export. No GUI code: the UI polls `messages`."""
import os
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

from PIL import Image

from photo_editor.core.levels import Levels
from photo_editor.core.pipeline import process_image, save_image

EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


@dataclass
class ExportJob:
    """Everything a worker needs for one photo (a snapshot - workers never touch the GUI)."""
    path: str
    levels: Levels
    crop: Optional[tuple] = None
    bg: tuple = (255, 255, 255)
    prod: Optional[tuple] = None
    obst: object = None


class BatchExporter:
    """Processes ExportJobs on a thread pool.

    Messages posted to `messages`:
        ("item", filename, error_or_None)   after each photo
        ("done", output_dir)                once, at the end
    """

    def __init__(self):
        self.messages = queue.Queue()
        self._cancel = threading.Event()
        self._lock = threading.Lock()
        self._reserved = set()

    # -- control -----------------------------------------------------------
    def cancel(self):
        self._cancel.set()

    @property
    def cancelled(self):
        return self._cancel.is_set()

    # -- work --------------------------------------------------------------
    def unique_path(self, outdir, stem, ext):
        """Never overwrite: name, name_1, name_2 ... (thread-safe)."""
        with self._lock:
            n, name = 0, f"{stem}{ext}"
            while os.path.exists(os.path.join(outdir, name)) or (outdir, name.lower()) in self._reserved:
                n += 1
                name = f"{stem}_{n}{ext}"
            self._reserved.add((outdir, name.lower()))
            return os.path.join(outdir, name)

    def process_one(self, job, outdir, settings, fmt, quality, suffix):
        if self._cancel.is_set():
            return job.path, "cancelled"
        with Image.open(job.path) as im:
            im.load()
            out = process_image(im, settings, job.levels, crop=job.crop, bg=job.bg,
                                prod=job.prod, obst=job.obst)
        stem = os.path.splitext(os.path.basename(job.path))[0] + suffix
        save_image(out, self.unique_path(outdir, stem, EXTENSIONS[fmt]), fmt, quality)
        return job.path, None

    def start(self, jobs, outdir, settings, fmt, quality, suffix):
        """Run in a background thread and return immediately."""
        self._cancel.clear()
        self._reserved.clear()
        threading.Thread(target=self._run, daemon=True,
                         args=(list(jobs), outdir, settings, fmt, quality, suffix)).start()

    def _run(self, jobs, outdir, settings, fmt, quality, suffix):
        workers = max(1, min(8, os.cpu_count() or 2))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(self.process_one, j, outdir, settings, fmt, quality, suffix): j for j in jobs}
            for fut in as_completed(futs):
                try:
                    _, err = fut.result()
                except Exception as e:  # one bad photo must not stop the batch
                    err = str(e)
                self.messages.put(("item", os.path.basename(futs[fut].path), err))
        self.messages.put(("done", outdir))
