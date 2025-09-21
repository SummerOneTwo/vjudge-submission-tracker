import argparse
import json
import os
import shutil
import datetime
from typing import Dict, Any

ALLOW_ERROR = "No recent submissions found"


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def backup_file(path: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{path}.bak-{ts}"
    shutil.copy(path, backup_path)
    return backup_path


def clean_file(path: str, dry_run: bool) -> Dict[str, int]:
    try:
        data = load_json(path)
    except FileNotFoundError:
        return {"kept": 0, "removed": 0, "total": 0}

    if not isinstance(data, dict):
        print(f"[WARN] {path} 不是 dict，跳过")
        return {"kept": 0, "removed": 0, "total": 0}

    total = len(data)
    kept_dict = {}
    for k, v in data.items():
        if not isinstance(v, dict):
            # 异常结构直接过滤
            continue
        if v.get("success") is True or v.get("error") == ALLOW_ERROR:
            kept_dict[k] = v

    kept = len(kept_dict)
    removed = total - kept

    if not dry_run:
        save_json(path, kept_dict)
    else:
        print(f"[DRY-RUN] 将保留 {kept} 条，移除 {removed} 条 (文件: {path})")

    return {"kept": kept, "removed": removed, "total": total}


def main():
    parser = argparse.ArgumentParser(description="清理 success_problems.json 中不应存在的失败记录")
    parser.add_argument("--dirs", nargs="*", default=["atcoder", "codeforces", "luogu"], help="需要清理的目录列表")
    parser.add_argument("--dry-run", action="store_true", help="只显示将进行的变更，不写回文件")
    parser.add_argument("--no-backup", action="store_true", help="不生成 .bak 备份文件")

    args = parser.parse_args()

    summary = []

    for d in args.dirs:
        path = os.path.join(d, "success_problems.json")
        if not os.path.exists(path):
            print(f"[SKIP] {path} 不存在")
            continue
        if not args.no_backup and not args.dry_run:
            backup_path = backup_file(path)
            print(f"[BACKUP] 已备份 -> {backup_path}")
        stats = clean_file(path, args.dry_run)
        summary.append((path, stats))
        if not args.dry_run:
            print(f"[CLEAN] {path}: 保留 {stats['kept']} / {stats['total']} (移除 {stats['removed']})")

    print("\n========== 汇总 ==========")
    for path, s in summary:
        print(f"{path}: 保留 {s['kept']} / {s['total']} (移除 {s['removed']})")

    if args.dry_run:
        print("(dry-run 模式未修改任何文件)")


if __name__ == "__main__":
    main()
