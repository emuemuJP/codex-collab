#!/usr/bin/env python3
"""
tmux session setup and management for Code and Codex collaboration.
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

COLLAB_DIR = Path("/tmp/codex_collab")
SESSIONS_FILE = COLLAB_DIR / "sessions.json"
PANE_INFO_FILE = COLLAB_DIR / "pane_info.json"

def ensure_collab_dir():
    """Ensure collaboration directory exists."""
    COLLAB_DIR.mkdir(exist_ok=True, parents=True)
    if not SESSIONS_FILE.exists():
        atomic_write_json(SESSIONS_FILE, {})


def atomic_write_json(filepath: Path, data: Any):
    """Write JSON atomically with exclusive lock."""
    tmp_path = filepath.with_suffix('.tmp')
    try:
        with open(tmp_path, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise e


def safe_load_json(filepath: Path, default: Any) -> Any:
    """Load JSON with corruption recovery."""
    if not filepath.exists():
        return default
    try:
        content = filepath.read_text()
        if not content.strip():
            return default
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Backup corrupted file and return default
        backup_path = filepath.with_suffix('.bak')
        try:
            filepath.rename(backup_path)
            print(f"⚠ {filepath.name} was corrupted, backed up to {backup_path.name}", file=sys.stderr)
        except Exception:
            print(f"⚠ {filepath.name} is corrupted: {e}", file=sys.stderr)
        return default

def load_sessions() -> Dict[str, Any]:
    """Load session metadata."""
    return safe_load_json(SESSIONS_FILE, {})


def save_sessions(sessions: Dict[str, Any]):
    """Save session metadata."""
    atomic_write_json(SESSIONS_FILE, sessions)


def save_pane_info(session_name: str, claude_pane: str, codex_pane: str):
    """Save pane IDs for dynamic reference."""
    pane_info = safe_load_json(PANE_INFO_FILE, {})
    pane_info[session_name] = {
        "claude_pane": claude_pane,
        "codex_pane": codex_pane,
        "updated": datetime.now().isoformat()
    }
    atomic_write_json(PANE_INFO_FILE, pane_info)


def get_pane_info(session_name: str) -> Optional[Dict[str, str]]:
    """Get pane IDs for a session."""
    pane_info = safe_load_json(PANE_INFO_FILE, {})
    return pane_info.get(session_name)

def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}", file=sys.stderr)
        print(f"Error: {e.stderr}", file=sys.stderr)
        if check:
            sys.exit(1)
        return e

def check_tmux_installed() -> bool:
    """Check if tmux is installed."""
    result = run_command(["which", "tmux"], check=False)
    return result.returncode == 0


def is_inside_tmux() -> bool:
    """Check if running inside tmux (handles VSCode terminal case)."""
    # First check environment variable
    if os.environ.get("TMUX"):
        return True
    # Fallback: try tmux display-message (works in VSCode terminal)
    result = run_command(
        ["tmux", "display-message", "-p", "#{session_name}"],
        check=False
    )
    return result.returncode == 0 and result.stdout.strip() != ""


def session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    result = run_command(["tmux", "has-session", "-t", session_name], check=False)
    return result.returncode == 0

def get_current_tmux_session() -> Optional[str]:
    """Get the current tmux session name."""
    result = run_command(
        ["tmux", "display-message", "-p", "#{session_name}"],
        check=False
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def get_window_width(session_name: str) -> int:
    """Get the current window width in columns."""
    result = run_command(
        ["tmux", "display-message", "-t", session_name, "-p", "#{window_width}"],
        check=False
    )
    if result.returncode == 0 and result.stdout.strip().isdigit():
        return int(result.stdout.strip())
    return 160  # Default fallback


def get_current_pane_id() -> Optional[str]:
    """Get the current pane ID."""
    result = run_command(
        ["tmux", "display-message", "-p", "#{pane_id}"],
        check=False
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def init_session(session_name: str, working_dir: Optional[str] = None):
    """Initialize collaboration session.

    - If inside tmux: add Codex pane to current session
    - If outside tmux: create new session with specified name
    """
    ensure_collab_dir()

    if not check_tmux_installed():
        print("Error: tmux is not installed.", file=sys.stderr)
        print("  macOS: brew install tmux", file=sys.stderr)
        print("  Linux: sudo apt-get install tmux", file=sys.stderr)
        sys.exit(1)

    working_dir = working_dir or str(Path.cwd())
    inside_tmux = is_inside_tmux()

    if inside_tmux:
        # Running inside tmux - add pane to current session
        current_session = get_current_tmux_session()
        if not current_session:
            print("Error: Could not determine current tmux session.", file=sys.stderr)
            sys.exit(1)

        target_session = current_session

        # Check current pane count
        result = run_command(
            ["tmux", "list-panes", "-t", current_session],
            check=False
        )
        pane_count = len(result.stdout.strip().split('\n')) if result.stdout else 1

        if pane_count >= 2:
            # Already has panes, try to get existing pane info
            pane_info = get_pane_info(current_session)
            if pane_info:
                print(f"✓ Session already has {pane_count} panes with collaboration setup.")
            else:
                print(f"✓ Session already has {pane_count} panes.")
            print("  Codex pane may already be running.")
            print("  Use Ctrl+b → o to switch panes.")
            # Save session info
            current_session_file = COLLAB_DIR / "current_session.txt"
            current_session_file.write_text(current_session)
            return

        print(f"🚀 Adding Codex pane to current session: {current_session}")
        print(f"   Working directory: {working_dir}")

        # Get current pane ID before split
        claude_pane = get_current_pane_id()

        # Split current window horizontally and get new pane ID
        result = run_command([
            "tmux", "split-window", "-h",
            "-t", f"{current_session}:",
            "-c", working_dir,
            "-P", "-F", "#{pane_id}"  # Print new pane ID
        ])
        codex_pane = result.stdout.strip() if result.stdout else None

    else:
        # Running outside tmux - create new session
        target_session = session_name

        if session_exists(session_name):
            print(f"⚠ Session '{session_name}' already exists.")
            print(f"  Attach with: tmux attach-session -t {session_name}")
            print(f"  Or end it with: python3 {__file__} --end --session-name {session_name}")
            return

        print(f"🚀 Creating new tmux session: {session_name}")
        print(f"   Working directory: {working_dir}")

        # Create new detached session
        run_command([
            "tmux", "new-session", "-d",
            "-s", session_name,
            "-c", working_dir
        ])

        # Get the pane ID of the first pane
        result = run_command([
            "tmux", "list-panes", "-t", session_name,
            "-F", "#{pane_id}"
        ])
        claude_pane = result.stdout.strip().split('\n')[0] if result.stdout else None

        # Split window and get new pane ID
        result = run_command([
            "tmux", "split-window", "-h",
            "-t", f"{session_name}:",
            "-c", working_dir,
            "-P", "-F", "#{pane_id}"
        ])
        codex_pane = result.stdout.strip() if result.stdout else None

    # Set pane titles using pane IDs
    if claude_pane:
        run_command([
            "tmux", "select-pane", "-t", claude_pane,
            "-T", "Claude"
        ])
    if codex_pane:
        run_command([
            "tmux", "select-pane", "-t", codex_pane,
            "-T", "Codex"
        ])

    # Adjust pane sizes (left: 60%, right: 40%) using numeric width
    window_width = get_window_width(target_session)
    left_width = int(window_width * 0.6)
    if claude_pane:
        run_command([
            "tmux", "resize-pane", "-t", claude_pane,
            "-x", str(left_width)
        ])

    # Start Codex in right pane using dynamic pane ID
    if codex_pane:
        run_command([
            "tmux", "send-keys", "-t", codex_pane,
            "echo '=== Codex Workspace ==='", "C-m"
        ])
        run_command([
            "tmux", "send-keys", "-t", codex_pane,
            "codex --full-auto", "C-m"
        ])

    # Keep focus on left pane (Claude session)
    if claude_pane:
        run_command(["tmux", "select-pane", "-t", claude_pane])

    # Save pane info for communication scripts
    if claude_pane and codex_pane:
        save_pane_info(target_session, claude_pane, codex_pane)

    # Save session metadata
    sessions = load_sessions()
    sessions[target_session] = {
        "created": datetime.now().isoformat(),
        "working_dir": working_dir,
        "status": "active",
        "claude_pane": claude_pane,
        "codex_pane": codex_pane
    }
    save_sessions(sessions)

    # Save current session name for collab_communicate.py
    current_session_file = COLLAB_DIR / "current_session.txt"
    current_session_file.write_text(target_session)

    if inside_tmux:
        print(f"\n✓ Codex pane added successfully")
    else:
        print(f"\n✓ Session '{target_session}' created successfully")
        print(f"\nTo attach to the session:")
        print(f"  tmux attach-session -t {target_session}")

    print(f"\nPanes:")
    print(f"  Left  ({claude_pane or 'N/A'}): Claude - Implementation workspace")
    print(f"  Right ({codex_pane or 'N/A'}): Codex - Review workspace")
    print(f"\nKey bindings:")
    print(f"  Ctrl+b → o   : Switch between panes")
    print(f"  Ctrl+b → [   : Enter scroll mode (q to exit)")
    print(f"\nCommunication:")
    print(f"  Send to Codex: python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --type IMPLEMENT --message 'your message' --notify")
    print(f"  Read response: python3 ~/.claude/skills/codex-collab/scripts/collab_communicate.py --agent claude --action read")

def save_session(session_name: str):
    """Save session state."""
    ensure_collab_dir()
    
    if not session_exists(session_name):
        print(f"Error: Session '{session_name}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    sessions = load_sessions()
    if session_name in sessions:
        sessions[session_name]["last_saved"] = datetime.now().isoformat()
        save_sessions(sessions)
        print(f"✓ Session state saved: {session_name}")
    else:
        print(f"Warning: Session metadata not found for '{session_name}'")

def restore_session(session_name: str):
    """Restore and attach to a session."""
    ensure_collab_dir()
    
    if not session_exists(session_name):
        print(f"Error: Session '{session_name}' does not exist", file=sys.stderr)
        print(f"Use --init to create a new session", file=sys.stderr)
        sys.exit(1)
    
    print(f"Attaching to session: {session_name}")
    
    # Attach to session (this will replace current process)
    subprocess.run(["tmux", "attach-session", "-t", session_name])

def end_session(session_name: str):
    """End a collaboration session."""
    ensure_collab_dir()
    
    if not session_exists(session_name):
        print(f"Warning: Session '{session_name}' does not exist")
        return
    
    # Kill tmux session
    run_command(["tmux", "kill-session", "-t", session_name])
    
    # Update session metadata
    sessions = load_sessions()
    if session_name in sessions:
        sessions[session_name]["status"] = "ended"
        sessions[session_name]["ended"] = datetime.now().isoformat()
        save_sessions(sessions)
    
    print(f"✓ Session ended: {session_name}")

def list_sessions():
    """List all collaboration sessions."""
    ensure_collab_dir()
    
    sessions = load_sessions()
    
    if not sessions:
        print("No collaboration sessions found.")
        return
    
    print(f"\n{'='*60}")
    print("Collaboration Sessions")
    print(f"{'='*60}\n")
    
    for name, metadata in sessions.items():
        status = metadata.get("status", "unknown")
        created = metadata.get("created", "unknown")
        working_dir = metadata.get("working_dir", "unknown")
        
        active = session_exists(name)
        status_marker = "🟢" if active else "⚫"
        
        print(f"{status_marker} {name}")
        print(f"   Created: {created}")
        print(f"   Working Dir: {working_dir}")
        print(f"   Status: {status} ({'active' if active else 'inactive'})")
        print()

def main():
    parser = argparse.ArgumentParser(
        description="tmux session management for Code and Codex collaboration"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize a new collaboration session"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save current session state"
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore and attach to a session"
    )
    parser.add_argument(
        "--end",
        action="store_true",
        help="End a collaboration session"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all sessions"
    )
    parser.add_argument(
        "--session-name",
        default="claude-codex-dev",
        help="Name of the tmux session (default: claude-codex-dev)"
    )
    parser.add_argument(
        "--working-dir",
        help="Working directory for the session (default: current directory)"
    )
    
    args = parser.parse_args()
    
    if args.init:
        init_session(args.session_name, args.working_dir)
    elif args.save:
        save_session(args.session_name)
    elif args.restore:
        restore_session(args.session_name)
    elif args.end:
        end_session(args.session_name)
    elif args.list:
        list_sessions()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
