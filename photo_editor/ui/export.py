"""Process-all button: snapshot jobs, run BatchExporter, show progress."""

import os
import queue
from tkinter import messagebox

from photo_editor.core.batch import ExportJob


class ExportMixin:
    """Connects the GUI to core.batch.BatchExporter."""

    def run_batch(self):
        if not self.photos:
            messagebox.showinfo("Nothing to do", "Add some photos first.")
            return
        outdir = self.out_dir.get().strip()
        if not outdir:
            messagebox.showinfo("Output folder", "Choose an output folder in the Output tab.")
            return
        try:
            os.makedirs(outdir, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Output folder", str(e))
            return

        s, fmt, q, suffix = self.settings(), self.fmt.get(), self.quality.get(), self.suffix.get()
        jobs = [ExportJob(path=p.path, levels=self.levels_for(p).copy(),
                          crop=p.crop if s["crop_enabled"] else None,
                          bg=p.bg, prod=p.prod, obst=p.obst) for p in self.photos]
        self.progress.config(maximum=len(jobs), value=0)
        self.go_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.status.set(f"Processing 0 / {len(jobs)}…")
        self.done_count, self.errors, self.total = 0, [], len(jobs)
        self.exporter.start(jobs, outdir, s, fmt, q, suffix)
        self.after(100, self.poll)

    def poll(self):
        finished, outdir = False, ""
        try:
            while True:
                m = self.exporter.messages.get_nowait()
                if m[0] == "item":
                    self.done_count += 1
                    if m[2] and m[2] != "cancelled":
                        self.errors.append(f"{m[1]}: {m[2]}")
                    self.progress.config(value=self.done_count)
                    self.status.set(f"Processing {self.done_count} / {self.total}…")
                else:
                    finished, outdir = True, m[1]
        except queue.Empty:
            pass
        if not finished:
            self.after(100, self.poll)
            return
        self.go_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        ok = self.done_count - len(self.errors)
        self.status.set("Cancelled." if self.exporter.cancelled
                        else f"Done: {ok} saved, {len(self.errors)} failed.")
        msg = f"Saved to:\n{outdir}"
        if self.errors:
            msg += "\n\nFailed:\n" + "\n".join(self.errors[:10])
        messagebox.showinfo("Finished", msg)
