"""Command-line interface for RelayShell."""

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional

import click

from .core import RelayShell
from .config import Config


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, config: Optional[str], debug: bool):
    """RelayShell - AI-powered development assistant with Tamil/English speech support."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['debug'] = debug


@cli.command()
@click.pass_context
def start(ctx):
    """Start RelayShell in interactive mode."""
    config_path = ctx.obj.get('config_path')
    debug = ctx.obj.get('debug', False)
    
    # Create RelayShell instance
    relay = RelayShell(config_path)
    
    if debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    async def run_relay():
        """Run RelayShell with graceful shutdown."""
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        
        def signal_handler():
            print("\nShutting down RelayShell...")
            asyncio.create_task(relay.stop())
            loop.stop()
        
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, signal_handler)
        
        try:
            # Start RelayShell
            await relay.start()
            
            # Keep running until stopped
            while relay.is_running:
                await asyncio.sleep(1.0)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await relay.stop()
    
    # Run the async function
    try:
        asyncio.run(run_relay())
    except KeyboardInterrupt:
        print("\nGoodbye!")


@cli.command()
@click.argument('prompt')
@click.option('--context', help='Additional context for the prompt')
@click.pass_context
def query(ctx, prompt: str, context: Optional[str]):
    """Query LLMs with a prompt."""
    config_path = ctx.obj.get('config_path')
    
    async def run_query():
        relay = RelayShell(config_path)
        
        try:
            # Initialize LLM manager only
            response = await relay.llm_manager.get_best_response(prompt, context)
            
            if response:
                print(f"\n--- Response from {response.provider} ({response.model}) ---")
                print(f"Confidence: {response.confidence_score:.2f}")
                print(f"Response time: {response.response_time:.2f}s")
                print("\n" + response.response_text)
            else:
                print("No response received from any LLM backend.")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            relay.llm_manager.shutdown()
    
    asyncio.run(run_query())


@cli.command()
@click.pass_context
def status(ctx):
    """Show status of RelayShell components."""
    config_path = ctx.obj.get('config_path')
    
    async def show_status():
        relay = RelayShell(config_path)
        
        try:
            status_info = relay.get_status()
            
            print("=== RelayShell Status ===\n")
            
            print(f"Running: {status_info['running']}")
            print(f"Conversation history: {status_info['conversation_history_length']} items\n")
            
            # Speech status
            speech = status_info['speech']
            print("Speech Recognition:")
            print(f"  Listening: {speech['listening']}")
            print(f"  Current language: {speech['current_language']}")
            print(f"  Available languages: {', '.join(speech['available_languages'])}\n")
            
            # LLM status
            print("LLM Backends:")
            for name, llm_info in status_info['llm'].items():
                print(f"  {name}: {llm_info['provider']} ({llm_info['model']})")
                print(f"    Available: {llm_info['available']}")
                print(f"    Priority: {llm_info['priority']}\n")
            
            # Monitoring status
            monitoring = status_info['monitoring']
            print("Monitoring:")
            print(f"  Clipboard: {'Active' if monitoring['clipboard']['monitoring'] else 'Inactive'}")
            print(f"  Terminal: {'Active' if monitoring['terminal']['monitoring'] else 'Inactive'}")
            print(f"  Files: {monitoring['files']['watched_files']} watched files\n")
            
            # Services status
            print("AI Services:")
            for name, service_status in status_info['services'].items():
                print(f"  {name}: {service_status.status}")
                if service_status.pid:
                    print(f"    PID: {service_status.pid}")
                if service_status.health_status != "unknown":
                    print(f"    Health: {service_status.health_status}")
            
        except Exception as e:
            print(f"Error getting status: {e}")
        finally:
            if hasattr(relay, 'llm_manager'):
                relay.llm_manager.shutdown()
    
    asyncio.run(show_status())


@cli.command()
@click.option('--example', is_flag=True, help='Create example configuration')
@click.pass_context
def init(ctx, example: bool):
    """Initialize RelayShell configuration."""
    config_path = ctx.obj.get('config_path')
    
    if not config_path:
        config_path = Path.home() / ".relayshell" / "config.yaml"
    else:
        config_path = Path(config_path)
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    if config_path.exists():
        click.confirm(f"Configuration file {config_path} already exists. Overwrite?", abort=True)
    
    # Create configuration
    if example:
        config = Config.create_default()
    else:
        config = Config()
    
    config.save_to_file(str(config_path))
    
    print(f"Configuration file created at: {config_path}")
    print("\nNext steps:")
    print("1. Edit the configuration file to add your API keys")
    print("2. Run 'relayshell start' to begin using RelayShell")


@cli.group()
def service():
    """Manage AI services."""
    pass


@service.command('start')
@click.argument('service_name')
@click.pass_context
def start_service(ctx, service_name: str):
    """Start a specific AI service."""
    config_path = ctx.obj.get('config_path')
    
    async def run_start_service():
        relay = RelayShell(config_path)
        
        try:
            success = await relay.service_manager.start_service(service_name)
            if success:
                print(f"Service '{service_name}' started successfully")
            else:
                print(f"Failed to start service '{service_name}'")
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(run_start_service())


@service.command('stop')
@click.argument('service_name')
@click.pass_context
def stop_service(ctx, service_name: str):
    """Stop a specific AI service."""
    config_path = ctx.obj.get('config_path')
    
    async def run_stop_service():
        relay = RelayShell(config_path)
        
        try:
            success = await relay.service_manager.stop_service(service_name)
            if success:
                print(f"Service '{service_name}' stopped successfully")
            else:
                print(f"Failed to stop service '{service_name}'")
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(run_stop_service())


@service.command('list')
@click.pass_context
def list_services(ctx):
    """List all configured AI services."""
    config_path = ctx.obj.get('config_path')
    
    async def run_list_services():
        relay = RelayShell(config_path)
        
        try:
            services = relay.service_manager.get_all_status()
            
            if not services:
                print("No services configured")
                return
            
            print("=== AI Services ===\n")
            
            for name, status in services.items():
                print(f"{name}:")
                print(f"  Status: {status.status}")
                if status.pid:
                    print(f"  PID: {status.pid}")
                if status.port:
                    print(f"  Port: {status.port}")
                if status.health_status != "unknown":
                    print(f"  Health: {status.health_status}")
                if status.restart_count > 0:
                    print(f"  Restarts: {status.restart_count}")
                print()
                
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(run_list_services())


@service.command('deploy')
@click.argument('yaml_file')
@click.pass_context
def deploy_services(ctx, yaml_file: str):
    """Deploy services from a YAML file."""
    config_path = ctx.obj.get('config_path')
    
    async def run_deploy():
        relay = RelayShell(config_path)
        
        try:
            success = await relay.deploy_services(yaml_file)
            if success:
                print(f"Services deployed successfully from {yaml_file}")
            else:
                print(f"Failed to deploy services from {yaml_file}")
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(run_deploy())


@cli.command()
@click.argument('language', type=click.Choice(['en-US', 'ta-IN']))
@click.pass_context
def set_language(ctx, language: str):
    """Set the default language for speech recognition."""
    config_path = ctx.obj.get('config_path')
    
    # Update configuration
    config = Config.load_from_file(config_path or "~/.relayshell/config.yaml")
    config.speech_config.default_language = language
    config.save_to_file(config_path or "~/.relayshell/config.yaml")
    
    print(f"Default language set to: {language}")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()