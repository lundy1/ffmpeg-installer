import os
import sys
import requests
import zipfile
import subprocess
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

class FFmpegInstaller(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("FFmpeg Installer")
        self.geometry("500x400")
        
        self.install_dir = tk.StringVar(value=str(Path("C:/ffmpeg")))
        self.progress_var = tk.DoubleVar()
        
        self.create_widgets()
        
    def create_widgets(self):

        frame = ttk.Frame(self, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text="Installation Directory:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.install_dir, width=50).grid(row=1, column=0, sticky=(tk.W, tk.E))
        ttk.Button(frame, text="Browse", command=self.browse_directory).grid(row=1, column=1, padx=5)
        
        self.progress = ttk.Progressbar(frame, length=300, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=2, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(frame, text="Ready to install")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)

        self.install_button = ttk.Button(frame, text="Install FFmpeg", command=self.start_installation)
        self.install_button.grid(row=4, column=0, columnspan=2, pady=10)

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir="/")
        if directory:
            self.install_dir.set(directory)

    def start_installation(self):
        if not self.check_admin():
            messagebox.showerror("Error", "Please run this installer as administrator")
            return
            
        self.install_button.config(state='disabled')
        threading.Thread(target=self.install_ffmpeg, daemon=True).start()

    def check_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def update_status(self, message, progress=None):
        self.status_label.config(text=message)
        if progress is not None:
            self.progress_var.set(progress)
        self.update()

    def download_ffmpeg(self, url, dest):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        downloaded = 0
        
        if response.status_code == 200:
            with open(dest, 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    downloaded += len(data)
                    progress = (downloaded / total_size) * 50  
                    self.update_status(f"Downloading: {int(progress*2)}%", progress)
        else:
            raise Exception("Failed to download FFmpeg")

    def install_ffmpeg(self):
        try:
            FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            install_path = Path(self.install_dir.get())
            ffmpeg_zip = install_path / "ffmpeg.zip"

            install_path.mkdir(parents=True, exist_ok=True)

            self.update_status("Downloading FFmpeg...", 0)
            self.download_ffmpeg(FFMPEG_URL, ffmpeg_zip)

            self.update_status("Extracting FFmpeg...", 50)
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall(install_path)

            bin_dir = None
            for root, dirs, files in os.walk(install_path):
                if 'bin' in dirs:
                    bin_dir = Path(root) / 'bin'
                    break

            if not bin_dir:
                raise Exception("Could not find FFmpeg bin directory")

            self.update_status("Adding to System PATH...", 75)
            self.add_to_path(str(bin_dir))

            ffmpeg_zip.unlink()

            self.update_status("Verifying installation...", 90)
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.update_status("FFmpeg installed successfully!", 100)
                messagebox.showinfo("Success", "FFmpeg has been installed successfully!")
            else:
                raise Exception("FFmpeg installation verification failed")

        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
        finally:
            self.install_button.config(state='normal')

    def add_to_path(self, new_path):
        existing_paths = os.environ.get('Path', '').split(os.pathsep)
        if new_path not in existing_paths:
            existing_paths.append(new_path)
            system_path = os.pathsep.join(existing_paths)
            subprocess.call(['setx', '/M', 'Path', system_path], shell=True)

if __name__ == "__main__":
    app = FFmpegInstaller()
    app.mainloop()