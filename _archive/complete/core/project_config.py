"""
Project Config - Loads project-specific instructions (like CLAUDE.md/AGENTS.md)
"""
import os
from typing import Optional, List


class ProjectConfig:
    """Load project-specific instructions."""

    # Files to search for (in order of priority)
    INSTRUCTION_FILES = [
        "AGENTS.md",
        "CLAUDE.md",
        ".agents/AGENTS.md",
        ".claude/CLAUDE.md",
        "PROJECT.md",
        "AI_INSTRUCTIONS.md",
    ]

    def __init__(self, workspace_root: str):
        """
        Initialize project config.

        Args:
            workspace_root: Root directory of the project
        """
        self.workspace_root = workspace_root
        self.instructions: Optional[str] = None
        self.instruction_file: Optional[str] = None
        self._load_instructions()

    def _load_instructions(self):
        """Find and load project instruction file."""
        for filename in self.INSTRUCTION_FILES:
            path = os.path.join(self.workspace_root, filename)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.instructions = f.read()
                    self.instruction_file = filename
                    return
                except IOError:
                    continue

    def get_instructions(self) -> str:
        """
        Get project instructions for system prompt.

        Returns:
            Formatted instructions or empty string
        """
        if not self.instructions:
            return ""

        return f"""
## Project Instructions (from {self.instruction_file})

{self.instructions}

---
"""

    def has_instructions(self) -> bool:
        """Check if project has instruction file."""
        return self.instructions is not None

    def reload(self):
        """Reload instructions from file."""
        self.instructions = None
        self.instruction_file = None
        self._load_instructions()

    @staticmethod
    def create_template(workspace_root: str, filename: str = "AGENTS.md") -> str:
        """
        Create template instruction file.

        Args:
            workspace_root: Root directory
            filename: Template filename

        Returns:
            Path to created file
        """
        template = """# Project Instructions

## Code Style
- Use descriptive variable names
- Add comments for complex logic
- Follow existing patterns in codebase

## Conventions
- [Add your project conventions here]

## Important Files
- [List important files the AI should know about]

## Testing
- [Describe how to run tests]

## Important Notes
- [Add important context for the AI here]
"""
        path = os.path.join(workspace_root, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(template)
        return path

    def get_file_path(self) -> Optional[str]:
        """Get full path to instruction file."""
        if self.instruction_file:
            return os.path.join(self.workspace_root, self.instruction_file)
        return None
