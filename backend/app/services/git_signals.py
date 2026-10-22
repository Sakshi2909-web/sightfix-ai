from pathlib import Path
from typing import Dict, List, Any
import git


class GitSignalService:
    def get_recent_churn(self, repo_dir: Path, max_commits: int = 15) -> Dict[str, float]:
        """Calculates a recency/churn score (0.0 - 1.0) for files modified in recent commits."""
        churn_scores: Dict[str, float] = {}
        try:
            repo = git.Repo(repo_dir)
            commits = list(repo.iter_commits(max_count=max_commits))
            total = len(commits)
            if total == 0:
                return {}

            for idx, commit in enumerate(commits):
                # More recent commits get higher weight
                weight = 1.0 - (idx / total)
                # Get modified files in commit
                diffs = commit.stats.files.keys()
                for fpath in diffs:
                    norm = fpath.replace("\\", "/")
                    churn_scores[norm] = max(churn_scores.get(norm, 0.0), weight)
        except Exception:
            # If not a git repo or error, return empty dict
            pass

        return churn_scores

    def get_commit_summary_for_file(self, repo_dir: Path, file_path: str) -> str | None:
        """Returns the most recent commit message touching file_path."""
        try:
            repo = git.Repo(repo_dir)
            commits = list(repo.iter_commits(paths=file_path, max_count=1))
            if commits:
                c = commits[0]
                return f"Modified in {c.hexsha[:7]} by {c.author.name}: '{c.message.strip().splitlines()[0]}'"
        except Exception:
            pass
        return None


git_signals = GitSignalService()
