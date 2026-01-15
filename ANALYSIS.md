# codex-collab 改善分析レポート

## 1. 重大な問題 (Critical Issues)

### 1.1 JSON同時書き込みによるデータ破損リスク
**場所**: `collab_communicate.py:70-72`, `collab_communicate.py:75-77`

```python
# 現在のコード（問題あり）
messages = load_messages()  # Agent A と Agent B が同時に読み込み
messages.append(msg)         # それぞれがメッセージ追加
save_messages(messages)      # 後から保存した方が勝ち → 片方のメッセージ消失
```

**修正案**: ファイルロックを追加
```python
import fcntl

def save_messages_atomic(messages):
    with open(MESSAGES_FILE, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # 排他ロック
        json.dump(messages, f, indent=2)
        fcntl.flock(f, fcntl.LOCK_UN)
```

### 1.2 タイムアウト機能が未実装
**問題**: SKILL.mdに「60秒タイムアウトでsimple modeにフォールバック」と記載されているが、コードには実装なし

**SKILL.mdの記述**:
> If no response within 60 seconds, automatically switch to simple mode

**実装案**:
```python
def wait_for_response(agent: str, timeout: int = 60) -> Optional[Dict]:
    """タイムアウト付きで相手のメッセージを待つ"""
    start = time.time()
    while time.time() - start < timeout:
        messages = read_messages(agent, unread_only=True)
        if messages:
            return messages[-1]
        time.sleep(2)  # ポーリング間隔
    return None  # タイムアウト
```

### 1.3 セキュリティ：パーミッションが緩い
**場所**: `session_manager.py:19`, `collab_communicate.py:22`

```python
# 現在のコード
COLLAB_DIR.mkdir(exist_ok=True, parents=True)  # デフォルトパーミッション
```

**問題**: `/tmp/codex_collab/`が他のユーザーから読み取り可能

**修正案**:
```python
COLLAB_DIR.mkdir(exist_ok=True, parents=True, mode=0o700)
```

---

## 2. 中程度の問題 (Medium Issues)

### 2.1 履歴の無制限成長
**場所**: `collab_communicate.py:75-77`

```python
history = load_history()
history.append(msg)  # 無制限に追加され続ける
save_history(history)
```

**修正案**: 最大件数を設定
```python
MAX_HISTORY = 1000

def save_history(history):
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]  # 古いものを削除
    HISTORY_FILE.write_text(json.dumps(history, indent=2))
```

### 2.2 subprocess エラー未処理
**場所**: `session_manager.py:168`

```python
# 現在のコード（エラー処理なし）
subprocess.run(["tmux", "attach-session", "-t", session_name])
```

**修正案**:
```python
try:
    subprocess.run(["tmux", "attach-session", "-t", session_name], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error attaching to session: {e}", file=sys.stderr)
    sys.exit(1)
```

### 2.3 tmux resize構文の問題
**場所**: `session_manager.py:105-108`

```python
# 現在のコード（一部のtmuxバージョンで失敗する可能性）
run_command([
    "tmux", "resize-pane", "-t", f"{session_name}:0.0",
    "-x", "60%"
])
```

**修正案**: パーセント指定の代替
```python
# tmux 2.9以降
run_command([
    "tmux", "resize-pane", "-t", f"{session_name}:0.0",
    "-p", "60"  # -p でパーセント指定
])
```

### 2.4 run_command の戻り値型不整合
**場所**: `session_manager.py:44-49`

```python
except subprocess.CalledProcessError as e:
    # ...
    return e  # CompletedProcess ではなく Exception を返している
```

**修正案**:
```python
except subprocess.CalledProcessError as e:
    print(f"Error running command: {' '.join(cmd)}", file=sys.stderr)
    if check:
        sys.exit(1)
    return e.returncode  # または None を返す
```

---

## 3. ドキュメントの問題

### 3.1 未実装機能の記載
SKILL.mdで言及されているが実装されていない機能:
- 60秒タイムアウト
- simple modeへの自動フォールバック
- Codex応答のポーリング

### 3.2 記載が不足している内容
- セキュリティに関する注意事項
- `/tmp/codex_collab/`のクリーンアップ方法
- 同時に複数セッションを実行する際の注意
- メッセージサイズの制限

---

## 4. 追加すべき機能

### 4.1 メッセージID (重複防止)
```python
import uuid

msg = {
    "id": str(uuid.uuid4()),  # ユニークID追加
    "timestamp": datetime.now().isoformat(),
    "agent": agent,
    # ...
}
```

### 4.2 既読管理
```python
def mark_as_read(agent: str, message_ids: List[str]):
    """メッセージを既読としてマーク"""
    messages = load_messages()
    for msg in messages:
        if msg["id"] in message_ids:
            msg.setdefault("read_by", []).append(agent)
    save_messages(messages)
```

### 4.3 クリーンアップコマンド
```python
def cleanup_old_sessions():
    """古いセッションファイルをクリーンアップ"""
    # 7日以上前のセッションを削除
    pass
```

---

## 5. 改善優先度

| 優先度 | 問題 | 作業量 |
|--------|------|--------|
| 高 | ファイルロック追加 | 小 |
| 高 | タイムアウト実装 | 中 |
| 高 | パーミッション修正 | 小 |
| 中 | 履歴ローテーション | 小 |
| 中 | subprocess エラー処理 | 小 |
| 中 | ドキュメント更新 | 中 |
| 低 | メッセージID追加 | 小 |
| 低 | 既読管理 | 中 |

---

## 6. ファイル構成

```
~/.claude/skills/codex-collab/
├── SKILL.md                    (620行) - メインドキュメント
├── scripts/
│   ├── session_manager.py      (273行) - セッション管理
│   └── collab_communicate.py   (213行) - メッセージング
├── references/
│   ├── communication_protocol.md (233行)
│   └── best_practices.md       (316行)
└── assets/                     (空)
```
