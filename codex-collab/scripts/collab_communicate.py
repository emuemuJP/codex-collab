#!/usr/bin/env python3
"""
Inter-agent communication handler for Code and Codex collaboration.
"""

import fcntl
import json
import os
import sys
import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

COLLAB_DIR = Path("/tmp/codex_collab")
MESSAGES_FILE = COLLAB_DIR / "messages.json"
HISTORY_FILE = COLLAB_DIR / "history.json"
SESSION_FILE = COLLAB_DIR / "current_session.txt"
PANE_INFO_FILE = COLLAB_DIR / "pane_info.json"

MESSAGE_TYPES = ["IMPLEMENT", "REVIEW", "SUGGEST", "APPROVE", "QUESTION", "COMPLETE"]


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


def ensure_collab_dir():
    """Ensure collaboration directory exists."""
    COLLAB_DIR.mkdir(exist_ok=True, parents=True)
    if not MESSAGES_FILE.exists():
        atomic_write_json(MESSAGES_FILE, [])
    if not HISTORY_FILE.exists():
        atomic_write_json(HISTORY_FILE, [])


def load_messages() -> List[Dict[str, Any]]:
    """Load current messages."""
    return safe_load_json(MESSAGES_FILE, [])


def save_messages(messages: List[Dict[str, Any]]):
    """Save messages to file."""
    atomic_write_json(MESSAGES_FILE, messages)


def load_history() -> List[Dict[str, Any]]:
    """Load message history."""
    return safe_load_json(HISTORY_FILE, [])


def save_history(history: List[Dict[str, Any]]):
    """Save message history."""
    atomic_write_json(HISTORY_FILE, history)

def save_current_session(session_name: str):
    """Save current session name to file."""
    ensure_collab_dir()
    SESSION_FILE.write_text(session_name)


def get_current_session() -> Optional[str]:
    """Get current session name from file."""
    try:
        if SESSION_FILE.exists():
            session = SESSION_FILE.read_text().strip()
            if session:
                return session
    except Exception:
        pass
    return None


def get_active_session() -> Optional[str]:
    """Get session from file, or find active codex-collab session."""
    # First try to read from saved session file
    saved = get_current_session()
    if saved:
        # Verify session still exists
        result = subprocess.run(
            ["tmux", "has-session", "-t", saved],
            capture_output=True, check=False
        )
        if result.returncode == 0:
            return saved

    # Fallback: find any codex-collab session with 2 panes
    try:
        result = subprocess.run(
            ["tmux", "ls", "-F", "#{session_name}"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            for session in result.stdout.strip().split('\n'):
                if 'codex-collab' in session:
                    pane_result = subprocess.run(
                        ["tmux", "list-panes", "-t", session],
                        capture_output=True, text=True, check=False
                    )
                    pane_count = len(pane_result.stdout.strip().split('\n'))
                    if pane_count >= 2:
                        return session
    except Exception:
        pass
    return None

def check_tmux_installed() -> bool:
    """Check if tmux is installed."""
    result = subprocess.run(["which", "tmux"], capture_output=True, check=False)
    return result.returncode == 0


def get_pane_info(session_name: str) -> Optional[Dict[str, str]]:
    """Get pane IDs for a session from pane_info.json."""
    pane_info = safe_load_json(PANE_INFO_FILE, {})
    return pane_info.get(session_name)


def get_pane_target(session_name: str, role: str) -> str:
    """Get the pane target (ID or fallback) for a role.

    Args:
        session_name: The tmux session name
        role: Either 'claude' or 'codex'

    Returns:
        Pane ID if available, otherwise fallback to :0.0 or :0.1
    """
    pane_info = get_pane_info(session_name)
    if pane_info:
        key = f"{role}_pane"
        if key in pane_info:
            return pane_info[key]

    # Fallback to traditional format
    return f"{session_name}:0.0" if role == "claude" else f"{session_name}:0.1"


def sanitize_message(message: str, max_length: int = 80) -> str:
    """Sanitize message for tmux send-keys.

    - Truncate to max_length
    - Remove/escape control characters
    - Escape quotes
    """
    # Remove newlines and control characters
    sanitized = ''.join(c if c.isprintable() and c != '\n' else ' ' for c in message)
    # Truncate
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    # Escape quotes
    sanitized = sanitized.replace('"', '\\"').replace("'", "\\'")
    return sanitized


def notify_codex(session_name: str, message: str):
    """Send notification to Codex pane via tmux."""
    if not check_tmux_installed():
        print("⚠ tmux is not installed, cannot notify", file=sys.stderr)
        return False

    try:
        # Get dynamic pane target
        pane_target = get_pane_target(session_name, "codex")

        # Sanitize message for display
        short_msg = sanitize_message(message)
        prompt = f"Claudeから新しいメッセージ: {short_msg} /tmp/codex_collab/messages.json を読んで対応してください。"

        # Send the prompt text using -l for literal string
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_target, "-l", prompt],
            check=False
        )
        # Send Enter key separately to execute
        time.sleep(0.3)
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_target, "Enter"],
            check=False
        )
        print(f"✓ Codex に通知しました (pane: {pane_target})")
        return True
    except Exception as e:
        print(f"⚠ Codex への通知に失敗: {e}", file=sys.stderr)
        return False


def notify_claude(session_name: str, message: str):
    """Send notification to Claude pane via tmux."""
    if not check_tmux_installed():
        print("⚠ tmux is not installed, cannot notify", file=sys.stderr)
        return False

    try:
        # Get dynamic pane target
        pane_target = get_pane_target(session_name, "claude")

        # Sanitize message for display
        short_msg = sanitize_message(message)
        prompt = f"Codexから新しいメッセージ: {short_msg} /tmp/codex_collab/messages.json を読んで対応してください。"

        # Send the prompt text using -l for literal string
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_target, "-l", prompt],
            check=False
        )
        # Send Enter key separately to execute
        time.sleep(0.3)
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_target, "Enter"],
            check=False
        )
        print(f"✓ Claude に通知しました (pane: {pane_target})")
        return True
    except Exception as e:
        print(f"⚠ Claude への通知に失敗: {e}", file=sys.stderr)
        return False

def wait_for_response(agent: str, timeout: int = 60, poll_interval: int = 3) -> Optional[Dict[str, Any]]:
    """Wait for a response from another agent."""
    other_agent = "codex" if agent == "claude" else "claude"
    start_time = time.time()
    initial_messages = load_messages()
    initial_count = len([m for m in initial_messages if m.get("agent") == other_agent])

    print(f"⏳ {other_agent} からの応答を待っています... (タイムアウト: {timeout}秒)")

    while time.time() - start_time < timeout:
        time.sleep(poll_interval)
        current_messages = load_messages()
        current_count = len([m for m in current_messages if m.get("agent") == other_agent])

        if current_count > initial_count:
            # New message received
            new_messages = [m for m in current_messages if m.get("agent") == other_agent]
            latest = new_messages[-1]
            print(f"\n✓ {other_agent} から応答がありました!")
            print(f"  Type: {latest.get('type')}")
            print(f"  Message: {latest.get('message')}")
            return latest

        elapsed = int(time.time() - start_time)
        print(f"  ... 待機中 ({elapsed}秒経過)", end='\r')

    print(f"\n⚠ タイムアウト: {timeout}秒以内に応答がありませんでした")
    return None

def write_message(
    agent: str,
    msg_type: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    notify: bool = False,
    session_name: Optional[str] = None
):
    """Write a message from an agent."""
    ensure_collab_dir()

    if msg_type not in MESSAGE_TYPES:
        print(f"Warning: Unknown message type '{msg_type}'. Valid types: {', '.join(MESSAGE_TYPES)}")

    msg = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "type": msg_type,
        "message": message,
        "context": context or {}
    }

    messages = load_messages()
    messages.append(msg)
    save_messages(messages)

    # Also append to history
    history = load_history()
    history.append(msg)
    save_history(history)

    print(f"✓ Message sent by {agent}")
    print(f"  Type: {msg_type}")
    print(f"  Message: {message}")

    # Notify the other agent if requested
    if notify:
        session = session_name or get_active_session()
        if session:
            if agent == "claude":
                notify_codex(session, message)
            elif agent == "codex":
                notify_claude(session, message)
        else:
            print("⚠ アクティブなセッションが見つかりません。通知をスキップします。")

def read_messages(agent: str, unread_only: bool = True, limit: Optional[int] = None):
    """Read messages for an agent."""
    ensure_collab_dir()
    
    messages = load_messages()
    
    if not messages:
        print("No messages available.")
        return
    
    # Filter out messages from the same agent if unread_only
    if unread_only:
        messages = [m for m in messages if m.get("agent") != agent]
    
    if limit:
        messages = messages[-limit:]
    
    if not messages:
        print("No new messages.")
        return
    
    print(f"\n{'='*60}")
    print(f"Messages for {agent} ({len(messages)} unread)")
    print(f"{'='*60}\n")
    
    for msg in messages:
        print(f"[{msg['timestamp']}] {msg['agent']} → {msg['type']}")
        print(f"  {msg['message']}")
        if msg.get('context'):
            print(f"  Context: {json.dumps(msg['context'], indent=4)}")
        print()
    
    return messages

def clear_messages():
    """Clear all current messages (moves to history)."""
    ensure_collab_dir()
    save_messages([])
    print("✓ Messages cleared")

def show_history(limit: Optional[int] = None):
    """Show message history."""
    ensure_collab_dir()
    
    history = load_history()
    
    if not history:
        print("No message history.")
        return
    
    if limit:
        history = history[-limit:]
    
    print(f"\n{'='*60}")
    print(f"Message History ({len(history)} messages)")
    print(f"{'='*60}\n")
    
    for msg in history:
        print(f"[{msg['timestamp']}] {msg['agent']} → {msg['type']}")
        print(f"  {msg['message']}")
        print()

def main():
    parser = argparse.ArgumentParser(
        description="Inter-agent communication for Code and Codex"
    )
    parser.add_argument(
        "--agent",
        choices=["claude", "codex"],
        help="Agent sending or reading messages"
    )
    parser.add_argument(
        "--action",
        choices=["write", "read", "clear", "history", "wait"],
        default="write",
        help="Action to perform"
    )
    parser.add_argument(
        "--type",
        choices=MESSAGE_TYPES,
        help="Message type (for write action)"
    )
    parser.add_argument(
        "--message",
        help="Message content (for write action)"
    )
    parser.add_argument(
        "--context",
        help="Additional context as JSON string"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of messages to display"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Read all messages including own (for read action)"
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Notify Codex via tmux after sending message (for write action)"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for response after sending message"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds for waiting (default: 60)"
    )
    parser.add_argument(
        "--session",
        help="tmux session name (auto-detected if not specified)"
    )

    args = parser.parse_args()

    if args.action == "write":
        if not all([args.agent, args.type, args.message]):
            parser.error("write action requires --agent, --type, and --message")

        context = None
        if args.context:
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in --context", file=sys.stderr)
                sys.exit(1)

        write_message(
            args.agent,
            args.type,
            args.message,
            context,
            notify=args.notify,
            session_name=args.session
        )

        # Wait for response if requested
        if args.wait:
            wait_for_response(args.agent, timeout=args.timeout)

    elif args.action == "read":
        if not args.agent:
            parser.error("read action requires --agent")

        read_messages(args.agent, unread_only=not args.all, limit=args.limit)

    elif args.action == "clear":
        clear_messages()

    elif args.action == "history":
        show_history(limit=args.limit)

    elif args.action == "wait":
        if not args.agent:
            parser.error("wait action requires --agent")
        wait_for_response(args.agent, timeout=args.timeout)

if __name__ == "__main__":
    main()
