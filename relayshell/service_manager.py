"""Service manager for AI service deployment and management."""

import asyncio
import logging
import subprocess
import psutil
import requests
import signal
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from .config import ServiceConfig


@dataclass
class ServiceStatus:
    """Status of a managed service."""
    name: str
    pid: Optional[int] = None
    status: str = "stopped"  # stopped, starting, running, error
    port: Optional[int] = None
    uptime: float = 0.0
    restart_count: int = 0
    last_error: Optional[str] = None
    health_status: str = "unknown"  # healthy, unhealthy, unknown


class ServiceManager:
    """Manages AI services and their lifecycle."""
    
    def __init__(self, service_configs: List[ServiceConfig]):
        self.services = {config.name: config for config in service_configs}
        self.service_status = {config.name: ServiceStatus(name=config.name) 
                              for config in service_configs}
        self.processes = {}  # name -> subprocess.Popen
        self.logger = logging.getLogger(__name__)
        
        # Monitoring task
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
    
    async def start_service(self, service_name: str) -> bool:
        """Start a specific service."""
        if service_name not in self.services:
            self.logger.error(f"Unknown service: {service_name}")
            return False
        
        config = self.services[service_name]
        status = self.service_status[service_name]
        
        if status.status == "running":
            self.logger.info(f"Service {service_name} is already running")
            return True
        
        try:
            self.logger.info(f"Starting service: {service_name}")
            status.status = "starting"
            
            # Prepare environment
            env = dict(os.environ)
            env.update(config.env_vars)
            
            # Start the process
            process = subprocess.Popen(
                config.command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
            
            # Store process reference
            self.processes[service_name] = process
            status.pid = process.pid
            status.status = "running"
            status.uptime = time.time()
            
            self.logger.info(f"Service {service_name} started with PID {process.pid}")
            
            # Wait a moment and check if still running
            await asyncio.sleep(2.0)
            if process.poll() is not None:
                # Process died immediately
                stdout, stderr = process.communicate()
                error_msg = stderr.decode('utf-8') if stderr else "Process exited immediately"
                status.status = "error"
                status.last_error = error_msg
                self.logger.error(f"Service {service_name} failed to start: {error_msg}")
                return False
            
            # Start health monitoring if not already running
            if not self.is_monitoring:
                await self.start_monitoring()
            
            return True
            
        except Exception as e:
            status.status = "error"
            status.last_error = str(e)
            self.logger.error(f"Failed to start service {service_name}: {e}")
            return False
    
    async def stop_service(self, service_name: str) -> bool:
        """Stop a specific service."""
        if service_name not in self.services:
            self.logger.error(f"Unknown service: {service_name}")
            return False
        
        status = self.service_status[service_name]
        
        if status.status == "stopped":
            self.logger.info(f"Service {service_name} is already stopped")
            return True
        
        try:
            self.logger.info(f"Stopping service: {service_name}")
            
            # Get process
            process = self.processes.get(service_name)
            if process:
                # Try graceful shutdown first
                try:
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(process.wait), 
                            timeout=10.0
                        )
                    except asyncio.TimeoutError:
                        # Force kill if graceful shutdown failed
                        self.logger.warning(f"Force killing service {service_name}")
                        if hasattr(os, 'killpg'):
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        else:
                            process.kill()
                        await asyncio.to_thread(process.wait)
                    
                except (ProcessLookupError, OSError):
                    # Process already dead
                    pass
                
                # Clean up
                del self.processes[service_name]
            
            # Update status
            status.status = "stopped"
            status.pid = None
            status.uptime = 0.0
            status.health_status = "unknown"
            
            self.logger.info(f"Service {service_name} stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service."""
        await self.stop_service(service_name)
        await asyncio.sleep(1.0)  # Brief pause
        return await self.start_service(service_name)
    
    async def start_all_auto_services(self):
        """Start all services marked for auto-start."""
        for service_name, config in self.services.items():
            if config.auto_start:
                await self.start_service(service_name)
    
    async def stop_all_services(self):
        """Stop all running services."""
        for service_name in list(self.processes.keys()):
            await self.stop_service(service_name)
        
        # Stop monitoring
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
            self.is_monitoring = False
    
    async def start_monitoring(self):
        """Start service health monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_services())
        self.logger.info("Service monitoring started")
    
    async def _monitor_services(self):
        """Monitor service health and restart if needed."""
        while self.is_monitoring:
            try:
                for service_name, config in self.services.items():
                    await self._check_service_health(service_name, config)
                
                await asyncio.sleep(10.0)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Service monitoring error: {e}")
                await asyncio.sleep(30.0)
    
    async def _check_service_health(self, service_name: str, config: ServiceConfig):
        """Check health of a specific service."""
        status = self.service_status[service_name]
        
        try:
            # Check if process is still running
            process = self.processes.get(service_name)
            if process:
                if process.poll() is not None:
                    # Process died
                    stdout, stderr = process.communicate()
                    error_msg = stderr.decode('utf-8') if stderr else "Process exited unexpectedly"
                    
                    status.status = "error"
                    status.last_error = error_msg
                    status.pid = None
                    status.health_status = "unhealthy"
                    
                    del self.processes[service_name]
                    
                    self.logger.error(f"Service {service_name} died: {error_msg}")
                    
                    # Restart if configured
                    if config.restart_on_failure:
                        self.logger.info(f"Attempting to restart {service_name}")
                        status.restart_count += 1
                        await asyncio.sleep(5.0)  # Brief delay before restart
                        await self.start_service(service_name)
                    
                    return
                
                # Update uptime
                status.uptime = time.time() - status.uptime
            
            # Check health endpoint if configured
            if config.health_check_url and status.status == "running":
                try:
                    response = requests.get(
                        config.health_check_url, 
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        status.health_status = "healthy"
                    else:
                        status.health_status = "unhealthy"
                        self.logger.warning(f"Service {service_name} health check failed: {response.status_code}")
                        
                except requests.RequestException as e:
                    status.health_status = "unhealthy"
                    self.logger.warning(f"Service {service_name} health check error: {e}")
            
        except Exception as e:
            self.logger.error(f"Error checking health of {service_name}: {e}")
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get status of a specific service."""
        return self.service_status.get(service_name)
    
    def get_all_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services."""
        return self.service_status.copy()
    
    def get_running_services(self) -> List[str]:
        """Get list of currently running services."""
        return [name for name, status in self.service_status.items() 
                if status.status == "running"]
    
    def is_service_running(self, service_name: str) -> bool:
        """Check if a service is currently running."""
        status = self.service_status.get(service_name)
        return status and status.status == "running"
    
    def get_service_logs(self, service_name: str, lines: int = 50) -> Optional[str]:
        """Get recent logs from a service."""
        process = self.processes.get(service_name)
        if not process:
            return None
        
        try:
            # This is a simplified version - in a real implementation,
            # you'd want to capture and store logs properly
            return f"Logs for {service_name} not available (PID: {process.pid})"
        except Exception as e:
            self.logger.error(f"Error getting logs for {service_name}: {e}")
            return None
    
    async def deploy_from_yaml(self, yaml_path: str) -> bool:
        """Deploy services from a YAML configuration file."""
        try:
            import yaml
            
            with open(yaml_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            services_data = config_data.get('services', [])
            
            for service_data in services_data:
                service_config = ServiceConfig(**service_data)
                self.services[service_config.name] = service_config
                self.service_status[service_config.name] = ServiceStatus(name=service_config.name)
            
            self.logger.info(f"Loaded {len(services_data)} services from {yaml_path}")
            
            # Start auto-start services
            await self.start_all_auto_services()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy from YAML: {e}")
            return False
    
    def export_to_yaml(self, yaml_path: str) -> bool:
        """Export current service configuration to YAML."""
        try:
            import yaml
            
            services_data = []
            for config in self.services.values():
                services_data.append({
                    'name': config.name,
                    'command': config.command,
                    'port': config.port,
                    'health_check_url': config.health_check_url,
                    'env_vars': config.env_vars,
                    'auto_start': config.auto_start,
                    'restart_on_failure': config.restart_on_failure
                })
            
            config_data = {'services': services_data}
            
            with open(yaml_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Exported services to {yaml_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export to YAML: {e}")
            return False


# Import os at the top level
import os