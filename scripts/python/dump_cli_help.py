#!/usr/bin/env python3
"""
CLI Help Documentation Generator

Automatically generates CLI reference documentation by capturing
help output from all available commands and subcommands.
"""

import argparse
import pathlib
import subprocess
import sys
from typing import Dict, List, Tuple
import re


def get_cli_commands() -> List[str]:
    """Get list of main CLI commands by parsing help output."""
    try:
        # Get main help
        result = subprocess.run([
            sys.executable, "-m", "ecgcourse.cli", "--help"
        ], capture_output=True, text=True, cwd=pathlib.Path(__file__).parents[2])
        
        if result.returncode != 0:
            raise RuntimeError(f"CLI help failed: {result.stderr}")
        
        # Parse commands from help output
        commands = []
        help_lines = result.stdout.split('\n')
        in_commands_section = False
        
        for line in help_lines:
            if '─ Commands ─' in line:
                in_commands_section = True
                continue
            elif in_commands_section:
                if line.startswith('╰─'):
                    break
                elif line.strip() and not line.startswith('│'):
                    # Extract command name
                    match = re.match(r'│\s+(\w+)', line)
                    if match:
                        commands.append(match.group(1))
        
        return commands
        
    except Exception as e:
        print(f"Error getting CLI commands: {e}", file=sys.stderr)
        return []


def get_subcommands(command: str) -> List[str]:
    """Get subcommands for a specific command."""
    try:
        result = subprocess.run([
            sys.executable, "-m", "ecgcourse.cli", command, "--help"
        ], capture_output=True, text=True, cwd=pathlib.Path(__file__).parents[2])
        
        if result.returncode != 0:
            return []  # No subcommands or error
        
        subcommands = []
        help_lines = result.stdout.split('\n')
        in_commands_section = False
        
        for line in help_lines:
            if '─ Commands ─' in line:
                in_commands_section = True
                continue
            elif in_commands_section:
                if line.startswith('╰─'):
                    break
                elif line.strip() and not line.startswith('│'):
                    # Extract subcommand name
                    match = re.match(r'│\s+(\S+)', line)
                    if match:
                        subcommands.append(match.group(1))
        
        return subcommands
        
    except Exception:
        return []


def capture_help_output(command_path: List[str]) -> Tuple[str, bool]:
    """Capture help output for a command path."""
    try:
        cmd = [sys.executable, "-m", "ecgcourse.cli"] + command_path + ["--help"]
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=pathlib.Path(__file__).parents[2]
        )
        
        return result.stdout, result.returncode == 0
        
    except Exception as e:
        return f"Error capturing help for {' '.join(command_path)}: {e}", False


def format_markdown_section(title: str, content: str, level: int = 2) -> str:
    """Format a markdown section with proper heading level."""
    heading = "#" * level
    
    # Clean up content - remove excessive whitespace and format code blocks
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Keep important formatting but clean up excessive spaces
        if line.strip():
            cleaned_lines.append(line.rstrip())
        else:
            cleaned_lines.append('')
    
    # Join and format as code block
    formatted_content = '\n'.join(cleaned_lines)
    
    return f"{heading} {title}\n\n```\n{formatted_content}\n```\n\n"


def generate_cli_documentation(output_path: pathlib.Path) -> bool:
    """Generate complete CLI documentation."""
    
    # Set up PYTHONPATH for CLI import
    repo_root = pathlib.Path(__file__).parents[2]
    cli_app_path = repo_root / "cli_app"
    
    import os
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    os.environ['PYTHONPATH'] = f"{cli_app_path}:{current_pythonpath}".rstrip(':')
    
    try:
        # Start building documentation
        doc_lines = [
            "# ECG Course CLI Reference\n",
            "*This documentation is auto-generated from CLI help output.*\n",
            f"*Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
        ]
        
        # Get main help
        main_help, success = capture_help_output([])
        if success:
            doc_lines.append(format_markdown_section("Main Command", main_help, 2))
        else:
            doc_lines.append("## Main Command\n\n*Error capturing main help*\n\n")
        
        # Get all commands
        print("Discovering CLI commands...")
        commands = get_cli_commands()
        
        if not commands:
            print("Warning: No commands found. Using fallback list.")
            # Fallback list based on code inspection
            commands = ["analyze", "quiz", "ingest", "assets", "cv", "report", "checklist", "rhythm", "precordials"]
        
        print(f"Found {len(commands)} main commands: {', '.join(commands)}")
        
        # Document each command and its subcommands
        for command in commands:
            print(f"Documenting command: {command}")
            
            # Get help for the main command
            help_output, success = capture_help_output([command])
            if success:
                doc_lines.append(format_markdown_section(f"Command: {command}", help_output, 2))
                
                # Get subcommands
                subcommands = get_subcommands(command)
                if subcommands:
                    print(f"  Found {len(subcommands)} subcommands: {', '.join(subcommands)}")
                    
                    for subcommand in subcommands:
                        subhelp_output, subsuccess = capture_help_output([command, subcommand])
                        if subsuccess:
                            doc_lines.append(format_markdown_section(
                                f"{command} {subcommand}", 
                                subhelp_output, 
                                3
                            ))
                        else:
                            doc_lines.append(f"### {command} {subcommand}\n\n*Error capturing help*\n\n")
            else:
                doc_lines.append(f"## Command: {command}\n\n*Error capturing help*\n\n")
        
        # Write documentation
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(doc_lines)
        
        print(f"CLI documentation generated: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error generating documentation: {e}", file=sys.stderr)
        return False
    
    finally:
        # Restore PYTHONPATH
        if current_pythonpath:
            os.environ['PYTHONPATH'] = current_pythonpath
        else:
            os.environ.pop('PYTHONPATH', None)


def main():
    parser = argparse.ArgumentParser(
        description="Generate CLI reference documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--output", "-o",
        default="docs/cli_reference.md",
        help="Output markdown file path (default: docs/cli_reference.md)"
    )
    
    args = parser.parse_args()
    
    # Resolve output path relative to repository root
    repo_root = pathlib.Path(__file__).parents[2]
    output_path = repo_root / args.output
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Generating CLI reference documentation...")
    print(f"Output file: {output_path}")
    
    success = generate_cli_documentation(output_path)
    
    if success:
        print("Documentation generation completed successfully!")
        return 0
    else:
        print("Documentation generation failed!", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())