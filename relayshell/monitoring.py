"""Monitoring components for clipboard and terminal output."""

import asyncio
import logging
import psutil
import threading
import time
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

try:
    import pyperclip
except ImportError:
    pyperclip = None
    logging.warning("pyperclip not available - clipboard monitoring disabled")

from .config import MonitoringConfig


@dataclass
class MonitorEvent:
    """Event detected by monitoring system."""
    source: str  # "clipboard", "terminal", "file"
    content: str
    timestamp: float
    metadata: Dict[str, Any]


class ClipboardMonitor:
    """Monitors clipboard for changes."""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_monitoring = False
        self.last_content = ""
        self.monitor_thread = None
        
        # Callback for clipboard changes
        self.on_clipboard_change: Optional[Callable[[MonitorEvent], None]] = None
    
    def start(self) -> bool:
        """Start clipboard monitoring."""
        if not pyperclip or not self.config.clipboard_enabled:
            self.logger.warning("Clipboard monitoring not available or disabled")
            return False
        
        if self.is_monitoring:
            return True
        
        try:
            # Get initial clipboard content
            self.last_content = pyperclip.paste()
            self.is_monitoring = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            self.logger.info("Clipboard monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start clipboard monitoring: {e}")
            return False
    
    def stop(self):
        """Stop clipboard monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        self.logger.info("Clipboard monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                current_content = pyperclip.paste()
                
                if current_content != self.last_content and current_content.strip():
                    # Clipboard changed
                    self.logger.debug(f"Clipboard changed: {current_content[:100]}...")
                    
                    event = MonitorEvent(
                        source="clipboard",
                        content=current_content,
                        timestamp=time.time(),
                        metadata={"length": len(current_content)}
                    )
                    
                    if self.on_clipboard_change:
                        self.on_clipboard_change(event)
                    
                    self.last_content = current_content
                
                time.sleep(self.config.clipboard_poll_interval)
                
            except Exception as e:
                self.logger.error(f"Clipboard monitoring error: {e}")
                time.sleep(1.0)


class TerminalMonitor:
    """Monitors terminal processes for error keywords."""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_monitoring = False
        self.monitored_processes = {}
        
        # Callback for terminal events
        self.on_terminal_event: Optional[Callable[[MonitorEvent], None]] = None
    
    def start(self) -> bool:
        """Start terminal monitoring."""
        if not self.config.terminal_enabled:
            self.logger.warning("Terminal monitoring disabled")
            return False
        
        if self.is_monitoring:
            return True
        
        try:
            self.is_monitoring = True
            
            # Start monitoring in background
            asyncio.create_task(self._monitor_processes())
            
            self.logger.info("Terminal monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start terminal monitoring: {e}")
            return False
    
    def stop(self):
        """Stop terminal monitoring."""
        self.is_monitoring = False
        self.monitored_processes.clear()
        self.logger.info("Terminal monitoring stopped")
    
    async def _monitor_processes(self):
        """Monitor running processes for terminal activity."""
        while self.is_monitoring:
            try:
                # Get current terminal processes
                current_processes = self._get_terminal_processes()
                
                # Check for new processes
                for pid, proc_info in current_processes.items():
                    if pid not in self.monitored_processes:
                        self.monitored_processes[pid] = proc_info
                        asyncio.create_task(self._monitor_process(pid, proc_info))
                
                # Clean up finished processes
                finished_pids = []
                for pid in self.monitored_processes:
                    if not psutil.pid_exists(pid):
                        finished_pids.append(pid)
                
                for pid in finished_pids:
                    del self.monitored_processes[pid]
                
                await asyncio.sleep(2.0)  # Check every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Process monitoring error: {e}")
                await asyncio.sleep(5.0)
    
    def _get_terminal_processes(self) -> Dict[int, Dict[str, Any]]:
        """Get list of current terminal processes."""
        terminal_processes = {}
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'terminal']):
                try:
                    proc_info = proc.info
                    
                    # Check if it's a terminal-related process
                    if (proc_info['terminal'] or 
                        any(term in proc_info['name'].lower() for term in 
                            ['bash', 'zsh', 'fish', 'sh', 'python', 'node', 'npm', 'cargo', 'go'])):
                        
                        terminal_processes[proc_info['pid']] = {
                            'name': proc_info['name'],
                            'cmdline': proc_info['cmdline'],
                            'terminal': proc_info['terminal']
                        }
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error getting terminal processes: {e}")
        
        return terminal_processes
    
    async def _monitor_process(self, pid: int, proc_info: Dict[str, Any]):
        """Monitor a specific process for output."""
        try:
            process = psutil.Process(pid)
            
            # Monitor process status and potential error conditions
            while self.is_monitoring and process.is_running():
                try:
                    status = process.status()
                    
                    # Check if process has exited with error
                    if status == psutil.STATUS_ZOMBIE:
                        returncode = process.returncode()
                        if returncode != 0:
                            # Process failed
                            event = MonitorEvent(
                                source="terminal",
                                content=f"Process failed: {' '.join(proc_info['cmdline'])}",
                                timestamp=time.time(),
                                metadata={
                                    "pid": pid,
                                    "returncode": returncode,
                                    "process_name": proc_info['name']
                                }
                            )
                            
                            if self.on_terminal_event:
                                self.on_terminal_event(event)
                        break
                    
                    await asyncio.sleep(1.0)
                    
                except psutil.NoSuchProcess:
                    break
                except Exception as e:
                    self.logger.error(f"Error monitoring process {pid}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Process monitoring setup error for {pid}: {e}")


class FileMonitor:
    """Monitors files for changes (like log files)."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.watched_files = {}
        self.is_monitoring = False
        
        # Callback for file changes
        self.on_file_change: Optional[Callable[[MonitorEvent], None]] = None
    
    def add_file(self, file_path: str, keywords: List[str] = None):
        """Add a file to monitor."""
        try:
            path = Path(file_path)
            if path.exists():
                self.watched_files[str(path)] = {
                    "path": path,
                    "keywords": keywords or [],
                    "last_size": path.stat().st_size,
                    "last_mtime": path.stat().st_mtime
                }
                self.logger.info(f"Added file to monitor: {file_path}")
            else:
                self.logger.warning(f"File does not exist: {file_path}")
        except Exception as e:
            self.logger.error(f"Error adding file to monitor: {e}")
    
    def remove_file(self, file_path: str):
        """Remove a file from monitoring."""
        if file_path in self.watched_files:
            del self.watched_files[file_path]
            self.logger.info(f"Removed file from monitor: {file_path}")
    
    def start(self) -> bool:
        """Start file monitoring."""
        if self.is_monitoring:
            return True
        
        try:
            self.is_monitoring = True
            asyncio.create_task(self._monitor_files())
            self.logger.info("File monitoring started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start file monitoring: {e}")
            return False
    
    def stop(self):
        """Stop file monitoring."""
        self.is_monitoring = False
        self.logger.info("File monitoring stopped")
    
    async def _monitor_files(self):
        """Monitor watched files for changes."""
        while self.is_monitoring:
            try:
                for file_path, file_info in self.watched_files.items():
                    await self._check_file_changes(file_path, file_info)
                
                await asyncio.sleep(1.0)  # Check every second
                
            except Exception as e:
                self.logger.error(f"File monitoring error: {e}")
                await asyncio.sleep(5.0)
    
    async def _check_file_changes(self, file_path: str, file_info: Dict[str, Any]):
        """Check if a specific file has changed."""
        try:
            path = file_info["path"]
            
            if not path.exists():
                return
            
            stat = path.stat()
            
            # Check if file was modified
            if stat.st_mtime > file_info["last_mtime"]:
                # File was modified, read new content
                new_content = await self._read_new_content(path, file_info["last_size"])
                
                if new_content and file_info["keywords"]:
                    # Check for keywords
                    for keyword in file_info["keywords"]:
                        if keyword.lower() in new_content.lower():
                            event = MonitorEvent(
                                source="file",
                                content=new_content,
                                timestamp=time.time(),
                                metadata={
                                    "file_path": file_path,
                                    "keyword": keyword
                                }
                            )
                            
                            if self.on_file_change:
                                self.on_file_change(event)
                            break
                
                # Update tracking info
                file_info["last_size"] = stat.st_size
                file_info["last_mtime"] = stat.st_mtime
                
        except Exception as e:
            self.logger.error(f"Error checking file {file_path}: {e}")
    
    async def _read_new_content(self, path: Path, last_size: int) -> str:
        """Read new content from file since last check."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to last position
                f.seek(last_size)
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            return ""


class MonitorManager:
    """Manages all monitoring components."""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize monitors
        self.clipboard_monitor = ClipboardMonitor(config)
        self.terminal_monitor = TerminalMonitor(config)
        self.file_monitor = FileMonitor()
        
        # Event callback
        self.on_monitor_event: Optional[Callable[[MonitorEvent], None]] = None
        
        # Setup callbacks
        self.clipboard_monitor.on_clipboard_change = self._handle_monitor_event
        self.terminal_monitor.on_terminal_event = self._handle_monitor_event
        self.file_monitor.on_file_change = self._handle_monitor_event
    
    def start(self) -> bool:
        """Start all monitoring components."""
        success = True
        
        try:
            if not self.clipboard_monitor.start():
                success = False
            
            if not self.terminal_monitor.start():
                success = False
            
            if not self.file_monitor.start():
                success = False
            
            if success:
                self.logger.info("All monitors started successfully")
            else:
                self.logger.warning("Some monitors failed to start")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to start monitors: {e}")
            return False
    
    def stop(self):
        """Stop all monitoring components."""
        self.clipboard_monitor.stop()
        self.terminal_monitor.stop()
        self.file_monitor.stop()
        self.logger.info("All monitors stopped")
    
    def _handle_monitor_event(self, event: MonitorEvent):
        """Handle events from any monitor."""
        self.logger.debug(f"Monitor event from {event.source}: {event.content[:100]}...")
        
        # Check for auto-trigger keywords
        if self._should_auto_trigger(event):
            self.logger.info(f"Auto-trigger detected from {event.source}")
        
        # Forward to main callback
        if self.on_monitor_event:
            self.on_monitor_event(event)
    
    def _should_auto_trigger(self, event: MonitorEvent) -> bool:
        """Check if event should trigger automatic response."""
        content_lower = event.content.lower()
        
        # Check for trigger keywords
        for keyword in self.config.auto_trigger_keywords:
            if keyword.lower() in content_lower:
                return True
        
        # Check for error patterns
        for keyword in self.config.terminal_keywords:
            if keyword.lower() in content_lower:
                return True
        
        return False
    
    def add_log_file(self, file_path: str):
        """Add a log file to monitor."""
        self.file_monitor.add_file(file_path, self.config.terminal_keywords)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all monitors."""
        return {
            "clipboard": {
                "enabled": self.config.clipboard_enabled,
                "monitoring": self.clipboard_monitor.is_monitoring
            },
            "terminal": {
                "enabled": self.config.terminal_enabled,
                "monitoring": self.terminal_monitor.is_monitoring,
                "processes": len(self.terminal_monitor.monitored_processes)
            },
            "files": {
                "monitoring": self.file_monitor.is_monitoring,
                "watched_files": len(self.file_monitor.watched_files)
            }
        }