# クイックスタートガイド

## 🚀 5分で始める

### デフォルト：tmuxモード

#### 1. tmuxインストール

```bash
# macOS
brew install tmux

# Linux
sudo apt-get install tmux

# 確認
tmux -V
```

#### 2. コラボレーション開始

Claudeに言う：
```
「CodexでJWT認証を作って」
```

Claudeが自動的に：
1. ✅ tmuxセッション作成
2. ✅ 通信インフラ構築  
3. ✅ 次のステップをガイド

#### 3. 2つのペインで作業

**ターミナル1（Code - 実装）:**
```bash
tmux attach-session -t jwt-auth
# 左ペインを選択
# この会話が続く
```

**ターミナル2（Codex - レビュー）:**
```bash
tmux attach-session -t jwt-auth
# 右ペインを選択
# 新しいClaude会話を開始
```

#### 4. メッセージ通信

**Code（左）:**
```bash
# ガイダンス要求
python scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "JWT実装の設計アドバイスを"

# 60秒待機...

# Codexの応答を読む
python scripts/collab_communicate.py --agent claude --action read
```

**Codex（右）:**
```bash
# メッセージ読む
python scripts/collab_communicate.py --agent codex --action read

# 応答
python scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "PyJWT推奨。RS256、15分有効期限"
```

---

### ⚡ 60秒タイムアウト（自動フォールバック）

Codexが60秒以内に応答しない場合、自動的に簡易モードに：

```
⚠️ Codexから応答なし（60秒）
簡易モードに切り替えます

[Codexモード 🔍]
アーキテクチャガイダンス...

[Codeモード 🔧]
実装中...
```

開発は止まりません！Codexが後で参加可能。

---

## 📝 チートシート

### メッセージタイプ

| タイプ | 用途 | 使用者 |
|--------|------|--------|
| IMPLEMENT | ガイダンス要求 | Code |
| REVIEW | レビュー依頼 | Code |
| SUGGEST | 提案・フィードバック | Codex |
| APPROVE | 承認 | Codex |
| QUESTION | 質問 | 両方 |
| COMPLETE | 完了報告 | Code |

### tmux基本操作

| 操作 | コマンド |
|------|----------|
| ペイン切り替え | `Ctrl+b` → `o` |
| デタッチ | `Ctrl+b` → `d` |
| コピーモード | `Ctrl+b` → `[` |
| ペーストモード | `Ctrl+b` → `]` |
| ヘルプ | `Ctrl+b` → `?` |

### よく使うスクリプト

```bash
# 読む
python scripts/collab_communicate.py --agent [claude|codex] --action read

# 書く
python scripts/collab_communicate.py --agent [claude|codex] --type [TYPE] --message "..."

# 履歴
python scripts/collab_communicate.py --action history --limit 10

# クリア
python scripts/collab_communicate.py --action clear
```

---

## 💡 ヒント

### いつtmuxモードを使う？

✅ **使うべき時:**
- 長期プロジェクト（複数日）
- 複雑な機能開発
- 詳細なコードレビューが必要
- チーム開発

❌ **使わない時:**
- クイックな修正
- プロトタイピング
- tmux未インストール

### 効率的なワークフロー

1. **小さく始める**: 1機能ずつ開発
2. **頻繁にレビュー**: 大きな変更前に確認
3. **履歴を活用**: 過去の決定を参照
4. **セッション永続化**: `Ctrl+b d`でデタッチ、後で再開

### トラブル時

```bash
# 何か変な時は再初期化
python scripts/session_manager.py --end --session-name problematic
python scripts/session_manager.py --init --session-name fresh-start

# メッセージが詰まったらクリア
python scripts/collab_communicate.py --action clear
```

---

## 🎯 実践例

### 例1: API開発（15分）

```bash
# セッション開始
python scripts/session_manager.py --init --session-name api-dev
tmux attach-session -t api-dev

# [左] ガイダンス要求
python scripts/collab_communicate.py --agent claude --type IMPLEMENT \
  --message "ユーザー登録APIの設計"

# [右] 読んで返答
python scripts/collab_communicate.py --agent codex --action read
python scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "POST /api/register: email validation, password strength, rate limiting"

# [左] 実装
# ... コーディング ...

# [左] レビュー依頼
python scripts/collab_communicate.py --agent claude --type REVIEW \
  --message "登録API完成"

# [右] レビュー
python scripts/collab_communicate.py --agent codex --type APPROVE \
  --message "Good to go!"
```

### 例2: バグ修正（5分）

```bash
# [左] 問題報告
python scripts/collab_communicate.py --agent claude --type QUESTION \
  --message "メモリリークしてる。どこを見るべき？"

# [右] アドバイス
python scripts/collab_communicate.py --agent codex --type SUGGEST \
  --message "Check: 1) Event listeners, 2) Circular refs, 3) Cache growth"

# [左] 修正
# ... デバッグ & 修正 ...

# [左] 完了報告
python scripts/collab_communicate.py --agent claude --type COMPLETE \
  --message "リスナークリーンアップ追加。メモリ安定"
```

---

## 🆘 ヘルプ

詳細は以下を参照：
- `SKILL.md` - 完全なドキュメント
- `references/communication_protocol.md` - プロトコル詳細
- `references/best_practices.md` - ベストプラクティス

問題があれば：
1. `tmux ls` でセッション確認
2. `/tmp/code_codex_collab/` のファイル確認
3. 再初期化を試す
